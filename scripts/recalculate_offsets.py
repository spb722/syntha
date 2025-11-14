#!/usr/bin/env python3
"""
Recalculate byte offsets in metadata after JSONL file has been modified.

Use this when the JSONL file has been edited but metadata offsets are out of sync.
"""

import argparse
import json
from pathlib import Path


def recalculate_offsets(jsonl_path: Path, meta_path: Path):
    """
    Recalculate byte offsets by reading the JSONL file and update metadata.
    """
    print(f"\n{'=' * 80}")
    print("RECALCULATING BYTE OFFSETS")
    print(f"{'=' * 80}\n")

    # Read JSONL file and record actual byte offsets
    print(f"📖 Reading JSONL file: {jsonl_path}")
    offsets = []
    with open(jsonl_path, 'r', encoding='utf-8') as f:
        while True:
            offset = f.tell()
            line = f.readline()
            if not line:
                break
            offsets.append(offset)

    print(f"✓ Found {len(offsets)} records")

    # Load metadata
    print(f"\n📖 Loading metadata: {meta_path}")
    with open(meta_path, 'r', encoding='utf-8') as f:
        metadata = json.load(f)

    # Update offsets in plan
    if 'plan' not in metadata:
        print("✗ Error: Metadata does not contain 'plan' array")
        return False

    plan = metadata['plan']
    if len(plan) != len(offsets):
        print(f"⚠️  Warning: Plan has {len(plan)} entries but file has {len(offsets)} records")
        print("   Using minimum of both")

    print(f"\n🔧 Updating byte offsets...")
    updated_count = 0
    for idx in range(min(len(plan), len(offsets))):
        old_offset = plan[idx].get('offset')
        new_offset = offsets[idx]

        if old_offset != new_offset:
            plan[idx]['offset'] = new_offset
            updated_count += 1

    print(f"✓ Updated {updated_count} byte offsets (out of {len(plan)} records)")

    # Save updated metadata
    print(f"\n💾 Saving updated metadata...")
    tmp_path = meta_path.with_name(meta_path.name + '.tmp')
    with open(tmp_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)
    tmp_path.replace(meta_path)
    print(f"✓ Metadata saved")

    print(f"\n{'=' * 80}")
    print(f"✓ COMPLETE: {updated_count} offsets recalculated")
    print(f"{'=' * 80}\n")

    return True


def parse_args():
    parser = argparse.ArgumentParser(
        description="Recalculate byte offsets in metadata after JSONL modifications"
    )
    parser.add_argument(
        '--input',
        default='outputs/datasets/campaign_rules_dataset.jsonl',
        help='Path to JSONL file'
    )
    parser.add_argument(
        '--meta',
        help='Path to metadata file (default: <input>.meta.json)'
    )
    return parser.parse_args()


def main():
    args = parse_args()

    jsonl_path = Path(args.input)
    if not jsonl_path.exists():
        print(f"✗ Error: File not found: {jsonl_path}")
        return 1

    meta_path = Path(args.meta) if args.meta else jsonl_path.with_suffix('.jsonl.meta.json')
    if not meta_path.exists():
        print(f"✗ Error: Metadata not found: {meta_path}")
        return 1

    success = recalculate_offsets(jsonl_path, meta_path)
    return 0 if success else 1


if __name__ == '__main__':
    exit(main())
