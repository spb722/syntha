import argparse
import json
import random
from datetime import datetime
from pathlib import Path

import pandas as pd
from ollama import Client

# Initialize Ollama client
client = Client(host="http://localhost:11434")
MODEL = "glm-4.6:cloud"
ORDERED_COMPLEXITIES = ["simple", "medium", "complex"]


# ============================================================================
# KPI DATA LOADING
# ============================================================================

def load_kpi_data(csv_filename):
    """
    Load KPI data from CSV file.

    Args:
        csv_filename: Name of CSV file (e.g., "kpi_profiles.csv")

    Returns:
        DataFrame with PROFILE_ID, PROFILE_NAME, GENERATED_DESCRIPTION
    """
    try:
        df = pd.read_csv(csv_filename)
        print(f"✓ Loaded {len(df)} KPIs from {csv_filename}")
        return df
    except FileNotFoundError:
        print(f"✗ Error: Could not find {csv_filename}")
        return None
    except Exception as e:
        print(f"✗ Error loading CSV: {e}")
        return None


# ============================================================================
# KPI SAMPLING
# ============================================================================

def sample_kpis(kpi_df, complexity):
    """
    Sample KPIs based on complexity level.

    Args:
        kpi_df: DataFrame with KPI data
        complexity: "simple", "medium", or "complex"

    Returns:
        Sampled DataFrame subset
    """
    if complexity == "simple":
        n = random.randint(1, 2)  # 1-2 KPIs
    elif complexity == "medium":
        n = random.randint(3, 4)  # 3-4 KPIs
    else:  # complex
        n = random.randint(4, 5)  # 4-5 KPIs

    # Ensure we don't sample more than available
    n = min(n, len(kpi_df))

    return kpi_df.sample(n=n).reset_index(drop=True)


# ============================================================================
# TONE DEFINITIONS
# ============================================================================

TONE_GUIDELINES = {
    "formal": """
Use formal business language:
- Start with: "I would like to...", "Please target...", "We need to reach..."
- Professional and structured
- Complete sentences with proper grammar
""",

    "direct": """
Use direct command language:
- Start with: "Target...", "Send...", "Reach out to...", "Execute..."
- Clear and imperative
- Action-oriented instructions
""",

    "casual": """
Use casual planning language:
- Start with: "Let's...", "How about we...", "We should...", "Maybe we can..."
- Conversational and collaborative
- Friendly team discussion tone
"""
}

# ============================================================================
# SCHEDULE EXAMPLES (KPI-independent)
# ============================================================================

SCHEDULE_CONTEXT = """
**Schedule Types & Natural Phrasing:**
- Daily: "run this daily at 10 AM starting February 15th 2025"
- Daily with interval: "execute every 4 hours from 9 AM to 5 PM starting March 1st 2025"
- Weekly: "run every Monday and Thursday at 2 PM from February 10th until April 30th 2025"
- Weekly with interval: "execute every Tuesday every 2 hours from 10 AM to 6 PM starting next week"
- Monthly: "run on the 1st and 15th of each month at 9 AM from March 2025 to June 2025"
- Monthly with interval: "execute on the 5th and 20th every month, every 3 hours from 8 AM to 5 PM"
- Monthly specifics: "run on the first Monday of every month at 10 AM starting February 2025"
- Interval: "run every 6 hours starting February 20th 2025 until March 31st 2025"
"""


# ============================================================================
# UTILITY HELPERS
# ============================================================================

def parse_distribution_arg(raw_value):
    """
    Parse a distribution string or JSON payload into a dict of counts.

    Accepts JSON (e.g., '{"simple": 4, "complex": 1}') or comma-separated
    key=value pairs like "simple=4,medium=3".
    """
    if raw_value is None:
        return None

    try:
        data = json.loads(raw_value)
        if isinstance(data, dict):
            return {k: int(data[k]) for k in data}
    except json.JSONDecodeError:
        pass

    distribution = {}
    for chunk in raw_value.split(","):
        if not chunk.strip():
            continue
        if "=" not in chunk:
            raise ValueError(
                f"Invalid distribution component '{chunk}'. Expected key=value."
            )
        key, value = chunk.split("=", 1)
        try:
            distribution[key.strip()] = int(value.strip())
        except ValueError as exc:
            raise ValueError(
                f"Invalid integer value in distribution for '{key.strip()}'."
            ) from exc

    return distribution


