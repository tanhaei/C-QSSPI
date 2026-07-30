#!/usr/bin/env python3
"""Compute the BioArc CQSS-SPI results directly from the paper's equations.

The CSV contains two-decimal SPI values for human-readable display.  Those
values are validated on load, but every analytical result is calculated from
the authoritative ``EV_s / PV_s`` ratio and the unrounded penalty factors.
Rounding occurs only when a publication table is built or printed.
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
DISPLAY_DECIMALS = 3

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
    return [column for column in required if column not in present_set]


def validate_metric_parameters(lambda_q: float, lambda_s: float, epsilon: float) -> None:
    """Validate the sensitivity parameters used by the CQSS-SPI equations."""
    values = np.asarray([lambda_q, lambda_s, epsilon], dtype=float)
    if not np.isfinite(values).all():
        raise ValueError("lambda_q, lambda_s, and epsilon must be finite.")
    if lambda_q < 0 or lambda_s < 0:
        raise ValueError("lambda_q and lambda_s must be non-negative.")
    if epsilon <= 0:
        raise ValueError("epsilon must be strictly positive.")


def load_data(csv_path: Path) -> pd.DataFrame:
    """Load and validate the eight-sprint BioArc retrospective dataset.

    ``SPI_s`` in the source file is a two-decimal display field.  Once it has
    been checked against ``EV_s / PV_s``, it is replaced in the returned frame
    by the full-precision ratio so downstream calculations cannot accidentally
    use rounded inputs.
    """
    df = pd.read_csv(csv_path)

    missing = _missing(REQUIRED_COLUMNS, df.columns)
    if missing:
        raise ValueError(f"Missing required columns in {csv_path}: {missing}.")

    allowed = set(REQUIRED_COLUMNS + OPTIONAL_COLUMNS)
    unexpected = [column for column in df.columns if column not in allowed]
    if unexpected:
        raise ValueError(f"Unexpected columns in {csv_path}: {unexpected}.")

    df = df.copy()
    for column in REQUIRED_COLUMNS:
        df[column] = pd.to_numeric(df[column], errors="raise")

    numeric = df[REQUIRED_COLUMNS].to_numpy(dtype=float)
    if not np.isfinite(numeric).all():
        raise ValueError("All required numeric fields must be finite.")

    if not np.allclose(df["Sprint"], np.round(df["Sprint"]), atol=0, rtol=0):
        raise ValueError("Sprint identifiers must be integers.")

    df["Sprint"] = df["Sprint"].astype(int)
    df = df.sort_values("Sprint").reset_index(drop=True)
    if len(df) != 8 or df["Sprint"].tolist() != list(range(1, 9)):
        raise ValueError("The BioArc case must contain exactly one record for each Sprint 1--8.")

    if (df["PV_s"] <= 0).any() or (df["EV_s"] <= 0).any():
        raise ValueError("PV_s and EV_s must be positive for all sprints.")

    for column in ("A_s", "C_s", "G_s"):
        if not df[column].between(0.0, 1.0, inclusive="both").all():
            raise ValueError(f"{column} must lie in [0, 1].")

    reported_spi = df["SPI_s"].to_numpy(dtype=float)
    exact_spi = (df["EV_s"] / df["PV_s"]).to_numpy(dtype=float)
    if not np.allclose(reported_spi, exact_spi, atol=0.005, rtol=0):
        raise ValueError("The reported SPI_s values are inconsistent with EV_s / PV_s at two-decimal precision.")

    # Exact EV/PV is the analytical source of truth; the CSV SPI is display-only.
    df["SPI_s"] = exact_spi
    return df


def compute_continuous_metrics(
    df: pd.DataFrame,
    lambda_q: float = LAMBDA_Q,
    lambda_s: float = LAMBDA_S,
    epsilon: float = EPSILON,
) -> pd.DataFrame:
    """Compute unrounded quantities from the CQSS-SPI equations."""
    validate_metric_parameters(lambda_q, lambda_s, epsilon)
    missing = _missing(REQUIRED_COLUMNS, df.columns)
    if missing:
        raise ValueError(f"Cannot compute CQSS-SPI; missing columns: {missing}.")

    out = df.copy()
    out["SPI_s"] = out["EV_s"] / out["PV_s"]
    out["d_q_s"] = np.maximum(out["Delta_TD_s"], 0.0) / (out["EV_s"] + epsilon)
    out["d_s_s"] = np.maximum(out["Delta_SD_s"], 0.0) / (out["EV_s"] + epsilon)
    out["QF_s"] = np.exp(-lambda_q * out["d_q_s"])
    out["SF_s"] = np.exp(-lambda_s * out["d_s_s"])
    out["QSSPI_q_s"] = out["SPI_s"] * out["QF_s"]
    out["QSSPI_s"] = out["QSSPI_q_s"] * out["SF_s"]
    return out


def build_table6_sprint_case(df: pd.DataFrame) -> pd.DataFrame:
    """Build the paper's BioArc sprint-input table."""
    columns = REQUIRED_COLUMNS + (["Notes"] if "Notes" in df.columns else [])
    table = df[columns].copy()
    table["Sprint"] = table["Sprint"].astype(int)
    table["SPI_s"] = (table["EV_s"] / table["PV_s"]).round(2)
    return table


