"""Re-apply the current scorers in tasks.py to the stored answers in bench/results/*.json.
Answers are never regenerated: scripts are scored from their stored stdout, the rest from the stored final text.
Where a score changes, the earlier value is kept in the item as `ok_before_rescore`.
usage: python bench/rescore.py            (prints changes, rewrites the result files)"""
import json
from pathlib import Path
import tasks

B = Path(__file__).parent
T = json.load(open(B / "data/truth.json"))
want = {t[0]: t[2] for t in tasks.REASON_TASKS}
pat = {t[0]: t[2] for t in tasks.RETR_TASKS}
for f in sorted((B / "results").glob("*.json")):
    if f.name.endswith(".bench.json") or f.name == "rag_index.json":
        continue
    d = json.load(open(f)); changed = []
    for k, v in d["items"].items():
        sec, tid = k.split(":")
        if sec == "script":
            new = v.get("rc") == 0 and tasks.score_script(tid, v.get("stdout", ""), T)
        elif sec == "reason":
            new = tasks.score_reason(v["content"], want[tid])
        else:
            new = tasks.score_retr(v["content"], pat[tid])
        if bool(new) != bool(v["ok"]):
            v.setdefault("ok_before_rescore", v["ok"]); v["ok"] = bool(new); changed.append(f"{k}: {not new} -> {bool(new)}")
    if changed:
        json.dump(d, open(f, "w"), indent=1)
    print(f.name, changed or "no change")
