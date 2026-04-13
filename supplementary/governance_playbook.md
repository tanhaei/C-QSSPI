# Governance Playbook for CQSS-SPI Deployment

## Purpose

This playbook translates the CQSS-SPI framework into lightweight release-governance actions. It is intended for engineering managers, DevSecOps leads, and project-control stakeholders who need to interpret raw velocity against hidden quality and security liabilities.

## Core decision rule

At sprint close, review three quantities together:

1. **Raw SPI**
2. **Debt-adjusted descriptive QSSPI**
3. **Estimated or scenario-based CQSSPI comparisons**

A useful governance conversation starts with the gap among these values.

## Decision matrix

| Raw signal | Debt-adjusted signal | Counterfactual question | Suggested action |
|---|---|---|---|
| High SPI | High QSSPI | Is CQSSPI stable under nearby governance changes? | Continue current governance and monitor for drift |
| High SPI | Low QSSPI | Would stricter gating materially improve realistic schedule status? | Increase review and security gating before expanding scope |
| High SPI | Low QSSPI | Would selective AI restriction improve risk-adjusted schedule position? | Restrict AI use in critical modules while preserving it in low-risk repetitive work |
| Low SPI | Low QSSPI | Would easing compression improve realistic schedule position? | Re-plan scope or timeline |
| Low SPI | Moderate QSSPI | Do nearby scenario changes alter the decision materially? | Investigate blockers such as dependencies, staffing, or architecture |

## Recommended rollout

### Phase 1: silent rehearsal
- compute the corrected metrics for several sprints
- do not tie the numbers to incentives
- validate data quality and remediation estimates

### Phase 2: leadership visibility
- expose the gap between SPI and QSSPI to engineering leadership
- keep the interpretation explanatory, not punitive

### Phase 3: targeted governance experiments
Try one change at a time, such as:
- stronger SAST gating in critical modules
- selective AI restriction in high-risk components
- expanded review depth for AI-generated pull requests

### Phase 4: organizational learning
- revise review norms
- revise severity weights if needed
- document how governance changes affected realistic schedule performance

## Practical checklist

- [ ] Are debt inputs coming from stable and documented tools?
- [ ] Are severity weights documented?
- [ ] Is AI usage intensity defined consistently?
- [ ] Are release-blocking rules explicit?
- [ ] Are counterfactual comparisons clearly labeled as estimated or scenario-based?
- [ ] Are managers trained not to over-interpret raw velocity?

## Cautions

- A corrected schedule metric should improve managerial realism, not become a surveillance mechanism.
- Synthetic scenario values must never be presented as fitted empirical causal effects.
- The metric is most useful when paired with transparent engineering process knowledge.

## Relation to the illustrative repository

This repository demonstrates the mechanics of the metric on a synthetic eight-sprint scenario. The playbook should therefore be interpreted as a deployment guide for future empirical use, not as a claim that the repository's scenario values are themselves field estimates.
