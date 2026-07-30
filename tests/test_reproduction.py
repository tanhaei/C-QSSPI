from __future__ import annotations

import math
from pathlib import Path
import sys
import tempfile
import unittest

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
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
    ABLATED_SCENARIO,
    EXPECTED_SPRINT5_RECORD,
    build_counterfactual_table,
    cqsspi_from_assumptions,
    solve_security_debt_for_on_plan,
    sprint5_scenarios,
)
from generate_figures import (  # noqa: E402
    SCM_EDGES,
    build_ablation_causal,
    build_ablation_penalties,
    build_counterfactual,
    build_scatter,
    build_time_series,
    generate_all_figures,
    parse_mermaid_scm,
)


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

    def test_epsilon_is_reported_not_hard_coded(self) -> None:
        default = sprint5_worked_example(self.df)
        widened = sprint5_worked_example(self.df, epsilon=5.0)
        self.assertEqual(default["epsilon"], EPSILON)
        self.assertEqual(widened["epsilon"], 5.0)
        self.assertAlmostEqual(widened["d_q_5_exact"], 22 / (124 + 5.0))

    def test_scenario_reductions_are_relative_to_the_observed_record(self) -> None:
        row = self.df.loc[self.df["Sprint"] == 5].iloc[0]
        for column, expected in EXPECTED_SPRINT5_RECORD.items():
            self.assertEqual(float(row[column]), expected)
        by_name = {s.name: s for s in sprint5_scenarios(row)}
        self.assertEqual(by_name["Stronger gating (scenario)"].ev_cf, 123.0)
        self.assertEqual(by_name["Selective AI restriction (scenario)"].delta_td_cf, 18.0)
        self.assertEqual(by_name["Lower compression (scenario)"].delta_sd_cf, 3.0)

    def test_scenario_guard_rejects_mismatched_sprint5_record(self) -> None:
        modified = self.df.copy()
        modified.loc[modified["Sprint"] == 5, "EV_s"] = 130.0
        with self.assertRaises(ValueError):
            build_counterfactual_table(modified)


class TestFiguresMatchPublishedTables(unittest.TestCase):
    """Guard against figures drifting away from the tables they illustrate.

    These tests read the values back off the Matplotlib artists, so a figure
    built from stale or rounded inputs fails here instead of reaching the PDF.
    """

    TABLE7_QSSPI = [0.935, 0.968, 0.953, 0.958, 0.946, 0.907, 0.904, 0.948]
    TABLE8_CQSSPI = [0.946, 0.984, 0.980, 0.992]

    @classmethod
    def setUpClass(cls) -> None:
        cls.df = load_data(DEFAULT_DATA)
        cls.metrics = compute_continuous_metrics(cls.df)
        cls.scenarios = build_counterfactual_table(cls.df)

    @staticmethod
    def _line_data(fig, label_fragment: str) -> np.ndarray:
        ax = fig.axes[0]
        for line in ax.lines:
            if label_fragment.lower() in str(line.get_label()).lower():
                return np.asarray(line.get_ydata(), dtype=float)
        raise AssertionError(f"No plotted line matching {label_fragment!r}")

    @staticmethod
    def _bar_heights(fig) -> np.ndarray:
        ax = fig.axes[0]
        return np.asarray([p.get_height() for p in ax.patches], dtype=float)

    def test_time_series_draws_exact_ev_over_pv_and_table7(self) -> None:
        fig = build_time_series(self.metrics)
        try:
            spi = self._line_data(fig, "SPI_s")
            qsspi = self._line_data(fig, "QSSPI_s")
            # Must be the exact ratio, never the two-decimal CSV display field.
            np.testing.assert_allclose(spi, self.df["EV_s"] / self.df["PV_s"], rtol=0, atol=1e-12)
            np.testing.assert_allclose(np.round(qsspi, 3), self.TABLE7_QSSPI, rtol=0, atol=1e-12)
        finally:
            plt.close(fig)

    def test_ablation_penalties_draws_all_three_table7_layers(self) -> None:
        fig = build_ablation_penalties(self.metrics)
        try:
            np.testing.assert_allclose(
                self._line_data(fig, "Raw SPI"),
                self.df["EV_s"] / self.df["PV_s"], rtol=0, atol=1e-12,
            )
            np.testing.assert_allclose(
                self._line_data(fig, "Quality-only"),
                self.metrics["QSSPI_q_s"], rtol=0, atol=1e-12,
            )
            np.testing.assert_allclose(
                np.round(self._line_data(fig, "Full QSSPI"), 3),
                self.TABLE7_QSSPI, rtol=0, atol=1e-12,
            )
        finally:
            plt.close(fig)

    def test_scatter_draws_security_debt_density(self) -> None:
        fig = build_scatter(self.metrics)
        try:
            drawn = np.sort(
                np.concatenate([c.get_offsets()[:, 1] for c in fig.axes[0].collections])
            )
            np.testing.assert_allclose(
                drawn, np.sort(self.metrics["d_s_s"].to_numpy()), rtol=0, atol=1e-12
            )
        finally:
            plt.close(fig)

    def test_counterfactual_bars_match_table8(self) -> None:
        fig = build_counterfactual(self.scenarios)
        try:
            np.testing.assert_allclose(
                np.round(self._bar_heights(fig), 3), self.TABLE8_CQSSPI, rtol=0, atol=1e-12
            )
        finally:
            plt.close(fig)

    def test_causal_ablation_bars_match_table9_panel_b(self) -> None:
        fig = build_ablation_causal(self.scenarios)
        try:
            heights = np.round(self._bar_heights(fig), 3)
            self.assertEqual(len(heights), 5)
            # The ablated bar is a null intervention: identical to the observed bar.
            self.assertEqual(heights[0], heights[1])
            np.testing.assert_allclose(
                np.delete(heights, 1), self.TABLE8_CQSSPI, rtol=0, atol=1e-12
            )
        finally:
            plt.close(fig)

    def test_scm_edges_match_the_manuscript_equations(self) -> None:
        """Equations 23-25 plus the QSSPI parents define the graph exactly."""
        self.assertEqual(set(SCM_EDGES), self._equation_edges())
        self.assertIn(("T", "EV"), set(SCM_EDGES))

    @staticmethod
    def _equation_edges() -> set:
        expected = set()
        for parent in ("A", "C", "R", "X", "M"):          # Equation 23
            expected.add((parent, "TD"))
        for parent in ("A", "C", "G", "R", "X", "M"):     # Equation 24
            expected.add((parent, "SD"))
        for parent in ("A", "C", "X", "T", "M"):          # Equation 25
            expected.add((parent, "EV"))
        for parent in ("TD", "SD", "EV", "PV"):           # Equation 22
            expected.add((parent, "Q"))
        return expected

    def test_mermaid_figure1_matches_the_equations(self) -> None:
        """The Mermaid source of Figure 1 must encode the same causal graph."""
        edges, _ = parse_mermaid_scm()
        normalised = {(s, "Q" if d == "QSSPI" else d) for s, d in edges}
        self.assertEqual(normalised, self._equation_edges())
        self.assertEqual(len(edges), len(set(edges)), "duplicate edge in the Mermaid source")

    def test_mermaid_link_styles_cover_every_edge_once(self) -> None:
        """Adding an edge silently shifts linkStyle indices, so pin the mapping."""
        edges, link_styles = parse_mermaid_scm()
        styled = [index for indices in link_styles.values() for index in indices]
        self.assertEqual(sorted(styled), list(range(len(edges))))
        self.assertEqual(len(styled), len(set(styled)), "an edge is styled twice")


if __name__ == "__main__":
    unittest.main()
