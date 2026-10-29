import json, sys, collections, statistics
for f in sys.argv[1:]:
    d = json.load(open(f)); c = collections.Counter(); n = collections.Counter(); tps = []
    for k, v in d["items"].items():
        g = k.split(":")[0]; n[g] += 1; c[g] += bool(v["ok"]); tps += [v["tg_tps"]] if v.get("tg_tps") else []
    print(f'{d["name"]:24s} {sum(n.values()):2d}/53  ' + "  ".join(f"{g} {c[g]}/{n[g]}" for g in ("script", "reason", "closed", "rag") if n[g]) + f'  ~{statistics.median(tps):.0f} tok/s' if tps else "")
