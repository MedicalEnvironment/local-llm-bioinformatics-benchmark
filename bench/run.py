"""Run the benchmark against local llama.cpp models.

usage: run.py embed                      # build RAG index once (EmbeddingGemma)
       run.py model NAME GGUF [extra llama-server args...]
"""
import json, os, re, subprocess, sys, tempfile, threading, time, urllib.request
from pathlib import Path
import numpy as np
import tasks

# Paths can be overridden so the same harness runs on the laptop, Azure and the HPC container.
HOME = Path(os.environ.get("LLM_HOME", Path.home() / "llm"))
MODELS = Path(os.environ.get("LLM_MODELS", HOME / "models"))
if "LLAMA_BIN" in os.environ:
    BIN = Path(os.environ["LLAMA_BIN"]); ENV = dict(os.environ)
else:
    BIN = next((HOME / "llama.cpp").glob("llama-b*"))
    CUDART = next((HOME / "llama.cpp").glob("cudart-*"))
    ENV = dict(os.environ, LD_LIBRARY_PATH=f"{BIN}:{CUDART}")
PORT = int(os.environ.get("LLM_PORT", 8090))
BENCH = Path(__file__).parent
DATA = BENCH / "data"
RES = BENCH / "results"
RES.mkdir(exist_ok=True)
PY = os.environ.get("BENCH_PY", str(HOME / "venv/bin/python"))


def post(port, path, body, timeout=900):
    req = urllib.request.Request(f"http://127.0.0.1:{port}{path}", json.dumps(body).encode(), {"Content-Type": "application/json"})
    return json.load(urllib.request.urlopen(req, timeout=timeout))


def start_server(gguf, port, extra, log):
    cmd = [str(BIN / "llama-server"), "-m", str(gguf), "--port", str(port), "--host", "127.0.0.1", *extra]
    p = subprocess.Popen(cmd, env=ENV, stdout=open(log, "w"), stderr=subprocess.STDOUT)
    for _ in range(600):
        time.sleep(1)
        if p.poll() is not None:
            raise RuntimeError(f"server exited, see {log}")
        try:
            if json.load(urllib.request.urlopen(f"http://127.0.0.1:{port}/health", timeout=2)).get("status") == "ok":
                return p
        except Exception:
            pass
    p.kill()
    raise RuntimeError("server did not become healthy")


def gpu_mem():
    ids = ["-i", os.environ["CUDA_VISIBLE_DEVICES"]] if os.environ.get("CUDA_VISIBLE_DEVICES") else []  # only this job's GPUs on shared nodes
    o = subprocess.run(["nvidia-smi", *ids, "--query-gpu=memory.used", "--format=csv,noheader,nounits"], capture_output=True, text=True).stdout
    return sum(int(x) for x in o.split())  # summed over all visible GPUs


# ---------------- RAG index ----------------
def chunks():
    out = []
    for f in sorted((DATA / "docs").glob("*.txt")):
        paras = [p.strip() for p in f.read_text().split("\n\n") if p.strip()]
        if f.name == "genes.txt":  # one chunk per gene
            out += [(f.name, p) for p in paras]
            continue
        buf = ""
        for p in paras:
            if len(buf) + len(p) > 1200 and buf:
                out.append((f.name, buf))
                buf = buf[-300:]  # overlap
            buf += "\n" + p
        if buf:
            out.append((f.name, buf))
    return out


def embed(port, texts):
    vs = []
    for i in range(0, len(texts), 32):
        r = post(port, "/v1/embeddings", {"input": texts[i : i + 32]})
        vs += [d["embedding"] for d in sorted(r["data"], key=lambda d: d["index"])]
    v = np.array(vs, dtype=np.float32)
    return v / np.linalg.norm(v, axis=1, keepdims=True)


def build_index():
    ch = chunks()
    p = start_server(HOME / "models/embeddinggemma-300M-Q8_0.gguf", 8091, ["--embeddings", "-c", "2048", "-ub", "2048", "-ngl", "99"], RES / "embed.log")
    try:
        cv = embed(8091, [f"title: {src} | text: {t}" for src, t in ch])
        qv = embed(8091, [f"task: search result | query: {q}" for _, q, _ in tasks.RETR_TASKS])
    finally:
        p.terminate(); p.wait()
    top = {}
    for (tid, q, pat), v in zip(tasks.RETR_TASKS, qv):
        idx = np.argsort(-(cv @ v))[:5]
        top[tid] = [{"src": ch[i][0], "text": ch[i][1]} for i in idx]
    # retrieval quality independent of LLM: does any top-5 chunk contain the answer?
    hit = {tid: any(re.search(pat, c["text"]) for c in top[tid]) for tid, _, pat in tasks.RETR_TASKS}
    json.dump({"top": top, "hit": hit, "n_chunks": len(ch)}, open(RES / "rag_index.json", "w"), indent=1)
    print(f"{len(ch)} chunks; retrieval hit@5 = {sum(hit.values())}/{len(hit)}")
    print({k: v for k, v in hit.items() if not v})


