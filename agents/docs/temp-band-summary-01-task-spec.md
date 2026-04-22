# 01 Task Spec

## Task Summary

- Request: Add a temperature-band column in the prepare stage, aggregate mean rentals by temperature band in the analyze stage, and include a temperature-band summary table in the report stage markdown output.
- Intended repo change: `prepare.py` derives a categorical `temp_band` column from the existing `temp_c` column using fixed bin edges (e.g. cold / mild / warm / hot). `analyze.py` produces a new `temp_band_summary.csv` artifact with mean rentals and observation counts per band. `report.py` reads that artifact and appends a temperature-band section to `analysis_summary.md`. Config files and the `PREPARED_COLUMNS` contract are updated to match.
- Why this task is appropriate for delegation:
  - **Pattern already exists in the repo.** The `weather` column follows the exact same lifecycle this task requires: a categorical map in `prepare.py` (lines 12-16, `WEATHER_MAP`), a groupby-agg-sort-write in `analyze.py` (lines 61-74, `weather_summary`), and artifact consumption in `report.py`. The agent can replicate the pattern rather than invent one.
  - **Bounded and workshop-sized.** The task touches three files in `steps/` plus config, with no changes to CLI entry points, workflow orchestration, or the fetch stage. A single agent can complete it in one delegation loop.
  - **Crosses a real stage boundary.** The new column is created in prepare, consumed in analyze, and surfaced in report. This exercises the artifact handoff contract -- the part of the codebase most likely to break silently -- while remaining small enough to isolate in review.
  - **Verification is concrete, not subjective.** Every acceptance criterion maps to a deterministic assertion: column presence (`test_invariants.py:38` checks `list(columns) == PREPARED_COLUMNS`), artifact file existence (`test_analyze_report.py:37-40`), and markdown content strings (`test_analyze_report.py:62-66`). The reviewer inspects outputs, not reasoning.
  - **No interpretive judgment required.** Temperature-band bin edges are an arbitrary grouping choice (like `SEASON_MAP`), not a scientific claim. The agent does not need domain expertise to choose defensible defaults, and the reviewer can override edges via config without touching logic.
  - **Contrast with worse alternatives.** A change to the `temp_c` formula in `prepare.py:75` would be equally small but carry high interpretive risk -- it would silently change every downstream number. A CLI refactor would be equally safe but would not exercise cross-stage contracts, making it a weaker learning task.

## Risk and Review Burden

- Technical debt risk: **Low.** The implementation copies an established pattern (`WEATHER_MAP` at `prepare.py:12-16`, `weather_summary` aggregation at `analyze.py:61-74`). No new abstractions, helper modules, or third-party dependencies are introduced. The only structural addition is one new key in each stage's return dict and one new CSV artifact, both following existing conventions.
- Interpretive risk: **Low.** Temperature-band bin edges are an arbitrary categorical grouping, structurally identical to `SEASON_MAP` (line 10). They do not represent a scientific claim. The default edges can be overridden in config, so a bad default is a config change, not a code fix. The one area to watch: if the agent names bands with language that implies causal relationships (e.g. "dangerous_heat"), the reviewer should rename to neutral labels.
- Verifiability: **High.** Every acceptance criterion reduces to a deterministic assertion against existing test patterns:
  - Column presence: `test_invariants.py:38` asserts `list(prepared.columns) == PREPARED_COLUMNS` -- if `PREPARED_COLUMNS` and the actual `.assign()` call diverge, this test fails.
  - Bin correctness: `test_prepare.py:43-49` already checks specific cell values for known inputs -- new assertions follow the same pattern with known `temp_c` values mapped to expected band labels.
  - Artifact existence: `test_analyze_report.py:37-40` checks `Path(...).exists()` for each analyze output.
  - Markdown content: `test_analyze_report.py:62-66` asserts substring presence in the summary markdown.
  - No assertion requires subjective judgment; all are string/numeric equality or existence checks.
- Blast radius: **Medium, but well-guarded.** The primary risk surface is the `PREPARED_COLUMNS` list (`prepare.py:19-36`), which acts as an implicit schema contract. Three tests assert against it directly:
  - `test_prepare.py:43` -- `assert list(prepared.columns) == PREPARED_COLUMNS`
  - `test_invariants.py:38` -- identical assertion on different fixture data
  - `test_analyze_report.py:14-18` -- fixture CSV headers must match for analyze to consume them
  If the agent updates `PREPARED_COLUMNS` but not the test fixture CSV headers (or vice versa), at least one of these tests will fail, catching the inconsistency before review. The handoff test (`test_integration_stage_handoff.py`) only checks path plumbing (line 65-67), not column schema, so it will not catch a column mismatch -- this is a gap the reviewer should be aware of. The change is purely additive (append-only to columns list), so no existing column is at risk.
- Review burden: **Low-to-medium.** Automated checks cover: column contract consistency, bin assignment for known values, artifact existence, and markdown content. What remains for the reviewer:
  1. Are the default bin edges reasonable for the dataset's actual `temp_c` range (-8 to 39 C, derived from `temp * 47 - 8` at `prepare.py:75`)?
  2. Does the config key name and structure follow existing conventions in `configs/stages/prepare.yaml`?
  3. Does the new markdown section match the voice and formatting of the existing summary (bullet-list with backtick-wrapped values)?
  4. Is the new analyze return dict key (`temp_band_summary_csv`) consistent with the existing naming pattern (`weather_summary_csv`, `hourly_profile_csv`)?
  These are all quick visual checks on a bounded diff -- checklist review, not judgment call.