def build_table7_schedule_indicators(
    df: pd.DataFrame,
    lambda_q: float = LAMBDA_Q,
    lambda_s: float = LAMBDA_S,
    epsilon: float = EPSILON,
) -> pd.DataFrame:
    """Build the paper's raw/corrected schedule table from unrounded results."""
    metrics = compute_continuous_metrics(df, lambda_q, lambda_s, epsilon)
    if len(metrics) != len(INTERPRETATIONS):
        raise ValueError("The publication interpretation labels expect exactly eight sprints.")

    return pd.DataFrame(
        {
            "Sprint": metrics["Sprint"].astype(int),
            "SPI_s": metrics["SPI_s"].round(2),
            "QF_s": metrics["QF_s"].round(DISPLAY_DECIMALS),
            "SF_s": metrics["SF_s"].round(DISPLAY_DECIMALS),
            "QSSPI_s": metrics["QSSPI_s"].round(DISPLAY_DECIMALS),
            "Interpretation": INTERPRETATIONS,
        }
    )


# Backward-compatible alias retained for repository users.
build_publication_table = build_table7_schedule_indicators


def sprint5_worked_example(
    df: pd.DataFrame,
    lambda_q: float = LAMBDA_Q,
    lambda_s: float = LAMBDA_S,
    epsilon: float = EPSILON,
) -> dict[str, float]:
    """Return exact and publication-rounded Sprint 5 values."""
    metrics = compute_continuous_metrics(df, lambda_q, lambda_s, epsilon)
    row = metrics.loc[metrics["Sprint"] == 5].iloc[0]

    return {
        "PV_5": float(row["PV_s"]),
        "EV_5": float(row["EV_s"]),
        "Delta_TD_5": float(row["Delta_TD_s"]),
        "Delta_SD_5": float(row["Delta_SD_s"]),
        "epsilon": float(epsilon),
        "SPI_5_exact": float(row["SPI_s"]),
        "d_q_5_exact": float(row["d_q_s"]),
        "d_s_5_exact": float(row["d_s_s"]),
        "QF_5_exact": float(row["QF_s"]),
        "SF_5_exact": float(row["SF_s"]),
        "QSSPI_5_exact": float(row["QSSPI_s"]),
        "d_q_5_display": round(float(row["d_q_s"]), DISPLAY_DECIMALS),
        "d_s_5_display": round(float(row["d_s_s"]), DISPLAY_DECIMALS),
        "QF_5_display": round(float(row["QF_s"]), DISPLAY_DECIMALS),
        "SF_5_display": round(float(row["SF_s"]), DISPLAY_DECIMALS),
        "QSSPI_5_display": round(float(row["QSSPI_s"]), DISPLAY_DECIMALS),
        "apparent_lead_pct": round((float(row["SPI_s"]) - 1.0) * 100.0, 1),
        "behind_plan_pct": round((1.0 - float(row["QSSPI_s"])) * 100.0, 1),
    }


