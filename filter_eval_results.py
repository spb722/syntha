import argparse
import json
from pathlib import Path
from typing import Dict, List


def load_jsonl(path: Path) -> List[Dict]:
    """Load all records from a JSONL file."""
    records = []
    with open(path, "r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def write_jsonl(path: Path, records: List[Dict]) -> None:
    """Write records to a JSONL file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        for record in records:
            json.dump(record, handle, ensure_ascii=False)
            handle.write("\n")


def create_record_id_map(structured_records: List[Dict]) -> Dict[str, Dict]:
    """Create a map of record_id to structured data."""
    return {record["record_id"]: record for record in structured_records}


def filter_eval_results(
    eval_path: Path,
    structured_path: Path,
    passed_output: Path,
    failed_output: Path,
) -> None:
    """
    Filter evaluation results into passed and failed files,
    including corresponding structured data.
    """
    print(f"Loading evaluation results from: {eval_path}")
    eval_records = load_jsonl(eval_path)

    print(f"Loading structured data from: {structured_path}")
    structured_records = load_jsonl(structured_path)
    structured_map = create_record_id_map(structured_records)

    passed_records = []
    failed_records = []

    for eval_record in eval_records:
        record_id = eval_record["record_id"]
        overall_pass = eval_record["overall_pass"]

        # Get corresponding structured data
        structured_data = structured_map.get(record_id)
        if not structured_data:
            print(f"Warning: No structured data found for {record_id}")
            continue

        # Combine evaluation results with structured data
        combined_record = {
            **structured_data,
            "evaluation": {
                "metric_results": eval_record["metric_results"],
                "overall_score": eval_record["overall_score"],
                "overall_pass": eval_record["overall_pass"],
                "evaluated_at": eval_record["evaluated_at"],
            }
        }

        if overall_pass:
            passed_records.append(combined_record)
        else:
            failed_records.append(combined_record)

    # Write results
    write_jsonl(passed_output, passed_records)
    write_jsonl(failed_output, failed_records)

    # Print summary
    total = len(eval_records)
    passed_count = len(passed_records)
    failed_count = len(failed_records)

    print(f"\n{'=' * 80}")
    print(f"FILTERING COMPLETE")
    print(f"{'=' * 80}")
    print(f"Total records evaluated: {total}")
    print(f"Passed: {passed_count} ({passed_count/total*100:.1f}%)")
    print(f"Failed: {failed_count} ({failed_count/total*100:.1f}%)")
    print(f"\nOutput files:")
    print(f"  Passed: {passed_output.resolve()}")
    print(f"  Failed: {failed_output.resolve()}")
    print(f"{'=' * 80}\n")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Filter evaluation results into passed and failed records."
    )
    parser.add_argument(
        "--eval",
        default="campaign_rules_eval.jsonl",
        help="Path to evaluation results JSONL file.",
    )
    parser.add_argument(
        "--structured",
        default="campaign_rules_structured.jsonl",
        help="Path to structured dataset JSONL file.",
    )
    parser.add_argument(
        "--passed-output",
        default="campaign_rules_passed.jsonl",
        help="Output file for passed records.",
    )
    parser.add_argument(
        "--failed-output",
        default="campaign_rules_failed.jsonl",
        help="Output file for failed records.",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    eval_path = Path(args.eval)
    structured_path = Path(args.structured)
    passed_output = Path(args.passed_output)
    failed_output = Path(args.failed_output)

    if not eval_path.exists():
        raise FileNotFoundError(f"Evaluation file not found: {eval_path}")

    if not structured_path.exists():
        raise FileNotFoundError(f"Structured data file not found: {structured_path}")

    filter_eval_results(eval_path, structured_path, passed_output, failed_output)


if __name__ == "__main__":
    main()