## Likely Files and Surfaces

- Code or docs likely involved:
  - `src/nextgen2026_coding_bootcamp/steps/prepare.py` -- add `temp_band` derivation and update `PREPARED_COLUMNS`
  - `src/nextgen2026_coding_bootcamp/steps/analyze.py` -- add `temp_band_summary` aggregation and write `temp_band_summary.csv`; update return dict
  - `src/nextgen2026_coding_bootcamp/steps/report.py` -- read `temp_band_summary.csv` via `_resolve_analyze_inputs`; append markdown section
  - `configs/stages/prepare.yaml` -- add `temp_band_edges` or equivalent config key
  - `configs/stages/analyze.yaml` -- no change expected (groupby key comes from data, not config)
  - `configs/profiles/base.yaml` -- may need temp-band config if profiles override stage defaults
- Tests or commands to inspect:
  - `uv run pytest tests/test_prepare.py -v` -- column contract and transform correctness
  - `uv run pytest tests/test_analyze_report.py -v` -- new artifact existence, content, and report markdown
  - `uv run pytest tests/test_integration_stage_handoff.py -v` -- cross-stage artifact contract
  - `uv run pytest tests/test_known_answer.py -v` -- known-answer regression
  - `uv run pytest -q` -- full suite, no regressions
  - `uv run python scripts/run_workflow.py --profile base --run-name temp-band-check` -- end-to-end smoke run
- Existing artifacts or outputs to check:
  - `data/intermediate/hourly_bike_data.csv` -- should gain a `temp_band` column
  - `results/` directory -- should contain a new `temp_band_summary.csv` after a full run
  - `results/analysis_summary.md` (or run-scoped equivalent) -- should contain a temperature-band section

## Constraints and Non-Goals

- Constraints:
  - `temp_band` must be derived from the existing `temp_c` column, not from the raw normalised `temp` field.
  - Bin edges must be configurable via the existing OmegaConf config structure, not hard-coded in logic.
  - The new column must appear in `PREPARED_COLUMNS` so the prepared CSV contract remains the single source of truth.
  - The new analyze artifact must follow the same write pattern as `weather_summary.csv` (groupby, agg, sort, write CSV).
  - All existing tests must continue to pass without modification to their assertions (new tests are added, not retrofitted into old ones).
- Non-goals:
  - No visualisation (plot/figure) for temperature bands -- that can be a separate follow-up task.
  - No statistical analysis or modelling of temperature effects on demand.
  - No changes to the fetch stage or raw data schema.
  - No changes to CLI argument parsing or script entry points.
  - No changes to the workflow stage ordering (fetch -> prepare -> analyze -> report).
- What must not change:
  - Stage ordering and CLI semantics (per `AGENTS.md`).
  - Existing columns in `PREPARED_COLUMNS` (only append, never remove or rename).
  - Existing artifact contracts consumed by downstream stages (e.g. `hourly_profile.csv`, `high_demand_summary.json`).
  - Scientific meaning of existing transformations (temperature conversion formula, season/weather mappings).

## Verification Plan

| Layer | Planned check | Repo surface or command | What it proves | What still needs your review |
| --- | --- | --- | --- | --- |
| Unit | `temp_band` column present with correct bin labels for known `temp_c` values | `uv run pytest tests/test_prepare.py -v` | Bin assignment logic matches config edges | Whether the chosen default bin edges are sensible for the dataset's temperature range |
| Unit | `temp_band_summary.csv` exists with expected columns and row count | `uv run pytest tests/test_analyze_report.py -v` | Aggregation runs and produces well-formed output | Whether mean-rentals-by-band values are plausible |
| Integration | Prepared CSV flows through analyze and report without errors | `uv run pytest tests/test_integration_stage_handoff.py -v` | Cross-stage column contract is intact after adding `temp_band` | Whether the handoff test fixture data covers edge-case bins (e.g. boundary temperatures) |
| End-to-end or smoke | Full workflow completes and produces all artifacts including new ones | `uv run python scripts/run_workflow.py --profile base --run-name temp-band-check` | No runtime errors; all stages accept the updated schema | Spot-check `temp_band_summary.csv` contents against the dataset |
| Artifact or contract | `PREPARED_COLUMNS` matches actual CSV header; analyze return dict includes `temp_band_summary_csv` key | `uv run pytest tests/test_invariants.py -v` | Contract consistency between code and artifacts | Whether the return dict documentation (if any) is updated |
| Your review | Diff review of all changed files | `git diff` | All changes are additive; no existing behaviour altered | Bin edge choices, config key naming, markdown formatting tone |

## Decision Threshold

- Accept when: all existing tests pass, new tests cover bin assignment and artifact generation, the full workflow completes without error, and the diff is limited to the files listed above with no unrelated changes.
- Revise when: tests pass but bin edges are hard-coded instead of configurable, or the report section is added but doesn't match the existing markdown style, or `PREPARED_COLUMNS` is updated but test fixtures don't include `temp_band`, or the analyze return dict is missing the new artifact key.
- Reject when: existing tests fail, the prepared CSV schema drops or renames existing columns, stage ordering or CLI semantics change, or the diff touches files outside the declared surface area without justification.

## Approval

- Reviewer: Bella
- Status: Draft
