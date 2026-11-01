# High-school recruiting and career evaluation

Updated November 1, 2026. Sam chose **high-school recruiting stars** for historical sampling, plus post-college outcomes and a broader player evaluation where available. Apply the same enrichment fields to 2018/2019 and 2025–26 players. This supersedes the previous provisional production-quartile design. Old samples/workbook are retained as superseded artifacts, not the approved historical analysis sample.

## Sampling design

Use the college-season roster as the population, then match each athlete's **earlier high-school recruiting class**. A 2018 college roster is not the 2018 recruit class: it contains athletes recruited in several prior years. Fetch the appropriate class window and keep transfer/JUCO ratings distinct from high-school ratings. The first source pull covers classes/observed college seasons 2012–2026; any earlier entrant remains incomplete.

Historical samples use 1,000 unique athletes, 250 per rank quartile. Order by stars descending, then the same provider's continuous recruiting rating descending. Ties can cross quartiles and are flagged. A dense score of the ordered (stars, rating) pair is used only for sorting/sampling; it is not an interval-scale evaluation variable or regression outcome. The groups are not equivalent to 2-, 3-, 4-, and 5-star categories. Unknown/unrated players are not zero-star observations. Do not replace missing ratings with college production or future outcomes.

`enrich_player_evaluations.py` retains the complete frame and only generates `SPORT_YEAR_HS_quartiles_1000.csv` when at least 1,000 unique athletes have verified high-school ratings and a consistent provider. Missing coverage can select the rated/US-recruited subset, so publish the coverage funnel before analysis. Current basketball's requested final sample remains **NIL-stratified**, with recruiting/career information added after selection; it is not resampled by stars.

The collector's public football export contains star ratings but loses high-school/JUCO classification. Those candidate matches are labeled `Recruit_HS_Verified=False`; the grade is kept as `Recruit_Source_Grade`, not mislabeled as a verified original composite. No final historical HS sample was generated. The previous historical collector now defaults to source frames only; its old samples require explicit `--legacy-production-samples` to reproduce.

## Sources actually collected

