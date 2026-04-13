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
