#!/usr/bin/env python3
"""
Synthetic counterfactual sandbox for the CQSS-SPI metric.

Important:
- This script is a scenario-analysis tool for the illustrative scenario.
- It does not estimate a fitted causal model from empirical field data.
- Default examples are synthetic and are included to support policy reasoning.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import brentq
from scipy import stats

from compute_qssspi import EPSILON, LAMBDA_Q, LAMBDA_S, PUBLISHED_QSSPI, load_data


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
    d_q = max(delta_td_cf, 0.0) / (ev_cf + epsilon)
    d_s = max(delta_sd_cf, 0.0) / (ev_cf + epsilon)
    return (ev_cf / pv) * np.exp(-lambda_q * d_q - lambda_s * d_s)


def default_synthetic_scenarios(pv_sprint5: float) -> pd.DataFrame:
    """
    Provide internally consistent synthetic examples for Sprint 5.

    These are scenario assumptions for illustration only.
    """
    scenarios = [
        ("Observed Sprint 5 (publication value)", np.nan, np.nan, np.nan, float(PUBLISHED_QSSPI[4])),
        ("Stronger gating (synthetic assumption)", 123.0, 20.0, 6.0, None),
        ("Selective AI restriction (synthetic assumption)", 121.0, 18.0, 5.0, None),
        ("Lower compression (synthetic assumption)", 119.0, 15.0, 6.0, None),
    ]

    rows = []
    for name, ev_cf, delta_td_cf, delta_sd_cf, published_value in scenarios:
        if published_value is not None:
            cqsspi_value = published_value
        else:
            cqsspi_value = round(
                cqsspi_from_assumptions(ev_cf, pv_sprint5, delta_td_cf, delta_sd_cf), 3
            )

        rows.append(
            {
                "Scenario": name,
                "EV_cf": ev_cf,
                "Delta_TD_cf": delta_td_cf,
                "Delta_SD_cf": delta_sd_cf,
                "CQSSPI": cqsspi_value,
                "Status": "synthetic scenario value",
            }
        )

    return pd.DataFrame(rows)


def solve_security_debt_for_on_plan(
    ev_cf: float,
    pv: float,
    delta_td_cf: float,
    target_cqsspi: float = 1.0,
) -> float:
    """
    Solve the security-debt level required to achieve a target CQSSPI
    under fixed EV and technical debt assumptions.
    """

    def objective(delta_sd_cf: float) -> float:
        return cqsspi_from_assumptions(ev_cf, pv, delta_td_cf, delta_sd_cf) - target_cqsspi

    return brentq(objective, 0.0, 50.0)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the synthetic CQSS-SPI counterfactual sandbox.")
    parser.add_argument(
        "--data",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "data" / "illustrative_sprints.csv",
        help="Path to illustrative_sprints.csv",
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

    print("\nSynthetic Sprint 5 counterfactual scenarios")
    print("=" * 80)
    default_df = default_synthetic_scenarios(pv_sprint5)
    print(default_df.to_string(index=False))
    print("=" * 80)

    summary = stats.describe(default_df["CQSSPI"])
    print("\nScenario summary")
    print("-" * 80)
    print(f"mean       = {np.mean(default_df['CQSSPI']):.3f}")
    print(f"min / max  = {summary.minmax[0]:.3f} / {summary.minmax[1]:.3f}")
    print("-" * 80)

    required_sd = solve_security_debt_for_on_plan(
        ev_cf=float(sprint5["EV_s"]),
        pv=float(sprint5["PV_s"]),
        delta_td_cf=float(sprint5["Delta_TD_s"]),
        target_cqsspi=1.0,
    )
    print(
        "\nIllustrative threshold analysis\n"
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
        print("-" * 80)
        print(f"EV_cf       = {args.ev_cf:.3f}")
        print(f"Delta_TD_cf = {args.delta_td_cf:.3f}")
        print(f"Delta_SD_cf = {args.delta_sd_cf:.3f}")
        print(f"CQSSPI      = {user_value:.3f}")
        print("-" * 80)


if __name__ == "__main__":
    main()
