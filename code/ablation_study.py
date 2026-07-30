#!/usr/bin/env python3
"""Reproduce the component-wise BioArc ablation summary from equations."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

from compute_qssspi import (
    DEFAULT_DATA,
    EPSILON,
    LAMBDA_Q,
    LAMBDA_S,
    compute_continuous_metrics,
    load_data,
)
from counterfactual_analysis import ABLATED_SCENARIO, OBSERVED_SCENARIO, build_counterfactual_table


def compute_quality_only(
    df: pd.DataFrame,
    lambda_q: float = LAMBDA_Q,
    lambda_s: float = LAMBDA_S,
    epsilon: float = EPSILON,
) -> np.ndarray:
    """Return the unrounded quality-only layer, SPI_s times QF_s."""
    metrics = compute_continuous_metrics(df, lambda_q, lambda_s, epsilon)
    return metrics["QSSPI_q_s"].to_numpy(dtype=float)


def build_table9(
    df: pd.DataFrame,
    lambda_q: float = LAMBDA_Q,
    lambda_s: float = LAMBDA_S,
    epsilon: float = EPSILON,
) -> pd.DataFrame:
    """Build the ablation table using unrounded means and scenario outputs."""
    metrics = compute_continuous_metrics(df, lambda_q, lambda_s, epsilon)
    raw_avg_exact = float(metrics["SPI_s"].mean())
    quality_avg_exact = float(metrics["QSSPI_q_s"].mean())
    full_avg_exact = float(metrics["QSSPI_s"].mean())

    rows: list[dict[str, float | str]] = [
        {
            "Panel": "Panel A. Eight-sprint average values",
            "Model variant": "Raw SPI_s",
            "Index_exact": raw_avg_exact,
            "Index value": round(raw_avg_exact, 3),
            "Comparison basis": "Reference",
        },
        {
            "Panel": "Panel A. Eight-sprint average values",
            "Model variant": "Quality-only (SPI_s x QF_s)",
            "Index_exact": quality_avg_exact,
            "Index value": round(quality_avg_exact, 3),
            "Comparison basis": f"{(quality_avg_exact - raw_avg_exact) * 100:.1f} percentage points vs. raw SPI_s",
        },
        {
            "Panel": "Panel A. Eight-sprint average values",
            "Model variant": "Full QSSPI (SPI_s x QF_s x SF_s)",
            "Index_exact": full_avg_exact,
            "Index value": round(full_avg_exact, 3),
            "Comparison basis": f"{(full_avg_exact - raw_avg_exact) * 100:.1f} percentage points vs. raw SPI_s",
        },
    ]

    scenarios = build_counterfactual_table(df, lambda_q, lambda_s, epsilon)
    reported = scenarios[scenarios["Scenario"] != ABLATED_SCENARIO]
    for scenario in reported.itertuples(index=False):
        comparison = "Reference" if scenario.Scenario == OBSERVED_SCENARIO else (
            f"{scenario.Change_pp:+.1f} percentage points vs. observed QSSPI_5"
        )
        rows.append(
            {
                "Panel": "Panel B. BioArc Sprint 5 scenario values",
                "Model variant": scenario.Scenario,
                "Index_exact": float(scenario.CQSSPI_exact),
                "Index value": round(float(scenario.CQSSPI_exact), 3),
                "Comparison basis": comparison,
            }
        )

    return pd.DataFrame(rows)


# Backward-compatible alias from the earlier repository version.
build_table7 = build_table9


def print_summary(table9: pd.DataFrame, quality_only: np.ndarray) -> None:
    print("\nReproduced Table 9: ablation values for the BioArc retrospective case")
    print("=" * 120)
    print(table9.drop(columns="Index_exact").to_string(index=False))
    print("=" * 120)

    summary = stats.describe(quality_only)
    print("\nQuality-only descriptive summary (unrounded values)")
    print("-" * 100)
    print(f"n          = {summary.nobs}")
    print(f"min / max  = {summary.minmax[0]:.3f} / {summary.minmax[1]:.3f}")
    print(f"mean       = {np.mean(quality_only):.3f}")
    print(f"variance   = {summary.variance:.6f}")
    print("-" * 100)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Reproduce the BioArc CQSS-SPI ablation summary.")
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA)
    parser.add_argument("--lambda-q", type=float, default=LAMBDA_Q)
    parser.add_argument("--lambda-s", type=float, default=LAMBDA_S)
    parser.add_argument("--epsilon", type=float, default=EPSILON)
    parser.add_argument("--csv-out", type=Path, default=None)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    df = load_data(args.data)
    table9 = build_table9(df, args.lambda_q, args.lambda_s, args.epsilon)
    quality_only = compute_quality_only(df, args.lambda_q, args.lambda_s, args.epsilon)
    print_summary(table9, quality_only)

    if args.csv_out is not None:
        args.csv_out.parent.mkdir(parents=True, exist_ok=True)
        table9.to_csv(args.csv_out, index=False)
        print(f"\nSaved reproduced Table 9 to: {args.csv_out}")


if __name__ == "__main__":
    main()
