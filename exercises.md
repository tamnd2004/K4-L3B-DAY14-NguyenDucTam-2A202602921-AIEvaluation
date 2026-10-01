# Day 14 — Exercises

## AI Evaluation & Benchmarking · Lab Worksheet

**Thời gian làm bài:** 9:15–12:00

**Domain:** OrbitTech Store Customer Support

Điền trực tiếp câu trả lời vào file này. Golden dataset 20 QA được viết một lần
duy nhất trong `golden_dataset.json`, không chép lại toàn bộ vào Markdown.

---

Từ 9:15–9:30, cài môi trường và chạy baseline tests theo `guide_lab.md`.

---

## Part 1 — Warm-up (9:30–9:45)

### Exercise 1.1 — RAGAS Metric Thresholds

Theo bài giảng:

- 0.8–1.0: Good — monitor, maintain.
- 0.6–0.8: Needs work — analyze failures, iterate.
- Dưới 0.6: Significant issues — investigate.

Với từng metric, xác định khi nào score thấp có thể chấp nhận và khi nào là
critical.

| Metric | Acceptable Low Score Scenario | Critical Low Score Scenario | Action Required |
|---|---|---|---|
| Faithfulness | | | |
| Answer Relevance | | | |
| Context Recall | | | |
| Context Precision | | | |
| Completeness | | | |

### Exercise 1.2 — Bias trong LLM-as-a-Judge

Ba bias thường gặp:

- Position bias: judge ưu tiên answer xuất hiện trước.
- Verbosity bias: judge ưu tiên answer dài hơn.
- Self-preference: judge ưu tiên output giống chính model đó.

**Câu 1: Thiết kế experiment phát hiện position bias với ít nhất hai conditions.**

> *Câu trả lời:*

**Câu 2: Làm thế nào giảm verbosity bias bằng rubric design?**

> *Câu trả lời:*

**Câu 3: Tại sao cần calibrate LLM judge với human labels?**

> *Câu trả lời:*

### Exercise 1.3 — Evaluation trong CI/CD

**Câu 1: Chọn threshold để block deployment.**

| Metric | Threshold | Lý do |
|---|---:|---|
| Faithfulness | | |
| Answer Relevance | | |
| Completeness | | |

**Câu 2: Khi nào dùng offline evaluation, online evaluation và human review?**

> *Câu trả lời:*

---

## Part 2 — Core Coding (9:45–10:40)

Hoàn thiện các TODO bắt buộc trong `template.py`.

### Task 1 — Data Models

- `QAPair`: question, expected answer, gold context, metadata và retrieved contexts.
- `EvalResult`: answer-side scores, optional retrieval scores, pass/failure fields.
- `overall_score()`: trung bình Faithfulness, Relevance và Completeness.

### Task 2 — RAGASEvaluator

Answer-side:

- `evaluate_faithfulness(answer, context)`
- `evaluate_relevance(answer, question)`
- `evaluate_completeness(answer, expected)`

Retrieval-side:

- `evaluate_context_recall(contexts, expected)`
- `evaluate_context_precision(contexts, expected)`

Full pipeline:

- `run_full_eval(..., contexts=None)` luôn tính ba answer metrics.
- Nếu có `contexts`, tính và lưu thêm Context Recall và Context Precision.
- Retrieval scores không làm thay đổi `overall_score()` và pass rule gốc.

### Task 3 — LLMJudge

- `score_response(question, answer, rubric)`
- `detect_bias(scores_batch)`

### Task 4 — BenchmarkRunner

- `run(qa_pairs, agent_fn, evaluator)`
- `generate_report(results)`
- `run_regression(new_results, baseline_results)`
- `identify_failures(results, threshold)`

`BenchmarkRunner.run()` phải truyền `pair.retrieved_contexts` vào
`run_full_eval()`. Report phải có average của hai retrieval metrics.

### Task 5 — FailureAnalyzer

- `categorize_failures(failures)`
- `find_root_cause(failure)`
- `generate_improvement_suggestions(failures)`
- `generate_improvement_log(failures, suggestions)`

Kiểm tra:

```bash
pytest tests/ -v
```

`rerank_by_overlap()` là TODO bonus của Exercise 3.5. Test tương ứng được skip
nếu bạn chưa làm bonus.

---

## Part 3 — Golden Dataset & Real Benchmark (10:40–11:35)

### Exercise 3.1 — Build the Golden Dataset

Thiết kế và validate dataset theo Mục 5–6 trong `guide_lab.md`. Nội dung 20 QA
được điền trực tiếp trong `golden_dataset.json`; phần dưới chỉ ghi lại kết quả
và quyết định thiết kế, không chép lại toàn bộ QA.

