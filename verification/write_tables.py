"""Print Markdown tables (Mine / Published / Difference / OK) from comparison.json."""
import json, os
HERE = os.path.dirname(os.path.abspath(__file__))
res = json.load(open(os.path.join(HERE, "comparison.json")))


def fmt(v):
    if v is None:
        return "n/a"
    if isinstance(v, float) and abs(v) < 1.5 and v != int(v):
        return f"{v:.4f}"
    return f"{v:,.0f}" if isinstance(v, (int, float)) else str(v)


for fig, lst in res.items():
    ok = all(x["ok"] for x in lst)
    print(f"\n#### {fig} : {'PASS' if ok else 'FAIL'}\n")
    print("| Key | Mine | Published | Difference | Match |\n|---|---:|---:|---:|---|")
    for x in lst:
        print(f"| {x['key']} | {fmt(x['mine'])} | {fmt(x['published'])} | {fmt(x['diff'])} | {'yes' if x['ok'] else 'NO'} |")