| Layer | Source and scope | Status/limitations |
|---|---|---|
| Football recruiting | [SportsDataverse cfb_recruits](https://github.com/sportsdataverse/sportsdataverse-data/releases/tag/cfb_recruits), 2012–2026 | Downloaded. Source construction uses the 247 recruit store; exact normalized name + ESPN committed-team ID candidate joins only. The release does not retain HS/JUCO classification or establish a pre-decision rating date. Recruit ID is not assumed to be a college athlete ID. |
| Verified HS recruiting | [CFBD recruiting](https://api.collegefootballdata.com/api/recruiting), [CBBD recruiting](https://api.collegebasketballdata.com/api/recruiting) | New collector implemented and offline-tested. CFBD explicitly requests `classification=HighSchool`; CBBD documents high-school composites. No key is available, so no live records were collected. Different provider IDs are not assumed to be ESPN IDs. Exact name + commitment-school joins remain candidates requiring identity review; transfers may remain unmatched. |
| Basketball evaluation | [SportsDataverse player value](https://py.sportsdataverse.org/docs/mbb/reference/loaders/player), 2012–2026 | Downloaded box offensive/defensive/total BPM, minutes and qualification flags. Join by ESPN player+team+season. Units: estimated points per 100 possessions above average. Low-minute/unqualified estimates are retained with flags. This is a retrospective model-derived evaluation, not an ESPN ranking or CBBD PORPAG. Model construction/changes and historical information use still need review before a formal cross-era model. |
| NBA draft | [SportsDataverse NBA Stats draft](https://github.com/sportsdataverse/sportsdataverse-data/releases/tag/nba_stats_draft), draft years 2018–2026 | Downloaded 533 rows. These assets use an ending-season convention: asset `draft_2020` contains the 2019 draft. Normalization records actual draft year as source season minus one. A secondary ESPN export disagreed on most pick/name pairs (39 of 533 pairs agreed including round); the NBA Stats values are retained with per-row disagreement flags. [NBA's 2019 results](https://www.nba.com/news/2019-nba-draft-results-picks-1-60?team=LAC) confirmed the Hunter/Garland order in NBA Stats. This is a spot check, not full validation. |
| NFL draft | [nflverse/nflreadr draft picks](https://nflreadr.nflverse.com/reference/load_draft_picks.html) | Downloaded the published 12,927-row export; enrichment uses years through 2026. Match exact normalized name+college and subsequent draft year; transfers, aliases and ambiguous matches remain unresolved. |
| Observed college history | ESPN football roster exports; basketball positive-minute player-value rows, 2012–2026 | Downloaded. Count distinct recorded seasons before the cohort and through the as-of snapshot separately. They are lower bounds: redshirts, injuries, non-D1/JUCO/international years and source gaps can be absent. They do not prove enrollment years, eligibility used, graduation or completed career length. |
| Overseas contracts | Dated official club/league announcements, reviewed event input | One verified historical example: Markus Howard/Baskonia, evidenced by an [official ACB announcement](https://acb.com/es/supercopa/noticias/baskonia-y-markus-howard-juntos-hasta-2028-140642). The observation is known by November 1, 2026; it does not assert a signing date, first overseas contract, salary or current employment. Other athletes remain unknown. A roster listing alone does not establish a signed professional contract. |

[EvanMiya BPR](https://evanmiya.com/how-it-works) is a relevant player-evaluation candidate. Historical season coverage, access/export rights, and methodology consistency have not been established here; no subscription or bulk pull was made. [ESPN BPI](https://espnpressroom.com/feature/breaking-down-espns-new-tool-the-bpi-with-jay-bilas/) is a **team** rating. No verified public all-position football composite covering every requested season/player was established, so the football evaluation field explicitly remains unavailable.

## Fields and timing

- `Recruit_Stars`, `Recruit_Rating`, `Recruit_Class_Year`, `Recruit_HS_Verified`, provider, source URL, match status and provenance. Final class ratings are not verified measurements before a scholarship decision.
- `College_Box_BPM`, `College_Box_OBPM`, `College_Box_DBPM`, `College_BPM_Minutes`, `College_BPM_Qualified` for basketball. Do not rank unqualified five-minute players as the best athletes without a justified exposure rule.
- `Draft_Year`, `Draft_Round`, `Draft_Overall_Pick`, league, professional ID, source, match status and secondary disagreement flag. A smaller round/pick indicates earlier selection. NBA and NFL draft scales differ; keep sports separate or explicitly standardize within league. No-match is **unknown**, never round 0, zero talent, or verified undrafted.
- `Overseas_Professional_Contract` is true only with reviewed evidence; otherwise missing. Club, league, event/observation date and evidence URL are retained. Absence of news is not a negative contract outcome.
- `Observed_College_Seasons_By_Cohort` is a recorded-history lower bound available by the cohort. `Observed_College_Seasons_Through_AsOf` uses later history. `College_Years_Total` stays missing until evidenced, with `College_Career_Completion_Status`. Neither class label nor final observed season establishes total years in college.
- `Career_As_Of=2026-11-01`, `Career_Followup_Status=incomplete_not_a_final_career_outcome`. The reviewed snapshot is bounded to this date; changing it requires event-date review.

**No future leakage:** draft results, pro contracts, completed career duration and later season counts are outcomes/descriptive follow-up, not pre-college predictors or sampling variables. Some 2025–26 basketball/2025 football athletes have observed 2026 draft outcomes; other careers remain unresolved. Fall 2026 football is ongoing and has no subsequent draft observation in this snapshot. No missing future outcome was coded as failure.

Historical cohorts have much longer follow-up. A comparison of eventual pro success needs the same follow-up horizon (for example a pre-specified three years) and a censoring plan; current cohorts cannot yet supply three-year outcomes. Years in college also have no simple higher-is-better interpretation because elite athletes may leave early. Do not collapse draft round, overseas employment and years into an arbitrary score.

Using the same basketball BPM outcome in both eras could support a new association study about performance. It would not directly measure colleges' scholarship decisions. Recruiting and career fields alone do not recover missing historical social observations or a common scholarship outcome.

## Reproduction

```bash
# Collect old performance frames only; avoids recreating superseded samples.
python scripts/collect_historical_comparators.py
# Requires the earlier current basketball performance layer (README command).
python scripts/collect_evaluation_sources.py
python scripts/enrich_player_evaluations.py \
  --reviewed-events Data/curated/reviewed_career_events.csv
python -m unittest discover -s Tests -v
```

Source URLs, hashes, row counts and retrieval times are recorded in `reports/evaluation_sources_manifest.json`. Aggregate join/coverage status is `reports/evaluation_collection_audit.json`. Full source caches and enriched frames stay in ignored `Data/private/evaluation/`. Seven enriched supporting frames cover basketball 2018–19, 2019–20, 2025–26 and football 2018, 2019, 2025, 2026. These are full source layers, not seven final 1,000-player samples.

Once a key is configured locally, collect HS classes for both sports (example window; widen if the entrant coverage audit requires it):

```bash
python scripts/collect_recruiting.py --sport basketball --years 2012 2013 2014 2015 2016 2017 2018 2019 2020 2021 2022 2023 2024 2025
python scripts/collect_recruiting.py --sport football --years 2012 2013 2014 2015 2016 2017 2018 2019 2020 2021 2022 2023 2024 2025 2026
python scripts/enrich_player_evaluations.py \
  --official-recruits Data/private/evaluation/official_recruiting/basketball_hs_recruits.csv \
  --reviewed-events Data/curated/reviewed_career_events.csv
```

The official CSV input may concatenate both sports using the same generated schema. Offline JSON replay requires a provenance sidecar with the documented URL/params, retrieval time and SHA-256. The CLI collector fails before a request if no key is configured. Never paste credentials into chat or commit `.env`.

A verified ESPN-ID sample can be enriched with `--input PATH --sport basketball --cohort-start 2025`. It must supply ESPN athlete_id, team_id, Player_Name and College. Preserve the selected sample's rows even when joins fail. `build_basketball_nil_sample.py --evaluation-frame Data/private/evaluation/enriched/basketball_2025_evaluation_frame.csv` left-joins the new fields after the NIL draw using only accepted performance identities. Unmatched athletes remain in their original quartile with missing evaluation fields. The current NIL frame and its source dates are still required.
