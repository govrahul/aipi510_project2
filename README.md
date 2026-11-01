> **Latest design (November 1):** Historical sampling now uses high-school recruiting stars, with the same provider's finer rating to order ties. Previous production-quartile samples/workbook are superseded provisional artifacts. Career/draft fields and basketball box BPM were added for historical and 2025–26 players. Final HS samples await verified recruiting coverage; current basketball remains NIL-stratified. See [recruiting_and_career_evaluation.md](docs/recruiting_and_career_evaluation.md) for collected data, commands and timing limits.

# NIL social media and college athlete selection

This AIPI 510 project investigates whether social reach is associated with athlete valuation and whether its association with scholarship offers changed after NIL implementation. These require different datasets. The inherited football sample supports an exploratory current-valuation analysis; it does not contain historical scholarship outcomes or pre-NIL social measurements.

Read [PROJECT_CONTEXT.md](PROJECT_CONTEXT.md) first for the handoff, known issues and change log. Read [docs/research_design.md](docs/research_design.md) for hypotheses, collection priorities, source links and rubric gaps. [Historical source feasibility](docs/historical_data_sources.md) identifies recruiting, offer and follower-history candidates and the remaining data gaps.

## Latest sampling plan

Sam revised new basketball work to **1,000 players, 250 per full-frame NIL quartile**, sorted by stratum. This replaces the earlier 100-player plan for new basketball work. See [stratification and Instagram collection](docs/stratification_and_instagram.md). `scripts/build_basketball_nil_sample.py` implements it; a real NIL frame is still required, so no current NIL-stratified basketball file has been fabricated.

Four provisional historical samples are now local: football and basketball for start years 2018 and 2019, each 1,000 athletes and 250 per production-proxy quartile. Historical followers and a common regression outcome remain missing. The football proxy currently covers QB/RB/FB/WR/TE only. [Historical collection audit](reports/historical_comparator_collection.json). The readable workbook is at `outputs/nil-quartiles-20261101/historical_quartile_samples.xlsx` locally.

The repo now includes `sample_quartiles.py`, `collect_historical_comparators.py`, `collect_instagram_counts.py`, and the workbook exporter alongside the existing basketball collector. No live Instagram call or paid query has been made.

## Current status

- Main contains a 1,000-player football frame and 100-player sample. Partner PR [#2](https://github.com/govrahul/aipi510_project2/pull/2) adds enriched football data, collection and initial regression. This branch builds on that PR without merging it into main; [PR #3](https://github.com/govrahul/aipi510_project2/pull/3) contains the new work.
- The partner regression reproduces: social coefficient 0.2067, HC1 two-sided p=0.000327, R²=0.321. These are selected-sample associations, not a policy or scholarship effect. [Results and sensitivities](reports/football_results.md).
- The [data audit](reports/data_audit.json) flags 41 zero PPA values, 30 nonzero PPA values on defense/OL, no match provenance, and only one non-Power-4 observation. No source rows have been silently repaired.
- Basketball performance collection began November 1: an ESPN/SportsDataverse export was downloaded and aggregated into 5,680 player-team records across 365 D1 teams. [Collection details and commands](docs/basketball_collection.md). The NIL frame, followers, recruitment stars, historical scholarship data and CBBD PORPAG remain missing. Sam confirmed there is no API key yet; Sideline HTTP access remains denied.
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

The supplemental basketball performance data is already local under `Data/private/basketball/`. It is not the top-1,000 NIL frame. To reproduce the download and aggregation:

```bash
python scripts/collect_basketball_open_stats.py --season 2026 --as-of 2026-10-31 \
  --transport curl --report reports/basketball_collection_audit.json
```

See [basketball_collection.md](docs/basketball_collection.md) for source provenance, cleaning, spot checks and remaining work. No regression was fit to these files because NIL/social inputs are absent.

Obtain a source-authorized basketball CSV with at least 1,000 players and the fields `Player Name, Position, College, Conference, Grade, Valuation`. This importer supports a CSV export; it is not a tested scraper for a currently accessible Sideline page. Provide the actual snapshot date rather than substituting today's date for unknown source dates.

```bash
python scripts/prepare_sample.py --input /path/to/authorized_basketball.csv \
  --sport basketball --source-url https://thesideline.co/nil-tracker/basketball \
  --observed-at 2026-10-31
```

The command above is the **older 100-player plan**, retained for replication. For the revised 1,000/250-per-quartile design, use `scripts/build_basketball_nil_sample.py` and the new guide linked above. The legacy command saves the top 1,000, a seed-510 sample and a provenance manifest under `Data/private/`. It samples 25/50/25 without replacement from 250/500/250 rank strata. Every player has a 10% selection probability within that frame. It cannot support claims about athletes below the frame cutoff.

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

Requests keep TLS validation enabled and cache raw JSON plus timestamp, parameters and SHA-256. Set `--refresh` to fetch a new response, or `--raw-json /path/to/response.json` for an offline replay. The official collector also supports `--download-only --output Data/private/basketball_cbbd_performance_2026.csv` before a sample exists and `--env-file` for a local credential file. Matching uses a provided API ID or exact normalized name plus team, with position validation. Transfers can supply a verified `Performance College`; otherwise they remain unmatched. Basketball position abbreviations may require explicit source review. Missing/unsupported metrics stay missing, including freshmen and defensive players. Review `Match_Status` before modeling. Collection does not automatically turn these files into a fully validated regression dataset.

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
