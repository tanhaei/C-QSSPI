# CQSS-SPI Reproducibility Audit

Round 1: 2026-07-11 | Round 2: 2026-07-31

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


---

# Round 2 audit (2026-07-31)

## Scope

Round 1 corrected the code, the tables, and the reported text values. Round 2
re-verified those values with an independent implementation, and extended the
audit to the figures, the structural causal model, and repository hygiene.

## Confirmed correct

Every numeric claim in the manuscript text and in Tables 6-9 was recomputed from
scratch without importing repository code and matched digit for digit: all 32
values in Table 7, the Sprint 5 worked example, the Sprint 6 correction of 20.6
percentage points, Table 8, Table 9 Panels A and B, and the abstract.

## Round 2 findings

1. **Figures 2, 4, 5 and 6 in the submitted PDF are pre-correction artefacts.**
   Vector extraction from the submitted file shows Figure 2 and Figure 5 plot the
   two-decimal display SPI, giving 0.904 and 0.899 at Sprints 6 and 7 where the
   corrected values are 0.907 and 0.904, and Figures 4 and 6 print bar labels
   that contradict Table 8 on the same page. Figure 3 is numerically correct.
2. **`figures/counterfactual_bar.pdf` was committed as a zero-byte file.**
3. **The figure script did not reproduce the published figures.** It used a
   different palette, omitted the titles, and placed the Figure 5 legend inside
   the axes although the caption states that it sits outside.
4. **The structural causal model was inconsistent across four places.** Equation
   21 omits `M_s`; Figure 1 and Appendix A omit testing intensity entirely, while
   Equations 21 and 25 and the figure script include it. The Mermaid source of
   Figure 1 is now versioned at `figures/scm_graph.mmd`, includes the testing
   node, and is parsed by the test suite and compared with the equations.
5. **The Sprint 5 scenario inputs were absolute constants.** Running the analysis
   against a different dataset produced meaningless indices without any warning.
6. **The worked-example printout hard-coded `epsilon = 1`,** so a non-default
   `--epsilon` printed a formula that disagreed with the number beside it.
7. **Repository hygiene.** A committed `.DS_Store`, no `.gitignore`, a
   byte-identical duplicate dataset, an unused dependency, and no CI.

## Round 2 corrective actions

- All six figures are rebuilt from the equation-derived arrays, in the published
  visual style, with the corrected values.
- Figure builders are separated from figure export so the tests can read the
  values off the Matplotlib artists. `TestFiguresMatchPublishedTables` asserts
  that the plotted lines equal Table 7, that the bar heights equal Table 8, that
  the raw series is the exact `EV/PV` ratio and never the rounded display field,
  and that the SCM edge set equals the edges implied by Equations 22-25. A
  mutation check confirmed the guard fails when the original rounding bug is
  reintroduced.
- Figure export raises on an empty output file.
- Scenario assumptions are expressed as whole-unit reductions relative to the
  observed record and validated against it.
- `epsilon` is carried into the worked-example output.
- `.gitignore`, a three-version GitHub Actions workflow, and byte-reproducible
  vector export via a pinned `SOURCE_DATE_EPOCH` were added; CI fails if a
  rebuild changes any committed result or figure.
- Manuscript-side changes are itemised in `MANUSCRIPT_CORRECTIONS.md`.

## Verification performed

- `python -m unittest discover -s tests -v`: 20/20 passed.
- `python code/validate_reproduction.py`: all independent equation checks passed.
- All result CSVs regenerated byte-identically to the Round 1 outputs, confirming
  that the refactoring changed no reported value.
- Figures rebuilt twice byte-identically.
- Plotted values re-extracted from the rebuilt vector PDFs and matched against
  Tables 7 and 8.

## Remaining evidentiary limits

Unchanged from Round 1. The audit verifies internal reproducibility only. It
cannot verify that the normalized CSV values derive from the claimed BioArc
operational records, `lambda_q` and `lambda_s` remain case parameters rather
than calibrated estimates, and the Sprint 5 alternatives remain deterministic
sensitivity scenarios rather than identified causal effects.
