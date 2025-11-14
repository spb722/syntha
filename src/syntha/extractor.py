import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

from pydantic import BaseModel

from syntha.utils import ClientManager

# Global client manager and model configuration
client_manager = None
EXTRACT_MODEL = None


class UtteranceExtraction(BaseModel):
    normal_statements: List[str]
    schedule: str


EXTRACT_SYSTEM = """
You transform telecom campaign instructions into structured logic.

Telecom instructions often mix:
- Targeting logic
- Actions/offers
- Bonuses or incentives
- Sampling/throttling rules
- Policy/exclusion controls
- Scheduling/timing information
- Branching/fallback logic

Segmentation rules:
- Group related conditions/actions/bonuses/policies into standalone statements.
- Treat each branch (if / else if / otherwise) as a separate statement.
- Do NOT include scheduling in normal_statements—schedule belongs only in the schedule field.
- Avoid pronouns or cross references such as "these users".
- Every normal_statement must be self-contained and preserve all business meaning.
- If no schedule exists, return an empty string for schedule.

Output schema (strict):
{
  "type": "object",
  "properties": {
    "normal_statements": {
      "type": "array",
      "items": {
        "type": "string",
        "description": "Standalone rule containing conditions, actions, bonuses, sampling, and policies."
      },
      "description": "List of logically distinct rule statements."
    },
    "schedule": {
      "type": "string",
      "description": "Scheduling instruction only; leave empty if not provided."
    }
  },
  "required": ["normal_statements", "schedule"]
}
"""


def _clean_structured_payload(raw: str) -> str:
    """
    Remove Markdown fences if Ollama wraps structured output in ```json blocks.
    """
    text = raw.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        # drop opening fence
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        # drop closing fence(s)
        while lines and lines[-1].strip().startswith("```"):
            lines.pop()
        text = "\n".join(lines).strip()
    return text


def extract_structured(utterance: str, model: str, temperature: float):
    """
    Use Ollama structured output to parse an utterance.
    """
    resp = client_manager.chat(
        messages=[
            {"role": "system", "content": EXTRACT_SYSTEM.strip()},
            {"role": "user", "content": f"Extract fields from this instruction:\n{utterance}"}
        ],
        format=UtteranceExtraction.model_json_schema(),
        options={"temperature": temperature}
    )
    content = _clean_structured_payload(resp["message"]["content"])
    return UtteranceExtraction.model_validate_json(content)


def atomic_write_json(path: Path, payload):
    """
    Persist JSON atomically through a temporary file.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_name(path.name + ".tmp")
    with open(tmp_path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
    tmp_path.replace(path)


def append_jsonl(path: Path, record) -> int:
    """
    Append a JSON record to a JSONL file. Returns byte offset.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as handle:
        offset = handle.tell()
        json.dump(record, handle, ensure_ascii=False)
        handle.write("\n")
        handle.flush()
        return offset


def meta_path_for_output(output_path: Path) -> Path:
    suffix = output_path.suffix or ""
    return output_path.with_suffix(f"{suffix}.meta.json")


def load_json(path: Path):
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def prepare_plan_from_generation_meta(meta_path: Path):
    meta = load_json(meta_path)
    plan = meta.get("plan")
    if not plan:
        raise ValueError("Generation metadata is missing the plan array.")

    prepared = []
    for entry in plan:
        offset = entry.get("offset")
        record_id = entry.get("record_id")
        if offset is None or record_id is None:
            raise ValueError(
                "Generation metadata entries must include 'offset' and 'record_id'. "
                "Re-run step 1 with the latest generator before extracting."
            )
        prepared.append({
            "index": entry["index"],
            "record_id": record_id,
            "offset": offset,
            "complexity": entry.get("complexity"),
            "output_offset": None,
            "status": None
        })
    return prepared


