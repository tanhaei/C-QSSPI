from __future__ import annotations

from pathlib import Path
import sys
import unittest

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "code"))

from compute_qssspi import (  # noqa: E402
    DEFAULT_DATA,
    PUBLISHED_QSSPI,
    build_table6_sprint_case,
    build_table7_schedule_indicators,
    load_data,
    sprint5_worked_example,
)
from ablation_study import build_table9, compute_quality_only  # noqa: E402
from counterfactual_analysis import build_counterfactual_table  # noqa: E402


class TestManuscriptReproduction(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.df = load_data(DEFAULT_DATA)

    def test_table6_shape_and_notes(self) -> None:
        table6 = build_table6_sprint_case(self.df)
        self.assertEqual(len(table6), 8)
        self.assertIn("Notes", table6.columns)

    def test_table7_qsspi_values(self) -> None:
        table7 = build_table7_schedule_indicators(self.df)
        np.testing.assert_allclose(
            table7["QSSPI_s"].to_numpy(),
            np.array([0.934, 0.968, 0.954, 0.957, 0.947, 0.904, 0.899, 0.948]),
            rtol=0,
            atol=1e-12,
        )

    def test_sprint5_worked_example(self) -> None:
        worked = sprint5_worked_example(self.df)
        self.assertAlmostEqual(round(worked["SPI_5_exact"], 3), 1.127)
        self.assertAlmostEqual(worked["d_q_5"], 0.176)
        self.assertAlmostEqual(worked["d_s_5"], 0.112)
        self.assertAlmostEqual(worked["QSSPI_5_display"], 0.947)

    def test_table9_values(self) -> None:
        table9 = build_table9(self.df)
        self.assertAlmostEqual(float(np.round(self.df["SPI_s"].mean(), 3)), 1.042)
        self.assertAlmostEqual(float(np.round(compute_quality_only(self.df).mean(), 3)), 0.980)
        self.assertAlmostEqual(float(np.round(PUBLISHED_QSSPI.mean(), 3)), 0.939)
        for value in [0.983, 0.979, 0.993]:
            self.assertIn(value, set(table9["Index value"].round(3)))

    def test_counterfactual_values(self) -> None:
        cf = build_counterfactual_table(110.0)
        np.testing.assert_allclose(
            cf["CQSSPI"].to_numpy(),
            np.array([0.947, 0.947, 0.983, 0.979, 0.993]),
            rtol=0,
            atol=1e-12,
        )


if __name__ == "__main__":
    unittest.main()
