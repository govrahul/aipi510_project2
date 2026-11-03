# AIPI 510 Project 2 deliverables

> **November 3 sampling correction:** The basketball and combined findings in
> these existing artifacts use the legacy sample drawn from all 5,348 listings.
> They have not been rerun on the corrected top-1,000 population. Treat them as
> earlier draft results pending a validated performance join and rerun using
> `Data/curated/basketball_top1000_instagram_100.csv` (100 counts / 100 selected;
> 99 browser observations and one user report).
> See [correction notes](../docs/basketball_top1000_social.md).

Updated November 2, 2026 from the course rubric and the completed two-sport analysis.

- **project2_report.docx** — editable ten-page report with every rubric section in order: the main model (same formula in each sport), the sport-specific basketball and football models, assumption checks, post hoc tests, power analysis and limitations.
- **project2_report.pdf** — matching reading copy.
- **project2_presentation.pptx** — nine presented slides (about 7 minutes 5 seconds) followed by backup slides; every chart is a plain-language bar chart.
- **presentation_script.md** — speaker notes as editable text.
- **model_explainer_slide.pptx** — one-slide visual explanation of the football-specific model.
- **combined_model_slide.pptx** — one-slide visual explanation of the main model in both sports.
- **basketball_only_model_slide.pptx** — one-slide visual explanation of the basketball-specific model.
- **nil_growth_by_follower_group.png** — NIL value by follower group as a multiple of each sport's lowest group (avoids comparing dollar levels across the two samples).
- **submission_checklist.md** — rubric mapping, remaining research gaps and author/submission actions.

The report and slides cover the football and basketball follower analyses and the cross-sport comparison. The before/after NIL comparison could not be run (no pre-2021 follower data) and is described as a limitation rather than filled with invented results. The original partner PDF and raw/model inputs are preserved.

## Reproduce

From the repository root, using the analysis environment in the main README:

```bash
python scripts/summarize_deliverable_results.py
python scripts/make_manuscript_figures.py
python scripts/make_unified_figures.py      # add --cached to skip the bootstrap
python scripts/build_project_report.py
```

The analysis scripts use pandas, numpy, SciPy, statsmodels and matplotlib. The report builder uses python-docx and writes the DOCX plus `reports/deliverables/project2_report.md`. `model_statistics.json` contains the exact checked results, covariance conventions, family intervals, effect transformations, diagnostics and partial-term planning calculations.

The report uses ordinary Word paragraphs and tables. The PDF was exported from the DOCX with LibreOffice (`soffice --headless --convert-to pdf`); inspect every page after substantial text changes.

The presentation's charts are the PNG files in `figures/` (each slide chart has the same file name as its figure). `scripts/build_project_presentation.mjs` builds the earlier nine-slide football-only draft; the final deck was revised from that draft by hand to add the two-sport results, so rebuild the charts with the figure scripts rather than rerunning the deck builder.

Refresh the Markdown speaker notes from the completed PPTX with:

```bash
python scripts/export_presentation_notes.py
```
