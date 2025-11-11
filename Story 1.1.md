# Story 1.1 — Structured Utterance Extraction Plan

## Context
- Step 1 now streams campaign instructions into `campaign_rules_dataset.jsonl` with deterministic `record_id`s (`rule-000001`…) and byte offsets captured in the metadata plan so any downstream job can seek directly to the right line.
- Step 2 (this story) consumes that JSONL, converts each `utterance` into the required structured form, and writes a new JSONL (`campaign_rules_structured.jsonl`) while preserving original fields for traceability.
- Example input: `Target customers whose top-up channel in the last month was mobile, with a maximum total recharge amount of 10 RO for that month then Send a promotional SMS using Message ID 16 and If the customer’s recharge amount is between 6 RO and 10 RO, provide a 10 GB data pack valid for 15 days. Run this campaign every 4 hours, starting from 10 February 2025 and continuing until 10 March 2026.`
- Desired output structure separates business logic (`normal_statements`) from scheduling (`schedule`) so classification models and campaign tooling can ingest them independently.

## Functional Requirements
1. Accept a natural-language campaign instruction (utterance) as input.
2. Produce a single JSON object with:
   - `normal_statements`: array of standalone rule strings covering targeting, actions, bonuses, sampling, and policies for each branch; no scheduling text or pronouns.
   - `schedule`: single string describing timing/recurrence; empty if unspecified.
3. Preserve full logical meaning; handle branching (`if`, `else if`, `otherwise`).
4. Explicitly exclude schedule details from `normal_statements`.
5. Enforce the schema at generation time (type/object with required `normal_statements`, `schedule`).

## Prompting & Guidance
- Provide the LLM with telecom-specific context covering targeting, actions, bonuses, sampling, policy, schedule, branching components (per supplied bullet list).
- Restate segmentation rules: group related logic, avoid pronouns, no scheduling inside `normal_statements`, do not merge distinct branches.
- Include the strict JSON Schema in the system/user prompt to minimize drift.
- Example desired output for the sample input:
  ```json
  {
    "normal_statements": [
      "For customers whose top-up channel in the last month was mobile and whose total recharge amount for that month does not exceed 10 RO, send a promotional SMS using Message ID 16. If the customer’s recharge amount is between 6 RO and 10 RO, also provide a 10 GB data pack valid for 15 days."
    ],
    "schedule": "Run this campaign every 4 hours, starting from 10 February 2025 and continuing until 10 March 2026."
  }
  ```

## Technical Approach
- Define a Pydantic model `UtteranceExtraction` with `normal_statements: list[str]` and `schedule: str`.
- Implement `extract_structured(utterance: str, model=EXTRACT_MODEL, temperature=0.0)` mirroring the provided example:
  - Use `client.chat` with `format=UtteranceExtraction.model_json_schema()` to force structured output.
  - System prompt: instructions above (telecom breakdown + schema + rules).
  - User prompt: `Extract fields from this instruction:\n{utterance}`.
  - Parse via `UtteranceExtraction.model_validate_json(resp["message"]["content"])`.
- Add CLI/utility entry point (`structured_extractor.py`) that reads `campaign_rules_dataset.jsonl`, seeks to offsets recorded in `campaign_rules_dataset.jsonl.meta.json`, calls `extract_structured`, and appends enriched rows to `campaign_rules_structured.jsonl`.
- Streaming writer captures `structured_output`, `structured_status`, and `structured_error` (when applicable) plus the output-file offset so phase 3 could resume from the structured dataset as well.

## Validation Plan
1. Unit-test `parse_distribution_arg` unaffected (regression), plus new extractor via mocked Ollama response.
2. Create fixture utterances covering:
   - Single-branch instructions with schedule.
   - Multi-branch logic (if/else) to ensure multiple `normal_statements` entries.
   - Utterances missing schedule (expect empty string).
3. Manual smoke test by calling `extract_structured` on the provided example and verifying JSON matches expectation.
4. End-to-end testing: run `synthetic_generator.py --mode fresh --n-examples 10` followed by `structured_extractor.py --mode fresh --max-records 3` to confirm resume metadata progresses and structured JSON renders as expected.

## Runtime Workflow
1. **Generation (Step 1)**
   - CLI builds a plan with per-record IDs and writes each utterance to JSONL, capturing the byte offset once written.
   - Metadata (`campaign_rules_dataset.jsonl.meta.json`) stores `{index, record_id, complexity, offset}` for every row, enabling constant-time seeking later.
2. **Extraction (Step 2)**
   - Fresh mode clones the step-1 plan, extends it with `output_offset`/`status`, and resets `campaign_rules_structured.jsonl`.
   - For each entry, the extractor seeks to the saved offset, validates `record_id`, runs `extract_structured`, and appends the merged record to the structured JSONL.
   - Metadata (`campaign_rules_structured.jsonl.meta.json`) tracks progress (`completed`, `last_processed_id`) so resume mode can continue without rescanning the source file.

## Issues Encountered & Resolutions
- **Missing record identifiers/offsets**: Without stable IDs and offsets, the extractor would have to reread the source file from the beginning. Resolved by enhancing the generator to inject `record_id`s and capture byte offsets during write time.
- **Structured output wrapped in Markdown fences**: Ollama sometimes returned JSON inside ```json blocks, causing `UtteranceExtraction` validation failures (`json_invalid`). Added `_clean_structured_payload` to strip fences before parsing so the schema validation always receives raw JSON.
- **Potential reprocessing after failure**: Both scripts now append status fields (`processed`, `structured_status`) and checkpoint metadata after every successful write so an unexpected exit only affects the in-flight record.

## Additional Notes for Collaborators
- Keep both scripts pointed at the same Ollama host/model (`glm-4.6:cloud`) unless you update the metadata format; mismatched models/temperatures cause resume validation to fail by design.
- Output files are JSONL to allow streaming. For analytics that prefer arrays, run a conversion utility once both steps finish.
- To troubleshoot extraction errors, inspect `structured_status == "error"` entries in `campaign_rules_structured.jsonl`—they include `structured_error` strings with the raw exception.
- Future enhancements: add unit tests for `_clean_structured_payload`, introduce backoff/retry on transient Ollama failures, and optionally enrich metadata with per-complexity completion counts for reporting.

## Open Questions / Next Steps
- Where to persist the structured outputs (append to existing JSONL, separate file, or embed within metadata)?
- Should extraction run inline after generation or as a post-processing step? (Recommend post-processing to isolate concerns.)
- Confirm the target Ollama model (`glm-4.6:cloud` vs. a lighter extraction model) and availability of structured-output support.
