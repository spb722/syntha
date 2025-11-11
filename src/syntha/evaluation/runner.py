import argparse
import json
from datetime import datetime
from pathlib import Path
from statistics import mean
from typing import Dict, List, Optional

from deepeval.test_case import LLMTestCase

from .adapter import OllamaJudge
from .metrics import FaithfulnessMetric, SchemaMetric, ScheduleIsolationMetric


def meta_path_for_output(output_path: Path) -> Path:
    suffix = output_path.suffix or ""
    return output_path.with_suffix(f"{suffix}.meta.json")


def load_json(path: Path) -> Dict:
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def atomic_write_json(path: Path, payload: Dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_name(path.name + ".tmp")
    with open(tmp_path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
    tmp_path.replace(path)


def append_jsonl(path: Path, record: Dict) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as handle:
        offset = handle.tell()
        json.dump(record, handle, ensure_ascii=False)
        handle.write("\n")
        handle.flush()
        return offset


def prepare_plan_from_structured_meta(meta_path: Path) -> List[Dict]:
    meta = load_json(meta_path)
    plan = meta.get("plan")
    if not plan:
        raise ValueError("Structured dataset metadata missing plan.")

    prepared = []
    for entry in plan:
        offset = entry.get("output_offset")
        record_id = entry.get("record_id")
        if offset is None or record_id is None:
            raise ValueError(
                "Structured metadata entries must include 'output_offset' and 'record_id'. "
                "Re-run structured extraction so offsets are recorded."
            )
        prepared.append(
            {
                "index": entry["index"],
                "record_id": record_id,
                "offset": offset,
                "status": None,
                "eval_offset": None,
            }
        )
    return prepared


def create_eval_meta(
    input_file: Path,
    input_meta: Path,
    output_file: Path,
    plan: List[Dict],
    model: str,
    thresholds: Dict[str, float],
) -> Dict:
    return {
        "input_file": str(input_file.resolve()),
        "input_meta_file": str(input_meta.resolve()),
        "output_file": str(output_file.resolve()),
        "model": model,
        "thresholds": thresholds,
        "plan": plan,
        "completed": 0,
        "started_at": datetime.utcnow().isoformat(),
    }


def validate_resume_meta(meta: Dict, args, output_path: Path) -> None:
    if Path(meta.get("input_file")).resolve() != Path(args.input).resolve():
        raise ValueError("Input structured file mismatch; use --mode fresh.")
    if Path(meta.get("output_file")).resolve() != output_path.resolve():
        raise ValueError("Evaluation output path mismatch; use --mode fresh.")
    if meta.get("model") != args.model:
        raise ValueError(
            f"Model mismatch (meta uses {meta.get('model')}, CLI requests {args.model})."
        )


def load_structured_record(handle, offset: int) -> Dict:
    handle.seek(offset)
    line = handle.readline()
    if not line:
        raise ValueError(f"Reached EOF while seeking to offset {offset}.")
    return json.loads(line)


def compute_metric_entry(result, scale: int = 100) -> Dict:
    if isinstance(result, dict):
        score = result.get("score", 0.0)
        passed = result.get("passed", False)
        reason = result.get("reason", "")
    else:
        # JsonCorrectnessMetric currently returns bare 0/1
        score = float(result)
        passed = bool(result)
        reason = ""
    return {
        "score": round(score * scale, 2),
        "passed": bool(passed),
        "reason": reason,
    }


def run_evaluations(
    source_path: Path,
    output_path: Path,
    meta_path: Path,
    plan: List[Dict],
    start_index: int,
    model: str,
    thresholds: Dict[str, float],
    max_records: Optional[int],
) -> None:
    judge = OllamaJudge(model_name=model)
    metrics = {
        "schema": SchemaMetric(model=judge),
        "faithfulness": FaithfulnessMetric(llm=judge, threshold=thresholds["faithfulness"]),
        "schedule": ScheduleIsolationMetric(
            llm=judge, threshold=thresholds["schedule"]
        ),
    }

    processed = 0
    total = len(plan)

    print(f"\n{'=' * 80}")
    print(f"DEEPEVAL QUALITY CHECK ({total - start_index} remaining)")
    print(f"{'=' * 80}\n")

    with open(source_path, "r", encoding="utf-8") as handle:
        for idx in range(start_index, total):
            if max_records is not None and processed >= max_records:
                break

            entry = plan[idx]
            record_id = entry["record_id"]
            print(f"\n[{idx + 1}/{total}] Evaluating {record_id}")

            record = load_structured_record(handle, entry["offset"])
            utterance = record.get("utterance", "")
            structured = record.get("structured_output")

            metric_results = {}
            numeric_scores = []

            if not structured:
                reason = "structured_output missing; cannot evaluate"
                metric_results["schema"] = {
                    "score": 0.0,
                    "passed": False,
                    "reason": reason,
                }
            else:
                structured_json = json.dumps(structured, ensure_ascii=False)
                schema_case = LLMTestCase(
                    input=utterance,
                    actual_output=structured_json,
                )
                schema_result = metrics["schema"].measure(schema_case)
                metric_results["schema"] = compute_metric_entry(schema_result)
                if isinstance(schema_result, dict):
                    numeric_scores.append(schema_result.get("score", 0.0))
                else:
                    numeric_scores.append(float(schema_result))

                joined_statements = "\n".join(structured.get("normal_statements", []))
                faith_case = LLMTestCase(
                    input=utterance,
                    actual_output=joined_statements,
                )
                faith_result = metrics["faithfulness"].measure(faith_case)
                metric_results["faithfulness"] = compute_metric_entry(faith_result)
                numeric_scores.append(faith_result.get("score", 0.0))

                schedule_case = LLMTestCase(
                    input=utterance,
                    actual_output=structured.get("schedule", ""),
                )
                schedule_result = metrics["schedule"].measure(schedule_case)
                metric_results["schedule"] = compute_metric_entry(schedule_result)
                numeric_scores.append(schedule_result.get("score", 0.0))

            overall_score = mean(numeric_scores) if numeric_scores else 0.0
            overall_pass = all(entry["passed"] for entry in metric_results.values())

            eval_record = {
                "record_id": record_id,
                "metric_results": metric_results,
                "overall_score": round(overall_score * 100, 2),
                "overall_pass": overall_pass,
                "evaluated_at": datetime.utcnow().isoformat(),
            }

            eval_offset = append_jsonl(output_path, eval_record)
            entry["eval_offset"] = eval_offset
            entry["status"] = "completed"

            processed += 1

            meta = load_json(meta_path)
            meta["plan"][idx] = entry
            meta["completed"] = idx + 1
            meta["last_evaluated_id"] = record_id
            meta["last_evaluated_at"] = datetime.utcnow().isoformat()
            atomic_write_json(meta_path, meta)

            print(
                f"✓ Recorded evaluation for {record_id} "
                f"(overall {eval_record['overall_score']}/100, pass={overall_pass})"
            )

    print(f"\n{'=' * 80}")
    print(f"✓ Evaluated {processed} records this session")
    print(f"✓ Total completed: {start_index + processed} / {total}")
    print(f"{'=' * 80}\n")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Run DeepEval quality checks on structured campaign rules."
    )
    parser.add_argument(
        "--mode",
        choices=["fresh", "resume"],
        default="fresh",
        help="fresh: start over, resume: continue previous evaluation.",
    )
    parser.add_argument(
        "--input",
        default="campaign_rules_structured.jsonl",
        help="Structured dataset JSONL produced in step 2.",
    )
    parser.add_argument(
        "--input-meta",
        help="Path to structured dataset metadata (defaults to <input>.meta.json).",
    )
    parser.add_argument(
        "--output",
        default="campaign_rules_eval.jsonl",
        help="Destination JSONL for per-record evaluation scores.",
    )
    parser.add_argument(
        "--model",
        default="glm-4.6:cloud",
        help="Ollama model to use for LLM-as-judge metrics.",
    )
    parser.add_argument(
        "--faithfulness-threshold",
        type=float,
        default=0.8,
        help="Threshold for faithfulness metric pass/fail.",
    )
    parser.add_argument(
        "--schedule-threshold",
        type=float,
        default=0.8,
        help="Threshold for schedule isolation metric pass/fail.",
    )
    parser.add_argument(
        "--max-records",
        type=int,
        help="Optional limit on number of records to evaluate this run.",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        raise FileNotFoundError(f"Structured dataset '{input_path}' not found.")

    input_meta_path = Path(
        args.input_meta if args.input_meta else meta_path_for_output(input_path)
    )
    if not input_meta_path.exists():
        raise FileNotFoundError(
            f"Structured metadata '{input_meta_path}' missing. Run step 2 first."
        )

    output_path = Path(args.output)
    if output_path.suffix != ".jsonl":
        output_path = output_path.with_suffix(".jsonl")
    eval_meta_path = meta_path_for_output(output_path)

    thresholds = {
        "faithfulness": args.faithfulness_threshold,
        "schedule": args.schedule_threshold,
    }

    if args.mode == "resume":
        if not eval_meta_path.exists():
            raise FileNotFoundError(
                f"Evaluation metadata '{eval_meta_path}' missing. Start with --mode fresh."
            )
        meta = load_json(eval_meta_path)
        validate_resume_meta(meta, args, output_path)
        plan = meta.get("plan", [])
        if not plan:
            raise ValueError("Evaluation metadata contains no plan.")
        start_index = int(meta.get("completed", 0))
    else:
        plan = prepare_plan_from_structured_meta(input_meta_path)
        meta = create_eval_meta(
            input_file=input_path,
            input_meta=input_meta_path,
            output_file=output_path,
            plan=plan,
            model=args.model,
            thresholds=thresholds,
        )
        if output_path.exists():
            output_path.unlink()
        if eval_meta_path.exists():
            eval_meta_path.unlink()
        atomic_write_json(eval_meta_path, meta)
        start_index = 0

    print("\nEvaluation plan:")
    print(f"  Input structured : {input_path.resolve()}")
    print(f"  Input meta       : {input_meta_path.resolve()}")
    print(f"  Output eval file : {output_path.resolve()}")
    print(f"  Eval meta        : {eval_meta_path.resolve()}")
    print(f"  Total records    : {len(plan)}")
    print(f"  Completed        : {start_index}")

    run_evaluations(
        source_path=input_path,
        output_path=output_path,
        meta_path=eval_meta_path,
        plan=plan,
        start_index=start_index,
        model=args.model,
        thresholds=thresholds,
        max_records=args.max_records,
    )


if __name__ == "__main__":
    main()
