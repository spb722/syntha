# Story 1.2 — DeepEval Quality Gate for Structured Outputs

## Context
- Step 1+2 now yield `campaign_rules_dataset.jsonl` (raw utterances) and `campaign_rules_structured.jsonl` (LLM-extracted `normal_statements`/`schedule` JSON).
- We need an automated judge to verify that each structured record faithfully mirrors its source instruction before downstream teams rely on it.
- DeepEval provides LLM-as-a-judge metrics and tooling that we can run locally via our existing Ollama endpoint (`glm-4.6:cloud`).

## Evaluation Goals
1. **Schema sanity:** Ensure `structured_output` respects our JSON contract (array of statements + schedule string, no missing fields).
2. **Semantic fidelity:** Confirm each `normal_statement` is supported by the original utterance (no hallucinations or missing logic).
3. **Schedule isolation:** Verify the `schedule` field contains only timing info mentioned in the utterance—no targeting/actions leaking in.
4. **Traceability:** Tag every score with `record_id` so we can trace failures back to the exact dataset row and regenerate or fix extractions if needed.

## Tooling Plan
- Use DeepEval’s Python API.
  - `JSONCorrectnessMetric` (or custom) for schema validation.
  - `FaithfulnessMetric` or `AnswerRelevancyMetric` with `glm-4.6:cloud` to judge statement fidelity (prompt = utterance, response = concatenated statements).
  - Custom DeepEval metric for schedule separation: LLM receives both the original schedule sentence(s) and the extracted `schedule`, and returns pass/fail plus rationale.
- Wrap metrics inside a `deepeval.evaluate` test suite that iterates over `campaign_rules_structured.jsonl`. Input fields for each test case:
  ```json
  {
    "record_id": "rule-000042",
    "utterance": "...",
    "structured_output": {
      "normal_statements": [...],
      "schedule": "..."
    }
  }
  ```
- Configure DeepEval to call our local Ollama endpoint via a custom `LLM` adapter (if needed) so we stay offline.

## Implementation Outline
1. **Adapter/Client**
   - Implement a lightweight DeepEval-compatible `OllamaLLM` wrapper that POSTs to `http://localhost:11434` with model `glm-4.6:cloud`.
2. **Metrics**
   - `SchemaMetric`: checks for required keys, non-empty statements, schedule string type.
   - `FaithfulnessMetric`: `input=utterance`, `actual=structured_output["normal_statements"]` joined; judge prompt asks if statements faithfully represent the campaign logic (Yes/No + confidence).
   - `ScheduleMetric`: `input=schedule_in_utterance`, `actual=structured_output["schedule"]`; judge ensures only timing info is present and matches the source text.
3. **Runner Script**
   - CLI: `python deepeval_runner.py --input campaign_rules_structured.jsonl --max-records 100`.
   - Loads JSONL, builds DeepEval dataset, runs metrics, prints per-record failures, and exports summary (overall pass rate, histograms, etc.).
   - Supports resume or chunking by filtering the input file (not as critical because evaluation is read-only).
4. **Reporting**
   - Write results to `deepeval_reports/` as JSON (raw scores) plus Markdown summary (top failing record IDs, reasons).
   - Optionally add a “quality gate” threshold (e.g., fail pipeline if faithfulness < 0.9).

## Validation & Next Steps
- Smoke-test with a handful of records to calibrate prompts and thresholds.
- Once stable, integrate into CI or a nightly job to guard the dataset.
- Future enhancements:
  - Add more metrics (toxicity, policy adherence) if needed.
  - Compare structured outputs against human-written gold samples to benchmark extraction accuracy.
