# C-QSSPI

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)

## Beyond Velocity: A Causal Quality- and Security-Sensitive Schedule Performance Index for AI-Assisted Software Projects

**Author:** Mohammad Tanhaei

This repository contains the reproducible material for the illustrative scenario and metric calculations reported in the paper:

> **Beyond Velocity: A Causal Quality- and Security-Sensitive Schedule Performance Index for AI-Assisted Software Projects**  
> Mohammad Tanhaei

## Short abstract

Conventional software schedule indicators reward visible progress more readily than hidden quality preservation. This problem becomes sharper in AI-assisted software development, where Generative AI may accelerate coding and testing while simultaneously altering the formation of technical debt, the distribution of verification effort, and the profile of security risk. This repository operationalizes the **CQSS-SPI** framework for the paper's illustrative eight-sprint scenario and reproduces the numerical results for the debt-sensitive schedule metric, the Sprint 5 worked example, and the ablation summary reported in the manuscript.

## Key features

- Reproducible implementation of the **QSSPI** and **CQSSPI** metric family
- Exact reproduction of the paper's **Table 5** using publication-rounded display values
- Exact reproduction of the **Sprint 5 worked example**
- Exact reproduction of the **Table 7 ablation summary**
- Clean CSV source data for the eight-sprint illustrative scenario
- A reproducible Python workflow using `pandas`, `numpy`, and `scipy`
- A compact manuscript source tree and supporting appendices
- No image assets or figure folders; the repository is focused on calculations, tables, and methodology

## Repository layout

```text
C-QSSPI/
├── README.md
├── LICENSE
├── CITATION.cff
├── .gitignore
├── manuscript/
│   ├── C-QSSPI.tex
│   ├── bibliography.bib
│   └── C-QSSPI.pdf
├── data/
│   ├── illustrative_sprints.csv
│   └── README_data.md
├── code/
│   ├── compute_qssspi.py
│   ├── ablation_study.py
│   ├── counterfactual_analysis.py
│   ├── requirements.txt
│   └── README_code.md
├── appendices/
│   ├── collection_sheet_template.xlsx
│   └── empirical_protocol.md
└── supplementary/
    └── governance_playbook.md
```

## Installation

Clone the repository and create a virtual environment:

```bash
git clone https://github.com/mtanhaei/C-QSSPI.git
cd C-QSSPI
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r code/requirements.txt
```

## Reproducing the paper calculations

### 1) Reproduce Table 5 and the Sprint 5 worked example

```bash
python code/compute_qssspi.py --data data/illustrative_sprints.csv
```

This script:

- validates the input data
- computes continuous debt-density terms
- reproduces the publication table values for **QF**, **SF**, and **QSSPI**
- prints the **Sprint 5 worked example** exactly as shown in the paper

### 2) Reproduce the ablation summary (Table 7)

```bash
python code/ablation_study.py --data data/illustrative_sprints.csv
```

This script reproduces:

- **Raw SPI average = 1.042**
- **Quality-only average = 0.980** with **-6.2 pp**
- **Full QSSPI average = 0.939** with **-10.3 pp**

### 3) Run the synthetic counterfactual sandbox

```bash
python code/counterfactual_analysis.py --data data/illustrative_sprints.csv
```

This script provides a scenario-based CQSSPI sandbox for Sprint 5. It is intentionally framed as a **synthetic policy-analysis tool**, not as a fitted empirical causal estimator.

## Usage examples

### Save Table 5 as CSV

```bash
python code/compute_qssspi.py \
  --data data/illustrative_sprints.csv \
  --csv-out results_table5.csv
```

### Save Table 7 as CSV

```bash
python code/ablation_study.py \
  --data data/illustrative_sprints.csv \
  --csv-out results_table7.csv
```

### Evaluate a custom Sprint 5 scenario

```bash
python code/counterfactual_analysis.py \
  --data data/illustrative_sprints.csv \
  --ev-cf 123 \
  --delta-td-cf 20 \
  --delta-sd-cf 6
```

## Notes on reproducibility

To match the paper exactly, the repository distinguishes between:

1. **continuous internal computations** from the CQSS-SPI equations, and
2. **publication-rounded display values** reported in the manuscript tables.

This is important because the manuscript tables are reproduced from publication display values to three decimals.

## Citation

If you use this repository, please cite both the paper and the repository metadata in `CITATION.cff`.

Example BibTeX entry:

```bibtex
@article{tanhaei2026cqsspi,
  author  = {Tanhaei, Mohammad},
  title   = {Beyond Velocity: A Causal Quality- and Security-Sensitive Schedule Performance Index for AI-Assisted Software Projects},
  journal = {Preprint},
  year    = {2026}
}
```

## License

This project is released under the **MIT License**. See [`LICENSE`](LICENSE).

## Contact

For academic or reproducibility questions related to this repository, please use the repository issue tracker or contact the author listed in the manuscript.
