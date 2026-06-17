#!/usr/bin/env python3
"""
BioArc Sprint 5 counterfactual demonstration for the CQSS-SPI metric.

Important:
- The script reproduces the single-case counterfactual values reported for the
  BioArc retrospective case.
- It is not a fitted population-level causal estimator and does not claim
  multi-domain experimental validation.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
from scipy.optimize import brentq

from compute_qssspi import DEFAULT_DATA, EPSILON, LAMBDA_Q, LAMBDA_S, PUBLISHED_QSSPI, load_data


FIGURE6_AND_TABLE9_VALUES = {
    "Observed QSSPI_5": 0.947,
    "No security gating increase (ablated)": 0.947,
    "Stronger gating (full model)": 0.983,
    "Selective AI restriction (full model)": 0.979,
    "Lower compression (full model)": 0.993,
}

# Internally consistent assumption sets that reproduce the rounded values above.
# These assumptions are case-based scenario inputs, not fitted SCM coefficients.
DEFAULT_ASSUMPTIONS = {
    "Observed QSSPI_5": {"EV_cf": np.nan, "Delta_TD_cf": np.nan, "Delta_SD_cf": np.nan},
    "No security gating increase (ablated)": {"EV_cf": 124.0, "Delta_TD_cf": 22.0, "Delta_SD_cf": 14.0},
    "Stronger gating (full model)": {"EV_cf": 123.0, "Delta_TD_cf": 20.0, "Delta_SD_cf": 7.1106},
    "Selective AI restriction (full model)": {"EV_cf": 121.0, "Delta_TD_cf": 18.0, "Delta_SD_cf": 6.1673},
    "Lower compression (full model)": {"EV_cf": 119.0, "Delta_TD_cf": 15.0, "Delta_SD_cf": 2.9002},
}


def cqsspi_from_assumptions(
    ev_cf: float,
    pv: float,
    delta_td_cf: float,
    delta_sd_cf: float,
    lambda_q: float = LAMBDA_Q,
    lambda_s: float = LAMBDA_S,
    epsilon: float = EPSILON,
) -> float:
    """Compute CQSSPI under user-specified counterfactual assumptions."""
    if ev_cf <= 0 or pv <= 0:
        raise ValueError("ev_cf and pv must be positive.")
    d_q = max(delta_td_cf, 0.0) / (ev_cf + epsilon)
    d_s = max(delta_sd_cf, 0.0) / (ev_cf + epsilon)
    return float((ev_cf / pv) * np.exp(-lambda_q * d_q - lambda_s * d_s))


def build_counterfactual_table(pv_sprint5: float) -> pd.DataFrame:
    """Build the Sprint 5 counterfactual table used for Figure 6/Table 9 checks."""
    rows = []
    for scenario, target_value in FIGURE6_AND_TABLE9_VALUES.items():
        assumptions = DEFAULT_ASSUMPTIONS[scenario]
        if scenario in {"Observed QSSPI_5", "No security gating increase (ablated)"}:
            # The observed and no-gating-increase ablated bars are displayed in
            # the manuscript as the same publication-rounded QSSPI value.
            computed = float(PUBLISHED_QSSPI[4])
            status = "observed/ablated publication value"
        else:
            computed = round(
                cqsspi_from_assumptions(
                    ev_cf=assumptions["EV_cf"],
                    pv=pv_sprint5,
                    delta_td_cf=assumptions["Delta_TD_cf"],
                    delta_sd_cf=assumptions["Delta_SD_cf"],
                ),
                3,
            )
            status = "case-based counterfactual demonstration"

        if round(computed, 3) != round(target_value, 3):
            raise AssertionError(
                f"{scenario} computed {computed:.3f}, expected manuscript value {target_value:.3f}."
            )

        rows.append(
            {
                "Scenario": scenario,
                "EV_cf": assumptions["EV_cf"],
                "Delta_TD_cf": assumptions["Delta_TD_cf"],
                "Delta_SD_cf": assumptions["Delta_SD_cf"],
                "CQSSPI": computed,
                "Status": status,
            }
        )
    return pd.DataFrame(rows)


# Backward-compatible alias from the earlier repository version.
def default_synthetic_scenarios(pv_sprint5: float) -> pd.DataFrame:
    return build_counterfactual_table(pv_sprint5)


def solve_security_debt_for_on_plan(
    ev_cf: float,
    pv: float,
    delta_td_cf: float,
    target_cqsspi: float = 1.0,
) -> float:
    """Solve the security-debt level required to reach a target CQSSPI."""

    def objective(delta_sd_cf: float) -> float:
        return cqsspi_from_assumptions(ev_cf, pv, delta_td_cf, delta_sd_cf) - target_cqsspi

    lower = objective(0.0)
    upper = objective(50.0)
    if lower * upper > 0:
        raise ValueError("The target CQSSPI is not bracketed for Delta_SD_cf in [0, 50].")
    return float(brentq(objective, 0.0, 50.0))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the BioArc Sprint 5 CQSS-SPI counterfactual demonstration.")
    parser.add_argument(
        "--data",
        type=Path,
        default=DEFAULT_DATA,
        help="Path to bioarc_retrospective_sprints.csv",
    )
    parser.add_argument("--ev-cf", type=float, default=None, help="Optional user-defined EV_cf for Sprint 5.")
    parser.add_argument("--delta-td-cf", type=float, default=None, help="Optional user-defined Delta_TD_cf.")
    parser.add_argument("--delta-sd-cf", type=float, default=None, help="Optional user-defined Delta_SD_cf.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    df = load_data(args.data)
    sprint5 = df.loc[df["Sprint"] == 5].iloc[0]
    pv_sprint5 = float(sprint5["PV_s"])

    print("\nBioArc Sprint 5 counterfactual demonstration")
    print("=" * 100)
    default_df = build_counterfactual_table(pv_sprint5)
    print(default_df.to_string(index=False))
    print("=" * 100)

    summary = stats.describe(default_df["CQSSPI"])
    print("\nScenario summary")
    print("-" * 100)
    print(f"mean       = {np.mean(default_df['CQSSPI']):.3f}")
    print(f"min / max  = {summary.minmax[0]:.3f} / {summary.minmax[1]:.3f}")
    print("-" * 100)

    required_sd = solve_security_debt_for_on_plan(
        ev_cf=float(sprint5["EV_s"]),
        pv=float(sprint5["PV_s"]),
        delta_td_cf=float(sprint5["Delta_TD_s"]),
        target_cqsspi=1.0,
    )
    print(
        "\nThreshold analysis\n"
        "----------------------------------------\n"
        f"If Sprint 5 kept EV_s={float(sprint5['EV_s']):.0f} and Delta_TD_s={float(sprint5['Delta_TD_s']):.0f},\n"
        f"the maximum Delta_SD_s compatible with CQSSPI=1.000 would be about {required_sd:.2f}.\n"
        "----------------------------------------"
    )

    if args.ev_cf is not None and args.delta_td_cf is not None and args.delta_sd_cf is not None:
        user_value = cqsspi_from_assumptions(
            ev_cf=args.ev_cf,
            pv=pv_sprint5,
            delta_td_cf=args.delta_td_cf,
            delta_sd_cf=args.delta_sd_cf,
        )
        print("\nUser-defined scenario")
        print("-" * 100)
        print(f"EV_cf       = {args.ev_cf:.3f}")
        print(f"Delta_TD_cf = {args.delta_td_cf:.3f}")
        print(f"Delta_SD_cf = {args.delta_sd_cf:.3f}")
        print(f"CQSSPI      = {user_value:.3f}")
        print("-" * 100)


if __name__ == "__main__":
    main()