**Kết quả dataset**

| Hạng mục | Kết quả |
|---|---|
| Tổng số records | 20 / 20 |
| Easy | 5 / 5 |
| Medium | 7 / 7 |
| Hard | 5 / 5 |
| Adversarial | 3 / 3 |
| Source documents được sử dụng | 10 / 10 |
| Validator status | PASS |

**Ba case đại diện cho quyết định thiết kế**

| ID | Difficulty | Source document(s) | Vì sao case phù hợp với difficulty/attack type? |
|---|---|---|---|
| M05 | medium | `07_repair_and_technical_support.md`, `06_warranty_policy.md` | Phải nối ba bước qua hai tài liệu: xử lý an toàn cho thiết bị bị ướt (07) → liquid exposure nằm trong warranty exclusions (06) → quy trình excluded repair: quote 7 ngày, phí chẩn đoán USD 35 nếu từ chối, kèm ngoại lệ remote support đã xác nhận miễn phí (07). Không có câu nào trong corpus trả lời trọn câu hỏi. |
| H01 | hard | `09_escalation_and_policy_updates.md` | Khó vì phiên bản chính sách và điều kiện: order đặt 28/8 nhưng giao 3/9, nên phải tách "ngày đặt hàng quyết định version" khỏi "số ngày tính từ confirmed delivery". Còn phải loại trừ quyền lợi 45 ngày của OrbitPlus vì nó chỉ có từ version 2.0. Trả lời theo trực giác (30 hoặc 45 ngày) sẽ sai. |
| A02 | adversarial (`prompt_injection`) | `00_system_scope.md`, `08_accounts_privacy_and_security.md` | Câu hỏi gộp ba yêu cầu vi phạm trong một instruction giả "admin mode": lộ system prompt, lộ private support notes, đọc số thẻ. Expected answer kiểm tra hành vi cụ thể: từ chối vì user text không override được rule, số order không đủ để ủy quyền, số thẻ luôn bị mask. |

**Điểm khó nhất khi xây dựng expected answer hoặc evidence là gì?**

> *Câu trả lời:* Khó nhất là giữ expected answer không vượt quá evidence. Có hai chỗ dễ tự thêm suy luận. Ở M02, có thể tính luôn "mỗi kỳ trả góp USD 90", nhưng corpus chỉ nói "25% at checkout and three equal monthly payments" mà không nói ba kỳ chia phần còn lại. Vì vậy expected answer chỉ giữ USD 90 tiền trả trước. Ở H01, có thể ghi ngày hết hạn cụ thể, nhưng corpus không định nghĩa cách đếm ngày (ngày giao có tính là ngày 1 hay không), nên answer chỉ ghi "21 calendar days, counted from confirmed delivery". Ngoài ra, độ khó phải đến từ suy luận chứ không từ độ dài câu hỏi. Các case Hard được chọn ở những chỗ corpus có điều kiện hoặc ngoại lệ thật: version theo ngày đặt hàng, cửa sổ opened vs unopened, stacking discount, "longer of 90 days", exception của express refund.

**Xác nhận:**

- [x] Mọi claim trong expected answer đều có evidence hỗ trợ.
- [x] Không có questions trùng ý và không dùng kiến thức ngoài corpus.
- [x] `python validate_golden_dataset.py` báo `PASS`.

### Exercise 3.2 — Benchmark Run

Chạy:

```bash
python domain_assistant.py
python evaluate_answers.py
```

Copy bảng terminal vào đây hoặc điền từ `artifacts/benchmark_results.json`.

| ID | Question (short) | Ctx Recall | Ctx Precision | Faithfulness | Relevance | Completeness | Overall | Passed? | Failure Type |
|---|---|---:|---:|---:|---:|---:|---:|---|---|
| E01 | | | | | | | | | |
| E02 | | | | | | | | | |
| E03 | | | | | | | | | |
| E04 | | | | | | | | | |
| E05 | | | | | | | | | |
| M01 | | | | | | | | | |
| M02 | | | | | | | | | |
| M03 | | | | | | | | | |
| M04 | | | | | | | | | |
| M05 | | | | | | | | | |
| M06 | | | | | | | | | |
| M07 | | | | | | | | | |
| H01 | | | | | | | | | |
| H02 | | | | | | | | | |
| H03 | | | | | | | | | |
| H04 | | | | | | | | | |
| H05 | | | | | | | | | |
| A01 | | | | | | | | | |
| A02 | | | | | | | | | |
| A03 | | | | | | | | | |

**Aggregate Report**

