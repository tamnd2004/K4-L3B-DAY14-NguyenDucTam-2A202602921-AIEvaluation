"""Exercise 3.4 — run RAGAS and DeepEval on the SAME saved inputs (20 QA, Gemini answers).

Run from the repo root in a separate venv (see bonus/README.md):
    python bonus/framework_comparison.py deepeval ragas

Inputs come from the lab artifacts only (no new answers are generated):
  question, actual_answer, retrieved_contexts (ranked), expected_answer.
Both frameworks use the same judge model so differences come from the frameworks.

Resumable: every finished (case, metric) is checkpointed to OUT; re-running only scores the gaps.
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
import time
from pathlib import Path

os.environ.setdefault("DEEPEVAL_TELEMETRY_OPT_OUT", "YES")

import httpx
from dotenv import dotenv_values
from openai import AsyncOpenAI

LAB = Path(__file__).resolve().parents[1]  # repo root
BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"
JUDGE = os.environ.get("JUDGE_MODEL", "gemini-3.5-flash-lite")
EMBED = "gemini-embedding-001"
LIMIT = int(os.environ.get("LIMIT", "0")) or None
CONCURRENCY = int(os.environ.get("CONCURRENCY", "2"))
MAX_RETRIES = int(os.environ.get("MAX_RETRIES", "6"))
MIN_INTERVAL = float(os.environ.get("MIN_INTERVAL", "4.5"))  # seconds between requests (free-tier RPM)
OUT = Path(os.environ.get("OUT", Path(__file__).with_name("framework_results.json")))

API_KEY = dotenv_values(LAB / ".env")["GEMINI_API_KEY"].strip()

# ------------------------------------------------------------------ inputs
golden = {p["id"]: p for p in json.loads((LAB / "golden_dataset.json").read_text(encoding="utf-8"))["qa_pairs"]}
actual = json.loads((LAB / "artifacts" / "actual_answers.json").read_text(encoding="utf-8"))
bench = {r["id"]: r for r in json.loads((LAB / "artifacts" / "benchmark_results.json").read_text(encoding="utf-8"))["results"]}
cases = []
for a in actual["answers"]:
    g = golden[a["id"]]
    cases.append({
        "id": a["id"],
        "question": g["question"],
        "answer": a["actual_answer"],
        "contexts": [c["text"].strip() for c in a["retrieved_contexts"]],
        "expected": g["expected_answer"],
    })
cases = cases[:LIMIT] if LIMIT else cases

RESULT = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else {}
RESULT.update({
    "judge": JUDGE, "embedding": EMBED, "n_cases": len(cases),
    "generator": actual["agent"]["model"], "answers_generated_at": actual["generated_at"],
    "lab_core": {c["id"]: {k: bench[c["id"]][k] for k in ("faithfulness", "relevance", "completeness",
                                                           "context_recall", "context_precision", "passed")}
                 for c in cases},
})


def save():
    OUT.write_text(json.dumps(RESULT, ensure_ascii=False, indent=2), encoding="utf-8")


# ------------------------------------------------------------------ pacing + call counting
ok_calls = {"ragas": 0, "deepeval": 0}  # HTTP 200 responses only (429 retries excluded)
_pace = {"lock": None, "last": 0.0}


async def _throttle():
    if MIN_INTERVAL <= 0:
        return
    if _pace["lock"] is None:
        _pace["lock"] = asyncio.Lock()
    async with _pace["lock"]:
        wait = _pace["last"] + MIN_INTERVAL - time.monotonic()
        if wait > 0:
            await asyncio.sleep(wait)
        _pace["last"] = time.monotonic()


def gemini_client(tag: str) -> AsyncOpenAI:
    async def on_request(request):
        await _throttle()

    async def on_response(response):
        if response.status_code == 200:
            ok_calls[tag] += 1
    return AsyncOpenAI(api_key=API_KEY, base_url=BASE_URL, max_retries=MAX_RETRIES,
                       http_client=httpx.AsyncClient(timeout=120, event_hooks={"request": [on_request],
                                                                                "response": [on_response]}))


# ------------------------------------------------------------------ shared runner
async def run_framework(fw: str, jobs: dict) -> None:
    """jobs: metric name -> async fn(case) -> float. Only (case, metric) pairs without a score run."""
    block = RESULT.setdefault(fw, {"seconds": 0.0, "scores": {}})
    scores = block.setdefault("scores", {})
    for c in cases:
        scores.setdefault(c["id"], {})
    sem = asyncio.Semaphore(CONCURRENCY)
    t0 = time.perf_counter()
    start_calls = ok_calls[fw]
    done = 0

    async def one(case, name, fn):
        nonlocal done
        slot = scores[case["id"]]
        if slot.get(name) is not None:
            return
        async with sem:
            try:
                slot[name] = float(await fn(case))
                slot.pop(f"{name}_error", None)
                done += 1
            except Exception as exc:  # keep going; record the failure
                slot[name] = None
                slot[f"{name}_error"] = f"{type(exc).__name__}: {str(exc)[:200]}"
            save()

    await asyncio.gather(*(one(c, n, fn) for c in cases for n, fn in jobs.items()))
    block["seconds"] = round(block.get("seconds", 0) + time.perf_counter() - t0, 1)
    block.setdefault("ok_calls_log", []).append({"ok_calls": ok_calls[fw] - start_calls, "items_scored": done})
    save()
    missing = sum(1 for s in scores.values() for n in jobs if s.get(n) is None)
    print(f"{fw}: scored {done} items with {ok_calls[fw] - start_calls} successful calls; still missing {missing}", flush=True)


# ------------------------------------------------------------------ RAGAS
async def run_ragas():
    from ragas.embeddings import embedding_factory
    from ragas.llms import llm_factory
    from ragas.metrics.collections import (AnswerRelevancy, ContextPrecisionWithReference,
                                           ContextRecall, Faithfulness)

    client = gemini_client("ragas")
    # Default max_tokens=1024 truncated structured output in the smoke test (IncompleteOutputException).
    llm = llm_factory(JUDGE, provider="openai", client=client, max_tokens=4096, temperature=0)
    emb = embedding_factory("openai", model=EMBED, client=client)
    faith, rel = Faithfulness(llm=llm), AnswerRelevancy(llm=llm, embeddings=emb)
    rec, prec = ContextRecall(llm=llm), ContextPrecisionWithReference(llm=llm)

    async def f(c): return (await faith.ascore(user_input=c["question"], response=c["answer"], retrieved_contexts=c["contexts"])).value
    async def r(c): return (await rel.ascore(user_input=c["question"], response=c["answer"])).value
    async def cr(c): return (await rec.ascore(user_input=c["question"], retrieved_contexts=c["contexts"], reference=c["expected"])).value
    async def cp(c): return (await prec.ascore(user_input=c["question"], reference=c["expected"], retrieved_contexts=c["contexts"])).value

    await run_framework("ragas", {"faithfulness": f, "answer_relevancy": r, "context_recall": cr, "context_precision": cp})


# ------------------------------------------------------------------ DeepEval
def build_deepeval_judge():
    from deepeval.models import DeepEvalBaseLLM

    client = gemini_client("deepeval")

    class GeminiJudge(DeepEvalBaseLLM):
        """Gemini via its OpenAI-compatible endpoint; structured output when a schema is given."""

        def __init__(self):
            super().__init__(JUDGE)

        def load_model(self):
            return client

        def get_model_name(self):
            return f"{JUDGE} (OpenAI-compatible)"

        def generate(self, prompt: str, schema=None):
            raise NotImplementedError("async only (metrics run with a_measure)")

        async def a_generate(self, prompt: str, schema=None):
            msgs = [{"role": "user", "content": prompt}]
            if schema is not None:
                r = await client.beta.chat.completions.parse(model=JUDGE, messages=msgs, response_format=schema, temperature=0)
                return r.choices[0].message.parsed or r.choices[0].message.content
            r = await client.chat.completions.create(model=JUDGE, messages=msgs, temperature=0)
            return r.choices[0].message.content

    return GeminiJudge()


async def run_deepeval():
    from deepeval.metrics import (AnswerRelevancyMetric, ContextualPrecisionMetric,
                                  ContextualRecallMetric, FaithfulnessMetric)
    from deepeval.test_case import LLMTestCase

    judge = build_deepeval_judge()

    def job(metric_cls):
        async def fn(c):
            metric = metric_cls(model=judge, include_reason=False)  # fresh instance: metrics keep state
            tc = LLMTestCase(input=c["question"], actual_output=c["answer"],
                             expected_output=c["expected"], retrieval_context=c["contexts"])
            await metric.a_measure(tc, _show_indicator=False)
            return metric.score
        return fn

    await run_framework("deepeval", {"faithfulness": job(FaithfulnessMetric),
                                     "answer_relevancy": job(AnswerRelevancyMetric),
                                     "context_recall": job(ContextualRecallMetric),
                                     "context_precision": job(ContextualPrecisionMetric)})


async def main():
    for fw in sys.argv[1:] or ["deepeval", "ragas"]:
        await (run_ragas() if fw == "ragas" else run_deepeval())
    print("saved", OUT.resolve())


if __name__ == "__main__":
    asyncio.run(main())
