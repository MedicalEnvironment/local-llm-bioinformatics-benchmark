"""Draw the README figures from bench/results/*.json as static SVGs (light and dark variants) into docs/figures/.
Colours: validated categorical palette (adjacent CVD dE >= 8.4 in both modes). Rerun: python bench/make_figures.py"""
import json, statistics
from pathlib import Path
from xml.sax.saxutils import escape

B = Path(__file__).parent; OUT = B.parent / "docs/figures"; OUT.mkdir(parents=True, exist_ok=True)
RUNS = [("hpc-qwen3.5-122b-a10b", "Qwen3.5-122B-A10B", "RTU HPC · 2× L40S"),
        ("t4-qwen3.5-35b-a3b", "Qwen3.5-35B-A3B", "Azure · T4"),
        ("t4-gpt-oss-20b", "gpt-oss-20b", "Azure · T4"),
        ("hpc-qwen3.5-9b", "Qwen3.5-9B", "RTU HPC · L40S"),
        ("t4-qwen3.5-9b", "Qwen3.5-9B", "Azure · T4"),
        ("laptop-qwen3.5-9b", "Qwen3.5-9B", "Laptop · RTX 4060"),
        ("t4-gemma4-e4b", "Gemma-4-E4B", "Azure · T4"),
        ("laptop-gemma4-e4b", "Gemma-4-E4B", "Laptop · RTX 4060")]
SECS = [("script", "Scripting", 7), ("reason", "Calculations", 10), ("closed", "Facts from memory", 18), ("rag", "Facts with docs (RAG)", 18)]
THEME = {
    "light": dict(text="#0b0b0b", text2="#52514e", muted="#8a8984", grid="#e4e3df", surface="#ffffff",
                  series=["#2a78d6", "#eb6834", "#1baf7a", "#eda100"], dot="#2a78d6", track="#f0efec"),
    "dark": dict(text="#f0efec", text2="#c3c2b7", muted="#8f8e88", grid="#383835", surface="#0d1117",
                 series=["#3987e5", "#d95926", "#199e70", "#c98500"], dot="#3987e5", track="#26262a"),
}
FONT = "font-family=\"-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif\""

data = []
for rid, model, machine in RUNS:
    it = json.load(open(B / "results" / f"{rid}.json"))["items"]
    sec = {s: sum(v["ok"] for k, v in it.items() if k.startswith(s + ":")) for s, _, _ in SECS}
    tps = statistics.median(v["tg_tps"] for v in it.values() if v.get("tg_tps"))
    data.append(dict(model=model, machine=machine, sec=sec, total=sum(sec.values()), tps=tps))


def svg(w, h, body, title):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" '
            f'aria-label="{escape(title)}" {FONT}><title>{escape(title)}</title>{body}</svg>\n')


def bar_end(x, y, w, h, r, fill):
    """Rect with only the right end rounded (the data end); the left edge sits on the baseline."""
    if w <= r:
        return f'<rect x="{x:.1f}" y="{y}" width="{w:.1f}" height="{h}" fill="{fill}"/>'
    return (f'<path d="M{x:.1f},{y} h{w - r:.1f} a{r},{r} 0 0 1 {r},{r} v{h - 2 * r} a{r},{r} 0 0 1 -{r},{r} '
            f'h-{w - r:.1f} z" fill="{fill}"/>')


def stacked(mode):
    t = THEME[mode]; W, L, R = 900, 232, 56; top = 92; row = 40; bh = 22; scale = (W - L - R) / 53
    H = top + row * len(data) + 34
    b = [f'<text x="0" y="22" font-size="17" font-weight="600" fill="{t["text"]}">Score by section, per run (out of 53)</text>',
         f'<text x="0" y="44" font-size="13" fill="{t["text2"]}">Each item asked once; one point per correct answer. Sorted by total.</text>']
    lx = 0
    for i, (_, name, mx) in enumerate(SECS):  # legend, in stack order
        b.append(f'<rect x="{lx}" y="60" width="12" height="12" rx="3" fill="{t["series"][i]}"/>')
        label = f"{name} /{mx}"
        b.append(f'<text x="{lx + 18}" y="70.5" font-size="12.5" fill="{t["text2"]}">{escape(label)}</text>')
        lx += 18 + 7.2 * len(label) + 22
    for g in (0, 10, 20, 30, 40, 50, 53):  # recessive grid
        x = L + g * scale
        b.append(f'<line x1="{x:.1f}" y1="{top - 6}" x2="{x:.1f}" y2="{top + row * len(data) - 10}" stroke="{t["grid"]}" stroke-width="1"/>')
        b.append(f'<text x="{x:.1f}" y="{top + row * len(data) + 8}" font-size="11" fill="{t["muted"]}" text-anchor="middle">{g}</text>')
    for r, d in enumerate(data):
        y = top + r * row
        b.append(f'<text x="{L - 14}" y="{y + 10}" font-size="13.5" font-weight="600" fill="{t["text"]}" text-anchor="end">{escape(d["model"])}</text>')
        b.append(f'<text x="{L - 14}" y="{y + 26}" font-size="11.5" fill="{t["text2"]}" text-anchor="end">{escape(d["machine"])}</text>')
        x = L
        segs = [(i, d["sec"][s]) for i, (s, _, _) in enumerate(SECS) if d["sec"][s]]
        for j, (i, v) in enumerate(segs):
            w = v * scale - (2 if j < len(segs) - 1 else 0)  # 2px surface gap between fills
            last = j == len(segs) - 1
            b.append(bar_end(x, y, w, bh, 4, t["series"][i]) if last else f'<rect x="{x:.1f}" y="{y}" width="{w:.1f}" height="{bh}" fill="{t["series"][i]}"/>')
            if w > 22:
                ink = "#ffffff" if (mode == "dark" or i in (0, 1)) else "#0b0b0b"
                b.append(f'<text x="{x + w / 2:.1f}" y="{y + 15.5}" font-size="11.5" font-weight="600" fill="{ink}" text-anchor="middle">{v}</text>')
            x += v * scale
        b.append(f'<text x="{x + 8:.1f}" y="{y + 16}" font-size="14" font-weight="700" fill="{t["text"]}">{d["total"]}</text>')
    return svg(W, H, "".join(b), "Benchmark score by section for each run")


