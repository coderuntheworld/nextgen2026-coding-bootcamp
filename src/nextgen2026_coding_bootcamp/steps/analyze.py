from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


def run_analyze(cfg) -> dict:
    prepared_csv = Path(cfg.paths.intermediate_dir) / "hourly_bike_data.csv"
    output_dir = Path(cfg.paths.results_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    prepared = pd.read_csv(prepared_csv)
    threshold = float(prepared["total_rentals"].quantile(cfg.analysis.high_demand_quantile))

    hourly_profile = (
        prepared.groupby(["hour", "day_type"], as_index=False)["total_rentals"]
        .mean()
        .rename(columns={"total_rentals": "mean_rentals"})
    )

    profile_path = output_dir / "hourly_profile.csv"
    summary_path = output_dir / "high_demand_summary.json"

    hourly_profile.to_csv(profile_path, index=False)
    summary_path.write_text(
        json.dumps(
            {
                "high_demand_quantile": float(cfg.analysis.high_demand_quantile),
                "high_demand_threshold": threshold,
                "rows_in": int(len(prepared)),
            },
            indent=2,
        )
        + "\n"
    )

    return {
        "prepared_csv": str(prepared_csv),
        "hourly_profile_csv": str(profile_path),
        "summary_json": str(summary_path),
    }