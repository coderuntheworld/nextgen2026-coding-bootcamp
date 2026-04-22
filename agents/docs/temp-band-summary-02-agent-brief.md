# 02 Agent Brief

## Approved Objective

- Task spec reference: `agents/docs/temp-band-summary-01-task-spec.md`
- Objective: Add a configurable `temp_band` categorical column in the prepare stage, a `temp_band_summary.csv` aggregation artifact in the analyze stage, and a temperature-band section in the report stage markdown output. The change must follow the existing `weather`/`weather_summary` pattern, keep all existing tests passing, and add new test assertions as specified in the task spec verification plan.

## Bounded Scope

- In scope:
  - `src/nextgen2026_coding_bootcamp/steps/prepare.py` — add `temp_band` derivation from `temp_c` using configurable bin edges; append `temp_band` to `PREPARED_COLUMNS`.
  - `src/nextgen2026_coding_bootcamp/steps/analyze.py` — add `temp_band_summary` groupby-agg-sort-write following the `weather_summary` pattern (lines 61-74); add `temp_band_summary_csv` key to the return dict.
  - `src/nextgen2026_coding_bootcamp/steps/report.py` — read `temp_band_summary.csv` via `_resolve_analyze_inputs`; append a temperature-band bullet-list section to `analysis_summary.md`.
  - `configs/stages/prepare.yaml` — add config key for bin edges (e.g. `temp_band_edges`).
  - `tests/test_prepare.py` — add `temp_band` assertions for known `temp_c` values.
  - `tests/test_analyze_report.py` — update fixture CSV header to include `temp_band`; add assertions for `temp_band_summary.csv` existence, columns, row count; add markdown substring assertion.
  - `tests/test_known_answer.py` — update `KNOWN_PREPARED_CSV` to include `temp_band`; add pinned-value assertions for the new aggregation.
  - `tests/test_workflow_smoke.py` — add `assert Path(ctx.artifacts["analyze"]["temp_band_summary_csv"]).exists()` after line 79.
- Out of scope:
  - No changes to `fetch.py` or the fetch stage.
  - No new plots or figures for temperature bands.
  - No changes to CLI entry points, script argument parsing, or workflow stage ordering.
  - No changes to `test_integration_stage_handoff.py` (path-only test; schema coverage is a separate task).
  - No statistical modelling or causal interpretation of temperature effects.
  - No changes to `configs/profiles/base.yaml` unless profiles override prepare-stage config.

## Durable Instructions

- Repo rules to keep front-of-mind:
  - **`AGENTS.md` "Do Not Change" list:** stage script CLI semantics, stage ordering (`fetch -> prepare -> analyze -> report`), artifact contracts consumed by downstream stages, scientific meaning of existing transformations.
  - **Column contract:** `PREPARED_COLUMNS` in `prepare.py` is the single source of truth for the prepared CSV schema. It must be append-only — never remove or rename existing columns. The new column must appear in both `PREPARED_COLUMNS` and the `.assign()` chain, or `test_invariants.py:38` and `test_prepare.py:43` will fail.
  - **Artifact naming convention:** follow the existing pattern — `weather_summary_csv`, `hourly_profile_csv` — so the new key should be `temp_band_summary_csv`.
  - **Config over constants:** bin edges must be read from OmegaConf config (`configs/stages/prepare.yaml`), not hard-coded in Python logic. Follow the existing pattern where `cfg.prepare.*` drives behaviour.
  - **Test fixtures must stay consistent:** when updating fixture CSV headers to include `temp_band`, the labels must match what the prepare logic would produce for the `temp_c` values already in the fixture. Do not change existing fixture `temp_c` values.
  - **Existing assertions are read-only:** add new assertions; do not weaken, remove, or modify existing ones.
  - **Markdown voice:** the report summary uses backtick-wrapped values in a bullet list (e.g. `` - High-demand quantile: `0.9` ``). Match this style exactly.

## Minimal Context Bundle

- File or command: `AGENTS.md`
  Why included: contains the "Do Not Change" rules and canonical commands. Must be read before any implementation to know what is off-limits.

- File or command: `agents/docs/temp-band-summary-01-task-spec.md`
  Why included: the approved task contract. Defines scope, constraints, non-goals, and the full verification plan with specific assertion examples.

- File or command: `src/nextgen2026_coding_bootcamp/steps/prepare.py`
  Why included: primary implementation target. Contains `PREPARED_COLUMNS` (lines 19-36), `WEATHER_MAP`/`SEASON_MAP` (lines 10-16) as the pattern to follow, the `.assign()` chain (lines 69-79), and the `temp_c` derivation formula (line 75).

