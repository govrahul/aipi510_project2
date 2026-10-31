# NIL social media and college athlete selection

This AIPI 510 project investigates whether social reach is associated with athlete valuation and whether its association with scholarship offers changed after NIL implementation. These require different datasets. The inherited football sample supports an exploratory current-valuation analysis; it does not contain historical scholarship outcomes or pre-NIL social measurements.

Read [PROJECT_CONTEXT.md](PROJECT_CONTEXT.md) first for the handoff, known issues and change log. Read [docs/research_design.md](docs/research_design.md) for hypotheses, collection priorities, source links and rubric gaps.

## Current status

- Main contains a 1,000-player football frame and 100-player sample. Partner PR [#2](https://github.com/govrahul/aipi510_project2/pull/2) adds enriched football data, collection and initial regression. This branch builds on that PR without merging it into main; [PR #3](https://github.com/govrahul/aipi510_project2/pull/3) contains the new work.
- The partner regression reproduces: social coefficient 0.2067, HC1 two-sided p=0.000327, R²=0.321. These are selected-sample associations, not a policy or scholarship effect. [Results and sensitivities](reports/football_results.md).
- The [data audit](reports/data_audit.json) flags 41 zero PPA values, 30 nonzero PPA values on defense/OL, no match provenance, and only one non-Power-4 observation. No source rows have been silently repaired.
- Basketball NIL/follower data and all historical scholarship data remain missing. New collector code is offline-tested; live API collection has **not** been completed because no key is configured. Sideline web requests were denied by Cloudflare.
- Source values are estimates, not verified compensation. Confirm permissions for the existing bulk CSVs before further redistribution; newly collected licensed data defaults to ignored `Data/private/`.

## Reproduce available analysis

Python 3.11 or newer is recommended. Commands assume the repository root.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m unittest discover -s Tests -v
python scripts/audit_data.py
python scripts/analyze_football.py
python scripts/power_sensitivity.py
```

The scripts write aggregate reports, coefficient tables, diagnostics and a PNG to `reports/`. The existing data files are inputs and are not overwritten. The partner's original replication remains available via `python Tests/football_test.py`; `Tests/football_diagnostics.py` now actually uses HC3 where its labels say HC3. The original `power_analysis.py` is preserved for replication, but its overall-model power does not justify power for one social coefficient or interaction.

The legacy `Data/sample_data.py` overwrites the inherited sample if executed. Use the new importer below for additional datasets; its rank strata handle valuation ties explicitly.

## Collect basketball or refresh football performance

Obtain a source-authorized basketball CSV with at least 1,000 players and the fields `Player Name, Position, College, Conference, Grade, Valuation`. This importer supports a CSV export; it is not a tested scraper for a currently accessible Sideline page. Provide the actual snapshot date rather than substituting today's date for unknown source dates.

```bash
python scripts/prepare_sample.py --input /path/to/authorized_basketball.csv \
  --sport basketball --source-url https://thesideline.co/nil-tracker/basketball \
  --observed-at 2026-10-31
```

This saves the top 1,000, a seed-510 sample and a provenance manifest under `Data/private/`. It samples 25/50/25 without replacement from 250/500/250 rank strata. Every player has a 10% selection probability within that frame. It cannot support claims about athletes below the frame cutoff.

Enrich the sample using the header contract in `Data/templates/basketball_enrichment.csv`: record observed Instagram followers with observation date and evidence URL, recruitment stars with their source, and valuation date/source/type. Preserve missing values. Public profile handles alone do not supply verified follower counts. Do not infer race or other demographic attributes from names or photographs.

```bash
cp .env.example .env
# Enter API credentials locally in .env. Never commit or paste the key into chat.
python scripts/collect_performance.py --sport basketball --season 2026 \
  --sample Data/private/basketball_enriched.csv \
  --output Data/private/basketball_performance_joined.csv
python scripts/collect_performance.py --sport football --season 2025 \
  --sample 'Data/NIL and Player History Data - Football Sample.csv' \
  --output Data/private/football_performance_joined.csv
```

CBBD uses the **ending year**: `2026` means 2025–26. Football uses `2025` for the 2025 football season. Select the season preceding the valuation snapshot and verify that all included games occurred before that snapshot. CBBD collection extracts PORPAG; CFBD extracts average PPA per play. The metrics are not interchangeable.

Requests keep TLS validation enabled and cache raw JSON plus timestamp, parameters and SHA-256. Set `--refresh` to fetch a new response, or `--raw-json /path/to/response.json` for an offline replay. Matching uses a provided API ID or exact normalized name plus team, with position validation. Transfers can supply a verified `Performance College`; otherwise they remain unmatched. Basketball position abbreviations may require explicit source review. Missing/unsupported metrics stay missing, including freshmen and defensive players. Review `Match_Status` before modeling. Collection does not automatically turn these files into a fully validated regression dataset.

## Original before and after scholarship question

Populate `Data/templates/scholarship_prepost.csv` with actual athlete-school decisions, including both offers and verified non-offers in both periods. A lack of a public offer report is not a verified non-offer. Use comparable athletic scores and follower measurements dated before each decision. Current followers on old players are not valid historical measurements.

```bash
python scripts/analyze_prepost.py --input Data/private/scholarship_decisions.csv --sport football
python scripts/analyze_prepost.py --input Data/private/scholarship_decisions.csv --sport basketball
```

The linear probability model tests `log_followers:post`, with post starting July 1, 2021, athletic score, position/school controls and a linear calendar-year trend. Each sport is fit separately. It checks timing, outcome variation, duplicate records, matrix rank and athlete cluster count, then uses athlete-clustered errors. A minimum of 30 clusters is a guardrail, not proof of reliable inference. School dependence, policy co-changes, reporting bias and unobserved confounding still need study. There is no pre/post result until real qualifying data exists.

## Tests and collaboration

`Tests/test_pipeline.py` contains synthetic offline fixtures only, never research evidence. Tests cover incorrect/ambiguous identity matching, missing vs observed-zero performance, basketball response schema, sampling with ties, look-ahead bias, selected-only outcomes, interaction fitting and partial-term power.

No credentials, local course documents or new bulk source exports are included in commits. Review the new work before merging. Finish partner PR #2 first, then retarget this branch's PR to main if necessary. Update `PROJECT_CONTEXT.md` whenever data, methods or results change.