def create_extraction_meta(input_file: Path, input_meta: Path, output_file: Path,
                           plan, model: str, temperature: float):
    return {
        "input_file": str(input_file.resolve()),
        "input_meta_file": str(input_meta.resolve()),
        "output_file": str(output_file.resolve()),
        "model": model,
        "temperature": temperature,
        "plan": plan,
        "completed": 0,
        "started_at": datetime.utcnow().isoformat(),
    }


def validate_resume_meta(meta, args, output_path: Path):
    if Path(meta.get("input_file")).resolve() != Path(args.input).resolve():
        raise ValueError("Input file mismatch between metadata and CLI arguments.")
    if Path(meta.get("output_file")).resolve() != output_path.resolve():
        raise ValueError("Output path mismatch between metadata and CLI arguments.")
    if meta.get("model") != args.model:
        raise ValueError(
            f"Extractor model mismatch (meta uses {meta.get('model')}, CLI requests {args.model})."
        )
    if abs(meta.get("temperature", args.temperature) - args.temperature) > 1e-9:
        raise ValueError(
            "Temperature mismatch. Use the same temperature as the in-progress run or start fresh."
        )


def load_input_record(handle, offset: int):
    handle.seek(offset)
    line = handle.readline()
    if not line:
        raise ValueError(f"Reached EOF while seeking to offset {offset}.")
    return json.loads(line)


def run_extraction(source_path: Path, output_path: Path, meta_path: Path, plan,
                   start_index: int, model: str, temperature: float,
                   max_records: Optional[int], meta: dict) -> Tuple[int, Optional[dict]]:
    total = len(plan)
    if start_index >= total:
        print("✓ No remaining records to process.")
        return 0, None

    processed_this_run = 0
    first_completed = None

    print(f"\n{'=' * 80}")
    print(
        f"EXTRACTING STRUCTURED RULES ({total - start_index} remaining, resume index {start_index})"
    )
    print(f"{'=' * 80}\n")

    with open(source_path, "r", encoding="utf-8") as source_handle:
        for idx in range(start_index, total):
            if max_records is not None and processed_this_run >= max_records:
                break

            entry = plan[idx]
            record_id = entry["record_id"]
            print(f"\n[{idx + 1}/{total}] Processing {record_id}")

            record = load_input_record(source_handle, entry["offset"])
            input_record_id = record.get("record_id")
            if input_record_id and input_record_id != record_id:
                raise ValueError(
                    f"Record ID mismatch at index {idx}: meta has {record_id}, "
                    f"dataset contains {input_record_id}."
                )

            status = "completed"
            try:
                extraction = extract_structured(
                    record["utterance"],
                    model=model,
                    temperature=temperature,
                )
                record["structured_output"] = extraction.model_dump()
                record.pop("structured_error", None)
            except Exception as exc:
                print(f"\n{'=' * 80}")
                print(f"✗ EXTRACTION FAILED for {record_id}")
                print(f"Error: {exc}")
                print(f"{'=' * 80}\n")
                raise  # Exit immediately on any error

            record["structured_status"] = status
            output_offset = append_jsonl(output_path, record)

            entry["output_offset"] = output_offset
            entry["status"] = status

            processed_this_run += 1
            if status == "completed" and first_completed is None:
                first_completed = record

            meta["plan"][idx] = entry
            meta["completed"] = idx + 1
            meta["last_processed_id"] = record_id
            meta["last_processed_at"] = datetime.utcnow().isoformat()
            atomic_write_json(meta_path, meta)

            print(f"✓ Stored structured record for {record_id} ({status})")

    print(f"\n{'=' * 80}")
    print(f"✓ Processed {processed_this_run} records this session")
    print(f"✓ Total completed: {start_index + processed_this_run} / {total}")
    print(f"{'=' * 80}\n")

    return processed_this_run, first_completed