def qsspi_summary(
    df: pd.DataFrame,
    lambda_q: float = LAMBDA_Q,
    lambda_s: float = LAMBDA_S,
    epsilon: float = EPSILON,
) -> dict[str, float]:
    """Return descriptive statistics based on unrounded QSSPI values."""
    values = compute_continuous_metrics(df, lambda_q, lambda_s, epsilon)["QSSPI_s"].to_numpy()
    summary = stats.describe(values)
    return {
        "n": float(summary.nobs),
        "min": float(summary.minmax[0]),
        "max": float(summary.minmax[1]),
        "mean": float(np.mean(values)),
        "variance": float(summary.variance),
    }


def print_table(title: str, table: pd.DataFrame) -> None:
    print(f"\n{title}")
    print("=" * 100)
    print(table.to_string(index=False))
    print("=" * 100)


def print_worked_example(example: dict[str, float]) -> None:
    print("\nSprint 5 worked example")
    print("-" * 100)
    print(f"SPI_5 = {example['EV_5']:.0f} / {example['PV_5']:.0f} = {example['SPI_5_exact']:.3f}")
    epsilon = example["epsilon"]
    print(
        f"d_q_5 = {example['Delta_TD_5']:.0f} / ({example['EV_5']:.0f} + {epsilon:g}) "
        f"= {example['d_q_5_display']:.3f}"
    )
    print(
        f"d_s_5 = {example['Delta_SD_5']:.0f} / ({example['EV_5']:.0f} + {epsilon:g}) "
        f"= {example['d_s_5_display']:.3f}"
    )
    print(f"QF_5     = {example['QF_5_display']:.3f}")
    print(f"SF_5     = {example['SF_5_display']:.3f}")
    print(f"QSSPI_5  = {example['QSSPI_5_display']:.3f}")
    print(
        f"Interpretation: the sprint appears {example['apparent_lead_pct']:.1f}% ahead "
        f"under raw SPI, but {example['behind_plan_pct']:.1f}% behind plan after correction."
    )
    print("-" * 100)


def print_qsspi_summary(summary: dict[str, float]) -> None:
    print("\nQSSPI descriptive summary (unrounded values)")
    print("-" * 100)
    print(f"n          = {summary['n']:.0f}")
    print(f"min / max  = {summary['min']:.3f} / {summary['max']:.3f}")
    print(f"mean       = {summary['mean']:.3f}")
    print(f"variance   = {summary['variance']:.6f}")
    print("-" * 100)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Reproduce the BioArc sprint tables and Sprint 5 CQSS-SPI worked example."
    )
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA)
    parser.add_argument("--lambda-q", type=float, default=LAMBDA_Q)
    parser.add_argument("--lambda-s", type=float, default=LAMBDA_S)
    parser.add_argument("--epsilon", type=float, default=EPSILON)
    parser.add_argument("--table6-csv-out", type=Path, default=None)
    parser.add_argument("--table7-csv-out", type=Path, default=None)
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
    table6 = build_table6_sprint_case(df)
    table7 = build_table7_schedule_indicators(df, args.lambda_q, args.lambda_s, args.epsilon)
    worked = sprint5_worked_example(df, args.lambda_q, args.lambda_s, args.epsilon)
    summary = qsspi_summary(df, args.lambda_q, args.lambda_s, args.epsilon)

    print_table("Reproduced Table 6: BioArc retrospective sprint case", table6)
    print_table("Reproduced Table 7: raw and corrected schedule indicators", table7)
    print_worked_example(worked)
    print_qsspi_summary(summary)

    if args.table6_csv_out is not None:
        args.table6_csv_out.parent.mkdir(parents=True, exist_ok=True)
        table6.to_csv(args.table6_csv_out, index=False)
        print(f"\nSaved reproduced Table 6 to: {args.table6_csv_out}")

    table7_out = args.table7_csv_out or args.csv_out
    if table7_out is not None:
        table7_out.parent.mkdir(parents=True, exist_ok=True)
        table7.to_csv(table7_out, index=False)
        print(f"\nSaved reproduced Table 7 to: {table7_out}")


if __name__ == "__main__":
    main()
