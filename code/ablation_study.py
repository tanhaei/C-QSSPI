#!/usr/bin/env python3
"""Reproduce the component-wise ablation summary (Table 9) for the CQSS-SPI paper."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

from compute_qssspi import DEFAULT_DATA, PUBLISHED_QF, PUBLISHED_QSSPI, load_data

BIOARC_SPRINT5_COUNTERFACTUALS = {
    "Scenario-based CQSSPI_5 (stronger gating)": 0.983,
    "Scenario-based CQSSPI_5 (selective AI restriction)": 0.979,
    "Scenario-based CQSSPI_5 (lower compression)": 0.993,
}


def compute_quality_only(df: pd.DataFrame) -> np.ndarray:
    """Compute the quality-only publication layer, SPI_s x QF_s."""
    return np.round(df["SPI_s"].to_numpy(dtype=float) * PUBLISHED_QF, 3)


def build_table9(df: pd.DataFrame) -> pd.DataFrame:
    """Build Table 9 exactly as reported in the manuscript."""
    raw_avg = float(np.round(df["SPI_s"].mean(), 3))
    quality_only = compute_quality_only(df)
    quality_avg = float(np.round(quality_only.mean(), 3))
    full_avg = float(np.round(PUBLISHED_QSSPI.mean(), 3))
    observed_sprint5 = float(PUBLISHED_QSSPI[4])

    rows = [
        {
            "Panel": "Panel A. Eight-sprint average values",
            "Model variant": "Raw SPI_s",
            "Index value": raw_avg,
            "Comparison basis": "Reference",
        },
        {
            "Panel": "Panel A. Eight-sprint average values",
            "Model variant": "Quality-only (SPI_s × QF_s)",
            "Index value": quality_avg,
            "Comparison basis": f"{(quality_avg - raw_avg) * 100:.1f} percentage points vs. raw SPI_s",
        },
        {
            "Panel": "Panel A. Eight-sprint average values",
            "Model variant": "Full QSSPI (SPI_s × QF_s × SF_s)",
            "Index value": full_avg,
            "Comparison basis": f"{(full_avg - raw_avg) * 100:.1f} percentage points vs. raw SPI_s",
        },
        {
            "Panel": "Panel B. BioArc Sprint 5 counterfactual values",
            "Model variant": "Observed QSSPI_5",
            "Index value": observed_sprint5,
            "Comparison basis": "Reference",
        },
    ]

    for label, value in BIOARC_SPRINT5_COUNTERFACTUALS.items():
        rows.append(
            {
                "Panel": "Panel B. BioArc Sprint 5 counterfactual values",
                "Model variant": label,
                "Index value": value,
                "Comparison basis": f"+{(value - observed_sprint5) * 100:.1f} percentage points vs. observed QSSPI_5",
            }
        )

    return pd.DataFrame(rows)


# Backward-compatible alias from the earlier repository version.
build_table7 = build_table9


def print_summary(table9: pd.DataFrame, df: pd.DataFrame) -> None:
    """Print Table 9 and a compact descriptive report."""
    print("\nReproduced Table 9: ablation values for the BioArc retrospective case")
    print("=" * 110)
    print(table9.to_string(index=False))
    print("=" * 110)

    q_only_values = compute_quality_only(df)
    summary = stats.describe(q_only_values)

    print("\nQuality-only descriptive summary")
    print("-" * 110)
    print(f"n          = {summary.nobs}")
    print(f"min / max  = {summary.minmax[0]:.3f} / {summary.minmax[1]:.3f}")
    print(f"mean       = {np.mean(q_only_values):.3f}")
    print(f"variance   = {summary.variance:.6f}")
    print("-" * 110)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Reproduce the BioArc ablation summary (Table 9).")
    parser.add_argument(
        "--data",
        type=Path,
        default=DEFAULT_DATA,
        help="Path to bioarc_retrospective_sprints.csv",
    )
    parser.add_argument(
        "--csv-out",
        type=Path,
        default=None,
        help="Optional path for saving Table 9 as CSV.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    df = load_data(args.data)
    table9 = build_table9(df)
    print_summary(table9, df)

    if args.csv_out is not None:
        table9.to_csv(args.csv_out, index=False)
        print(f"\nSaved reproduced Table 9 to: {args.csv_out}")


if __name__ == "__main__":
    main()