def parse_args():
    parser = argparse.ArgumentParser(
        description="Extract structured statements from campaign rule dataset entries."
    )
    parser.add_argument(
        "--mode",
        choices=["fresh", "resume"],
        default="fresh",
        help="fresh: start over, overwrite output/meta. resume: continue from previous run.",
    )
    parser.add_argument(
        "--input",
        default="outputs/datasets/campaign_rules_dataset.jsonl",
        help="Path to the generated campaign rules JSONL file from step 1.",
    )
    parser.add_argument(
        "--input-meta",
        help="Optional path to the step-1 metadata file. Defaults to <input>.meta.json.",
    )
    parser.add_argument(
        "--output",
        default="outputs/structured/campaign_rules_structured.jsonl",
        help="Destination JSONL file with structured statements.",
    )
    parser.add_argument(
        "--model",
        default="glm-4.6:cloud",
        help="Ollama model to use for structured extraction.",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.0,
        help="Sampling temperature for extraction.",
    )
    parser.add_argument(
        "--max-records",
        type=int,
        help="Optional cap on records to process in this run.",
    )
    return parser.parse_args()


def main():
    global client_manager, EXTRACT_MODEL

    args = parse_args()

    # Initialize ClientManager with multi-client rotation support
    client_manager = ClientManager()
    EXTRACT_MODEL = client_manager.model

    input_path = Path(args.input)
    if not input_path.exists():
        raise FileNotFoundError(f"Input dataset '{input_path}' not found.")

    input_meta_path = Path(
        args.input_meta
        if args.input_meta
        else meta_path_for_output(input_path)
    )
    if not input_meta_path.exists():
        raise FileNotFoundError(
            f"Step-1 metadata '{input_meta_path}' not found. Run the generator first."
        )

    output_path = Path(args.output)
    if output_path.suffix != ".jsonl":
        output_path = output_path.with_suffix(".jsonl")
    extractor_meta_path = meta_path_for_output(output_path)

    if args.mode == "resume":
        if not extractor_meta_path.exists():
            raise FileNotFoundError(
                f"Extractor metadata '{extractor_meta_path}' not found. "
                "Start with --mode fresh."
            )
        meta = load_json(extractor_meta_path)
        validate_resume_meta(meta, args, output_path)
        plan = meta.get("plan", [])
        if not plan:
            raise ValueError("Extractor metadata contains no plan.")
        start_index = int(meta.get("completed", 0))
    else:
        plan = prepare_plan_from_generation_meta(input_meta_path)
        meta = create_extraction_meta(
            input_file=input_path,
            input_meta=input_meta_path,
            output_file=output_path,
            plan=plan,
            model=args.model,
            temperature=args.temperature,
        )
        if output_path.exists():
            output_path.unlink()
        if extractor_meta_path.exists():
            extractor_meta_path.unlink()
        atomic_write_json(extractor_meta_path, meta)
        start_index = 0

    print("\nExtraction plan:")
    print(f"  Input dataset : {input_path.resolve()}")
    print(f"  Input meta    : {input_meta_path.resolve()}")
    print(f"  Output file   : {output_path.resolve()}")
    print(f"  Metadata file : {extractor_meta_path.resolve()}")
    print(f"  Total records : {len(plan)}")
    print(f"  Completed     : {start_index}")

    processed, sample = run_extraction(
        source_path=input_path,
        output_path=output_path,
        meta_path=extractor_meta_path,
        plan=plan,
        start_index=start_index,
        model=args.model,
        temperature=args.temperature,
        max_records=args.max_records,
        meta=meta,
    )

    if processed > 0 and sample:
        print("\n" + "=" * 80)
        print("SAMPLE STRUCTURED OUTPUT")
        print("=" * 80)
        print(f"Record ID: {sample.get('record_id')}")
        structured = sample.get("structured_output") or {}
        print("\nNormal Statements:")
        for statement in structured.get("normal_statements", []):
            print(f"  - {statement}")
        print(f"\nSchedule: {structured.get('schedule', '')}")


if __name__ == "__main__":
    main()