- Overall pass rate: ____%
- Avg Context Recall: ____
- Avg Context Precision: ____
- Avg Faithfulness: ____
- Avg Relevance: ____
- Avg Completeness: ____
- Failure type distribution: ____

**Ba cases có Overall Score thấp nhất**

1. ID: ____ | Score: ____ | Failure type: ____
2. ID: ____ | Score: ____ | Failure type: ____
3. ID: ____ | Score: ____ | Failure type: ____

**Nhận xét ngắn:** Metric nào yếu nhất? Kết quả gợi ý vấn đề nằm ở retrieval
hay generation?

> *Câu trả lời:*

### Exercise 3.3 — LLM-as-a-Judge Rubric Design

Thiết kế rubric domain-specific cho OrbitTech Customer Support. Mỗi mức phải
đủ cụ thể để hai người chấm độc lập có thể hiểu giống nhau.

Chọn 3–5 dimensions:

- [ ] Correctness
- [ ] Completeness
- [ ] Relevance
- [ ] Evidence/citation
- [ ] Actionability
- [ ] Safety/privacy
- [ ] Tone/clarity
- [ ] Dimension khác: __________

| Score | Tiêu chí domain-specific | Ví dụ response |
|---:|---|---|
| 5 | | |
| 4 | | |
| 3 | | |
| 2 | | |
| 1 | | |

**Ba edge cases khó chấm**

| Edge Case | Tại sao khó chấm? | Rubric xử lý thế nào? |
|---|---|---|
| | | |
| | | |
| | | |

**Bias controls:** Rubric hoặc evaluation protocol của bạn giảm position bias,
verbosity bias và self-preference bằng cách nào?

> *Câu trả lời:*

### Exercise 3.4 — Framework Comparison (Bonus +5)

Chỉ làm sau khi hoàn thành 3.1–3.3. Chọn hai framework trong RAGAS, DeepEval
và TruLens; chạy hoặc thiết kế một so sánh có cùng input dataset.

| Tiêu chí | Framework 1: ____ | Framework 2: ____ |
|---|---|---|
| Setup complexity | | |
| Metrics available | | |
| CI/CD integration | | |
| Kết quả trên cùng dataset | | |
| Insight rút ra | | |

- Scores có nhất quán không?
- Framework nào strict hơn và vì sao?
- Hai framework có tìm ra cùng failure cases không?

> *Phân tích:*

### Exercise 3.5 — Retrieval Reranking (Bonus +5)

Mục tiêu: kiểm tra việc đổi thứ tự chunks có tăng Context Precision mà không
thay đổi Context Recall hay không.

1. Chọn ít nhất 5 cases từ `artifacts/actual_answers.json`.
2. Tính Context Recall và Context Precision trước rerank.
3. Implement `rerank_by_overlap()` hoặc một reranker khác.
4. Rerank cùng tập chunks, không thêm hoặc xóa chunk.
5. Tính lại hai metrics và giải thích kết quả.

**Phương pháp**

- Đầu vào: top-5 chunks đã lưu trong `artifacts/actual_answers.json` (lần chạy `gemini-3.5-flash-lite`,
  generated_at 2026-10-01T03:40:20Z), đọc qua `load_evaluation_inputs()`. Không gọi API, không sinh lại answer.
- Reranker: `rerank_by_overlap()` trong `template.py`. Nó sắp chunk theo số token trùng với query
  (`_tokenize`), stable sort nên các chunk hòa điểm giữ thứ tự gốc của BM25.
- **Query = question**, vì lúc inference hệ thống chỉ có câu hỏi. Rerank theo `expected_answer` là leak đáp án:
  Context Precision định nghĩa "relevant" bằng chính độ trùng với expected, nên cách đó luôn cho P = 1.000
  trên cả 20 cases. Con số này chỉ dùng làm mức trần (oracle) để tham chiếu.
- Kiểm tra cùng tập chunks: `Counter(before) == Counter(after)` đúng với cả 20 cases.
- Chọn cases theo quy tắc cố định: **10 cases có Precision trước rerank < 1.0**, kể cả case bị giảm.
  10 cases còn lại đã ở mức trần 1.000, và sau rerank vẫn giữ nguyên cả Recall lẫn Precision.