- File or command: `src/nextgen2026_coding_bootcamp/steps/analyze.py`
  Why included: second implementation target. Contains the `weather_summary` groupby-agg-sort-write pattern (lines 61-74) to replicate, and the return dict structure (lines 100-108) to extend.

- File or command: `src/nextgen2026_coding_bootcamp/steps/report.py`
  Why included: third implementation target. Contains `_resolve_analyze_inputs` (lines 12-31) which must be extended to resolve the new artifact, and the markdown generation block (lines 100-124) whose style must be matched.

- File or command: `configs/stages/prepare.yaml`
  Why included: where the new `temp_band_edges` config key must be added. Currently only has `keep_holidays` and `write_prepared_csv` — establishes the naming convention.

- File or command: `tests/test_prepare.py`
  Why included: contains the fixture data (`RAW_CSV`, line 8-11) and existing assertions (lines 43-49) that the agent must extend. Shows the exact `temp_c` values the fixture produces.

- File or command: `tests/test_analyze_report.py`
  Why included: contains the 4-row fixture (lines 14-19) with `temp_c` values 4.99, 5.00, 15.00, 25.00 that must gain a `temp_band` column. Shows the artifact assertion pattern to replicate.

- File or command: `tests/test_known_answer.py`
  Why included: contains `KNOWN_PREPARED_CSV` (lines 10-16) with all rows at `temp_c=0.0`. Must be updated to include `temp_band` and gain pinned-value assertions for the new aggregation.

- File or command: `tests/test_workflow_smoke.py`
  Why included: contains the full-pipeline artifact assertions (lines 72-82). The agent must add one new assertion for `temp_band_summary_csv`.

**Not included in first turn (add only if a blocker appears):**

- `src/nextgen2026_coding_bootcamp/workflow.py` — only needed if the stage wiring is unclear; the task does not modify workflow orchestration.
- `configs/profiles/base.yaml` — only needed if profile-level overrides are required for the new config key.
- `tests/test_integration_stage_handoff.py` — out of scope; no changes planned.
- `scripts/` — CLI wrappers are not being modified.

## First Handoff Message

- Read `AGENTS.md` and `agents/docs/temp-band-summary-01-task-spec.md` first. Then read the implementation files listed in the context bundle. Before writing any code, return a plan in the Required Return Format below. Do not begin implementation until the plan is approved.

## Required Return Format

- Restated task: one-sentence summary of what you will implement.
- Files inspected: list every file you read from the context bundle.
- Files likely to change: list with one-line description of the change per file.
- Short plan: numbered steps in implementation order (prepare -> analyze -> report -> config -> tests).
- Verification commands: the exact commands you will run after implementation.
- Changed files: (after implementation) list of files changed with a one-line diff summary each.
- Checks run: (after implementation) paste the output of `uv run pytest -q`.
- Assumptions or open questions: anything you are uncertain about — bin edge values, label names, config key naming.
- Hold for approval confirmation: do not proceed past the plan step without explicit approval.

## Stop and Escalate Conditions

- Stage boundary is unclear: if you are unsure whether a transformation belongs in prepare or analyze, stop and ask. The rule: prepare derives columns from raw data; analyze aggregates prepared columns into summary artifacts.
- Wider file scope is needed: if you find you need to modify `workflow.py`, any script in `scripts/`, `fetch.py`, or `test_integration_stage_handoff.py`, stop and ask. These are outside the declared surface.
- Workflow entrypoints or CLI behavior would change: if the new config key would require changes to CLI argument parsing or script entry points, stop and ask. The task must not alter how stages are invoked.
- Scientific meaning may change beyond the approved task spec: if you are tempted to change the `temp_c` formula (`temp * 47 - 8`), any existing map (`SEASON_MAP`, `WEATHER_MAP`, `DAY_TYPE_MAP`), or any existing aggregation logic, stop and ask. These are pinned.
- Existing test assertions would need modification: if an existing assertion fails and you believe it needs updating rather than your code being wrong, stop and ask. Existing assertions are read-only.
- Bin edge choice feels interpretive: if you are unsure whether bin edges carry scientific meaning (e.g. heatwave thresholds vs. arbitrary quartiles), stop and ask. The task spec says arbitrary grouping, not domain-specific thresholds.

## Approval

- Reviewer: Bella
- Status: Draft
