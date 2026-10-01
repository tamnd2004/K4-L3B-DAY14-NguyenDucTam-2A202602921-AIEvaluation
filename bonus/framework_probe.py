"""Inspect two suspicious scores: DeepEval faithfulness on M06 and RAGAS faithfulness on H02."""
import asyncio
import os

os.environ["OUT"] = "probe_unused.json"  # never touch framework_results.json (probe does not save)

import framework_comparison as fc  # noqa: E402
from deepeval.metrics import FaithfulnessMetric  # noqa: E402
from deepeval.test_case import LLMTestCase  # noqa: E402
from ragas.llms import llm_factory  # noqa: E402
from ragas.metrics.collections import Faithfulness  # noqa: E402

case = {c["id"]: c for c in fc.cases}


async def main():
    m6 = case["M06"]
    print("M06 answer:", m6["answer"], flush=True)
    judge = fc.build_deepeval_judge()
    for run in (1, 2):
        met = FaithfulnessMetric(model=judge, include_reason=True)
        await met.a_measure(LLMTestCase(input=m6["question"], actual_output=m6["answer"],
                                        retrieval_context=m6["contexts"]), _show_indicator=False)
        print(f"\nDeepEval M06 faithfulness run{run}: {met.score}", flush=True)
        print("  claims:", met.claims)
        print("  verdicts:", [(v.verdict, (v.reason or "")[:120]) for v in met.verdicts])
        print("  reason:", (met.reason or "")[:300], flush=True)

    h2 = case["H02"]
    print("\nH02 answer:", h2["answer"], flush=True)
    llm = llm_factory(fc.JUDGE, provider="openai", client=fc.gemini_client("ragas"), max_tokens=4096, temperature=0)
    res = await Faithfulness(llm=llm).ascore(user_input=h2["question"], response=h2["answer"],
                                             retrieved_contexts=h2["contexts"])
    print("RAGAS H02 faithfulness rerun:", res.value)
    print("  reason:", str(getattr(res, "reason", ""))[:800], flush=True)


asyncio.run(main())
