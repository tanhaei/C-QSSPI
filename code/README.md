# Code README

## Overview

This directory contains the executable Python scripts required to reproduce the numerical content of the current CQSS-SPI manuscript. The scripts now follow the manuscript's revised framing: the data are an anonymized BioArc eight-sprint retrospective case, not a hypothetical synthetic dataset.

## Scripts

### `compute_qssspi.py`

Reproduces:

- the BioArc sprint case table reported as Table 6,
- the raw/corrected schedule indicator table reported as Table 7,
- the Sprint 5 worked example,
- a compact descriptive summary of the reproduced QSSPI values.

Run:

```bash
python code/compute_qssspi.py --data data/bioarc_retrospective_sprints.csv
```

Optional CSV export:

```bash
python code/compute_qssspi.py \
  --data data/bioarc_retrospective_sprints.csv \
  --table6-csv-out results_table6.csv \
  --table7-csv-out results_table7.csv
```

The older `--csv-out` option remains available as a backward-compatible alias for saving Table 7.

---

### `ablation_study.py`

Reproduces:

- the component-wise ablation summary reported as Table 9,
- raw, quality-only, and full-QSSPI average values,
- the BioArc Sprint 5 counterfactual values reported in the manuscript.

Run:

```bash
python code/ablation_study.py --data data/bioarc_retrospective_sprints.csv
```

Optional CSV export:

```bash
python code/ablation_study.py \
  --data data/bioarc_retrospective_sprints.csv \
  --csv-out results_table9.csv
```

---

### `counterfactual_analysis.py`

Provides:

- the BioArc Sprint 5 counterfactual demonstration,
- the Figure 6/Table 9 values: `0.947`, `0.947`, `0.983`, `0.979`, and `0.993`,
- a threshold analysis for the security-debt level required to return to `CQSSPI = 1.0`,
- optional user-defined counterfactual assumptions.

Run:

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

---

### `validate_reproduction.py`

Runs deterministic checks against the manuscript values.

```bash
python code/validate_reproduction.py
```

## Design note: publication-rounded vs continuous values

To reproduce the paper faithfully, the repository distinguishes between:

1. continuous values computed directly from the equations, and
2. publication-rounded values shown in the manuscript tables.

This distinction matters because the displayed paper tables are reported to three decimals and are reproduced exactly here.

## Dependencies

The codebase uses:

- `pandas`
- `numpy`
- `scipy`
- `openpyxl` for the supplemental Excel collection sheet

Install all requirements with:

```bash
pip install -r code/requirements.txt
```

## Reproducibility target values

### Table 7 QSSPI values

- Sprint 1: `0.934`
- Sprint 2: `0.968`
- Sprint 3: `0.954`
- Sprint 4: `0.957`
- Sprint 5: `0.947`
- Sprint 6: `0.904`
- Sprint 7: `0.899`
- Sprint 8: `0.948`

### Sprint 5 worked example

- `SPI_5 = 1.127`
- `d_q_5 = 0.176`
- `d_s_5 = 0.112`
- `QF_5 = 0.907`
- `SF_5 = 0.924`
- `QSSPI_5 = 0.947`

### Table 9 averages and counterfactual values

- Raw SPI = `1.042`
- Quality-only = `0.980`
- Full QSSPI = `0.939`
- Counterfactual values = `0.983`, `0.979`, and `0.993`
