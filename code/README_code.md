# Code README

## Overview

This directory contains the executable Python scripts required to reproduce the numerical content of the illustrative CQSS-SPI scenario.

## Scripts

### `compute_qssspi.py`

Reproduces:

- the publication-style **Table 5**
- the **Sprint 5 worked example**
- a compact descriptive summary of the reproduced QSSPI values

Run:

```bash
python code/compute_qssspi.py --data data/illustrative_sprints.csv
```

Optional CSV export:

```bash
python code/compute_qssspi.py \
  --data data/illustrative_sprints.csv \
  --csv-out results_table5.csv
```

---

### `ablation_study.py`

Reproduces:

- the publication-style **Table 7** ablation summary
- raw, quality-only, and full-QSSPI average values
- the synthetic causal illustration rows used in the conceptual ablation summary

Run:

```bash
python code/ablation_study.py --data data/illustrative_sprints.csv
```

Optional CSV export:

```bash
python code/ablation_study.py \
  --data data/illustrative_sprints.csv \
  --csv-out results_table7.csv
```

---

### `counterfactual_analysis.py`

Provides:

- a synthetic Sprint 5 counterfactual sandbox
- internally consistent scenario calculations
- a threshold analysis for the security-debt level required to return to `CQSSPI = 1.0`

Run:

```bash
python code/counterfactual_analysis.py --data data/illustrative_sprints.csv
```

Custom scenario:

```bash
python code/counterfactual_analysis.py \
  --data data/illustrative_sprints.csv \
  --ev-cf 123 \
  --delta-td-cf 20 \
  --delta-sd-cf 6
```

## Design note: publication-rounded vs continuous values

To reproduce the paper faithfully, the repository distinguishes between:

1. **continuous values** computed directly from the equations, and
2. **publication-rounded values** shown in the manuscript tables.

This distinction matters because the displayed paper tables are reported to three decimals and are reproduced exactly here.

## Dependencies

The codebase uses:

- `pandas`
- `numpy`
- `scipy`

Install all requirements with:

```bash
pip install -r code/requirements.txt
```

## Reproducibility target values

The repository is configured to reproduce the following values exactly:

### Table 5

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

### Table 7 averages

- Raw SPI = `1.042`
- Quality-only = `0.980`
- Full QSSPI = `0.939`
- Deltas = `-6.2 pp` and `-10.3 pp`
