"""Print one line per run: score per section, total score, and median generation speed.
usage: python bench/summarise.py bench/results/<run>.json [...]"""
import json, sys, collections, statistics

NAMES = {"script": "scripting", "reason": "calculations", "closed": "facts-from-memory", "rag": "facts-with-docs"}
for f in sys.argv[1:]:
    d = json.load(open(f)); c = collections.Counter(); n = collections.Counter(); tps = []
    for k, v in d["items"].items():
        g = k.split(":")[0]; n[g] += 1; c[g] += bool(v["ok"]); tps += [v["tg_tps"]] if v.get("tg_tps") else []
    secs = "  ".join(f"{NAMES[g]} {c[g]}/{n[g]}" for g in NAMES if n[g])
    speed = f"  median {statistics.median(tps):.0f} tokens/s" if tps else ""
    print(f'{d["name"]:24s} score {sum(c.values())}/{sum(n.values())}  {secs}{speed}')
