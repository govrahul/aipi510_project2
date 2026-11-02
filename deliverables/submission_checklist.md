# Project 2 submission checklist

Updated November 2, 2026 against the course **Module Project 2 Statistical Analysis** guidelines. The rubric calls for a report through Byline, a GitHub link, and a presentation of at most eight minutes on November 3. It does not specify a report page limit. The online cohort must also provide a viewable video link.

The report covers the football and basketball follower analyses and the cross-sport comparison. The before/after NIL test could not be run and is reported as a limitation. The rubric describes an experiment; this project is an observational study with stratified random sampling, and the design section says so plainly.

## Written report

| Rubric item | Location in the nine-page report | Status |
| --- | --- | --- |
| Title and abstract | Page 1 | Written |
| Background and motivation | Page 1 | Written |
| Null and alternative hypotheses | Pages 1–2 | H1 football, H2 basketball, H3 sport difference, with results; pre/post hypothesis stated as untestable |
| Experimental design: variables, controls, randomization | Page 2 | Written; no control group (observational), stratified random sampling with seed 510 |
| Power analysis: assumptions, calculations, software | Page 2 | Partial-term noncentral F calculation in SciPy (kept as written) |
| Data collection and cleaning | Page 3 | Both sports; raw versus cleaned files named |
| Statistical tests and rationale | Page 4 | Log-log OLS, HC3 errors, pooled interaction for H3, dominance analysis |
| Assumption checks | Page 6 | Breusch–Pagan, Jarque–Bera, VIF, Cook's distance, leverage, clustering |
| p values, confidence intervals, effect sizes | Pages 4–6 | % per doubling with 95% CI, partial f², R² shares, Bonferroni 98.33% CI |
| Post hoc tests | Page 6 | Kruskal–Wallis with Holm-corrected Mann–Whitney pairs (follower groups, recruiting stars) |
| Interpretation of results | Page 7 | Written |
| Limitations | Page 8 | Written |
| Conclusion and recommendations | Page 8 | Written |
| References | Page 9 | Data sources and methods references |

Files: `project2_report.docx` is editable; `project2_report.pdf` is the matching reading copy. Editable text is also in `reports/deliverables/project2_report.md`. The partner's original PDF remains unchanged.

## Repository

- [x] Collection, cleaning and analysis are scripts rather than notebooks.
- [x] README includes setup and reproduction commands, source notes and the handoff context.
- [x] Inherited public football inputs are present; new local player-level data have source/collection descriptions and reproducible code rather than being silently omitted.
- [x] Rahul has merged PRs ([#1](https://github.com/govrahul/aipi510_project2/pull/1), [#2](https://github.com/govrahul/aipi510_project2/pull/2), [#7](https://github.com/govrahul/aipi510_project2/pull/7)); Sam has merged PRs ([#4](https://github.com/govrahul/aipi510_project2/pull/4), [#5](https://github.com/govrahul/aipi510_project2/pull/5), [#8](https://github.com/govrahul/aipi510_project2/pull/8)).
- [ ] Rahul reviews the final report/README PR before it is merged.
- [ ] Confirm the final submitted repository link exposes the intended reviewed version and any required data descriptions.

## Presentation

- [x] Nine presented slides cover motivation, the two-sport results, what matters most, limitations and next steps, with backup slides after them.
- [x] All charts are plain-language bar charts; speaker notes include source references.
- [x] Notes allocate **425 seconds or 7 minutes 5 seconds**, leaving 55 seconds within the maximum. This is a target, not a measured rehearsal duration.
- [ ] Choose the division of speaking roles and rehearse aloud under eight minutes.
- [ ] Update the report and slides together if data or specifications change.
- [ ] For the online cohort only, record the presentation and confirm the video link is viewable by the course staff.

## Before submission

1. Both authors read the report and confirm that it reflects their intended scope. The conclusion is a valuation association in two sampled groups, not an established NIL policy or scholarship effect.
2. Validate the football follower identities and measurement dates, source valuation snapshot/methodology and performance fields where possible. Retain explicit limitations for unresolved observations; do not invent replacements.
3. Submit the report using the course Byline link and the repository using the course GitHub-link submission. Neither submission has been made.
4. Present on November 3, 2026, or submit the required video link for the online cohort. No video was recorded and no live presentation was performed.

## Data needed for the unfinished comparisons

A sport main effect needs football sampled across its full NIL range, as basketball was. The before/after NIL question needs follower counts from before 2021 and one outcome measured the same way in both eras. Career outcomes require verified positives/negatives and equal follow-up or a censoring-aware design. These are research gaps, not missing sections filled with simulated results.
