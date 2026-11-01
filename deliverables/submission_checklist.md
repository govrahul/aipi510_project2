# Project 2 submission checklist

Prepared November 1, 2026 against the supplied **Module Project 2 Statistical Analysis** Word guidelines. The rubric calls for a report through Byline, a GitHub link, and a presentation of at most eight minutes on November 3. It does not specify a report page limit. The online cohort must also provide a viewable video link.

The report and presentation cover the completed observational football analysis and the documented collection/EDA. Basketball, cross-sport and before/after hypothesis tests remain unperformed. The course describes an experiment; this project uses observational secondary data, so the authors should resolve whether that design satisfies the instructor's expectation before claiming full rubric compliance.

## Written report

| Rubric item | Location in the seven page report | Status |
| --- | --- | --- |
| Title and abstract | Page 1 | Written |
| Background and motivation | Page 1 | Written; 2021 NCAA policy attribution corrected |
| Null and alternative hypotheses | Page 1 | Written; completed and pending tests distinguished |
| Design, variables, controls, randomization | Page 2 | Written; observational design and sampling distinguished |
| Power assumptions, calculations, software | Page 3 | Partial-term planning replaces reliance on overall model power |
| Collection and cleaning | Pages 2–3 | Actual procedures, source gaps, unknowns and revised sampling described |
| Statistical tests and rationale | Pages 4–5 | OLS/log scale; HC3 and school-cluster sensitivity |
| Assumption checks | Page 5 | Heteroskedasticity, collinearity, residuals, influence and dependence |
| p values, confidence intervals, effect sizes | Page 4 | Two-sided p, 95% intervals, 98.33% family interval, doubling interpretation |
| Post hoc tests if appropriate | Page 4 | Not applicable; no pairwise post hoc testing claimed |
| Interpretation and limitations | Page 6 | Selection, timing, source validity, missing performance and career follow-up |
| Conclusion and recommendations | Page 6 | Current result and next collection priorities |
| References | Page 7 | Source and methodology references |

Files: `project2_report.docx` is editable; `project2_report.pdf` is the matching reading copy. Editable text is also in `reports/deliverables/project2_report.md`. The partner's original PDF remains unchanged.

## Repository

- [x] Collection, cleaning and analysis are scripts rather than notebooks.
- [x] README includes setup and reproduction commands, source notes and the handoff context.
- [x] Inherited public football inputs are present; new local player-level data have source/collection descriptions and reproducible code rather than being silently omitted.
- [x] Rahul has [PR 2](https://github.com/govrahul/aipi510_project2/pull/2); Sam has [PR 4](https://github.com/govrahul/aipi510_project2/pull/4). These are open review items, not evidence that reviews have been completed.
- [ ] Rahul and Sam review the changes and resolve source/identity issues that affect the submitted result.
- [ ] Merge partner PR 2 before retargeting/reviewing the stacked PR 4 for main. No merge has been performed by the assistant.
- [ ] Confirm the final submitted repository link exposes the intended reviewed version and any required data descriptions.

## Presentation

- [x] Nine editable slides cover motivation, hypotheses, observational design, power, key results, diagnostics, limitations and next steps.
- [x] Native charts and tables are editable; speaker notes include source references.
- [x] Notes allocate **425 seconds or 7 minutes 5 seconds**, leaving 55 seconds within the maximum. This is a target, not a measured rehearsal duration.
- [ ] Choose the division of speaking roles and rehearse aloud under eight minutes.
- [ ] Update the report and slides together if data or specifications change.
- [ ] For the online cohort only, record the presentation and confirm the video link is viewable by the course staff.

## Before submission

1. Both authors read the report and confirm that it reflects their intended scope. The current conclusion is a selected-sample valuation association, not an established NIL policy or scholarship effect.
2. Validate the football follower identities and measurement dates, source valuation snapshot/methodology and performance fields where possible. Retain explicit limitations for unresolved observations; do not invent replacements.
3. Decide with the course's requirements in mind whether to submit the completed football observational study or finish additional analyses. The report transparently labels the pending comparisons.
4. Submit the report using the course Byline link and the repository using the course GitHub-link submission. Neither submission has been made.
5. Present on November 3, 2026, or submit the required video link for the online cohort. No video was recorded and no live presentation was performed.

## Data needed for the unfinished comparisons

Current basketball needs an actual NIL frame and dated follower counts, followed by the requested 250-per-full-frame-quartile selection and validated covariates. Historical samples need verified high-school recruiting classification and follower measurements from the historical decision period. A before/after regression additionally needs one common outcome and comparable inclusion rules. Career outcomes require verified positives/negatives and equal follow-up or a censoring-aware design. These are research gaps, not missing sections filled with simulated results.
