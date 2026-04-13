# Empirical Protocol for Future CQSS-SPI Validation

## Purpose

This protocol documents how the illustrative CQSS-SPI framework can be extended into a future empirical field study. The present repository remains scenario-driven and reproducibility-focused; this document specifies how a later longitudinal validation can be designed.

## Research questions

1. How can a conventional SPI-style schedule indicator be extended to account explicitly for both technical debt and security debt in AI-assisted software projects?
2. How can causal structure be incorporated so that intervention and counterfactual schedule questions become answerable?
3. How does the corrected metric behave relative to raw SPI and a quality-only adjusted variant?
4. What practical measurement pipeline is required for deployment in real software organizations?

## Unit of analysis

### Preferred unit
- sprint or release increment

### Nested units
- module
- repository
- team

## Core variables

### Schedule variables
- `PV_s`: planned value
- `EV_s`: earned value
- `SPI_s = EV_s / PV_s`

### Debt variables
- `Delta_TD_s`: net technical-debt accumulation
- `Delta_SD_s`: net security-debt accumulation

### Governance variables
- `A_s`: AI assistance intensity
- `C_s`: schedule compression intensity
- `G_s`: security-gating intensity
- `R_s`: review intensity
- `T_s`: testing intensity
- `M_s`: module criticality
- `X_s`: experience mix

## Recommended data sources

- sprint planning tool or issue tracker
- release board
- SonarQube or equivalent static analysis system
- SAST pipeline such as Bandit or Semgrep
- code review metadata
- CI/CD policy configuration
- architecture and module-risk catalog
- lightweight sprint survey instruments

## Measurement pipeline

### Step 1: ingest schedule data
Collect `PV_s`, `EV_s`, sprint dates, and accepted scope.

### Step 2: ingest technical-debt data
Collect newly introduced and repaid remediation effort from static analysis and code-quality tools.

### Step 3: ingest security-debt data
Collect weighted remediation effort for newly introduced and repaid security findings.

### Step 4: compute descriptive corrections
Use repository code to compute:

- `d_s^q`
- `d_s^s`
- `QF_s`
- `SF_s`
- `QSSPI_s`

### Step 5: fit the causal layer
Estimate the structural relationships linking:

- AI assistance
- schedule compression
- review intensity
- security gating
- earned value
- debt accumulation

### Step 6: evaluate downstream outcomes
Compare the corrected indicators against:

- carry-over work
- next-sprint throughput loss
- rework effort
- post-release defects
- emergency patch frequency

## Hypotheses

- **H1**: AI assistance intensity is positively associated with same-sprint earned value.
- **H2**: Under weak review and weak security gating, higher AI assistance intensity is associated with higher net security debt.
- **H3**: CQSS-SPI predicts downstream schedule disruption better than raw SPI.
- **H4**: Stronger security gating can improve medium-horizon schedule realism even when immediate visible throughput declines.

## Statistical strategy

### Descriptive layer
- compare trajectories of `SPI_s`, quality-only schedule correction, and full `QSSPI_s`

### Hierarchical estimation
- use mixed-effects or Bayesian multilevel models when repeated measures are available

### Causal layer
- specify an SCM aligned with engineering process knowledge
- justify identification assumptions explicitly
- separate empirical estimates from scenario-based illustrations

## Threats to validity

### Construct validity
- static-analysis remediation estimates are proxies, not direct future effort
- AI usage intensity may be measured imperfectly

### Internal validity
- self-selection in AI use may confound estimated effects
- team experience and module criticality may influence both debt and output

### External validity
- hospital-style software settings may not generalize directly to consumer products or embedded systems

## Ethical and governance considerations

- do not treat the metric as an employee surveillance mechanism
- use the metric to improve realism in project control, not to assign blame
- preserve transparency in severity weighting, debt measurement, and release gating rules

## Expected artifacts for a future empirical release

- cleaned longitudinal dataset
- model estimation notebook or script
- uncertainty-aware tables
- repository-derived counterfactual summaries
- protocol deviations and data-quality notes
