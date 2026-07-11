#!/usr/bin/env python3
"""Transparent Sprint 5 intervention-sensitivity calculations.

The manuscript does not estimate structural coefficients from eight sprints.
Accordingly, the alternatives below are deterministic, case-based assumptions
about counterfactual earned value and debt.  The script computes every reported
index from those disclosed inputs; it does not tune hidden inputs to reproduce
preselected CQSSPI values.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
from scipy.optimize import brentq

from compute_qssspi import (
    DEFAULT_DATA,
    DISPLAY_DECIMALS,
    EPSILON,
    LAMBDA_Q,
    LAMBDA_S,
    load_data,
    validate_metric_parameters,
)


@dataclass(frozen=True)
class ScenarioAssumption:
    """Disclosed deterministic inputs for one Sprint 5 what-if scenario."""

    name: str
    ev_cf: float
    delta_td_cf: float
    delta_sd_cf: float
    status: str


def sprint5_scenarios(sprint5: pd.Series) -> list[ScenarioAssumption]:
    """Return observed and simple whole-unit sensitivity assumptions.

    The three intervention inputs stay within the range of the BioArc sprint
    record and intentionally use whole normalized-effort units.  They are
    assumptions for sensitivity analysis, not fitted causal estimates.
    """
    observed = {
        "ev_cf": float(sprint5["EV_s"]),
        "delta_td_cf": float(sprint5["Delta_TD_s"]),
        "delta_sd_cf": float(sprint5["Delta_SD_s"]),
    }
    return [
        ScenarioAssumption(
            "Observed QSSPI_5",
            **observed,
            status="observed record",
        ),
        ScenarioAssumption(
            "No security-gating increase (ablated)",
            **observed,
            status="null intervention; observed inputs retained",
        ),
        ScenarioAssumption(
            "Stronger gating (scenario)",
            ev_cf=123.0,
            delta_td_cf=20.0,
            delta_sd_cf=7.0,
            status="deterministic sensitivity assumption",
        ),
        ScenarioAssumption(
            "Selective AI restriction (scenario)",
            ev_cf=121.0,
            delta_td_cf=18.0,
            delta_sd_cf=6.0,
            status="deterministic sensitivity assumption",
        ),
        ScenarioAssumption(
            "Lower compression (scenario)",
            ev_cf=119.0,
            delta_td_cf=15.0,
            delta_sd_cf=3.0,
            status="deterministic sensitivity assumption",
        ),
    ]


def cqsspi_from_assumptions(
    ev_cf: float,
    pv: float,
    delta_td_cf: float,
    delta_sd_cf: float,
    lambda_q: float = LAMBDA_Q,
    lambda_s: float = LAMBDA_S,
    epsilon: float = EPSILON,
) -> float:
    """Compute CQSSPI for explicitly supplied counterfactual quantities."""
    validate_metric_parameters(lambda_q, lambda_s, epsilon)
    inputs = np.asarray([ev_cf, pv, delta_td_cf, delta_sd_cf], dtype=float)
    if not np.isfinite(inputs).all():
        raise ValueError("Counterfactual inputs must be finite.")
    if ev_cf <= 0 or pv <= 0:
        raise ValueError("ev_cf and pv must be positive.")

    d_q = max(delta_td_cf, 0.0) / (ev_cf + epsilon)
    d_s = max(delta_sd_cf, 0.0) / (ev_cf + epsilon)
    return float((ev_cf / pv) * np.exp(-lambda_q * d_q - lambda_s * d_s))


def build_counterfactual_table(
    df: pd.DataFrame,
    lambda_q: float = LAMBDA_Q,
    lambda_s: float = LAMBDA_S,
    epsilon: float = EPSILON,
) -> pd.DataFrame:
    """Build the disclosed Sprint 5 intervention-sensitivity table."""
    sprint5 = df.loc[df["Sprint"] == 5]
    if len(sprint5) != 1:
        raise ValueError("Exactly one Sprint 5 record is required.")
    row = sprint5.iloc[0]
    pv = float(row["PV_s"])

    records: list[dict[str, float | str]] = []
    for scenario in sprint5_scenarios(row):
        value = cqsspi_from_assumptions(
            scenario.ev_cf,
            pv,
            scenario.delta_td_cf,
            scenario.delta_sd_cf,
            lambda_q,
            lambda_s,
            epsilon,
        )
        records.append(
            {
                "Scenario": scenario.name,
                "EV_cf": scenario.ev_cf,
                "Delta_TD_cf": scenario.delta_td_cf,
                "Delta_SD_cf": scenario.delta_sd_cf,
                "CQSSPI_exact": value,
                "CQSSPI": round(value, DISPLAY_DECIMALS),
                "Status": scenario.status,
            }
        )

    table = pd.DataFrame(records)
    observed = float(table.loc[table["Scenario"] == "Observed QSSPI_5", "CQSSPI_exact"].iloc[0])
    table["Change_pp"] = ((table["CQSSPI_exact"] - observed) * 100.0).round(1)
    return table


def default_synthetic_scenarios(pv_sprint5: float) -> pd.DataFrame:
    """Backward-compatible wrapper for the repository's earlier public API."""
    df = load_data(DEFAULT_DATA)
    actual_pv = float(df.loc[df["Sprint"] == 5, "PV_s"].iloc[0])
    if not np.isclose(pv_sprint5, actual_pv, atol=1e-12, rtol=0):
        raise ValueError(f"The BioArc Sprint 5 PV is {actual_pv:g}, not {pv_sprint5:g}.")
    return build_counterfactual_table(df)


