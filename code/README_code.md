# Code guide

## Numerical convention

The analytical source of truth is the equation set in the manuscript:

```text
SPI_s   = EV_s / PV_s
d_q_s   = max(Delta_TD_s, 0) / (EV_s + epsilon)
d_s_s   = max(Delta_SD_s, 0) / (EV_s + epsilon)
QF_s    = exp(-lambda_q * d_q_s)
SF_s    = exp(-lambda_s * d_s_s)
QSSPI_s = SPI_s * QF_s * SF_s
```

Inputs and intermediate values remain at full floating-point precision. Rounding to three decimals occurs only when publication tables are constructed. The `SPI_s` field in the source CSV is checked for consistency but is replaced in memory by exact `EV_s / PV_s` before any metric is computed.

## Scripts

### `compute_qssspi.py`

Validates the BioArc data and reproduces Tables 6 and 7, the Sprint 5 worked example, and descriptive statistics.

```bash
python code/compute_qssspi.py \
  --data data/bioarc_retrospective_sprints.csv \
  --table6-csv-out results/table6_sprint_case.csv \
  --table7-csv-out results/table7_schedule_indicators.csv
```

The `--lambda-q`, `--lambda-s`, and `--epsilon` options support sensitivity checks. The earlier `--csv-out` option remains an alias for the Table 7 output.

### `counterfactual_analysis.py`

Computes Sprint 5 intervention-sensitivity values from disclosed scenario inputs. The defaults use whole normalized-effort units and are not fitted causal estimates.

```bash
python code/counterfactual_analysis.py \
  --data data/bioarc_retrospective_sprints.csv \
  --csv-out results/sprint5_scenarios.csv
```

A custom scenario requires all three inputs:

```bash
python code/counterfactual_analysis.py \
  --ev-cf 123 \
  --delta-td-cf 20 \
  --delta-sd-cf 7
```

### `ablation_study.py`

Computes the raw, quality-only, and full-QSSPI averages from unrounded sprint values and appends the disclosed Sprint 5 scenarios.

```bash
python code/ablation_study.py \
  --data data/bioarc_retrospective_sprints.csv \
  --csv-out results/table9_ablation.csv
```

### `generate_figures.py`

Generates `time_series`, `scatter_ai_debt`, `counterfactual_bar`, `ablation_penalties`, `ablation_causal`, and `scm_graph` in publication-ready vector formats.

```bash
python code/generate_figures.py --output-dir figures
```

### `validate_reproduction.py`

Checks the vectorized implementation against independent scalar calculations, verifies the corrected tables and scenario inputs, and checks the threshold solver.

```bash
python code/validate_reproduction.py
```

## Corrected display targets

- Table 7 QSSPI: `0.935`, `0.968`, `0.953`, `0.958`, `0.946`, `0.907`, `0.904`, `0.948`
- Sprint 5: `SPI = 1.127`, `d_q = 0.176`, `d_s = 0.112`, `QF = 0.908`, `SF = 0.925`, `QSSPI = 0.946`
- Eight-sprint averages: raw `1.043`, quality-only `0.981`, full `0.940`
- Sprint 5 scenario CQSSPI: observed `0.946`, stronger gating `0.984`, selective AI restriction `0.980`, lower compression `0.992`

## Tests

The standard-library test runner is sufficient; `pytest` is not required.

```bash
python -m unittest discover -s tests -v
```
