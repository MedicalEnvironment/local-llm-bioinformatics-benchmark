#!/bin/bash
# Run remaining models sequentially once downloaded+verified and the GPU is free, then llama-bench all.
cd ~/llm/bench
PY=~/llm/venv/bin/python
waitfor() {  # wait for verified gguf
  until [ -f ~/llm/models/$1 ] && grep " $1\$" ~/llm/models/sums.txt | (cd ~/llm/models && sha256sum -c --quiet); do sleep 30; done
}
idle() { while pgrep -f "run.py model" >/dev/null; do sleep 20; done; }
COMMON="-c 16384 -fa on --fit on --reasoning-budget 6144"
for spec in "qwen3.5-9b Qwen3.5-9B-Q4_K_M.gguf" "gemma4-e4b gemma-4-E4B-it-qat-UD-Q4_K_XL.gguf"; do
  set -- $spec; waitfor $2; idle
  echo "$(date +%T) start $1"; $PY -u run.py model $1 $2 $COMMON 2>&1 | tee -a results/$1.progress
done
idle
for spec in "qwen3.5-9b Qwen3.5-9B-Q4_K_M.gguf" "gemma4-e4b gemma-4-E4B-it-qat-UD-Q4_K_XL.gguf"; do
  set -- $spec; echo "$(date +%T) bench $1"; $PY run.py bench $1 $2 -fa on -fitt 512
done
echo ALL DONE
# Re-run items truncated by the old 4096-token retrieval cap (run.py skips items still present).
idle
$PY - <<'PY'
import json, glob
for f in glob.glob("results/*.json"):
    if f.endswith(("rag_index.json", ".bench.json")): continue
    d = json.load(open(f)); bad = [k for k, v in d["items"].items() if k.split(":")[0] in ("closed", "rag") and v.get("finish") == "length"]
    for k in bad: del d["items"][k]
    json.dump(d, open(f, "w"), indent=1); print(f, "rerun:", bad)
PY
for spec in "qwen3.5-9b Qwen3.5-9B-Q4_K_M.gguf" "gemma4-e4b gemma-4-E4B-it-qat-UD-Q4_K_XL.gguf"; do
  set -- $spec; echo "$(date +%T) start rerun $1"; $PY -u run.py model $1 $2 $COMMON 2>&1 | tee -a results/$1.progress
done
echo "RERUN DONE"
