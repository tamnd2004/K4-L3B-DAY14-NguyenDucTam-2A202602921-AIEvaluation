# Bonus — Exercise 3.4 và 3.5

Code và kết quả thô cho hai bài bonus. Phân tích nằm trong `exercises.md`.
Cả hai bài dùng lại các file đã lưu trong `artifacts/`, không sinh lại câu trả lời.

## Exercise 3.5 — Reranking

| File | Nội dung |
|---|---|
| `rerank_experiment.py` | Rerank top-5 chunks đã lưu bằng `rerank_by_overlap()` (query = question), tính lại Context Recall/Precision |
| `rerank_output.txt` | Output của lần chạy dùng trong worksheet |

Chạy bằng venv của lab, không gọi API:

```powershell
python bonus/rerank_experiment.py
```

## Exercise 3.4 — RAGAS vs DeepEval

| File | Nội dung |
|---|---|
| `framework_comparison.py` | Chấm 20 case bằng RAGAS 0.4.3 và DeepEval 4.2.7, cùng 4 metrics, cùng judge |
| `framework_results.json` | Điểm thô của từng case (80/80 lượt mỗi framework) kèm điểm core của lab |
| `analyze_framework_results.py` | Tính trung bình, Spearman, failure overlap từ file JSON |
| `framework_analysis.txt` | Output của script phân tích |
| `framework_probe.py`, `framework_probe_log.txt` | Chạy lại M06 (DeepEval) và H02 (RAGAS) để kiểm tra điểm bất thường |
| `requirements-frameworks.txt` | Phiên bản đã dùng |

- Judge: `gemini-3.5-flash-lite` cho cả hai framework, embedding `gemini-embedding-001`. Free tier chỉ cho
  `gemini-3.5-flash` 20 request/ngày nên không dùng được; judge trùng model sinh câu trả lời.
- Free tier giới hạn request/phút: lần chạy đầu bị 429 ở 23/80 (RAGAS) và 39/80 (DeepEval) lượt chấm.
  Script giãn nhịp ~4.5 giây/request và lưu checkpoint sau từng lượt; chạy lại chỉ chấm các lượt còn thiếu.
  `ok_calls_log` trong JSON chỉ ghi số lần gọi thành công của lượt chạy bù.

Chạy lại trong một venv riêng (cần `GEMINI_API_KEY` trong `.env`, tốn quota API):

```powershell
python -m venv .venv-frameworks
.\.venv-frameworks\Scripts\python.exe -m pip install -r bonus/requirements-frameworks.txt
.\.venv-frameworks\Scripts\python.exe bonus/framework_comparison.py deepeval ragas
python bonus/analyze_framework_results.py
```