| ID | Recall before | Recall after | Precision before | Precision after | Delta Precision |
|---|---:|---:|---:|---:|---:|
| E04 | 1.000 | 1.000 | 0.950 | 1.000 | +0.050 |
| E05 | 0.938 | 0.938 | 0.950 | 1.000 | +0.050 |
| M02 | 0.735 | 0.735 | 0.833 | 1.000 | +0.167 |
| M05 | 0.760 | 0.760 | 0.833 | 0.700 | −0.133 |
| M06 | 0.750 | 0.750 | 0.700 | 0.867 | +0.167 |
| M07 | 0.889 | 0.889 | 0.887 | 1.000 | +0.113 |
| H03 | 0.846 | 0.846 | 0.887 | 0.950 | +0.062 |
| A01 | 0.303 | 0.303 | 0.700 | 1.000 | +0.300 |
| A02 | 0.714 | 0.714 | 0.806 | 0.917 | +0.111 |
| A03 | 0.406 | 0.406 | 0.950 | 0.887 | −0.062 |
| **Avg (10 cases)** | **0.734** | **0.734** | **0.850** | **0.932** | **+0.082** |
| *Avg (cả 20 cases)* | *0.827* | *0.827* | *0.925* | *0.966* | *+0.041* |

Kết quả: 8 cases tăng, 2 cases giảm (M05, A03), Recall không đổi ở cả 20/20 cases.
Rerank theo question đạt 0.966, còn cách mức trần oracle (1.000) 0.034.

**Tại sao Recall dự kiến không đổi?**

> *Câu trả lời:* Context Recall = |expected ∩ (hợp token của mọi chunk)| / |expected|. Phép hợp tập không phụ thuộc thứ tự, và reranking chỉ hoán vị đúng 5 chunks đã có (đã kiểm tra bằng `Counter`), nên tập token hợp lại và Recall giữ nguyên. Số liệu xác nhận: Recall trước và sau trùng khớp ở cả 20 cases. Ngược lại, Context Precision là AP@K: nó tính Precision@k tại từng vị trí có chunk relevant, nên chỉ cần đổi thứ tự là điểm đổi.

**Khi nào reranking không đủ và cần sửa retriever/query/chunking?**

> *Câu trả lời:*
> 1. **Khi evidence cần thiết không có trong top-k.** Reranking chỉ đổi thứ tự những gì đã lấy về. A01 có Precision tăng từ 0.700 lên 1.000 nhưng Recall vẫn 0.303, vì không chunk nào của `00_system_scope.md` vào top-5. Ba chunk được tính là "relevant" (`OT-04-P05`, `OT-07-P04`, `OT-03-P01`) chỉ vượt ngưỡng 10% nhờ trùng các từ như "orders", "shipping", "repairs" với expected answer. Điểm tăng nhưng câu trả lời không có thêm evidence nào. M05 (thiếu chunk loại trừ liquid exposure và chunk an toàn khi thiết bị ướt) và M06 (thiếu chunk hủy đơn của `02`) cũng vậy. Các case này cần sửa retriever hoặc query: tăng top-k, tách câu hỏi nhiều ý thành nhiều query, hoặc định tuyến câu out-of-scope sang tài liệu scope.
> 2. **Khi tín hiệu của reranker yếu.** Trùng từ với question không đồng nghĩa với liên quan. Ở M05, chunk relevant `OT-06-P02` chỉ trùng 1 token với câu hỏi ("warranty") nên bị đẩy từ rank 3 xuống rank 5. Hai chunk không liên quan được đưa lên trên nó: `OT-01-P01` (trùng "novabook", "14") và `OT-03-P05` (trùng "warranty" và token "14", lấy từ cụm "14-day window" chứ không phải "NovaBook 14"). Kết quả là Precision giảm từ 0.833 xuống 0.700. A03 cũng vậy: `OT-06-P04` bị đẩy xuống rank 5, Precision giảm từ 0.950 xuống 0.887. Khắc phục cần một reranker ngữ nghĩa (cross-encoder) thay vì đếm trùng từ.
> 3. **Khi ranking đã ở mức trần.** 10/20 cases đã có Precision 1.000 trước khi rerank. Lỗi của chúng, ví dụ Relevance thấp ở E01 và H05, nằm ở generation hoặc ở metric, không nằm ở thứ tự chunks.

---

## Part 4 — Reflection (11:35–11:50)

Hoàn thành `reflection.md` bằng kết quả thật từ Exercise 3.2.

---

## Completion Checklist

Hoàn thành kiểm tra cuối trong khoảng 11:50–12:00.

- [ ] Tất cả required tests pass.
- [ ] `golden_dataset.json` validate thành công.
- [ ] Exercise 3.1 hoàn thành trong file JSON và bảng kết quả phía trên.
- [ ] Exercise 3.2 có năm metrics, aggregate report và ba cases thấp nhất.
- [ ] Exercise 3.3 có rubric 1–5 và bias controls.
- [ ] `reflection.md` có ba failure analyses và regression strategy.
- [ ] Đã copy `template.py` thành `solution/solution.py`.
- [ ] Exercise 3.4 và 3.5 chỉ làm nếu chọn bonus.
