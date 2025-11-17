#!/usr/bin/env python3
"""
Refine low-scoring structured outputs using evaluation feedback.

Loads evaluation results, identifies records below score threshold,
re-extracts structured output with feedback, re-evaluates, and updates
original files in-place.
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from statistics import mean
from typing import Dict, List

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from deepeval.test_case import LLMTestCase

from syntha.evaluation.adapter import OllamaJudge
from syntha.evaluation.metrics import FaithfulnessMetric, SchemaMetric, ScheduleIsolationMetric
from syntha import extractor
from syntha.extractor import extract_structured_with_feedback
from syntha.utils import ClientManager


def load_json(path: Path) -> Dict:
    """Load JSON file."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: Path, data: Dict) -> None:
    """Save JSON file atomically."""
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    tmp_path.replace(path)


def load_jsonl(path: Path) -> List[Dict]:
    """Load all records from JSONL file."""
    records = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def save_jsonl(path: Path, records: List[Dict]) -> List[int]:
    """
    Save records to JSONL file and return byte offsets.

    Returns:
        List of byte offsets for each record
    """
    offsets = []
    with open(path, "w", encoding="utf-8") as f:
        for record in records:
            offset = f.tell()
            offsets.append(offset)
            json.dump(record, f, ensure_ascii=False)
            f.write("\n")
    return offsets


def meta_path_for(path: Path) -> Path:
    """Get metadata path for a JSONL file."""
    return path.with_suffix(path.suffix + ".meta.json")


def evaluate_record(
    utterance: str,
    structured_output: dict,
    metrics: dict
) -> Dict:
    """
    Evaluate a single structured output.

    Returns:
        Dict with metric_results, overall_score, overall_pass
    """
    structured_json = json.dumps(structured_output, ensure_ascii=False)
    metric_results = {}
    numeric_scores = []

    # Schema metric
    schema_case = LLMTestCase(
        input=utterance,
        actual_output=structured_json,
    )
    schema_result = metrics["schema"].measure(schema_case)
    metric_results["schema"] = {
        "score": round(schema_result.get("score", 0.0) * 100, 2) if isinstance(schema_result, dict) else round(float(schema_result) * 100, 2),
        "passed": schema_result.get("passed", bool(schema_result)) if isinstance(schema_result, dict) else bool(schema_result),
        "reason": schema_result.get("reason", "") if isinstance(schema_result, dict) else "",
    }
    numeric_scores.append(schema_result.get("score", 0.0) if isinstance(schema_result, dict) else float(schema_result))

    # Faithfulness metric
    joined_statements = "\n".join(structured_output.get("normal_statements", []))
    faith_case = LLMTestCase(
        input=utterance,
        actual_output=joined_statements,
    )
    faith_result = metrics["faithfulness"].measure(faith_case)
    metric_results["faithfulness"] = {
        "score": round(faith_result.get("score", 0.0) * 100, 2),
        "passed": faith_result.get("passed", False),
        "reason": faith_result.get("reason", ""),
    }
    numeric_scores.append(faith_result.get("score", 0.0))

    # Schedule metric
    schedule_case = LLMTestCase(
        input=utterance,
        actual_output=structured_output.get("schedule", ""),
    )
    schedule_result = metrics["schedule"].measure(schedule_case)
    metric_results["schedule"] = {
        "score": round(schedule_result.get("score", 0.0) * 100, 2),
        "passed": schedule_result.get("passed", False),
        "reason": schedule_result.get("reason", ""),
    }
    numeric_scores.append(schedule_result.get("score", 0.0))

    overall_score = mean(numeric_scores) if numeric_scores else 0.0
    overall_pass = all(entry["passed"] for entry in metric_results.values())

    return {
        "metric_results": metric_results,
        "overall_score": round(overall_score * 100, 2),
        "overall_pass": overall_pass,
    }


