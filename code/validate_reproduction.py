#!/usr/bin/env python3
"""Deterministic reproduction checks for the CQSS-SPI repository."""

from __future__ import annotations

from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "code") not in sys.path:
    sys.path.insert(0, str(ROOT / "code"))

from compute_qssspi import (  # noqa: E402
    DEFAULT_DATA,
    PUBLISHED_QF,
    PUBLISHED_QSSPI,
    PUBLISHED_SF,
    build_table6_sprint_case,
    build_table7_schedule_indicators,
    load_data,
    sprint5_worked_example,
)
from ablation_study import build_table9, compute_quality_only  # noqa: E402
from counterfactual_analysis import build_counterfactual_table  # noqa: E402


def assert_close(actual: float, expected: float, name: str, tol: float = 1e-9) -> None:
    if not np.isclose(actual, expected, atol=tol, rtol=0):
        raise AssertionError(f"{name}: expected {expected}, got {actual}")


def main() -> None:
    df = load_data(DEFAULT_DATA)

    table6 = build_table6_sprint_case(df)
    if table6.shape[0] != 8:
        raise AssertionError("Table 6 should contain eight BioArc sprints.")
    if "Notes" not in table6.columns:
        raise AssertionError("Table 6 reproduction should include the Notes column.")

    table7 = build_table7_schedule_indicators(df)
    expected_qsspi = [0.934, 0.968, 0.954, 0.957, 0.947, 0.904, 0.899, 0.948]
    if not np.allclose(table7["QSSPI_s"].to_numpy(), expected_qsspi, atol=1e-12, rtol=0):
        raise AssertionError("Table 7 QSSPI values do not match the manuscript.")
    if not np.allclose(table7["QF_s"].to_numpy(), PUBLISHED_QF, atol=1e-12, rtol=0):
        raise AssertionError("Table 7 QF values do not match the manuscript.")
    if not np.allclose(table7["SF_s"].to_numpy(), PUBLISHED_SF, atol=1e-12, rtol=0):
        raise AssertionError("Table 7 SF values do not match the manuscript.")

    worked = sprint5_worked_example(df)
    assert_close(round(worked["SPI_5_exact"], 3), 1.127, "Sprint 5 SPI")
    assert_close(worked["d_q_5"], 0.176, "Sprint 5 d_q")
    assert_close(worked["d_s_5"], 0.112, "Sprint 5 d_s")
    assert_close(worked["QF_5_display"], 0.907, "Sprint 5 QF")
    assert_close(worked["SF_5_display"], 0.924, "Sprint 5 SF")
    assert_close(worked["QSSPI_5_display"], 0.947, "Sprint 5 QSSPI")

    table9 = build_table9(df)
    assert_close(float(np.round(df["SPI_s"].mean(), 3)), 1.042, "Raw SPI average")
    assert_close(float(np.round(compute_quality_only(df).mean(), 3)), 0.980, "Quality-only average")
    assert_close(float(np.round(PUBLISHED_QSSPI.mean(), 3)), 0.939, "Full QSSPI average")
    for expected in [0.983, 0.979, 0.993]:
        if expected not in set(table9["Index value"].round(3)):
            raise AssertionError(f"Table 9 is missing counterfactual value {expected}.")

    cf = build_counterfactual_table(float(df.loc[df["Sprint"] == 5, "PV_s"].iloc[0]))
    expected_cf = [0.947, 0.947, 0.983, 0.979, 0.993]
    if not np.allclose(cf["CQSSPI"].to_numpy(), expected_cf, atol=1e-12, rtol=0):
        raise AssertionError("Figure 6/Table 9 counterfactual values do not match the manuscript.")

    print("All CQSS-SPI reproduction checks passed.")


if __name__ == "__main__":
    main()
