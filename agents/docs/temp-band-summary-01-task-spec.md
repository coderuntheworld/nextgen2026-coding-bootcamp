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

### Part A — What tests can prove mechanically

Run `uv run pytest -q` after implementation. The following checks must all pass without human judgment.

**Existing tests (must pass unchanged):**

| Test file | What it guards | How it catches a regression |
| --- | --- | --- |
| `test_prepare.py` | Column contract, cell-value correctness | `list(prepared.columns) == PREPARED_COLUMNS` (line 43). If `PREPARED_COLUMNS` gains `temp_band` but `.assign()` does not produce it, this fails. |
| `test_invariants.py` | Column contract (independent fixture), value ranges | Same `== PREPARED_COLUMNS` assertion (line 38) on different data. Double-guards the schema. |
| `test_known_answer.py` | Exact numeric outputs from analyze | Pins `high_demand_threshold == 25.0`, `high_demand_share == [0.0, 1.0]`, `weather_summary mean_rentals == 40.0`. Any accidental change to existing aggregation logic fails here. |
| `test_integration_stage_handoff.py` | fetch-to-prepare path plumbing | `fetch_csv_path == prepare_input_path` (line 65). Confirms artifact wiring. Does **not** check column schema -- see Part C. |
| `test_workflow_smoke.py` | Full pipeline artifact existence | Asserts every key in `ctx.artifacts` for all four stages (lines 72-82). Currently does **not** assert `temp_band_summary_csv` -- see new assertions below. |
| `test_analyze_report.py` | Analyze artifact shape, report markdown content | Checks column names, row counts, sort order for `weather_summary`/`hourly_profile`/`high_demand_share`; checks markdown substrings. Fixture CSV header currently lacks `temp_band` -- see new assertions below. |

**New assertions the agent must add:**

1. **`test_prepare.py` — bin assignment for known inputs.**
   The existing fixture has `temp=0.24` and `temp=0.22`, producing `temp_c=3.28` and `temp_c=2.34` (via `temp * 47 - 8`). Both are low temperatures. The agent must add assertions like:
   ```python
   assert prepared.loc[0, "temp_band"] == "cold"  # temp_c=3.28
   assert prepared.loc[1, "temp_band"] == "cold"  # temp_c=2.34
   ```
   This proves: bin assignment logic runs and maps known `temp_c` values to the correct label.

2. **`test_analyze_report.py` — fixture update and artifact check.**
   The 4-row fixture already has `temp_c` values of 4.99, 5.00, 15.00, and 25.00. The agent must:
   - Add `temp_band` to the fixture CSV header with labels consistent with the configured bin edges (these four values should span at least two distinct bands).
   - Assert `temp_band_summary.csv` exists: `assert Path(analyze_artifacts["temp_band_summary_csv"]).exists()`
   - Assert columns: `assert list(temp_band_summary.columns) == ["temp_band", "mean_rentals", "observations"]`
   - Assert row count equals the number of distinct bands in the fixture.
   - Assert the report markdown contains a temperature-band section: `assert "temp_band" in summary_markdown` or equivalent substring.
   This proves: analyze produces the new artifact with the right schema; report consumes it.

3. **`test_known_answer.py` — pinned values for new aggregation.**
   The fixture has all rows at `temp_c=0.0`. The agent must:
   - Add `temp_band` column to `KNOWN_PREPARED_CSV` (all rows will map to the same band, e.g. `cold`).
   - Assert: `temp_band_summary = pd.read_csv(artifacts["temp_band_summary_csv"])` produces exactly one row with `mean_rentals` matching the overall mean of the fixture (27.5).
   This proves: the aggregation produces correct, pinned numeric output for a known input.

4. **`test_workflow_smoke.py` — new artifact key in full pipeline.**
   The agent must add one line after the existing analyze artifact assertions (after line 79):
   ```python
   assert Path(ctx.artifacts["analyze"]["temp_band_summary_csv"]).exists()
   ```
   This proves: the full pipeline wires the new artifact through `ctx.artifacts` end-to-end.

5. **`test_invariants.py` — no new assertions needed.**
   The existing `== PREPARED_COLUMNS` check already covers the new column automatically once `PREPARED_COLUMNS` is updated.

**Full pipeline smoke run:**

