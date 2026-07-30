# Data README

## Primary file

- `bioarc_retrospective_sprints.csv`

## Provenance

This CSV contains the anonymized eight-sprint BioArc retrospective case reported in the manuscript *Beyond Velocity: A Causal Quality- and Security-Sensitive Schedule Performance Index for AI-Assisted Software Projects*.

The values are normalized project-control and quality/security remediation records. They preserve the relationships needed for reproduction while avoiding disclosure of confidential internal project quantities.

## Relation to the manuscript

- The sprint records reproduce the manuscript's BioArc retrospective case table.
- The corrected values are computed directly from these records and reproduce the corrected raw/corrected schedule-indicator table.
- The dataset supports the Sprint 5 worked example and ablation summary.

## Columns

- `Sprint`: sprint identifier
- `PV_s`: planned value for sprint `s`
- `EV_s`: earned value for sprint `s`
- `SPI_s`: two-decimal display value of the schedule performance index for sprint `s`
- `Delta_TD_s`: net technical-debt accumulation in sprint `s`
- `Delta_SD_s`: net security-debt accumulation in sprint `s`
- `A_s`: AI assistance intensity
- `C_s`: schedule compression intensity
- `G_s`: security-gating intensity
- `Notes`: qualitative sprint context used in the manuscript table

## Notes on numeric conventions

- `SPI_s` is stored as displayed in the manuscript input table, not as a full-precision recomputation of `EV_s / PV_s`.
- The loader validates that the supplied value is consistent with `EV_s / PV_s` at two-decimal precision and then replaces it in memory with exact `EV_s / PV_s`.
- All metric factors are calculated at full precision; rounding occurs only in publication-output builders.
- The former `illustrative_sprints.csv` was a byte-identical duplicate of this file and has been removed. Use `bioarc_retrospective_sprints.csv`.

## Scope limitation

The BioArc dataset is a single-system retrospective case. It should not be interpreted as a controlled experiment, a population-level causal estimate, or a multi-domain validation.
