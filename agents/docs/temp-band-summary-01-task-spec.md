# 01 Task Spec

## Task Summary

- Request: Add a temperature-band column in the prepare stage, aggregate mean rentals by temperature band in the analyze stage, and include a temperature-band summary table in the report stage markdown output.
- Intended repo change: `prepare.py` derives a categorical `temp_band` column from the existing `temp_c` column using fixed bin edges (e.g. cold / mild / warm / hot). `analyze.py` produces a new `temp_band_summary.csv` artifact with mean rentals and observation counts per band. `report.py` reads that artifact and appends a temperature-band section to `analysis_summary.md`. Config files and the `PREPARED_COLUMNS` contract are updated to match.
- Why this task is appropriate for delegation:
  - The change is bounded: it adds a new derived column and a new aggregation, following patterns already established for `weather` and `day_type` in the same files.
  - It crosses a real stage boundary (prepare -> analyze -> report), exercising the artifact handoff contract, which makes it a meaningful test of an agent's ability to maintain cross-stage consistency.
  - The existing test structure (`test_prepare.py`, `test_analyze_report.py`) provides clear templates for verification: column checks, artifact existence checks, and content assertions.
  - The task produces a visible, inspectable artifact (a CSV and markdown section), making review concrete rather than abstract.
  - It does not require scientific judgment about what temperature bands mean -- the bin edges are a configuration choice, not an interpretive decision.

## Risk and Review Burden

- Technical debt risk: **Low.** Follows the existing pattern (see `WEATHER_MAP`, `weather_summary` aggregation). No new abstractions or dependencies are introduced.
- Interpretive risk: **Low.** Temperature-band bin edges are arbitrary categories for grouping, not scientific claims. The values are configurable and clearly labeled.
- Verifiability: **High.** The change is fully testable: column presence, bin assignment correctness, artifact file existence, and markdown content can all be asserted deterministically with the existing test fixtures.
- Blast radius: **Medium.** The `PREPARED_COLUMNS` list in `prepare.py` is an implicit contract consumed by `analyze.py` and checked by `test_prepare.py`. Adding `temp_band` to that list changes the prepared CSV schema, which downstream stages and tests depend on. However, the new column is purely additive (no existing columns are removed or renamed), so the blast radius is limited to forward-compatibility.
- Review burden: **Low-to-medium.** The reviewer needs to verify: (1) bin edges are sensible and match config, (2) `PREPARED_COLUMNS` is updated consistently with the actual output, (3) the new analyze artifact follows the same contract pattern as `weather_summary.csv`, (4) the report markdown section is appended without breaking existing content, and (5) all existing tests still pass. This is a checklist review, not a judgment call.

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
