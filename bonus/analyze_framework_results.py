"""Summarize bonus/framework_results.json for Exercise 3.4 (no API calls; runs in the lab venv).

Run from the repo root:  python bonus/analyze_framework_results.py
"""
import json
import sys
from pathlib import Path

path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).with_name("framework_results.json")
d = json.loads(path.read_text(encoding="utf-8"))
METRICS = ["faithfulness", "answer_relevancy", "context_recall", "context_precision"]
LAB_KEY = {"faithfulness": "faithfulness", "answer_relevancy": "relevance",
           "context_recall": "context_recall", "context_precision": "context_precision"}
ids = list(d["lab_core"])
R, D, L = d["ragas"]["scores"], d["deepeval"]["scores"], d["lab_core"]

print(f"judge={d['judge']} generator={d['generator']} n={d['n_cases']}")
for fw in ("ragas", "deepeval"):
    errs = {}
    for i, s in d[fw]["scores"].items():
        for k, v in s.items():
            if k.endswith("_error"):
                errs.setdefault(v.split(":")[0], []).append(f"{i}/{k[:-6]}")
    print(f"{fw}: {d[fw]['seconds']}s, successful calls per run {d[fw].get('ok_calls_log')}, errors={ {k: len(v) for k, v in errs.items()} } {sum(errs.values(), [])[:12]}")


def rank(xs):
    order = sorted(range(len(xs)), key=lambda i: xs[i])
    r = [0.0] * len(xs)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and xs[order[j + 1]] == xs[order[i]]:
            j += 1
        for k in range(i, j + 1):
            r[order[k]] = (i + j) / 2 + 1
        i = j + 1
    return r


def spearman(a, b):
    if len(a) < 3:
        return float("nan")
    ra, rb = rank(a), rank(b)
    ma, mb = sum(ra) / len(ra), sum(rb) / len(rb)
    cov = sum((x - ma) * (y - mb) for x, y in zip(ra, rb))
    va = sum((x - ma) ** 2 for x in ra) ** 0.5
    vb = sum((y - mb) ** 2 for y in rb) ** 0.5
    return cov / (va * vb) if va and vb else float("nan")


print("\n== averages over cases scored by BOTH frameworks | Spearman")
for m in METRICS:
    common = [i for i in ids if R[i].get(m) is not None and D[i].get(m) is not None]
    r = [R[i][m] for i in common]
    de = [D[i][m] for i in common]
    lab = [L[i][LAB_KEY[m]] for i in common]
    avg = lambda xs: sum(xs) / len(xs) if xs else float("nan")
    print(f"{m:18s} n={len(common):2d} RAGAS={avg(r):.3f} DeepEval={avg(de):.3f} lab={avg(lab):.3f} | "
          f"rho(R,D)={spearman(r, de):+.2f} rho(R,lab)={spearman(r, lab):+.2f} rho(D,lab)={spearman(de, lab):+.2f} "
          f"| mean|R-D|={avg([abs(x - y) for x, y in zip(r, de)]):.3f}")

print("\n== per case (R / D / lab)")
for i in ids:
    cells = []
    for m in METRICS:
        f = lambda v: "  -  " if v is None else f"{v:.2f}"
        cells.append(f"{m[:6]} {f(R[i].get(m))}/{f(D[i].get(m))}/{L[i][LAB_KEY[m]]:.2f}")
    print(i, " | ".join(cells))

print("\n== cases with an answer-side score < 0.5 (faithfulness or answer_relevancy)")
def low(src, i):
    return any((src[i].get(m) is not None and src[i][m] < 0.5) for m in ("faithfulness", "answer_relevancy"))
fr = {i for i in ids if low(R, i)}
fd = {i for i in ids if low(D, i)}
fl = {i for i in ids if not L[i]["passed"]}
print("RAGAS   :", sorted(fr))
print("DeepEval:", sorted(fd))
print("lab core fails (passed=False):", sorted(fl))
print("RAGAS∩DeepEval:", sorted(fr & fd), "| only RAGAS:", sorted(fr - fd), "| only DeepEval:", sorted(fd - fr))

print("\n== bottom 3 by mean(faithfulness, answer_relevancy)")
for name, src in (("RAGAS", R), ("DeepEval", D)):
    vals = []
    for i in ids:
        xs = [src[i][m] for m in ("faithfulness", "answer_relevancy") if src[i].get(m) is not None]
        if xs:
            vals.append((sum(xs) / len(xs), i))
    print(name, [(i, round(v, 3)) for v, i in sorted(vals)[:3]])