def scatter(mode):
    t = THEME[mode]; W, H = 900, 430; L, Rm, T, Bm = 64, 40, 70, 56
    x0, x1, y0, y1 = 0, 90, 35, 52
    X = lambda v: L + (v - x0) / (x1 - x0) * (W - L - Rm); Y = lambda v: T + (y1 - v) / (y1 - y0) * (H - T - Bm)
    b = [f'<text x="0" y="22" font-size="17" font-weight="600" fill="{t["text"]}">Accuracy against speed</text>',
         f'<text x="0" y="44" font-size="13" fill="{t["text2"]}">Total score (out of 53) vs median generation speed during the run. Up and to the right is better.</text>']
    for g in range(36, 53, 4):
        b.append(f'<line x1="{L}" y1="{Y(g):.1f}" x2="{W - Rm}" y2="{Y(g):.1f}" stroke="{t["grid"]}"/>')
        b.append(f'<text x="{L - 10}" y="{Y(g) + 4:.1f}" font-size="11" fill="{t["muted"]}" text-anchor="end">{g}</text>')
    for g in range(0, 91, 15):
        b.append(f'<text x="{X(g):.1f}" y="{H - Bm + 20}" font-size="11" fill="{t["muted"]}" text-anchor="middle">{g}</text>')
    b.append(f'<line x1="{L}" y1="{H - Bm}" x2="{W - Rm}" y2="{H - Bm}" stroke="{t["muted"]}"/>')
    b.append(f'<text x="{(L + W - Rm) / 2}" y="{H - 10}" font-size="12" fill="{t["text2"]}" text-anchor="middle">tokens per second</text>')
    b.append(f'<text x="14" y="{(T + H - Bm) / 2}" font-size="12" fill="{t["text2"]}" text-anchor="middle" transform="rotate(-90 14 {(T + H - Bm) / 2})">score /53</text>')
    # label placement (dx, dy, anchor) chosen by hand to avoid collisions
    place = {0: (12, -10, "start"), 1: (-12, -10, "end"), 2: (-12, 4, "end"), 3: (-12, -10, "end"),
             4: (12, 16, "start"), 5: (-12, 4, "end"), 6: (12, 4, "start"), 7: (-12, 4, "end")}
    for i, d in enumerate(data):
        cx, cy = X(d["tps"]), Y(d["total"]); dx, dy, a = place[i]
        b.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="6" fill="{t["dot"]}" stroke="{t["surface"]}" stroke-width="2"/>')
        b.append(f'<text x="{cx + dx:.1f}" y="{cy + dy:.1f}" font-size="12.5" font-weight="600" fill="{t["text"]}" text-anchor="{a}">{escape(d["model"])}'
                 f'<tspan font-weight="400" fill="{t["text2"]}"> · {escape(d["machine"])}</tspan></text>')
    return svg(W, H, "".join(b), "Total score against generation speed for each run")


def badge(label, value, mode):
    t = THEME[mode]; lw = 6.6 * len(label) + 14; vw = 6.6 * len(value) + 14; h = 22
    bg1, bg2, fg = (("#3a3a3c", "#2a78d6", "#ffffff") if mode == "light" else ("#30363d", "#3987e5", "#ffffff"))
    body = (f'<rect width="{lw + vw:.0f}" height="{h}" rx="5" fill="{bg1}"/>'
            f'<path d="M{lw:.0f},0 h{vw - 5:.0f} a5,5 0 0 1 5,5 v{h - 10} a5,5 0 0 1 -5,5 h-{vw - 5:.0f} z" fill="{bg2}"/>'
            f'<text x="{lw / 2:.0f}" y="15" font-size="11.5" fill="{fg}" text-anchor="middle">{escape(label)}</text>'
            f'<text x="{lw + vw / 2:.0f}" y="15" font-size="11.5" font-weight="600" fill="{fg}" text-anchor="middle">{escape(value)}</text>')
    return svg(round(lw + vw), h, body, f"{label}: {value}")


BADGES = [("licence", "MIT"), ("models", "5 open-weights"), ("runs", "8 on 3 machines"), ("items", "53 auto-scored"),
          ("data", "public NCBI + synthetic"), ("inference", "llama.cpp b11639")]
for mode in ("light", "dark"):
    (OUT / f"scores-{mode}.svg").write_text(stacked(mode))
    (OUT / f"accuracy-vs-speed-{mode}.svg").write_text(scatter(mode))
    for k, v in BADGES:
        (OUT / f"badge-{k}-{mode}.svg").write_text(badge(k, v, mode))
print("figures written to", OUT)
