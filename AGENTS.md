# Repository Guidelines

## Project Structure & Module Organization
- `synthetic_generator.py` holds every pipeline stage (KPI loading, prompt assembly, LLM call, dataset persistence). Treat it as the single entry-point module and keep helper functions grouped by the banner comments already in place.
- `kpi_profiles.csv` is the authoritative KPI catalog; adjust or replace it before generation runs. Do not edit generated JSON manually.
- `campaign_rules_dataset.json` is the default output artifact. Commit only sanitized samples; large full runs should remain local.

## Build, Test, and Development Commands
- Create an isolated environment: `python3 -m venv .venv && source .venv/bin/activate`.
- Install runtime deps: `pip install pandas ollama`. Ollama must be running at `http://localhost:11434` with `ollama pull glm-4.6:cloud` completed.
- Generate data locally: `python3 synthetic_generator.py` (tweak `CSV_FILE`, `N_EXAMPLES`, `CUSTOM_DIST` before running).
- Spot-check the JSON: `python3 -m json.tool campaign_rules_dataset.json | head` to ensure valid formatting.

## Coding Style & Naming Conventions
- Follow PEP 8 with 4-space indents, snake_case functions, and Upper_Snake_Case constants (see `MODEL`, `TONE_GUIDELINES`).
- Keep side-effecting code in the `if __name__ == "__main__"` block; helper functions should remain pure and typed when feasible.
- Prefer descriptive docstrings and lightweight inline comments only where the control flow (e.g., KPI sampling) is non-obvious.

## Testing Guidelines
- Before large batches, dry-run with `N_EXAMPLES = 1` and verify the printed sample block for tone/complexity accuracy.
- Validate KPI coverage by asserting the sampled KPI count matches `num_kpis`; a quick debug helper or unit test under `tests/` is welcome if more modules are added.
- Re-run the script after CSV edits to ensure no `FileNotFoundError` or schema drift occurs.

## Commit & Pull Request Guidelines
- With no established history, adopt Conventional Commits (`feat: add throttle controls`) written in the imperative mood and scoped to a single concern.
- PRs should summarize the scenario generated, list configuration toggles touched (`MODEL`, `CUSTOM_DIST`, paths), attach sanitized output snippets, and reference any tickets or acceptance criteria.

## Security & Configuration Tips
- Never check in real customer KPI data; keep `kpi_profiles.csv` synthetic or anonymized.
- Treat the Ollama host as a local dev dependency only; document any alternative endpoints in the PR if changed.
