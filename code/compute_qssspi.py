#!/usr/bin/env python3
"""
Reproduce the BioArc retrospective schedule-indicator tables and the Sprint 5
worked example for the CQSS-SPI paper.

The script follows the manuscript's current framing:
- the eight-sprint data are anonymized BioArc retrospective project-control
  records expressed in normalized effort units;
- the case is a single-system retrospective case, not a controlled experiment
  and not a multi-domain validation;
- publication tables are reproduced using the manuscript's display-rounded
  values so that the repository output matches the paper exactly.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd
from scipy import stats

LAMBDA_Q = 0.55
LAMBDA_S = 0.70
EPSILON = 1.0

REQUIRED_COLUMNS = [
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
OPTIONAL_COLUMNS = ["Notes"]

# Publication-rounded values used to reproduce Table 7 exactly as displayed in
# the manuscript. They are intentionally separated from continuous calculations
# because the paper reports values rounded for display.
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

DEFAULT_DATA = Path(__file__).resolve().parents[1] / "data" / "bioarc_retrospective_sprints.csv"


def _missing(required: Iterable[str], present: Iterable[str]) -> list[str]:
    present_set = set(present)
    return [col for col in required if col not in present_set]


def load_data(csv_path: Path) -> pd.DataFrame:
    """Load and validate the BioArc retrospective sprint dataset."""
    df = pd.read_csv(csv_path)

    missing = _missing(REQUIRED_COLUMNS, df.columns)
    if missing:
        raise ValueError(f"Missing required columns in {csv_path}: {missing}.")

    allowed = set(REQUIRED_COLUMNS + OPTIONAL_COLUMNS)
    unexpected = [col for col in df.columns if col not in allowed]
    if unexpected:
        raise ValueError(f"Unexpected columns in {csv_path}: {unexpected}.")

    df = df.copy()
    df = df.sort_values("Sprint").reset_index(drop=True)

    if len(df) != 8 or list(df["Sprint"].astype(int)) != list(range(1, 9)):
        raise ValueError("The BioArc case should contain exactly Sprints 1--8.")

    numeric_columns = REQUIRED_COLUMNS
    for col in numeric_columns:
        df[col] = pd.to_numeric(df[col], errors="raise")

    if (df["PV_s"] <= 0).any() or (df["EV_s"] <= 0).any():
        raise ValueError("PV_s and EV_s must be positive for all sprints.")

    # Validate that the displayed SPI values are consistent with EV/PV to the
    # precision used in the manuscript table.
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
    """Compute continuous metric terms from Equations 7--12 of the paper."""
    out = df.copy()

    out["d_q_cont"] = np.maximum(out["Delta_TD_s"], 0.0) / (out["EV_s"] + epsilon)
    out["d_s_cont"] = np.maximum(out["Delta_SD_s"], 0.0) / (out["EV_s"] + epsilon)
    out["QF_cont"] = np.exp(-lambda_q * out["d_q_cont"])
    out["SF_cont"] = np.exp(-lambda_s * out["d_s_cont"])
    out["QSSPI_cont"] = out["SPI_s"] * out["QF_cont"] * out["SF_cont"]

    return out


def build_table6_sprint_case(df: pd.DataFrame) -> pd.DataFrame:
    """Build the publication-style Table 6 BioArc sprint case."""
    columns = REQUIRED_COLUMNS + (["Notes"] if "Notes" in df.columns else [])
    table = df[columns].copy()
    table["Sprint"] = table["Sprint"].astype(int)
    return table


def build_table7_schedule_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Build the publication-style Table 7 raw/corrected indicator comparison."""
    if len(df) != len(PUBLISHED_QF):
        raise ValueError("Published display arrays expect exactly eight sprints.")

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


# Backward-compatible alias for earlier scripts/users.
build_publication_table = build_table7_schedule_indicators


