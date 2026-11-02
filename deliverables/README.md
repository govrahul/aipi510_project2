# AIPI 510 Project 2 deliverables

Prepared November 1, 2026 from the supplied Word rubric and the completed analysis.

- **project2_report.docx** — editable seven page report, with all rubric sections, replicated football results, corrected power analysis, EDA and limitations.
- **project2_report.pdf** — matching reading copy.
- **project2_presentation.pptx** — nine editable slides with charts, tables and timed speaker notes; target 7 minutes 5 seconds before rehearsal.
- **presentation_script.md** — speaker notes as editable text.
- **submission_checklist.md** — rubric mapping, remaining research gaps and author/submission actions.

These present the actual completed football association and supporting EDA. Basketball, cross-sport and before/after results have not been invented. No course submission, PR merge or video recording has been performed. The original partner PDF and raw/model inputs are preserved.

## Reproduce

From the repository root, using the analysis environment in the main README:

```bash
python scripts/summarize_deliverable_results.py
python scripts/build_project_report.py
```

The first command uses pandas, numpy, SciPy and statsmodels. The second uses python-docx and writes the DOCX plus `reports/deliverables/project2_report.md`. `model_statistics.json` contains the exact checked results, covariance conventions, family intervals, effect transformations, diagnostics and partial-term planning calculations.

For document QA and the matching PDF, use the installed documents skill's `render_docx.py` with `--emit_pdf`, inspect every page, and copy the resulting PDF to this folder. The report uses ordinary Word paragraphs and tables. Page breaks are intentional; inspect again after substantial text changes.

The deck builder uses `@oai/artifact-tool` with the bundled workspace runtime. It also exports `loadEvidence()` and `populatePresentation(presentation, evidence)` for use inside a presentation Artifact Session transaction. For a local export, expose the bundled Node packages through an ignored `node_modules` link and set the installed skill/Python paths:

```bash
PRESENTATIONS_SKILL_DIR=/absolute/path/to/installed/presentations/skill \
ARTIFACT_PYTHON=/absolute/path/to/bundled/python3 \
RUNTIME_NODE_MODULES=/absolute/path/to/bundled/node_modules \
  /absolute/path/to/bundled/node scripts/build_project_presentation.mjs
```

The file finalizer requires a new output path. If rebuilding an existing delivered deck, archive that copy first; do not overwrite a reviewed file without retaining its revision. The builder renders all slides to ignored `outputs/deliverable-qa/presentation/`, validates native charts/tables, and writes the PPTX. Inspect all slide images after edits. Source references are in speaker notes. Runtime/validation intermediates and larger private source layers are not part of the submission artifacts.

Refresh the Markdown speaker notes from the completed PPTX with:

```bash
python scripts/export_presentation_notes.py
```