After all tests pass, run:
```
uv run python scripts/run_workflow.py --profile base --run-name temp-band-check
```
This proves: real data (17,379 rows) flows through all stages without runtime errors and produces the new artifact on disk.

### Part B — What still needs your review

These items cannot be verified by any test. Each requires you to look at a specific artifact or diff section and make a judgment call.

1. **Bin edge defaults.** Open `configs/stages/prepare.yaml` and check that the configured edges are reasonable for `temp_c` range -8 to 39 C (derived from `temp * 47 - 8` at `prepare.py:75`). A bad split (e.g. all data in one band) would pass every test but produce a useless summary. Quick check: after the full-data run, open `temp_band_summary.csv` and confirm every band has a non-trivial number of observations.

2. **Band label neutrality.** Labels like "cold", "mild", "warm", "hot" are descriptive. Labels like "dangerous", "ideal", "uncomfortable" are evaluative and inappropriate for a data summary. Scan the diff for the label list.

3. **Report markdown voice.** The existing summary uses backtick-wrapped values in a bullet list (e.g. `` - High-demand quantile: `0.9` ``). The new temperature-band section should match this style. Read the generated `analysis_summary.md` from the full-data run and compare.

4. **Fixture diversity.** `test_known_answer.py` has all rows at `temp_c=0.0`, so it only exercises one band. This is acceptable for a known-answer regression test (it pins the value), but it does not guard against off-by-one errors at bin boundaries. Check whether the `test_analyze_report.py` fixture (with `temp_c` values 4.99, 5.00, 15.00, 25.00) exercises at least two bands. If all four land in the same band, ask for a revision.

5. **Artifact plausibility.** After the full-data run, open `temp_band_summary.csv` and check: (a) no NaN band labels, (b) observation counts sum to the total row count, (c) mean rentals increase or vary across bands in a way that is directionally plausible (warmer weather generally means more rentals in this dataset).

6. **Diff scope.** Run `git diff --stat` and confirm changes are limited to the declared surfaces. No files outside `steps/`, `configs/`, and `tests/` should be touched. No existing assertions should be weakened or removed.

### Part C — Known gaps in the test suite (out of scope to fix)

- `test_integration_stage_handoff.py` checks path plumbing between fetch and prepare but does not check column schema. A prepare-to-analyze column mismatch would not be caught by this test. Fixing this gap is a separate task.
- The 2-row smoke fixture in `test_workflow_smoke.py` has `temp=0.24` and `temp=0.22`, both producing low `temp_c` values. The smoke test will only exercise one temperature band. Adding fixture diversity to the smoke test is desirable but not required for this task.

## Decision Threshold

- Accept when:
  - **Part A clears:** `uv run pytest -q` passes with zero failures, all five new assertion groups (items 1-5 above) are present, and the full-data smoke run completes without error.
  - **Part B clears:** you have checked all six reviewer items and found no issues -- bin edges are sensible, labels are neutral, markdown matches existing voice, fixture diversity spans multiple bands, artifact values are plausible, and the diff is scoped to declared surfaces.
- Revise when:
  - Part A passes but Part B reveals a fixable issue:
    - Bin edges are hard-coded in `prepare.py` instead of read from config.
    - Test fixtures lack `temp_band` in CSV headers (tests pass vacuously because analyze never references the missing column).
    - `test_known_answer.py` fixture is not updated, so the known-answer test does not exercise the new aggregation.
    - `test_workflow_smoke.py` does not assert `temp_band_summary_csv` in `ctx.artifacts["analyze"]`.
    - Report markdown section exists but does not match the bullet-list-with-backtick style of existing content.
    - Band labels use evaluative language ("dangerous", "ideal") instead of neutral descriptors ("cold", "mild", "warm", "hot").
    - The `test_analyze_report.py` fixture puts all four rows into the same band, so the aggregation is never tested across multiple groups.
- Reject when:
  - Any existing test fails.
  - `PREPARED_COLUMNS` drops or renames an existing column.
  - Stage ordering or CLI semantics change.
  - The diff touches files outside the declared surface without justification.
  - The `temp_c` conversion formula or any existing map (`SEASON_MAP`, `WEATHER_MAP`, `DAY_TYPE_MAP`) is modified.
  - Existing test assertions are weakened or removed to make new code pass.

## Approval

- Reviewer: Bella
- Status: Draft