def solve_security_debt_for_on_plan(
    ev_cf: float,
    pv: float,
    delta_td_cf: float,
    target_cqsspi: float = 1.0,
    lambda_q: float = LAMBDA_Q,
    lambda_s: float = LAMBDA_S,
    epsilon: float = EPSILON,
) -> float:
    """Solve the maximum non-negative security debt for a target CQSSPI."""
    if target_cqsspi <= 0 or not np.isfinite(target_cqsspi):
        raise ValueError("target_cqsspi must be finite and positive.")

    def objective(delta_sd_cf: float) -> float:
        return (
            cqsspi_from_assumptions(
                ev_cf,
                pv,
                delta_td_cf,
                delta_sd_cf,
                lambda_q,
                lambda_s,
                epsilon,
            )
            - target_cqsspi
        )

    at_zero = objective(0.0)
    if np.isclose(at_zero, 0.0, atol=1e-12, rtol=0):
        return 0.0
    if at_zero < 0:
        raise ValueError("The target is unattainable even with zero security debt.")

    upper = 1.0
    while objective(upper) > 0 and upper < 1e6:
        upper *= 2.0
    if objective(upper) > 0:
        raise ValueError("Could not bracket the target security-debt threshold.")
    return float(brentq(objective, 0.0, upper))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the BioArc Sprint 5 deterministic intervention-sensitivity analysis."
    )
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA)
    parser.add_argument("--lambda-q", type=float, default=LAMBDA_Q)
    parser.add_argument("--lambda-s", type=float, default=LAMBDA_S)
    parser.add_argument("--epsilon", type=float, default=EPSILON)
    parser.add_argument("--csv-out", type=Path, default=None)
    parser.add_argument("--ev-cf", type=float, default=None)
    parser.add_argument("--delta-td-cf", type=float, default=None)
    parser.add_argument("--delta-sd-cf", type=float, default=None)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    df = load_data(args.data)
    sprint5 = df.loc[df["Sprint"] == 5].iloc[0]
    table = build_counterfactual_table(df, args.lambda_q, args.lambda_s, args.epsilon)

    print("\nBioArc Sprint 5 intervention-sensitivity analysis")
    print("=" * 120)
    print(table.to_string(index=False))
    print("=" * 120)

    summary = stats.describe(table["CQSSPI_exact"])
    print("\nScenario summary (unrounded values)")
    print("-" * 80)
    print(f"mean       = {np.mean(table['CQSSPI_exact']):.3f}")
    print(f"min / max  = {summary.minmax[0]:.3f} / {summary.minmax[1]:.3f}")
    print("-" * 80)

    try:
        required_sd = solve_security_debt_for_on_plan(
            ev_cf=float(sprint5["EV_s"]),
            pv=float(sprint5["PV_s"]),
            delta_td_cf=float(sprint5["Delta_TD_s"]),
            target_cqsspi=1.0,
            lambda_q=args.lambda_q,
            lambda_s=args.lambda_s,
            epsilon=args.epsilon,
        )
        print(
            "\nThreshold analysis\n"
            "----------------------------------------\n"
            f"At EV={float(sprint5['EV_s']):.0f} and Delta_TD={float(sprint5['Delta_TD_s']):.0f}, "
            f"CQSSPI=1.000 permits Delta_SD up to approximately {required_sd:.2f}.\n"
            "----------------------------------------"
        )
    except ValueError as exc:
        print(f"\nThreshold analysis: {exc}")

    supplied = [args.ev_cf, args.delta_td_cf, args.delta_sd_cf]
    if any(value is not None for value in supplied) and not all(value is not None for value in supplied):
        raise SystemExit("--ev-cf, --delta-td-cf, and --delta-sd-cf must be supplied together.")
    if all(value is not None for value in supplied):
        user_value = cqsspi_from_assumptions(
            args.ev_cf,
            float(sprint5["PV_s"]),
            args.delta_td_cf,
            args.delta_sd_cf,
            args.lambda_q,
            args.lambda_s,
            args.epsilon,
        )
        print("\nUser-defined scenario")
        print("-" * 80)
        print(f"EV_cf       = {args.ev_cf:.3f}")
        print(f"Delta_TD_cf = {args.delta_td_cf:.3f}")
        print(f"Delta_SD_cf = {args.delta_sd_cf:.3f}")
        print(f"CQSSPI      = {user_value:.6f} (display: {user_value:.3f})")
        print("-" * 80)

    if args.csv_out is not None:
        args.csv_out.parent.mkdir(parents=True, exist_ok=True)
        table.to_csv(args.csv_out, index=False)
        print(f"\nSaved Sprint 5 scenario table to: {args.csv_out}")


if __name__ == "__main__":
    main()
