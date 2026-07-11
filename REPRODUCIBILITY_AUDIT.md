# CQSS-SPI Reproducibility Audit

Date: 2026-07-11

## Scope

This audit compared the BioArc data, manuscript equations and reported values, Python implementation, unit tests, scenario analysis, and quantitative figures.

## Material findings

1. **The earlier Table 7 implementation did not derive its displayed results from the equations.** `QF`, `SF`, and `QSSPI` were stored in fixed publication arrays and copied into output tables.
2. **The earlier continuous calculation used the two-decimal CSV display value of SPI.** The manuscript defines `SPI = EV/PV`, so using the rounded field changed several sprint-level results.
3. **Several earlier manuscript values were inconsistent with full-precision equation evaluation.** The largest affected QSSPI display values were Sprint 6 (`0.904` reported vs. `0.907` computed) and Sprint 7 (`0.899` vs. `0.904`).
4. **The earlier tests asserted manuscript constants rather than independently checking the equations.** They could pass even when a displayed result was not supported by the data and formulas.
5. **The earlier scenario inputs contained four-decimal security-debt values chosen to reproduce preselected three-decimal CQSSPI targets.** The revised analysis uses disclosed whole-unit assumptions and computes outputs without target matching.
6. **The repository did not generate the manuscript figures.** A vector-figure generation script and figure smoke test have been added.

## Corrective actions

- `EV/PV` is now the analytical SPI source of truth; the CSV SPI field is validation/display metadata only.
- Every density, factor, adjusted index, mean, ablation result, and worked-example value is computed at full precision.
- Rounding occurs only in publication-output builders.
- Counterfactual/sensitivity inputs and their evidentiary status are disclosed explicitly.
- Unit tests now compare the vectorized implementation with independent scalar calculations and test input validation, negative-debt clamping, scenario calculations, threshold solving, and figure generation.
- The manuscript abstract, Table 7, Sprint 5 worked example, scenario table, ablation table, captions, interpretation, and conclusion were updated to match the reproducible outputs.
- The exponential-penalty interpretation was corrected: it gives constant proportional decay per equal density increment, not an increasingly steep absolute penalty.

## Corrected numerical results

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

Eight-sprint means from unrounded values:

- Raw SPI: `1.043`
- Quality-only: `0.981`
- Full QSSPI: `0.940`
- Raw-to-full correction: `10.3` percentage points

Sprint 5 disclosed sensitivity scenarios:

| Scenario | EV_cf | Delta_TD_cf | Delta_SD_cf | CQSSPI | Change |
| --- | ---: | ---: | ---: | ---: | ---: |
| Observed | 124 | 22 | 14 | 0.946 | 0.0 pp |
| Stronger gating | 123 | 20 | 7 | 0.984 | +3.8 pp |
| Selective AI restriction | 121 | 18 | 6 | 0.980 | +3.4 pp |
| Lower compression | 119 | 15 | 3 | 0.992 | +4.6 pp |

## Verification performed

- `python -m unittest discover -s tests -v`: 11/11 tests passed.
- `python code/validate_reproduction.py`: all independent equation checks passed.
- All four analysis CLIs completed and exported their result tables.
- Six manuscript figures were generated in vector PDF; the five quantitative figures were also generated as EPS.
- Generated figures were rendered and visually checked for clipping, unreadable labels, or overlaps.
- The revised LaTeX source compiled successfully in a local compatibility harness, including the new wide scenario table and generated PDF figures.

## Remaining evidentiary limits

- The audit verifies internal reproducibility; it cannot independently verify that the normalized CSV values were derived from the claimed underlying BioArc operational records.
- `lambda_q = 0.55` and `lambda_s = 0.70` remain case parameters rather than empirically calibrated estimates.
- The Sprint 5 alternatives remain deterministic sensitivity scenarios, not identified counterfactual causal effects.
- A production compile using the original journal class and bibliography was not possible because those source assets were not included in the supplied files. The supplied reference PDF was inspected, and the revised source passed a syntax/layout compatibility compile.
