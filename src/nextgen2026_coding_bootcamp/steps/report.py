from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


def run_report(cfg) -> dict:
    results_dir = Path(cfg.paths.results_dir)
    output_dir = results_dir / "report"
    output_dir.mkdir(parents=True, exist_ok=True)

    profile_csv = results_dir / "hourly_profile.csv"
    summary_json = results_dir / "high_demand_summary.json"

    profile = pd.read_csv(profile_csv)
    summary = json.loads(summary_json.read_text())

    fig, ax = plt.subplots(figsize=(10, 5))
    for day_type, group in profile.groupby("day_type"):
        ax.plot(group["hour"], group["mean_rentals"], label=day_type, marker="o")

    ax.axhline(
        summary["high_demand_threshold"],
        color="red",
        linestyle="--",
        label=f"High demand (p{summary['high_demand_quantile']:.0%})",
    )
    ax.set_xlabel("Hour of Day")
    ax.set_ylabel("Mean Rentals")
    ax.set_title("Hourly Bike Demand Profile")
    ax.legend()
    ax.set_xticks(range(24))

    plot_path = output_dir / "hourly_demand.png"
    fig.savefig(plot_path, dpi=150, bbox_inches="tight")
    plt.close(fig)

    return {
        "plot": str(plot_path),
    }