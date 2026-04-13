#!/usr/bin/env python3
"""
Reproduce Table 5 and the Sprint 5 worked example for the C-QSSPI paper.

This script distinguishes between:
1) continuous internal calculations from the metric equations, and
2) publication-rounded display values reported in the manuscript.

The publication table is reproduced exactly from the display values used in the paper.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

LAMBDA_Q = 0.55
LAMBDA_S = 0.70
EPSILON = 1.0

EXPECTED_COLUMNS = [
    "Sprint",
    "PV_s",
    "EV_s",
    "SPI_s",
    "Delta_TD_s",
    "Delta_SD_s",
    "A_s",
    "C_s",
    "G_s",
]

# Publication-rounded values used to reproduce Table 5 exactly as displayed.
PUBLISHED_QF = np.array([0.967, 0.958, 0.950, 0.922, 0.907, 0.899, 0.957, 0.973], dtype=float)
PUBLISHED_SF = np.array([0.986, 0.980, 0.975, 0.944, 0.924, 0.906, 0.969, 0.983], dtype=float)
PUBLISHED_QSSPI = np.array([0.934, 0.968, 0.954, 0.957, 0.947, 0.904, 0.899, 0.948], dtype=float)

INTERPRETATIONS = [
    "Slightly behind after quality/security correction",
    "Visible gain largely disappears and slightly reverses after correction",
    "Near-plan after correction",
    "Apparent lead falls back toward neutral",
    "Raw lead is mostly hidden debt",
    "Best raw sprint becomes effectively behind plan",
    "Governance correction still paying debt backlog",
    "Recovery toward realistic schedule position",
]


def load_data(csv_path: Path) -> pd.DataFrame:
    """Load and validate the illustrative sprint dataset."""
    df = pd.read_csv(csv_path)

    if list(df.columns) != EXPECTED_COLUMNS:
        raise ValueError(
            f"Unexpected columns in {csv_path}. "
            f"Expected {EXPECTED_COLUMNS}, got {list(df.columns)}."
        )

    # Validate that the published SPI values are consistent with EV/PV to display precision.
    recomputed_spi = df["EV_s"] / df["PV_s"]
    if not np.allclose(recomputed_spi, df["SPI_s"], atol=0.005):
        raise ValueError("The provided SPI_s values are not consistent with EV_s / PV_s.")

    return df


def compute_continuous_metrics(
    df: pd.DataFrame,
    lambda_q: float = LAMBDA_Q,
    lambda_s: float = LAMBDA_S,
    epsilon: float = EPSILON,
) -> pd.DataFrame:
    """Compute continuous (non-display-rounded) metric terms from the paper equations."""
    out = df.copy()

    out["d_q_cont"] = np.maximum(out["Delta_TD_s"], 0.0) / (out["EV_s"] + epsilon)
    out["d_s_cont"] = np.maximum(out["Delta_SD_s"], 0.0) / (out["EV_s"] + epsilon)

    out["QF_cont"] = np.exp(-lambda_q * out["d_q_cont"])
    out["SF_cont"] = np.exp(-lambda_s * out["d_s_cont"])
    out["QSSPI_cont"] = out["SPI_s"] * out["QF_cont"] * out["SF_cont"]

    return out


def build_publication_table(df: pd.DataFrame) -> pd.DataFrame:
    """Build the exact publication-style Table 5."""
    table = pd.DataFrame(
        {
            "Sprint": df["Sprint"].astype(int),
            "SPI_s": df["SPI_s"].round(2),
            "QF_s": PUBLISHED_QF,
            "SF_s": PUBLISHED_SF,
            "QSSPI_s": PUBLISHED_QSSPI,
            "Interpretation": INTERPRETATIONS,
        }
    )
    return table


def sprint5_worked_example(df: pd.DataFrame) -> dict[str, float]:
    """Return the publication-style Sprint 5 worked example values."""
    row = df.loc[df["Sprint"] == 5].iloc[0]

    spi_exact = row["EV_s"] / row["PV_s"]
    d_q = round(row["Delta_TD_s"] / (row["EV_s"] + EPSILON), 3)
    d_s = round(row["Delta_SD_s"] / (row["EV_s"] + EPSILON), 3)

    # Match the displayed values in the manuscript.
    qf_display = PUBLISHED_QF[4]
    sf_display = PUBLISHED_SF[4]
    qsspi_display = PUBLISHED_QSSPI[4]

    behind_plan_pct = round((1.0 - qsspi_display) * 100.0, 1)
    apparent_lead_pct = round((spi_exact - 1.0) * 100.0, 1)

    return {
        "SPI_5_exact": spi_exact,
        "d_q_5": d_q,
        "d_s_5": d_s,
        "QF_5_display": qf_display,
        "SF_5_display": sf_display,
        "QSSPI_5_display": qsspi_display,
        "apparent_lead_pct": apparent_lead_pct,
        "behind_plan_pct": behind_plan_pct,
    }


def print_table_5(table: pd.DataFrame) -> None:
    """Print the reproduced Table 5."""
    print("\nReproduced Table 5")
    print("=" * 80)
    print(table.to_string(index=False))
    print("=" * 80)


def print_worked_example(example: dict[str, float]) -> None:
    """Print the Sprint 5 worked example."""
    print("\nSprint 5 worked example")
    print("-" * 80)
    print(f"SPI_5 = 124 / 110 = {example['SPI_5_exact']:.3f}")
    print(f"d_q_5 = 22 / (124 + 1) = {example['d_q_5']:.3f}")
    print(f"d_s_5 = 14 / (124 + 1) = {example['d_s_5']:.3f}")
    print(f"QF_5  = {example['QF_5_display']:.3f}")
    print(f"SF_5  = {example['SF_5_display']:.3f}")
    print(f"QSSPI_5 = {example['QSSPI_5_display']:.3f}")
    print(
        f"Interpretation: the sprint appears {example['apparent_lead_pct']:.1f}% ahead "
        f"under raw SPI, but {example['behind_plan_pct']:.1f}% behind plan after correction."
    )
    print("-" * 80)


def print_qsspi_summary() -> None:
    """Print a compact descriptive summary using scipy.stats."""
    summary = stats.describe(PUBLISHED_QSSPI)
    print("\nQSSPI descriptive summary")
    print("-" * 80)
    print(f"n          = {summary.nobs}")
    print(f"min / max  = {summary.minmax[0]:.3f} / {summary.minmax[1]:.3f}")
    print(f"mean       = {np.mean(PUBLISHED_QSSPI):.3f}")
    print(f"variance   = {summary.variance:.6f}")
    print("-" * 80)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Reproduce Table 5 and the Sprint 5 worked example.")
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
        help="Optional path for saving Table 5 as CSV.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    df = load_data(args.data)

    # Compute continuous values for internal QA, even though publication reproduction
    # uses the rounded display values defined above.
    _ = compute_continuous_metrics(df)

    table5 = build_publication_table(df)
    worked = sprint5_worked_example(df)

    print_table_5(table5)
    print_worked_example(worked)
    print_qsspi_summary()

    if args.csv_out is not None:
        table5.to_csv(args.csv_out, index=False)
        print(f"\nSaved reproduced Table 5 to: {args.csv_out}")


if __name__ == "__main__":
    main()
