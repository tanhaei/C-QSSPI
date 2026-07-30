# C-QSSPI

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)
![CI](https://github.com/tanhaei/C-QSSPI/actions/workflows/ci.yml/badge.svg)

Reproducible material for:

> **Beyond Velocity: A Causal Quality- and Security-Sensitive Schedule Performance Index for AI-Assisted Software Projects**  
> Mohammad Tanhaei

## Scope and evidentiary status

The repository analyzes an anonymized eight-sprint retrospective case from the BioArc hospital information system. The normalized sprint records are used to demonstrate the mechanics and interpretation of CQSS-SPI.

This is a single-system retrospective case. It is not a controlled experiment, a fitted population-level causal model, or multi-domain validation. The Sprint 5 alternatives are disclosed deterministic sensitivity assumptions; they are not identified causal-effect estimates.

## Reproducibility correction

All reported factors and indices are calculated directly from the manuscript equations. The two-decimal `SPI_s` values stored in the CSV are validated as display fields, but analysis uses full-precision `EV_s / PV_s`. Likewise, `QF_s`, `SF_s`, and `QSSPI_s` are rounded only after the complete equation has been evaluated. No publication-result arrays are used as computational inputs.

A second audit round extended this to the figures. Every figure is now built from the same equation-derived arrays as the tables, the test suite reads the plotted values back off the Matplotlib artists and compares them with Tables 7-9, and vector exports are byte-reproducible. See `REPRODUCIBILITY_AUDIT.md` and `MANUSCRIPT_CORRECTIONS.md`.

## Repository layout

```text
C-QSSPI/
├── README.md
├── REPRODUCIBILITY_AUDIT.md
├── MANUSCRIPT_CORRECTIONS.md
├── LICENSE
├── CITATION.cff
├── .github/workflows/ci.yml
├── data/
│   ├── bioarc_retrospective_sprints.csv
│   └── README_data.md
├── code/
│   ├── compute_qssspi.py
│   ├── ablation_study.py
│   ├── counterfactual_analysis.py
│   ├── generate_figures.py
│   ├── validate_reproduction.py
│   ├── requirements.txt
│   └── README_code.md
├── figures/
├── results/
├── tests/
│   └── test_reproduction.py
├── appendices/
│   ├── collection_sheet_template.xlsx
│   └── empirical_protocol.md
└── supplementary/
    └── governance_playbook.md
```

## Installation

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r code/requirements.txt
```

## Reproduce the manuscript

Rebuild every table in `results/`:

```bash
python code/compute_qssspi.py \
  --table6-csv-out results/table6_sprint_case.csv \
  --table7-csv-out results/table7_schedule_indicators.csv
python code/ablation_study.py --csv-out results/table9_ablation.csv
python code/counterfactual_analysis.py --csv-out results/sprint5_scenarios.csv
```

Rebuild every manuscript figure:

```bash
python code/generate_figures.py --output-dir figures
```

`generate_figures.py` pins `SOURCE_DATE_EPOCH`, so a rebuild is byte-identical to the committed vector files and CI can diff them.

Run the independent equation checks and the unit-test suite:

```bash
python code/validate_reproduction.py
python -m unittest discover -s tests -v
```

## Corrected reference outputs

Using `lambda_q = 0.55`, `lambda_s = 0.70`, and `epsilon = 1`:

| Sprint | QF | SF | QSSPI |
| ---: | ---: | ---: | ---: |
| 1 | 0.967 | 0.986 | 0.935 |
| 2 | 0.959 | 0.980 | 0.968 |
| 3 | 0.951 | 0.975 | 0.953 |
| 4 | 0.922 | 0.944 | 0.958 |
| 5 | 0.908 | 0.925 | 0.946 |
| 6 | 0.899 | 0.907 | 0.907 |
| 7 | 0.957 | 0.970 | 0.904 |
| 8 | 0.973 | 0.983 | 0.948 |

Eight-sprint averages are `1.043` for raw SPI, `0.981` for the quality-only index, and `0.940` for full QSSPI.

The disclosed Sprint 5 sensitivity inputs and outputs are:

| Scenario | EV_cf | Delta_TD_cf | Delta_SD_cf | CQSSPI | Change vs. observed |
| --- | ---: | ---: | ---: | ---: | ---: |
| Observed | 124 | 22 | 14 | 0.946 | 0.0 pp |
| Stronger gating | 123 | 20 | 7 | 0.984 | +3.8 pp |
| Selective AI restriction | 121 | 18 | 6 | 0.980 | +3.4 pp |
| Lower compression | 119 | 15 | 3 | 0.992 | +4.6 pp |

## Figure provenance

`figures/` contains the six figures used in the manuscript, all rebuilt from the corrected equations:

| File | Manuscript figure |
| --- | --- |
| `scm_graph.mmd` | Figure 1 source, structural causal model (Mermaid) |
| `scm_graph` | Figure 1, dependency-free Matplotlib rendering |
| `time_series` | Figure 2, raw SPI against QSSPI |
| `scatter_ai_debt` | Figure 3, AI intensity against security-debt density |
| `counterfactual_bar` | Figure 4, Sprint 5 sensitivity scenarios |
| `ablation_penalties` | Figure 5, penalty-component ablation |
| `ablation_causal` | Figure 6, causal-layer ablation |

## Citation and license

Citation metadata are provided in `CITATION.cff`. The code is released under the MIT License.
