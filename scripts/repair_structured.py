#!/usr/bin/env python3
"""Repair structured campaign rules that are missing JSON output."""

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from pydantic import ValidationError

from syntha import extractor as extractor_mod
from syntha.extractor import UtteranceExtraction
from syntha.utils import ClientManager


def load_jsonl(path: Path) -> List[Dict]:
    """Load JSONL records into memory."""
    records: List[Dict] = []
    with open(path, "r", encoding="utf-8") as handle:
        for line_num, raw in enumerate(handle, 1):
            raw = raw.strip()
            if not raw:
                continue
            try:
                record = json.loads(raw)
                record["_line_number"] = line_num
                records.append(record)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Malformed JSON on line {line_num}: {exc}") from exc
    return records


def save_jsonl(path: Path, records: List[Dict]) -> List[int]:
    """Persist records back to JSONL and return byte offsets."""
    offsets: List[int] = []
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        for record in records:
            record.pop("_line_number", None)
            offsets.append(handle.tell())
            json.dump(record, handle, ensure_ascii=False)
            handle.write("\n")
    return offsets


def load_metadata(path: Path) -> Dict:
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def save_metadata(path: Path, payload: Dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_name(path.name + ".tmp")
    with open(tmp_path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
    tmp_path.replace(path)


def _parse_structured_if_string(record: Dict) -> Optional[str]:
    structured = record.get("structured_output")
    if isinstance(structured, str):
        try:
            record["structured_output"] = json.loads(structured)
        except json.JSONDecodeError:
            return "structured_output_not_json"
    return None


def needs_regeneration(record: Dict) -> Optional[str]:
    """Return a string reason when structured data must be regenerated."""
    if "utterance" not in record:
        return "missing_utterance"

    parsed_issue = _parse_structured_if_string(record)
    if parsed_issue:
        return parsed_issue

    structured = record.get("structured_output")
    if structured is None:
        return "missing_structured_output"

    try:
        # Ensure schema compliance
        UtteranceExtraction.model_validate(structured)
    except ValidationError:
        return "invalid_structured_output"

    if record.get("structured_status") != "completed":
        return "incomplete_status"

    return None


def ensure_client_manager(config_path: Path) -> ClientManager:
    """Instantiate a ClientManager and register it with the extractor module."""
    if extractor_mod.client_manager is None:
        extractor_mod.client_manager = ClientManager(config_path=str(config_path))
        extractor_mod.EXTRACT_MODEL = extractor_mod.client_manager.model
    return extractor_mod.client_manager


def regenerate_structured(record: Dict, temperature: float) -> Tuple[Dict, Dict]:
    """Run extraction again and attach repair metadata."""
    extraction = extractor_mod.extract_structured(
        record["utterance"],
        model=extractor_mod.EXTRACT_MODEL or "unknown",
        temperature=temperature,
    )
    record["structured_output"] = extraction.model_dump()
    record["structured_status"] = "completed"
    record.pop("structured_error", None)

    history_entry = {
        "repaired_at": datetime.utcnow().isoformat(),
        "reason": "structured_regeneration",
    }
    history = record.get("repair_history") or []
    history.append(history_entry)
    record["repair_history"] = history
    return record, history_entry


def update_plan_offsets(metadata: Dict, records: List[Dict], offsets: List[int]):
    """Synchronize plan offsets/status with rewritten records."""
    id_to_state: Dict[str, Tuple[int, str]] = {}
    for record, offset in zip(records, offsets):
        record_id = record.get("record_id")
        if not record_id:
            continue
        status = record.get("structured_status") or "completed"
        id_to_state[record_id] = (offset, status)

    plan = metadata.get("plan") or []
    completed = 0
    last_completed_id = None
    for entry in plan:
        record_id = entry.get("record_id")
        if record_id in id_to_state:
            offset, status = id_to_state[record_id]
            entry["output_offset"] = offset
            entry["status"] = status
            if status == "completed":
                completed += 1
                last_completed_id = record_id
    metadata["completed"] = completed
    if last_completed_id:
        metadata["last_processed_id"] = last_completed_id
        metadata["last_processed_at"] = datetime.utcnow().isoformat()


def repair_structured_dataset(
    input_path: Path,
    meta_path: Path,
    config_path: Path,
    temperature: float,
    dry_run: bool = False,
):
    print(f"📖 Loading structured dataset from {input_path}...")
    records = load_jsonl(input_path)
    print(f"✓ Loaded {len(records)} records")

    print(f"📖 Loading metadata from {meta_path}...")
    metadata = load_metadata(meta_path)
    print("✓ Metadata loaded")

    issues: Dict[str, List[int]] = {}
    for idx, record in enumerate(records):
        reason = needs_regeneration(record)
        if reason:
            issues.setdefault(reason, []).append(idx)

    total_issues = sum(len(v) for v in issues.values())
    if total_issues == 0:
        print("✓ All records already contain valid structured output.")
        return {"total_records": len(records), "repaired": 0, "issues": issues}

    print(f"⚠️  Found {total_issues} record(s) missing structured JSON.")
    for reason, idxs in issues.items():
        print(f"  - {reason}: {len(idxs)} record(s)")

    if dry_run:
        print("ℹ️  DRY RUN enabled—no repairs executed.")
        return {"total_records": len(records), "repaired": 0, "issues": issues}

    ensure_client_manager(config_path)
    repaired = 0
    failed = 0

    for reason, idxs in issues.items():
        for idx in idxs:
            record = records[idx]
            record_id = record.get("record_id", f"line-{record.get('_line_number')}")
            print(f"🔄 Regenerating {record_id} ({reason})...")
            try:
                regenerate_structured(record, temperature)
                repaired += 1
                print(f"  ✓ Regenerated {record_id}")
            except Exception as exc:  # noqa: BLE001
                failed += 1
                record["structured_status"] = "failed"
                record["structured_error"] = str(exc)
                print(f"  ✗ Failed to regenerate {record_id}: {exc}")

    print("💾 Writing repaired dataset...")
    offsets = save_jsonl(input_path, records)
    print("✓ Dataset updated in place")

    update_plan_offsets(metadata, records, offsets)
    history = metadata.get("repair_history") or []
    history.append({
        "repaired_at": datetime.utcnow().isoformat(),
        "records_scanned": len(records),
        "records_repaired": repaired,
        "records_failed": failed,
        "issues_by_type": {k: len(v) for k, v in issues.items()},
    })
    metadata["repair_history"] = history

    print("💾 Updating metadata...")
    save_metadata(meta_path, metadata)
    print("✓ Metadata saved")

    return {
        "total_records": len(records),
        "repaired": repaired,
        "failed": failed,
        "issues": issues,
    }


def parse_args():
    parser = argparse.ArgumentParser(
        description="Repair structured campaign rules that are missing structured_output JSON."
    )
    parser.add_argument(
        "--input",
        default="outputs/structured/campaign_rules_structured.jsonl",
        help="Path to structured dataset JSONL (default: outputs/structured/campaign_rules_structured.jsonl)",
    )
    parser.add_argument(
        "--meta",
        help="Path to extractor metadata (default: <input>.meta.json)",
    )
    parser.add_argument(
        "--config",
        default="configs/generation_config.yaml",
        help="Path to Ollama client configuration",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.0,
        help="Temperature to use when regenerating structured output",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Analyze only; do not modify files",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        raise FileNotFoundError(f"Input dataset not found: {input_path}")

    meta_path = Path(args.meta) if args.meta else input_path.with_suffix(f"{input_path.suffix}.meta.json")
    if not meta_path.exists():
        raise FileNotFoundError(f"Metadata file not found: {meta_path}")

    config_path = Path(args.config)
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    repair_structured_dataset(
        input_path=input_path,
        meta_path=meta_path,
        config_path=config_path,
        temperature=args.temperature,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()
