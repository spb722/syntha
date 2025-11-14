#!/usr/bin/env python3
"""
Repair dataset by regenerating records with empty or invalid utterances.

This script:
1. Reads the dataset JSONL file and metadata
2. Validates each record (checks for empty utterances, too short, etc.)
3. Re-generates problematic records using original metadata (KPIs, complexity, tone)
4. Updates the JSONL file (in-place or new file)
5. Updates metadata to track repairs
"""

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

from syntha.generator import (
    load_kpi_data,
    generate_campaign_rule,
)
from syntha.utils import ClientManager


def load_jsonl(file_path: Path) -> List[Dict]:
    """Load all records from a JSONL file."""
    records = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            try:
                record = json.loads(line.strip())
                record['_line_number'] = line_num  # Track original line number
                records.append(record)
            except json.JSONDecodeError as e:
                print(f"⚠ Warning: Malformed JSON at line {line_num}: {e}")
                # Add placeholder for malformed record
                records.append({
                    '_line_number': line_num,
                    '_malformed': True,
                    '_error': str(e)
                })
    return records


def load_metadata(meta_path: Path) -> Dict:
    """Load metadata JSON file."""
    with open(meta_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_jsonl(file_path: Path, records: List[Dict]) -> List[int]:
    """
    Save records to JSONL file, removing internal tracking fields.

    Returns:
        List of byte offsets for each record
    """
    file_path.parent.mkdir(parents=True, exist_ok=True)
    offsets = []
    with open(file_path, 'w', encoding='utf-8') as f:
        for record in records:
            # Record the byte offset before writing
            offset = f.tell()
            offsets.append(offset)

            # Remove internal tracking fields before saving
            clean_record = {k: v for k, v in record.items()
                          if not k.startswith('_')}
            f.write(json.dumps(clean_record, ensure_ascii=False) + '\n')

    return offsets


def save_metadata(meta_path: Path, metadata: Dict):
    """Save metadata JSON file atomically."""
    meta_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = meta_path.with_name(meta_path.name + '.tmp')
    with open(tmp_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)
    tmp_path.replace(meta_path)


def validate_record(record: Dict, min_length: int = 10) -> Optional[str]:
    """
    Validate a record and return the issue type if invalid.

    Returns:
        None if valid, or a string describing the issue
    """
    # Check if record is malformed
    if record.get('_malformed'):
        return 'malformed_json'

    # Check if utterance exists
    if 'utterance' not in record:
        return 'missing_utterance_field'

    utterance = record.get('utterance', '').strip()

    # Check if utterance is empty
    if not utterance:
        return 'empty_utterance'

    # Check if utterance is too short
    word_count = len(utterance.split())
    if word_count < min_length:
        return f'too_short_{word_count}_words'

    # Check if required metadata exists
    if 'kpis_used' not in record:
        return 'missing_kpis_metadata'

    if 'complexity' not in record:
        return 'missing_complexity'

    return None


def analyze_dataset(records: List[Dict], min_length: int = 10) -> Dict:
    """
    Analyze dataset and categorize issues.

    Returns:
        Dict with issue statistics and problematic record indices
    """
    issues = {
        'total_records': len(records),
        'valid_records': 0,
        'invalid_records': 0,
        'issues_by_type': {},
        'problematic_indices': []
    }

    for idx, record in enumerate(records):
        issue = validate_record(record, min_length)
        if issue is None:
            issues['valid_records'] += 1
        else:
            issues['invalid_records'] += 1
            issues['problematic_indices'].append(idx)

            # Count issue types
            if issue not in issues['issues_by_type']:
                issues['issues_by_type'][issue] = []
            issues['issues_by_type'][issue].append(idx)

    return issues


def regenerate_record(record: Dict, kpi_df, client_manager, temperature: float = 0.85) -> Dict:
    """
    Regenerate a single record using its original metadata.

    Args:
        record: Original record with metadata
        kpi_df: KPI DataFrame
        client_manager: Initialized ClientManager
        temperature: Generation temperature

    Returns:
        Updated record with new utterance
    """
    # Extract original metadata
    complexity = record.get('complexity', 'medium')
    tone = record.get('tone')
    record_id = record.get('record_id', 'unknown')

    print(f"  🔄 Regenerating {record_id} ({complexity}, {tone or 'random'} tone)...")

    # Regenerate using generator function
    try:
        new_data = generate_campaign_rule(
            kpi_df=kpi_df,
            complexity=complexity,
            tone=tone,
            temperature=temperature,
            client_mgr=client_manager
        )

        # Preserve original record_id and metadata, update utterance and related fields
        record['utterance'] = new_data['utterance']
        record['kpis_used'] = new_data['kpis_used']
        record['complexity'] = new_data['complexity']
        record['tone'] = new_data['tone']
        record['num_kpis'] = new_data['num_kpis']

        # Add repair tracking
        if 'repair_history' not in record:
            record['repair_history'] = []
        record['repair_history'].append({
            'repaired_at': datetime.utcnow().isoformat(),
            'reason': 'utterance_regeneration'
        })

        print(f"  ✓ Successfully regenerated {record_id}")
        return record

    except Exception as e:
        print(f"  ✗ Failed to regenerate {record_id}: {e}")
        raise


def repair_dataset(
    input_path: Path,
    meta_path: Path,
    kpi_csv: str,
    output_path: Optional[Path] = None,
    min_length: int = 10,
    temperature: float = 0.85,
    dry_run: bool = False
) -> Dict:
    """
    Main repair function.

    Args:
        input_path: Path to input JSONL file
        meta_path: Path to metadata file
        kpi_csv: Path to KPI CSV file
        output_path: Path to output file (None = in-place update)
        min_length: Minimum word count for valid utterance
        temperature: Generation temperature
        dry_run: If True, only analyze without repairing

    Returns:
        Dict with repair statistics
    """
    print(f"\n{'=' * 80}")
    print("DATASET REPAIR TOOL")
    print(f"{'=' * 80}\n")

    # Load data
    print(f"📖 Loading dataset from {input_path}...")
    records = load_jsonl(input_path)
    print(f"✓ Loaded {len(records)} records")

    print(f"\n📖 Loading metadata from {meta_path}...")
    metadata = load_metadata(meta_path)
    print(f"✓ Loaded metadata")

    # Analyze dataset
    print(f"\n🔍 Analyzing dataset (min_length={min_length} words)...")
    analysis = analyze_dataset(records, min_length)

    print(f"\n{'=' * 80}")
    print("ANALYSIS RESULTS")
    print(f"{'=' * 80}")
    print(f"Total records:   {analysis['total_records']}")
    print(f"Valid records:   {analysis['valid_records']}")
    print(f"Invalid records: {analysis['invalid_records']}")

    if analysis['invalid_records'] > 0:
        print(f"\n📊 Issues by type:")
        for issue_type, indices in analysis['issues_by_type'].items():
            print(f"  - {issue_type}: {len(indices)} record(s)")
            # Show first few record IDs
            sample_records = [records[i].get('record_id', f'index-{i}')
                            for i in indices[:3]]
            print(f"    Examples: {', '.join(sample_records)}")
            if len(indices) > 3:
                print(f"    ... and {len(indices) - 3} more")

    print(f"{'=' * 80}\n")

    # If dry run, stop here
    if dry_run:
        print("ℹ️  DRY RUN mode - no changes made")
        return analysis

    # If no issues, nothing to do
    if analysis['invalid_records'] == 0:
        print("✓ No issues found - dataset is clean!")
        return analysis

    # Ask for confirmation
    print(f"⚠️  Found {analysis['invalid_records']} record(s) to repair.")
    if output_path:
        print(f"📝 Will create repaired file at: {output_path}")
    else:
        print(f"⚠️  Will update file IN-PLACE: {input_path}")

    # Initialize ClientManager and load KPIs
    print(f"\n🔧 Initializing repair environment...")
    client_manager = ClientManager()

    print(f"📖 Loading KPI data from {kpi_csv}...")
    kpi_df = load_kpi_data(kpi_csv)
    if kpi_df is None:
        raise ValueError(f"Failed to load KPI data from {kpi_csv}")

    # Repair records
    print(f"\n{'=' * 80}")
    print(f"REPAIRING {analysis['invalid_records']} RECORD(S)")
    print(f"{'=' * 80}\n")

    repaired_count = 0
    failed_count = 0

    for idx in analysis['problematic_indices']:
        record = records[idx]
        record_id = record.get('record_id', f'index-{idx}')
        issue = validate_record(record, min_length)

        print(f"[{repaired_count + failed_count + 1}/{analysis['invalid_records']}] "
              f"Repairing {record_id} (issue: {issue})")

        try:
            records[idx] = regenerate_record(record, kpi_df, client_manager, temperature)
            repaired_count += 1
        except Exception as e:
            print(f"  ✗ Failed to repair {record_id}: {e}")
            failed_count += 1
            # Keep the original record but mark as failed repair
            records[idx]['_repair_failed'] = True
            records[idx]['_repair_error'] = str(e)

    # Save repaired dataset and get new byte offsets
    output_file = output_path or input_path
    print(f"\n💾 Saving repaired dataset to {output_file}...")
    new_offsets = save_jsonl(output_file, records)
    print(f"✓ Saved {len(records)} records")

    # Update metadata with new byte offsets
    print(f"🔧 Recalculating byte offsets in metadata...")
    if 'plan' in metadata:
        for idx, entry in enumerate(metadata['plan']):
            # Update offset with new calculated position
            entry['offset'] = new_offsets[idx]
        print(f"✓ Updated {len(metadata['plan'])} byte offsets")

    # Add repair history
    metadata['repair_history'] = metadata.get('repair_history', [])
    metadata['repair_history'].append({
        'repaired_at': datetime.utcnow().isoformat(),
        'records_analyzed': analysis['total_records'],
        'records_repaired': repaired_count,
        'records_failed': failed_count,
        'issues_by_type': {k: len(v) for k, v in analysis['issues_by_type'].items()},
        'offsets_recalculated': True
    })

    output_meta = meta_path if output_path is None else output_path.with_suffix('.jsonl.meta.json')
    print(f"💾 Updating metadata at {output_meta}...")
    save_metadata(output_meta, metadata)
    print(f"✓ Metadata updated with corrected byte offsets")

    # Final summary
    print(f"\n{'=' * 80}")
    print("REPAIR SUMMARY")
    print(f"{'=' * 80}")
    print(f"✓ Successfully repaired: {repaired_count}")
    if failed_count > 0:
        print(f"✗ Failed to repair:      {failed_count}")
    print(f"{'=' * 80}\n")

    return {
        'analysis': analysis,
        'repaired': repaired_count,
        'failed': failed_count
    }


def parse_args():
    parser = argparse.ArgumentParser(
        description="Repair dataset by regenerating records with empty or invalid utterances.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry run - analyze without making changes
  python scripts/repair_dataset.py --dry-run

  # Repair in-place
  python scripts/repair_dataset.py

  # Create new repaired file
  python scripts/repair_dataset.py --output outputs/datasets/campaign_rules_repaired.jsonl

  # Custom validation (min 20 words)
  python scripts/repair_dataset.py --min-length 20
        """
    )

    parser.add_argument(
        '--input',
        default='outputs/datasets/campaign_rules_dataset.jsonl',
        help='Path to input JSONL dataset file (default: outputs/datasets/campaign_rules_dataset.jsonl)'
    )

    parser.add_argument(
        '--input-meta',
        help='Path to metadata file (default: <input>.meta.json)'
    )

    parser.add_argument(
        '--output',
        help='Path to output repaired file (default: update in-place)'
    )

    parser.add_argument(
        '--kpi-csv',
        default='data/kpi_profiles.csv',
        help='Path to KPI CSV file (default: data/kpi_profiles.csv)'
    )

    parser.add_argument(
        '--min-length',
        type=int,
        default=10,
        help='Minimum word count for valid utterance (default: 10)'
    )

    parser.add_argument(
        '--temperature',
        type=float,
        default=0.85,
        help='Generation temperature (default: 0.85)'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Analyze only, do not repair'
    )

    return parser.parse_args()


def main():
    args = parse_args()

    # Resolve paths
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"✗ Error: Input file not found: {input_path}")
        return 1

    meta_path = Path(args.input_meta) if args.input_meta else input_path.with_suffix('.jsonl.meta.json')
    if not meta_path.exists():
        print(f"✗ Error: Metadata file not found: {meta_path}")
        return 1

    output_path = Path(args.output) if args.output else None

    # Run repair
    try:
        repair_dataset(
            input_path=input_path,
            meta_path=meta_path,
            kpi_csv=args.kpi_csv,
            output_path=output_path,
            min_length=args.min_length,
            temperature=args.temperature,
            dry_run=args.dry_run
        )
        return 0
    except Exception as e:
        print(f"\n✗ Error during repair: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    exit(main())
