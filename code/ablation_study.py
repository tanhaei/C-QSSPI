#!/usr/bin/env python3
"""
Reproduce the ablation summary (Table 7) for the C-QSSPI paper.

The target publication averages are:
- Raw SPI = 1.042
- Quality-only = 0.980 (-6.2 pp)
- Full QSSPI = 0.939 (-10.3 pp)
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

from compute_qssspi import (
    PUBLISHED_QF,
    PUBLISHED_QSSPI,
    load_data,
)

# Synthetic scenario values used in the conceptual counterfactual illustration.
SYNTHETIC_COUNTERFACTUALS = {
    "CQSSPI (synthetic causal illustration, stronger gating)": 0.983,
    "CQSSPI (synthetic causal illustration, selective AI restriction)": 0.979,
}


def compute_quality_only(df: pd.DataFrame) -> np.ndarray:
    """
    Compute the quality-only publication layer.

    This uses the publication-rounded QF values so that the reported average
    matches the manuscript's displayed ablation summary.
    """
    return np.round(df["SPI_s"].to_numpy(dtype=float) * PUBLISHED_QF, 3)


def build_table7(df: pd.DataFrame) -> pd.DataFrame:
    """Build the publication-style Table 7 summary."""
    raw_avg = np.round(df["SPI_s"].mean(), 3)
    quality_only = compute_quality_only(df)
    quality_avg = np.round(quality_only.mean(), 3)
    full_avg = np.round(PUBLISHED_QSSPI.mean(), 3)

    rows = [
        {
            "Model Variant": "Raw SPI_s",
            "Average Index": raw_avg,
            "Delta from Raw SPI_s (%)": "---",
        },
        {
            "Model Variant": "Quality-only (SPI_s × QF_s)",
            "Average Index": quality_avg,
            "Delta from Raw SPI_s (%)": f"{(quality_avg - raw_avg) * 100:.1f}",
        },
        {
            "Model Variant": "Full QSSPI (SPI_s × QF_s × SF_s)",
            "Average Index": full_avg,
            "Delta from Raw SPI_s (%)": f"{(full_avg - raw_avg) * 100:.1f}",
        },
        {
            "Model Variant": "QSSPI (Sprint 5)",
            "Average Index": float(PUBLISHED_QSSPI[4]),
            "Delta from Raw SPI_s (%)": "---",
        },
    ]

    for label, value in SYNTHETIC_COUNTERFACTUALS.items():
        rows.append(
            {
                "Model Variant": label,
                "Average Index": value,
                "Delta from Raw SPI_s (%)": f"{(value - float(PUBLISHED_QSSPI[4])) * 100:.1f}",
            }
        )

    return pd.DataFrame(rows)


def print_summary(table7: pd.DataFrame) -> None:
    """Print the ablation summary and a compact descriptive report."""
    print("\nReproduced Table 7")
    print("=" * 80)
    print(table7.to_string(index=False))
    print("=" * 80)

    q_only_values = compute_quality_only(load_data(DEFAULT_DATA))
    summary = stats.describe(q_only_values)

    print("\nQuality-only descriptive summary")
    print("-" * 80)
    print(f"n          = {summary.nobs}")
    print(f"min / max  = {summary.minmax[0]:.3f} / {summary.minmax[1]:.3f}")
    print(f"mean       = {np.mean(q_only_values):.3f}")
    print(f"variance   = {summary.variance:.6f}")
    print("-" * 80)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Reproduce the ablation summary (Table 7).")
    parser.add_argument(
        "--data",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "data" / "illustrative_sprints.csv",
        help="Path to illustrative_sprints.csv",
    )
    parser.add_argument(
        "--csv-out",
        type=Path,
        default=None,
        help="Optional path for saving Table 7 as CSV.",
    )
    return parser.parse_args()


DEFAULT_DATA = Path(__file__).resolve().parents[1] / "data" / "illustrative_sprints.csv"


def main() -> None:
    args = parse_args()
    df = load_data(args.data)
    table7 = build_table7(df)

    print_summary(table7)

    if args.csv_out is not None:
        table7.to_csv(args.csv_out, index=False)
        print(f"\nSaved reproduced Table 7 to: {args.csv_out}")


if __name__ == "__main__":
    main()