def compute_complexity_distribution(n_examples, custom_dist=None):
    """
    Build a complexity distribution dict and resolve the final example count.
    """
    if custom_dist:
        normalized = {k: int(custom_dist.get(k, 0)) for k in ORDERED_COMPLEXITIES}
        total = sum(normalized.values())
        if total <= 0:
            raise ValueError("Custom distribution must request at least one example.")
        return normalized, total

    per_complexity = n_examples // 3
    remainder = n_examples % 3
    distribution = {
        "simple": per_complexity + (1 if remainder > 0 else 0),
        "medium": per_complexity + (1 if remainder > 1 else 0),
        "complex": per_complexity,
    }
    return distribution, sum(distribution.values())


def build_generation_plan(distribution):
    """
    Expand the distribution dict into a linear plan list containing
    record identifiers and placeholder offsets.
    """
    plan = []
    counter = 1
    for complexity in ORDERED_COMPLEXITIES:
        count = int(distribution.get(complexity, 0))
        for _ in range(count):
            plan.append({
                "index": len(plan),
                "record_id": f"rule-{counter:06d}",
                "complexity": complexity,
                "offset": None
            })
            counter += 1
    return plan


def append_jsonl(path, record):
    """
    Append a record to a JSONL file, ensuring directories exist.

    Returns:
        Byte offset at which the record was written.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as handle:
        offset = handle.tell()
        json.dump(record, handle, ensure_ascii=False)
        handle.write("\n")
        handle.flush()
        return offset


def atomic_write_json(path, payload):
    """
    Persist JSON via a temporary file to reduce corruption risk.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_name(path.name + ".tmp")
    with open(tmp_path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
    tmp_path.replace(path)


def load_meta(meta_path):
    """
    Load the metadata file describing resume progress.
    """
    meta_file = Path(meta_path)
    if not meta_file.exists():
        raise FileNotFoundError(
            f"Metadata file '{meta_file}' not found. Run in fresh mode first."
        )
    with open(meta_file, "r", encoding="utf-8") as handle:
        return json.load(handle)


def meta_path_for_output(output_path):
    """
    Calculate the metadata path associated with an output JSONL file.
    """
    output = Path(output_path)
    suffix = output.suffix or ""
    return output.with_suffix(f"{suffix}.meta.json")


# ============================================================================
# PROMPT GENERATION WITH SAMPLED KPIs
# ============================================================================

def create_kpi_section(sampled_kpis):
    """
    Create the KPI section for the prompt from sampled KPIs.

    Args:
        sampled_kpis: DataFrame with sampled KPI rows

    Returns:
        Formatted string with KPI descriptions
    """
    kpi_section = "**Available KPIs for this campaign:**\n\n"

    for idx, row in sampled_kpis.iterrows():
        kpi_section += f"KPI {idx + 1}: {row['GENERATED_DESCRIPTION']}\n\n"

    kpi_section += """**Your task:** Convert these technical KPI descriptions into natural, conversational business language when creating the campaign instruction. Use the KPIs to define targeting criteria and conditional logic.\n"""

    return kpi_section


def create_generation_prompt(sampled_kpis, complexity, tone):
    """
    Create the complete prompt for synthetic data generation.

    Args:
        sampled_kpis: DataFrame with sampled KPI rows
        complexity: "simple", "medium", or "complex"
        tone: "formal", "direct", or "casual"

    Returns:
        Complete prompt string
    """
    kpi_section = create_kpi_section(sampled_kpis)

    base_instructions = f"""You are a telecom campaign manager describing a campaign in natural, business-appropriate language.

{kpi_section}

{TONE_GUIDELINES[tone]}

{SCHEDULE_CONTEXT}

**Additional Context:**
- Actions: Send SMS, push notification, give bonus data (XGB valid for Y days), provide voice minutes, offer SMS bundle
- Policy: Can exclude segments, skip recently contacted customers, limit to max N users
- Sampling: Can throttle (e.g., "limit to 5000 customers", "reach 10% of eligible users")

Generate ONE campaign instruction with {complexity.upper()} complexity following these requirements:
"""

    if complexity == "simple":
        complexity_rules = """
**Structure:**
1. TARGET: Use 1-2 of the provided KPIs to define customer segment in natural language
2. ACTION: What to do (send SMS, offer bonus, etc.)
3. SCHEDULE: When to run (MUST include - use one of the schedule patterns above)

**Requirements:**
- Convert KPI technical descriptions into natural business language
- NO technical symbols: >, >=, <, AND, OR, ==
- Use conversational phrasing: "customers who", "users that", "people with"
- Numbers naturally: "more than 5", "between 3-8", "at least 10"
- Simple targeting (1-2 KPIs combined with AND if needed)
- One clear action
- Must include realistic scheduling
- Length: 25-50 words
- Use realistic dates (February-December 2025, or early 2026)

**Example Structure:** "Target [natural KPI condition]. [Action]. [Schedule]."

**Output:** ONE line only, no quotes, no JSON, no extra text.
"""

    elif complexity == "medium":
        complexity_rules = """
**Structure:**
1. TARGET: Use 2-3 of the provided KPIs for combined customer conditions
2. ACTION: With conditional bonus based on customer behavior
3. SAMPLING: Throttling/limiting (e.g., "limit to 5000 customers", "reach 10% of users")
4. SCHEDULE: When to run (MUST include - weekly or interval patterns work well)

**Requirements:**
- Convert 2-3 KPIs into natural language conditions connected with "and", "who", "that"
- NO symbols: >, >=, <, &&, ||
- Include conditional bonus: "if they [action], give [reward]"
- Add sampling/throttling naturally
- Must include realistic scheduling
- Length: 50-75 words
- Use realistic dates (February-December 2025, or early 2026)

**Example Structure:** "Target [KPI1 condition] and [KPI2 condition] and [KPI3 condition]. [Action]. If [behavior], give [bonus]. [Sampling]. [Schedule]."

**Output:** ONE line only, no quotes, no JSON, no extra text.
"""

    else:  # complex
        complexity_rules = """
**Structure:**
1. TARGET: Use 2-3 KPIs to define the initial customer segment
2. BRANCHING LOGIC: Use remaining KPIs for if/else conditions with different bonuses
   - Split logic: Use different KPIs in each branch
   - Example: "Target [KPI1 & KPI2 conditions]. If [KPI3 condition], provide [offer A] valid X days. Otherwise, if [KPI4 condition], provide [offer B] valid Y days."
3. EXCLUSIONS: Policy rules (e.g., "exclude VIP segment", "skip customers contacted in last 14 days")
4. DETAILED SCHEDULE: Must include exact dates and times

**Requirements:**
- Use 2-3 KPIs for targeting (WHO to reach)
- Use remaining KPIs for branching logic (WHAT to give based on different conditions)
- Each branch should have different KPI conditions and different offers
- Natural language throughout - NO symbols: >, >=, <, &&, ||, !
- Clear if/else branching: "If [condition], [offer]. Otherwise, if [condition], [different offer]."
- Include exclusion/policy rules naturally
- Detailed scheduling with specific start and end dates
- Length: 75-110 words
- Use realistic dates (February-December 2025, or early 2026)

**Example Structure:** "Target [KPI1 & KPI2]. If [KPI3 condition], give [offer A]. Otherwise, if [KPI4 condition], give [offer B]. [Exclusions]. [Detailed schedule]."

**Output:** ONE line only, no quotes, no JSON, no extra text.
"""

    return base_instructions + complexity_rules


# ============================================================================
# CAMPAIGN RULE GENERATION
# ============================================================================

def generate_campaign_rule(kpi_df, complexity, tone=None, temperature=0.85):
    """
    Generate one synthetic campaign rule using sampled KPIs.

    Args:
        kpi_df: DataFrame with all KPI data
        complexity: "simple", "medium", or "complex"
        tone: "formal", "direct", or "casual" (random if None)
        temperature: Generation temperature

    Returns:
        Dictionary with utterance and metadata
    """
    # Random tone if not specified
    if tone is None:
        tone = random.choice(["formal", "direct", "casual"])

    # Sample KPIs based on complexity
    sampled_kpis = sample_kpis(kpi_df, complexity)

    # Create prompt
    prompt = create_generation_prompt(sampled_kpis, complexity, tone)

    # Call LLM
    response = client.chat(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        options={"temperature": temperature}
    )

    utterance = response["message"]["content"].strip()

    # Prepare KPI metadata
    kpis_used = []
    for _, row in sampled_kpis.iterrows():
        kpis_used.append({
            "profile_id": int(row['PROFILE_ID']),
            "profile_name": row['PROFILE_NAME'],
            "description": row['GENERATED_DESCRIPTION']
        })

    return {
        "utterance": utterance,
        "kpis_used": kpis_used,
        "complexity": complexity,
        "tone": tone,
        "num_kpis": len(kpis_used)
    }


# ============================================================================
# BATCH DATASET GENERATION
# ============================================================================

def run_generation(kpi_df, plan, start_index, output_path, meta, meta_path,
                   temperature=0.85):
    """
    Stream campaign rules to disk following the provided plan.

    Returns:
        Tuple of (generated_count, first_sample_dict_or_None)
    """
    total = len(plan)
    if start_index >= total:
        print("✓ Nothing to do. Plan already completed.")
        return 0, None

    print(f"\n{'=' * 80}")
    print(
        f"GENERATING {total - start_index} SYNTHETIC CAMPAIGN RULES "
        f"(resume index {start_index})"
    )
    print(f"{'=' * 80}\n")

    generated_this_session = 0
    first_sample = None

    for idx in range(start_index, total):
        entry = plan[idx]
        complexity = entry["complexity"]
        record_id = entry["record_id"]
        print(f"\n[{idx + 1}/{total}] {complexity.upper()} example ({record_id})")
        try:
            result = generate_campaign_rule(
                kpi_df, complexity, temperature=temperature
            )
            result["processed"] = None
            result["record_id"] = record_id
            offset = append_jsonl(output_path, result)
            entry["offset"] = offset

            generated_this_session += 1
            if first_sample is None:
                first_sample = result

            meta["completed"] = idx + 1
            meta["last_generated_at"] = datetime.utcnow().isoformat()
            meta["plan"][idx] = entry
            atomic_write_json(meta_path, meta)

            print(
                f"✓ Stored example {idx + 1} ({record_id}, {result['tone']} tone, "
                f"{result['num_kpis']} KPIs)"
            )
        except Exception as exc:
            print(
                f"✗ Error generating example {idx + 1} ({complexity}): {exc}"
            )
            print("Stopping so you can address the issue. Resume once fixed.")
            break

    print(f"\n{'=' * 80}")
    print(f"✓ Generated {generated_this_session} new examples this session")
    print(
        f"✓ Total completed: {meta.get('completed', start_index)} / {len(plan)}"
    )
    print(f"{'=' * 80}\n")

    return generated_this_session, first_sample


def create_meta(csv_file, output_path, distribution, plan, requested_examples,
                resolved_examples, temperature):
    """
    Initialize metadata for a fresh generation run.
    """
    return {
        "csv_file": csv_file,
        "model": MODEL,
        "temperature": temperature,
        "output_file": str(Path(output_path).resolve()),
        "distribution": distribution,
        "plan": plan,
        "completed": 0,
        "requested_examples": requested_examples,
        "resolved_examples": resolved_examples,
        "started_at": datetime.utcnow().isoformat(),
    }


def validate_resume_meta(meta, args, output_path):
    """
    Ensure CLI arguments align with the metadata we are trying to resume.
    """
    recorded_output = Path(meta.get("output_file", "")).resolve()
    if recorded_output != Path(output_path).resolve():
        raise ValueError(
            f"Output path mismatch. Meta expects {recorded_output}, "
            f"but --output resolved to {Path(output_path).resolve()}."
        )

    if meta.get("csv_file") != args.csv_file:
        raise ValueError(
            "CSV file mismatch between resume metadata and current arguments."
        )

    if abs(meta.get("temperature", args.temperature) - args.temperature) > 1e-9:
        raise ValueError(
            "Temperature mismatch. Keep the same value or start with --mode fresh."
        )

    if meta.get("model") != MODEL:
        raise ValueError(
            f"Model has changed (meta uses {meta.get('model')}, script uses {MODEL})."
            " Start a fresh run if you need a new model."
        )


def parse_args():
    """
    CLI argument parser for batch generation.
    """
    parser = argparse.ArgumentParser(
        description="Generate synthetic telecom campaign rules."
    )
    parser.add_argument(
        "--mode",
        choices=["fresh", "resume"],
        default="fresh",
        help="fresh: start over. resume: continue from metadata progress.",
    )
    parser.add_argument(
        "--csv-file",
        default="data/kpi_profiles.csv",
        help="Path to the KPI CSV input.",
    )
    parser.add_argument(
        "--n-examples",
        type=int,
        default=5,
        help="Requested number of examples (ignored in resume mode).",
    )
    parser.add_argument(
        "--custom-dist",
        help=(
            "Optional custom distribution, e.g. "
            '\'{"simple":4,"complex":1}\' or "simple=4,complex=1".'
        ),
    )
    parser.add_argument(
        "--output",
        default="outputs/datasets/campaign_rules_dataset.jsonl",
        help="Output JSONL path (metadata stored alongside).",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.85,
        help="LLM sampling temperature.",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    output_path = Path(args.output)
    if output_path.suffix != ".jsonl":
        output_path = output_path.with_suffix(".jsonl")
    meta_path = meta_path_for_output(output_path)

    if args.mode == "resume":
        meta = load_meta(meta_path)
        validate_resume_meta(meta, args, output_path)
        plan = meta.get("plan", [])
        distribution = meta.get("distribution", {})
        resolved_examples = len(plan)
        start_index = int(meta.get("completed", 0))
        if not plan:
            raise ValueError("Metadata file does not contain a generation plan.")
        if not Path(output_path).exists():
            raise FileNotFoundError(
                f"Expected output file '{output_path}' for resume mode."
            )
    else:
        custom_dist = parse_distribution_arg(args.custom_dist)
        distribution, resolved_examples = compute_complexity_distribution(
            args.n_examples, custom_dist
        )
        plan = build_generation_plan(distribution)
        meta = create_meta(
            csv_file=args.csv_file,
            output_path=output_path,
            distribution=distribution,
            plan=plan,
            requested_examples=args.n_examples,
            resolved_examples=resolved_examples,
            temperature=args.temperature,
        )
        # Reset files for a fresh run.
        if output_path.exists():
            output_path.unlink()
        if Path(meta_path).exists():
            Path(meta_path).unlink()
        atomic_write_json(meta_path, meta)
        start_index = 0

    print("\nGeneration plan:")
    print(f"  Output file : {output_path.resolve()}")
    print(f"  Metadata    : {Path(meta_path).resolve()}")
    print(f"  CSV source  : {args.csv_file}")
    print(f"  Distribution: {distribution}")
    print(f"  Plan length : {len(plan)} examples")
    print(f"  Completed   : {start_index}")

    if start_index >= len(plan):
        print("All planned examples already generated. Nothing to do.")
        return

    kpi_df = load_kpi_data(args.csv_file)
    if kpi_df is None:
        return

    generated, sample = run_generation(
        kpi_df=kpi_df,
        plan=plan,
        start_index=start_index,
        output_path=output_path,
        meta=meta,
        meta_path=meta_path,
        temperature=args.temperature,
    )

    if generated > 0 and sample:
        print("\n" + "=" * 80)
        print("SAMPLE OUTPUT:")
        print("=" * 80)
        print(f"\nRecord ID: {sample.get('record_id')}")
        print(f"\nComplexity: {sample['complexity']}")
        print(f"Tone: {sample['tone']}")
        print(f"Number of KPIs: {sample['num_kpis']}")
        print(f"\nUtterance:\n{sample['utterance']}")
        print("\nKPIs Used:")
        for kpi in sample["kpis_used"]:
            print(f"  - {kpi['profile_name']}")


if __name__ == "__main__":
    main()