def refine_low_scoring_records(
    eval_records: List[Dict],
    structured_records: List[Dict],
    min_score: float,
    metrics: dict,
    model: str,
    temperature: float,
    dry_run: bool
) -> tuple[List[Dict], List[Dict], int]:
    """
    Refine low-scoring records and return updated lists.

    Returns:
        Tuple of (updated_structured_records, updated_eval_records, refined_count)
    """
    # Build record_id to index maps
    eval_map = {rec["record_id"]: idx for idx, rec in enumerate(eval_records)}
    struct_map = {rec["record_id"]: idx for idx, rec in enumerate(structured_records)}

    refined_count = 0

    print(f"\n{'=' * 80}")
    print(f"REFINEMENT PROCESS (threshold: {min_score}%)")
    print(f"{'=' * 80}\n")

    for eval_record in eval_records:
        record_id = eval_record["record_id"]
        overall_score = eval_record["overall_score"]

        # Skip if score is above threshold
        if overall_score >= min_score:
            continue

        # Find corresponding structured record
        if record_id not in struct_map:
            print(f"⚠ Warning: {record_id} not found in structured data, skipping")
            continue

        struct_idx = struct_map[record_id]
        struct_record = structured_records[struct_idx]

        utterance = struct_record.get("utterance", "")
        previous_output = struct_record.get("structured_output", {})

        if not previous_output:
            print(f"⚠ Warning: {record_id} has no structured_output, skipping")
            continue

        print(f"\n[{refined_count + 1}] Refining {record_id} (score: {overall_score}%)")

        if dry_run:
            print(f"  [DRY RUN] Would refine this record")
            refined_count += 1
            continue

        # Extract feedback
        feedback = eval_record.get("metric_results", {})

        try:
            # Re-extract with feedback
            print(f"  → Re-extracting with feedback...")
            new_extraction = extract_structured_with_feedback(
                utterance=utterance,
                previous_output=previous_output,
                feedback=feedback,
                model=model,
                temperature=temperature
            )

            new_structured_output = {
                "normal_statements": new_extraction.normal_statements,
                "schedule": new_extraction.schedule
            }

            # Re-evaluate
            print(f"  → Re-evaluating...")
            new_eval = evaluate_record(utterance, new_structured_output, metrics)

            # Update records
            structured_records[struct_idx]["structured_output"] = new_structured_output

            eval_idx = eval_map[record_id]
            eval_records[eval_idx].update({
                "metric_results": new_eval["metric_results"],
                "overall_score": new_eval["overall_score"],
                "overall_pass": new_eval["overall_pass"],
                "evaluated_at": datetime.utcnow().isoformat(),
            })

            print(f"  ✓ New score: {new_eval['overall_score']}% (Δ {new_eval['overall_score'] - overall_score:+.2f}%)")
            refined_count += 1

        except Exception as e:
            print(f"  ✗ Error refining {record_id}: {e}")
            continue

    return structured_records, eval_records, refined_count


