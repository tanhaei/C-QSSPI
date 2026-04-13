# Data README

## File

- `illustrative_sprints.csv`

## Provenance

This CSV contains the exact eight-sprint illustrative scenario reported in **Table 4** of the paper *Beyond Velocity: A Causal Quality- and Security-Sensitive Schedule Performance Index for AI-Assisted Software Projects*.

## Columns

- `Sprint`: sprint identifier
- `PV_s`: planned value for sprint `s`
- `EV_s`: earned value for sprint `s`
- `SPI_s`: published schedule performance index for sprint `s`
- `Delta_TD_s`: net technical-debt accumulation in sprint `s`
- `Delta_SD_s`: net security-debt accumulation in sprint `s`
- `A_s`: AI assistance intensity
- `C_s`: schedule compression intensity
- `G_s`: security-gating intensity

## Notes on numeric conventions

- `SPI_s` is stored exactly as displayed in the paper table, not as a full-precision recomputation of `EV_s / PV_s`.
- The code validates that the provided `SPI_s` values are consistent with `EV_s / PV_s` within display tolerance.
- Publication tables are reproduced using the manuscript's display conventions to match the paper exactly.

## Scenario meaning

The dataset is illustrative and synthetic. It is included to:

1. demonstrate the mechanics of the CQSS-SPI metric,
2. reproduce the paper's numerical tables,
3. support transparent and repeatable scenario analysis.

It is **not** a field dataset and must not be interpreted as empirical evidence from a completed industrial study.
