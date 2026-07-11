from __future__ import annotations

import math
from pathlib import Path
import sys
import tempfile
import unittest

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
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
    validate_metric_parameters,
)
from counterfactual_analysis import (  # noqa: E402
    build_counterfactual_table,
    cqsspi_from_assumptions,
    solve_security_debt_for_on_plan,
)
from generate_figures import generate_all_figures  # noqa: E402


class TestEquationBasedReproduction(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.df = load_data(DEFAULT_DATA)

    def test_table6_shape_notes_and_display_spi(self) -> None:
        table6 = build_table6_sprint_case(self.df)
        self.assertEqual(len(table6), 8)
        self.assertIn("Notes", table6.columns)
        np.testing.assert_allclose(
            table6["SPI_s"],
            [0.98, 1.03, 1.03, 1.10, 1.13, 1.11, 0.97, 0.99],
            rtol=0,
            atol=1e-12,
        )

    def test_load_replaces_display_spi_with_exact_ev_over_pv(self) -> None:
        np.testing.assert_allclose(
            self.df["SPI_s"],
            self.df["EV_s"] / self.df["PV_s"],
            rtol=0,
            atol=1e-15,
        )
        self.assertAlmostEqual(float(self.df.loc[self.df["Sprint"] == 5, "SPI_s"].iloc[0]), 124 / 110)

    def test_continuous_metric_matches_independent_scalar_formula(self) -> None:
        metrics = compute_continuous_metrics(self.df)
        expected = []
        for row in self.df.itertuples(index=False):
            spi = row.EV_s / row.PV_s
            d_q = max(row.Delta_TD_s, 0) / (row.EV_s + EPSILON)
            d_s = max(row.Delta_SD_s, 0) / (row.EV_s + EPSILON)
            expected.append(spi * math.exp(-LAMBDA_Q * d_q) * math.exp(-LAMBDA_S * d_s))
        np.testing.assert_allclose(metrics["QSSPI_s"], expected, rtol=0, atol=1e-12)

    def test_table7_rounds_only_final_equation_results(self) -> None:
        table7 = build_table7_schedule_indicators(self.df)
        np.testing.assert_allclose(
            table7["QF_s"],
            [0.967, 0.959, 0.951, 0.922, 0.908, 0.899, 0.957, 0.973],
            rtol=0,
            atol=1e-12,
        )
        np.testing.assert_allclose(
            table7["SF_s"],
            [0.986, 0.980, 0.975, 0.944, 0.925, 0.907, 0.970, 0.983],
            rtol=0,
            atol=1e-12,
        )
        np.testing.assert_allclose(
            table7["QSSPI_s"],
            [0.935, 0.968, 0.953, 0.958, 0.946, 0.907, 0.904, 0.948],
            rtol=0,
            atol=1e-12,
        )

    def test_sprint5_worked_example(self) -> None:
        worked = sprint5_worked_example(self.df)
        self.assertAlmostEqual(round(worked["SPI_5_exact"], 3), 1.127)
        self.assertEqual(worked["d_q_5_display"], 0.176)
        self.assertEqual(worked["d_s_5_display"], 0.112)
        self.assertEqual(worked["QF_5_display"], 0.908)
        self.assertEqual(worked["SF_5_display"], 0.925)
        self.assertEqual(worked["QSSPI_5_display"], 0.946)
        self.assertEqual(worked["behind_plan_pct"], 5.4)

    def test_ablation_uses_unrounded_values(self) -> None:
        table9 = build_table9(self.df)
        panel_a = table9[table9["Panel"].str.startswith("Panel A")]
        np.testing.assert_allclose(panel_a["Index value"], [1.043, 0.981, 0.940], rtol=0, atol=1e-12)
        self.assertAlmostEqual(float(np.mean(compute_quality_only(self.df))), 0.981017700309805)

    def test_counterfactual_values_follow_disclosed_inputs(self) -> None:
        table = build_counterfactual_table(self.df)
        np.testing.assert_allclose(table["CQSSPI"], [0.946, 0.946, 0.984, 0.980, 0.992], rtol=0, atol=1e-12)
        np.testing.assert_allclose(table["Change_pp"], [0.0, 0.0, 3.8, 3.4, 4.6], rtol=0, atol=1e-12)
        for row in table.itertuples(index=False):
            independently_computed = cqsspi_from_assumptions(
                row.EV_cf,
                110.0,
                row.Delta_TD_cf,
                row.Delta_SD_cf,
            )
            self.assertAlmostEqual(row.CQSSPI_exact, independently_computed)

    def test_threshold_solver_returns_on_plan_value(self) -> None:
        threshold = solve_security_debt_for_on_plan(124.0, 110.0, 22.0)
        self.assertGreater(threshold, 0)
        self.assertAlmostEqual(cqsspi_from_assumptions(124.0, 110.0, 22.0, threshold), 1.0, places=10)

    def test_negative_debt_is_clamped_to_zero_penalty(self) -> None:
        modified = self.df.copy()
        modified.loc[modified["Sprint"] == 1, ["Delta_TD_s", "Delta_SD_s"]] = [-5.0, -3.0]
        row = compute_continuous_metrics(modified).loc[lambda frame: frame["Sprint"] == 1].iloc[0]
        self.assertEqual(row["QF_s"], 1.0)
        self.assertEqual(row["SF_s"], 1.0)
        self.assertAlmostEqual(row["QSSPI_s"], row["SPI_s"])

    def test_invalid_data_and_parameters_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            validate_metric_parameters(-0.1, LAMBDA_S, EPSILON)
        with self.assertRaises(ValueError):
            validate_metric_parameters(LAMBDA_Q, LAMBDA_S, 0.0)

        source = pd.read_csv(DEFAULT_DATA)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "invalid.csv"
            inconsistent = source.copy()
            inconsistent.loc[0, "SPI_s"] = 9.0
            inconsistent.to_csv(path, index=False)
            with self.assertRaises(ValueError):
                load_data(path)

            invalid_gating = source.copy()
            invalid_gating.loc[0, "G_s"] = 1.5
            invalid_gating.to_csv(path, index=False)
            with self.assertRaises(ValueError):
                load_data(path)

    def test_all_manuscript_figures_generate(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            paths = generate_all_figures(self.df, output, formats=("pdf",))
            expected = {
                "time_series.pdf",
                "scatter_ai_debt.pdf",
                "counterfactual_bar.pdf",
                "ablation_penalties.pdf",
                "ablation_causal.pdf",
                "scm_graph.pdf",
            }
            self.assertEqual({path.name for path in paths}, expected)
            for path in paths:
                self.assertGreater(path.stat().st_size, 1_000)


if __name__ == "__main__":
    unittest.main()