# ---------------- model run ----------------
def chat(port, prompt, max_tokens=8192):
    t0 = time.time()
    r = post(port, "/v1/chat/completions", {
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens, "temperature": 0.6, "top_p": 0.95, "seed": 1})
    m = r["choices"][0]["message"]
    tm = r.get("timings", {})
    return dict(content=m.get("content") or "", reasoning=m.get("reasoning_content") or "",
                finish=r["choices"][0].get("finish_reason"), wall=round(time.time() - t0, 1),
                gen_tokens=tm.get("predicted_n"), tg_tps=tm.get("predicted_per_second"), pp_tps=tm.get("prompt_per_second"))


def extract_code(s):
    blocks = re.findall(r"```(?:python|py)?\s*\n(.*?)```", s, re.S)
    return max(blocks, key=len) if blocks else None


def run_model(name, gguf, extra):
    out = RES / f"{name}.json"
    rec = json.load(open(out)) if out.exists() else {"name": name, "gguf": gguf, "extra": extra, "items": {}}
    items = rec["items"]
    peak = [0]
    stop = threading.Event()
    def watch():
        while not stop.is_set():
            peak[0] = max(peak[0], gpu_mem()); time.sleep(1)
    base = gpu_mem()
    srv = start_server(MODELS / gguf, PORT, extra, RES / f"{name}.server.log")
    threading.Thread(target=watch, daemon=True).start()
    rag = json.load(open(RES / "rag_index.json"))["top"]
    try:
        def do(key, fn):
            if key in items:
                return
            items[key] = fn()
            json.dump(rec, open(out, "w"), indent=1)
            it = items[key]
            print(f"{name:14s} {key:26s} ok={it['ok']!s:5s} {it['wall']:6.1f}s tg={it.get('tg_tps') or 0:5.1f} tok/s  finish={it.get('finish')}", flush=True)

        T = json.load(open(DATA / "truth.json"))
        for t in tasks.SCRIPT_TASKS:
            def f(t=t):
                r = chat(PORT, t["prompt"] + "\n\n" + tasks.FMT)
                code = extract_code(r["content"])
                r["code"] = code
                if code is None:
                    r.update(ok=False, run="no code block"); return r
                with tempfile.TemporaryDirectory() as d:
                    sp = Path(d) / "s.py"; sp.write_text(code)
                    try:
                        pr = subprocess.run([PY, "-I", str(sp), *[str(DATA / "raw" / x) for x in t["files"]]], capture_output=True, text=True, timeout=120, cwd=d)
                        r.update(stdout=pr.stdout[-3000:], stderr=pr.stderr[-1500:], rc=pr.returncode)
                    except subprocess.TimeoutExpired:
                        r.update(ok=False, run="timeout"); return r
                r["ok"] = pr.returncode == 0 and tasks.score_script(t["id"], pr.stdout, T)
                return r
            do("script:" + t["id"], f)

        for tid, q, want in tasks.REASON_TASKS:
            def f(q=q, want=want):
                r = chat(PORT, q + tasks.REASON_SUFFIX); r["ok"] = tasks.score_reason(r["content"], want); r["want"] = want; return r
            do("reason:" + tid, f)

        for tid, q, pat in tasks.RETR_TASKS:
            def f(q=q, pat=pat):
                r = chat(PORT, q + tasks.RETR_SUFFIX, 8192); r["ok"] = tasks.score_retr(r["content"], pat); return r
            do("closed:" + tid, f)
            def g(tid=tid, q=q, pat=pat):
                ctx = "\n\n".join(f"[{i+1}] ({c['src']})\n{c['text']}" for i, c in enumerate(rag[tid]))
                p = f"Use the following documentation excerpts to answer the question.\n\n{ctx}\n\nQuestion: {q}"
                r = chat(PORT, p + tasks.RETR_SUFFIX, 8192); r["ok"] = tasks.score_retr(r["content"], pat); return r
            do("rag:" + tid, g)
    finally:
        stop.set()
        srv.terminate(); srv.wait()
    rec["vram_peak_mib"] = peak[0]; rec["vram_base_mib"] = base
    log = (RES / f"{name}.server.log").read_text(errors="replace")
    rec["offload_lines"] = [l for l in log.splitlines() if re.search(r"offload|fit|n_ctx\s*=|CPU_Mapped|CUDA0 model buffer", l)][:25]
    json.dump(rec, open(out, "w"), indent=1)


def bench(name, gguf, extra_bench):
    """llama-bench: raw prompt-processing and generation speed."""
    cmd = [str(BIN / "llama-bench"), "-m", str(MODELS / gguf), "-p", "512", "-n", "128", "-r", "3", "-o", "json", *extra_bench]
    r = subprocess.run(cmd, env=ENV, capture_output=True, text=True, timeout=1800)
    (RES / f"{name}.bench.json").write_text(r.stdout or r.stderr)
    print(r.stdout[-1500:] or r.stderr[-1500:])


if __name__ == "__main__":
    if sys.argv[1] == "embed":
        build_index()
    elif sys.argv[1] == "model":
        run_model(sys.argv[2], sys.argv[3], sys.argv[4:])
    elif sys.argv[1] == "bench":
        bench(sys.argv[2], sys.argv[3], sys.argv[4:])