def update_metadata(
    struct_meta_path: Path,
    eval_meta_path: Path,
    struct_offsets: List[int],
    eval_offsets: List[int]
) -> None:
    """Update metadata files with new offsets."""
    # Update structured metadata
    if struct_meta_path.exists():
        struct_meta = load_json(struct_meta_path)
        plan = struct_meta.get("plan", [])
        for entry in plan:
            idx = entry["index"]
            if idx < len(struct_offsets):
                entry["output_offset"] = struct_offsets[idx]
        save_json(struct_meta_path, struct_meta)
        print(f"  ✓ Updated {struct_meta_path}")

    # Update evaluation metadata
    if eval_meta_path.exists():
        eval_meta = load_json(eval_meta_path)
        plan = eval_meta.get("plan", [])
        for entry in plan:
            idx = entry["index"]
            if idx < len(eval_offsets):
                entry["eval_offset"] = eval_offsets[idx]
        save_json(eval_meta_path, eval_meta)
        print(f"  ✓ Updated {eval_meta_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Refine low-scoring structured outputs using evaluation feedback."
    )
    parser.add_argument(
        "--min-score",
        type=float,
        default=90.0,
        help="Minimum overall score threshold (default: 90.0)",
    )
    parser.add_argument(
        "--input-eval",
        default="outputs/evaluations/campaign_rules_eval.jsonl",
        help="Input evaluation JSONL file",
    )
    parser.add_argument(
        "--input-structured",
        default="outputs/structured/campaign_rules_structured.jsonl",
        help="Input structured JSONL file",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.0,
        help="LLM temperature for refinement (default: 0.0)",
    )
    parser.add_argument(
        "--faithfulness-threshold",
        type=float,
        default=0.8,
        help="Faithfulness metric threshold (default: 0.8)",
    )
    parser.add_argument(
        "--schedule-threshold",
        type=float,
        default=0.8,
        help="Schedule isolation metric threshold (default: 0.8)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview what would be refined without making changes",
    )
    args = parser.parse_args()

    eval_path = Path(args.input_eval)
    struct_path = Path(args.input_structured)

    # Validate inputs
    if not eval_path.exists():
        print(f"✗ Error: Evaluation file not found: {eval_path}")
        return 1

    if not struct_path.exists():
        print(f"✗ Error: Structured file not found: {struct_path}")
        return 1

    print(f"\n{'=' * 80}")
    print(f"LOW-SCORE REFINEMENT")
    print(f"{'=' * 80}")
    print(f"\nConfiguration:")
    print(f"  Min score threshold : {args.min_score}%")
    print(f"  Evaluation file     : {eval_path}")
    print(f"  Structured file     : {struct_path}")
    print(f"  Temperature         : {args.temperature}")
    print(f"  Dry run             : {args.dry_run}")

    # Load records
    print(f"\nLoading records...")
    eval_records = load_jsonl(eval_path)
    struct_records = load_jsonl(struct_path)
    print(f"  ✓ Loaded {len(eval_records)} evaluation records")
    print(f"  ✓ Loaded {len(struct_records)} structured records")

    # Count low-scoring records
    low_score_count = sum(1 for rec in eval_records if rec["overall_score"] < args.min_score)
    print(f"\n  Found {low_score_count} records below {args.min_score}% threshold")

    if low_score_count == 0:
        print(f"\n✓ No records need refinement!")
        return 0

    if args.dry_run:
        print(f"\n[DRY RUN MODE] Would refine {low_score_count} records")
        return 0

    # Initialize LLM and metrics
    print(f"\nInitializing LLM and metrics...")
    client_manager = ClientManager()

    # Initialize extractor module's global client_manager
    extractor.client_manager = client_manager

    model = client_manager.model
    print(f"  ✓ Using model: {model}")

    judge = OllamaJudge()
    metrics = {
        "schema": SchemaMetric(model=judge),
        "faithfulness": FaithfulnessMetric(llm=judge, threshold=args.faithfulness_threshold),
        "schedule": ScheduleIsolationMetric(llm=judge, threshold=args.schedule_threshold),
    }

    # Refine low-scoring records
    updated_struct, updated_eval, refined_count = refine_low_scoring_records(
        eval_records=eval_records,
        structured_records=struct_records,
        min_score=args.min_score,
        metrics=metrics,
        model=model,
        temperature=args.temperature,
        dry_run=args.dry_run
    )

    if refined_count == 0:
        print(f"\n⚠ No records were successfully refined")
        return 0

    # Write updated files
    print(f"\n{'=' * 80}")
    print(f"UPDATING FILES")
    print(f"{'=' * 80}\n")

    print(f"Writing updated structured records...")
    struct_offsets = save_jsonl(struct_path, updated_struct)
    print(f"  ✓ Wrote {len(updated_struct)} records to {struct_path}")

    print(f"Writing updated evaluation records...")
    eval_offsets = save_jsonl(eval_path, updated_eval)
    print(f"  ✓ Wrote {len(updated_eval)} records to {eval_path}")

    # Update metadata
    print(f"\nUpdating metadata files...")
    struct_meta_path = meta_path_for(struct_path)
    eval_meta_path = meta_path_for(eval_path)
    update_metadata(struct_meta_path, eval_meta_path, struct_offsets, eval_offsets)

    print(f"\n{'=' * 80}")
    print(f"✓ REFINEMENT COMPLETE")
    print(f"{'=' * 80}")
    print(f"\n  Refined: {refined_count} / {low_score_count} low-scoring records")
    print(f"  Updated: {struct_path}")
    print(f"  Updated: {eval_path}\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
