# C-QSSPI

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)

## Beyond Velocity: A Causal Quality- and Security-Sensitive Schedule Performance Index for AI-Assisted Software Projects

**Author:** Mohammad Tanhaei

This repository contains reproducible Python material for the current manuscript:

> **Beyond Velocity: A Causal Quality- and Security-Sensitive Schedule Performance Index for AI-Assisted Software Projects**  
> Mohammad Tanhaei

## Repository scope

The manuscript evaluates CQSS-SPI through an anonymized eight-sprint retrospective case from the BioArc hospital information system. The case data in this repository are normalized project-control and quality/security remediation records. They are intended to reproduce the manuscript's numerical tables and the Sprint 5 worked example.

The repository does **not** claim a controlled experiment, a fitted population-level causal model, or a multi-domain validation. Counterfactual values are presented as a BioArc single-case demonstration of the SCM logic used in the paper.

## Key features

- Reproduces the BioArc sprint case table used in the manuscript.
- Reproduces the raw and corrected schedule-indicator table: `SPI_s`, `QF_s`, `SF_s`, and `QSSPI_s`.
- Reproduces the Sprint 5 worked example.
- Reproduces the component-wise ablation summary reported as Table 9 in the manuscript.
- Reproduces the Sprint 5 counterfactual values used for Figure 6/Table 9 checks.
- Provides a data-collection template and governance playbook for future field validation.

## Repository layout

```text
C-QSSPI/
├── README.md
├── LICENSE
├── CITATION.cff
├── data/
│   ├── bioarc_retrospective_sprints.csv
│   ├── illustrative_sprints.csv              # compatibility copy of the BioArc case file
│   └── README_data.md
├── code/
│   ├── compute_qssspi.py
│   ├── ablation_study.py
│   ├── counterfactual_analysis.py
│   ├── validate_reproduction.py
│   ├── requirements.txt
│   └── README_code.md
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
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r code/requirements.txt
```

## Reproducing the manuscript calculations

### 1) Reproduce Table 6, Table 7, and the Sprint 5 worked example

```bash
python code/compute_qssspi.py --data data/bioarc_retrospective_sprints.csv
```

This script:

- validates the BioArc sprint data,
- checks that the displayed `SPI_s` values are consistent with `EV_s / PV_s`,
- reproduces the BioArc sprint table,
- reproduces the raw/corrected schedule-indicator table,
- prints the Sprint 5 worked example.

Optional exports:

```bash
python code/compute_qssspi.py \
  --data data/bioarc_retrospective_sprints.csv \
  --table6-csv-out results_table6.csv \
  --table7-csv-out results_table7.csv
```

### 2) Reproduce the component-wise ablation summary, Table 9

```bash
python code/ablation_study.py --data data/bioarc_retrospective_sprints.csv
```

Target values:

- Raw SPI average = `1.042`
- Quality-only average = `0.980`
- Full QSSPI average = `0.939`
- Sprint 5 counterfactual values = `0.983`, `0.979`, and `0.993`

### 3) Run the BioArc Sprint 5 counterfactual demonstration

```bash
python code/counterfactual_analysis.py --data data/bioarc_retrospective_sprints.csv
```

Custom scenario:

```bash
python code/counterfactual_analysis.py \
  --data data/bioarc_retrospective_sprints.csv \
  --ev-cf 123 \
  --delta-td-cf 20 \
  --delta-sd-cf 7.1106
```

### 4) Run all reproduction checks

```bash
python code/validate_reproduction.py
python -m unittest discover -s tests
```

## Notes on reproducibility

The manuscript reports publication-rounded display values to three decimals. The code therefore distinguishes between:

1. continuous internal calculations from the CQSS-SPI equations, and
2. publication-rounded values used to reproduce the manuscript tables exactly.

## Citation

If you use this repository, please cite the manuscript and repository metadata in `CITATION.cff`.

## License

This project is released under the MIT License. See `LICENSE`.
