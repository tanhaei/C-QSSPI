#!/usr/bin/env python3
"""Independent deterministic checks for the CQSS-SPI reproduction package."""

from __future__ import annotations

import math
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "code") not in sys.path:
    sys.path.insert(0, str(ROOT / "code"))

from ablation_study import build_table9, compute_quality_only  # noqa: E402
from compute_qssspi import (  # noqa: E402
    DEFAULT_DATA,
    EPSILON,
    LAMBDA_Q,
    LAMBDA_S,
    build_table6_sprint_case,
    build_table7_schedule_indicators,
    compute_continuous_metrics,
    load_data,
    sprint5_worked_example,
)
from counterfactual_analysis import (  # noqa: E402
    build_counterfactual_table,
    cqsspi_from_assumptions,
    solve_security_debt_for_on_plan,
)


EXPECTED_QF = np.array([0.967, 0.959, 0.951, 0.922, 0.908, 0.899, 0.957, 0.973])
EXPECTED_SF = np.array([0.986, 0.980, 0.975, 0.944, 0.925, 0.907, 0.970, 0.983])
EXPECTED_QSSPI = np.array([0.935, 0.968, 0.953, 0.958, 0.946, 0.907, 0.904, 0.948])
EXPECTED_SCENARIOS = np.array([0.946, 0.946, 0.984, 0.980, 0.992])


def assert_close(actual: float, expected: float, name: str, tol: float = 1e-9) -> None:
    if not np.isclose(actual, expected, atol=tol, rtol=0):
        raise AssertionError(f"{name}: expected {expected}, got {actual}")


def main() -> None:
    df = load_data(DEFAULT_DATA)
    table6 = build_table6_sprint_case(df)
    if table6.shape[0] != 8 or "Notes" not in table6.columns:
        raise AssertionError("Table 6 must contain eight BioArc sprints and the Notes column.")

    # Independent scalar calculations protect against a table that merely
    # copies manuscript constants.
    expected_exact: list[float] = []
    for row in df.itertuples(index=False):
        spi = row.EV_s / row.PV_s
        d_q = max(row.Delta_TD_s, 0.0) / (row.EV_s + EPSILON)
        d_s = max(row.Delta_SD_s, 0.0) / (row.EV_s + EPSILON)
        expected_exact.append(spi * math.exp(-LAMBDA_Q * d_q) * math.exp(-LAMBDA_S * d_s))

    metrics = compute_continuous_metrics(df)
    np.testing.assert_allclose(metrics["QSSPI_s"], expected_exact, atol=1e-12, rtol=0)

    table7 = build_table7_schedule_indicators(df)
    np.testing.assert_allclose(table7["QF_s"], EXPECTED_QF, atol=1e-12, rtol=0)
    np.testing.assert_allclose(table7["SF_s"], EXPECTED_SF, atol=1e-12, rtol=0)
    np.testing.assert_allclose(table7["QSSPI_s"], EXPECTED_QSSPI, atol=1e-12, rtol=0)

    worked = sprint5_worked_example(df)
    assert_close(round(worked["SPI_5_exact"], 3), 1.127, "Sprint 5 SPI")
    assert_close(worked["d_q_5_display"], 0.176, "Sprint 5 d_q")
    assert_close(worked["d_s_5_display"], 0.112, "Sprint 5 d_s")
    assert_close(worked["QF_5_display"], 0.908, "Sprint 5 QF")
    assert_close(worked["SF_5_display"], 0.925, "Sprint 5 SF")
    assert_close(worked["QSSPI_5_display"], 0.946, "Sprint 5 QSSPI")

    table9 = build_table9(df)
    panel_a = table9[table9["Panel"].str.startswith("Panel A")]["Index value"].to_numpy()
    np.testing.assert_allclose(panel_a, [1.043, 0.981, 0.940], atol=1e-12, rtol=0)
    assert_close(float(np.mean(compute_quality_only(df))), 0.981017700309805, "Quality-only exact average")

    scenarios = build_counterfactual_table(df)
    np.testing.assert_allclose(scenarios["CQSSPI"], EXPECTED_SCENARIOS, atol=1e-12, rtol=0)
    expected_inputs = np.array(
        [[124, 22, 14], [124, 22, 14], [123, 20, 7], [121, 18, 6], [119, 15, 3]],
        dtype=float,
    )
    np.testing.assert_allclose(
        scenarios[["EV_cf", "Delta_TD_cf", "Delta_SD_cf"]],
        expected_inputs,
        atol=0,
        rtol=0,
    )

    threshold = solve_security_debt_for_on_plan(124.0, 110.0, 22.0)
    assert_close(cqsspi_from_assumptions(124.0, 110.0, 22.0, threshold), 1.0, "Threshold solution")

    print("All equation-based CQSS-SPI reproduction checks passed.")


if __name__ == "__main__":
    main()
