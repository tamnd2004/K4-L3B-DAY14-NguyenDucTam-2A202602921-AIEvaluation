"""Exercise 3.5 — rerank the SAME saved chunks and re-score the retrieval metrics.

Run from the repo root with the lab venv (no API calls):
    python bonus/rerank_experiment.py

Query = question (what the system has at inference time). Reranking by the
expected answer leaks the reference, so it is printed only as an oracle ceiling.
"""
from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from evaluate_answers import load_evaluation_inputs  # noqa: E402
from template import RAGASEvaluator, rerank_by_overlap  # noqa: E402


def main() -> None:
    pairs, _ = load_evaluation_inputs(ROOT / "golden_dataset.json", ROOT / "artifacts" / "actual_answers.json")
    ev = RAGASEvaluator()
    rows = []
    for p in pairs:
        chunks = p.retrieved_contexts
        by_question = rerank_by_overlap(chunks, p.question)
        by_expected = rerank_by_overlap(chunks, p.expected_answer)  # oracle only
        assert Counter(by_question) == Counter(chunks), "reranking must not add or drop chunks"
        rows.append({
            "id": p.metadata["id"],
            "r_before": ev.evaluate_context_recall(chunks, p.expected_answer),
            "r_after": ev.evaluate_context_recall(by_question, p.expected_answer),
            "p_before": ev.evaluate_context_precision(chunks, p.expected_answer),
            "p_after": ev.evaluate_context_precision(by_question, p.expected_answer),
            "p_oracle": ev.evaluate_context_precision(by_expected, p.expected_answer),
            "new_order": [chunks.index(c) + 1 for c in by_question],
        })

    print("| ID | Recall before | Recall after | Precision before | Precision after | Delta | Oracle | New order (orig ranks) |")
    print("|---|---:|---:|---:|---:|---:|---:|---|")
    for r in rows:
        print(f"| {r['id']} | {r['r_before']:.3f} | {r['r_after']:.3f} | {r['p_before']:.3f} | "
              f"{r['p_after']:.3f} | {r['p_after'] - r['p_before']:+.3f} | {r['p_oracle']:.3f} | {r['new_order']} |")

    def avg(key: str, sub: list[dict]) -> float:
        return sum(r[key] for r in sub) / len(sub)

    below_ceiling = [r for r in rows if r["p_before"] < 1.0]
    for label, sub in (("All 20 cases", rows), (f"Precision before < 1.0 ({len(below_ceiling)} cases)", below_ceiling)):
        print(f"\n{label}: Recall {avg('r_before', sub):.3f} -> {avg('r_after', sub):.3f} | "
              f"Precision {avg('p_before', sub):.3f} -> {avg('p_after', sub):.3f} "
              f"({avg('p_after', sub) - avg('p_before', sub):+.3f}) | oracle {avg('p_oracle', sub):.3f}")
    print("improved:", [r["id"] for r in rows if r["p_after"] > r["p_before"] + 1e-9])
    print("worse:   ", [r["id"] for r in rows if r["p_after"] < r["p_before"] - 1e-9])
    print("recall changed anywhere:", any(abs(r["r_after"] - r["r_before"]) > 1e-12 for r in rows))


if __name__ == "__main__":
    main()