def sprint5_worked_example(df: pd.DataFrame) -> dict[str, float]:
    """Return the publication-style Sprint 5 worked-example values."""
    row = df.loc[df["Sprint"] == 5].iloc[0]

    spi_exact = row["EV_s"] / row["PV_s"]
    d_q = round(row["Delta_TD_s"] / (row["EV_s"] + EPSILON), 3)
    d_s = round(row["Delta_SD_s"] / (row["EV_s"] + EPSILON), 3)

    qf_display = PUBLISHED_QF[4]
    sf_display = PUBLISHED_SF[4]
    qsspi_display = PUBLISHED_QSSPI[4]

    return {
        "SPI_5_exact": spi_exact,
        "d_q_5": d_q,
        "d_s_5": d_s,
        "QF_5_display": qf_display,
        "SF_5_display": sf_display,
        "QSSPI_5_display": qsspi_display,
        "apparent_lead_pct": round((spi_exact - 1.0) * 100.0, 1),
        "behind_plan_pct": round((1.0 - qsspi_display) * 100.0, 1),
    }


def print_table(title: str, table: pd.DataFrame) -> None:
    """Print a table with a consistent console header."""
    print(f"\n{title}")
    print("=" * 100)
    print(table.to_string(index=False))
    print("=" * 100)


def print_worked_example(example: dict[str, float]) -> None:
    """Print the Sprint 5 worked example exactly as interpreted in the paper."""
    print("\nSprint 5 worked example")
    print("-" * 100)
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
    print("-" * 100)


def qsspi_summary() -> dict[str, float]:
    """Return a compact descriptive summary for the Table 7 QSSPI values."""
    summary = stats.describe(PUBLISHED_QSSPI)
    return {
        "n": float(summary.nobs),
        "min": float(summary.minmax[0]),
        "max": float(summary.minmax[1]),
        "mean": float(np.mean(PUBLISHED_QSSPI)),
        "variance": float(summary.variance),
    }


def print_qsspi_summary() -> None:
    """Print a compact descriptive summary using scipy.stats."""
    summary = qsspi_summary()
    print("\nQSSPI descriptive summary")
    print("-" * 100)
    print(f"n          = {summary['n']:.0f}")
    print(f"min / max  = {summary['min']:.3f} / {summary['max']:.3f}")
    print(f"mean       = {summary['mean']:.3f}")
    print(f"variance   = {summary['variance']:.6f}")
    print("-" * 100)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Reproduce the BioArc retrospective Table 6, Table 7, and Sprint 5 worked example."
    )
    parser.add_argument(
        "--data",
        type=Path,
        default=DEFAULT_DATA,
        help="Path to bioarc_retrospective_sprints.csv",
    )
    parser.add_argument(
        "--table6-csv-out",
        type=Path,
        default=None,
        help="Optional path for saving Table 6 as CSV.",
    )
    parser.add_argument(
        "--table7-csv-out",
        type=Path,
        default=None,
        help="Optional path for saving Table 7 as CSV.",
    )
    # Backward-compatible option from the earlier repository version.
    parser.add_argument(
        "--csv-out",
        type=Path,
        default=None,
        help="Backward-compatible alias for --table7-csv-out.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    df = load_data(args.data)
    _ = compute_continuous_metrics(df)  # Internal QA calculation.

    table6 = build_table6_sprint_case(df)
    table7 = build_table7_schedule_indicators(df)
    worked = sprint5_worked_example(df)

    print_table("Reproduced Table 6: BioArc retrospective sprint case", table6)
    print_table("Reproduced Table 7: raw and corrected schedule indicators", table7)
    print_worked_example(worked)
    print_qsspi_summary()

    if args.table6_csv_out is not None:
        table6.to_csv(args.table6_csv_out, index=False)
        print(f"\nSaved reproduced Table 6 to: {args.table6_csv_out}")

    table7_out = args.table7_csv_out or args.csv_out
    if table7_out is not None:
        table7.to_csv(table7_out, index=False)
        print(f"\nSaved reproduced Table 7 to: {table7_out}")


if __name__ == "__main__":
    main()
