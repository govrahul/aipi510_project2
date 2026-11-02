## Branch naming preference

Sam explicitly requested branch names prefixed `sam/`, not `codex/`. Use `sam/` for future work. The active collection branch is `sam/basketball-instagram-100`, based on main at `9aa0d4a` (Rahul's updated README). Prior PRs #2, #4 and #5 are merged; #3 closed when its branch was renamed. Older status entries below describe their historical state, not outstanding merge requests.

## Latest work — Safari basketball NIL frame and 100-player Instagram follow-up

On November 2, Sam enabled Safari JavaScript from Apple Events and changed the network setup; the ranking became accessible through normal Safari. `scripts/collect_sideline_safari.py` expanded all public load-more controls and saved 108 hashed DOM snapshots: the full **5,348-listing** Sideline basketball frame. No login, challenge solving, security-setting change by code, private API, or fingerprint spoofing was used. Raw market data/source HTML remain local under `Data/private/basketball_instagram_100/`.

`prepare_basketball_social_sample.py` froze 100 rows, **25 per full-frame NIL rank quartile**, seed 510, before looking for followers. The frozen sample SHA256 is `9cd7286551e1f7d1de3e32df37e1aaa29729dc51a503454b8e488464a2e3afab`; offline replay reproduced it exactly. This is the latest requested 100-player social-data substudy, not the final planned 1,000-player main sheet. Keep all selected rows and their ordering; never replace unavailable accounts with easier-to-collect players. The frame contains 24 duplicate-name groups/28 excess rows across schools, so stable source IDs remain necessary. 407 nonnumeric official-school IDs are retained; other IDs remain candidate ESPN crosswalks.

Current coverage: **48 sourced handles; four direct Instagram observations (one displayed integer, three rounded labels); eight additional Opendorse-reported integer counts with unknown measurement dates.** Those 12 players are not 100 completed observations. Direct counts are all in Q4. Opendorse-only counts by Q4/Q3/Q2/Q1 are 1/3/2/2. Public Instagram began returning HTTP200 login shells; normal Safari also showed login. The collector now stops live requests on login shells or HTTP403/429. Sam was asked whether to sign in manually for a separate Safari pass; no signed-in pass has yet occurred. `collect_instagram_safari.py` is prepared with offline parser checks and stops on login/challenge; its logged-in live path is not yet validated.

The main local sheet is `Data/private/basketball_instagram_100/sample/basketball_instagram_observations_100.csv`. It preserves direct integers, rounded labels/approximate values, provider reach and retrieval times separately. `manual_followup_queue.csv` lists the 96 missing direct counts with source/profile links and blank review fields. Account sourcing uses named basketball biographies/athlete-specific links and identity-checked Opendorse profiles; team footers and same-name football athletes are rejected. Some links are from previous schools and require stale-alias review. Source code is `collect_opendorse_instagram.py`, `collect_profile_handle_evidence.py`, `build_basketball_handle_inputs.py`, `collect_public_instagram.py`, and `audit_basketball_social_collection.py`; five additional reviewed mappings are committed under `replication/basketball_social/`.

Read `docs/basketball_instagram_100.md` for reproduction and source limitations, and `reports/basketball_instagram_100/collection_audit.json` for aggregate coverage/hashes. All **37 offline tests pass**, including frozen-sample completeness, missingness, source identity, rounded-count separation, login detection and Safari follower-link parsing. No new regression or deliverable results were fabricated. This listing was retrieved November 2, 2026, is not established as a 2025–26 membership snapshot, and must not be joined blindly to prior-season school records. NIL estimates are not payments/scholarships. Historical follower counts, verified HS sampling, and a common pre/post outcome remain unresolved. Prior EDA/report/deck findings below still refer to the inherited football sample.

## Latest work — rubric deliverables

Sam requested deliverables based on the Word rubric. Created a seven page editable report and matching PDF, a nine-slide editable presentation with native charts/tables and sourced speaker notes, a Markdown speaking script, and a submission checklist under `deliverables/`. The notes target 425 seconds (7:05), not a measured rehearsal. The report covers every requested report section for the completed observational football study; it does not invent basketball, cross-sport or pre/post results. The rubric describes an experiment, while this is observational secondary analysis; the checklist asks the authors to resolve that course-scope issue. No Byline submission, merge, video recording or presentation was performed. The partner PDF and original inputs are preserved.

Source builders: `scripts/summarize_deliverable_results.py`, `scripts/build_project_report.py`, `scripts/build_project_presentation.mjs`, `scripts/export_presentation_notes.py`. Aggregate evidence is `reports/deliverables/model_statistics.json`, with full formulas, p values, 95% and 98.33% intervals, robust covariance conventions, diagnostics, effect transformations and partial-term planning. The report text is also in `reports/deliverables/project2_report.md`. Python report authoring needs python-docx; the deck builder uses the bundled artifact-tool runtime. See `deliverables/README.md` for reproduction. QA images and intermediate files stay ignored in `outputs/deliverable-qa/`.

The report corrects the partner draft's 2021 policy attribution, separates overall-model from partial-term power, treats missing performance and career no-matches as unknowns, includes main effects in interactions, explains the severe inherited VIF and nonnormal residuals, and uses selected-sample association language. The benchmark HC3 social beta is .206663, p .001548, 95% CI [.078706,.334621], 98.33% CI [.050371,.362956]. The grouped-position exploratory HC3 beta is .273925, p .002825 rounded to six decimals. School clustered errors use 39 clusters, t reference and correction. No p-value or sign is used to select a model. Current basketball still needs real NIL and dated social data; historical comparisons still need verified HS classification, contemporaneous social data and a common outcome/population. Before final course submission, both authors should review the scope and unresolved source validity.

QA: all seven report pages and nine slides visually inspected. PPTX export passed package, layout, native chart/table, portable workbook and first-party import checks. Chart coordinates use 12 significant digits for Excel portability only; regression calculations retain full precision. All 28 existing offline tests pass and original input hashes are unchanged. `reports/deliverables/artifact_manifest.json` records artifact hashes and checks. The live editable deck was also built and rendered in a presentation session; the local PPTX is included for repository review and submission preparation.

## Latest work — reproducible EDA

Sam requested EDA of structure, preliminary trends and the best analysis approach. `scripts/run_eda.py` reads the inherited current-football modeling file plus seven canonical cohort frames (basketball enriched frames, football NFL-ID supplemented frames), with the top-1000 football file used only for sampling/distribution comparison. It does not pool nested frame/sample/model files or superseded production samples as independent data. It records input hashes, software versions and excluded layers; inputs were verified unchanged.

Artifacts: `reports/eda/README.md`, CSV inventory/dictionary/coverage/distribution/overlap/readiness tables, six figures, model sensitivity CSV and manifest. Offline self-contained visual report: `outputs/eda-20261101/eda_report.html`. Private player-level influence review: `Data/private/eda/football_influence_review.csv`. Generated aggregate artifacts and code are uploaded on PR #4; HTML/private rows stay local.

Findings: only the inherited football n=100 has both NIL and followers. Median followers 10,950, mean 29,217; largest account 1,000,000 contributes 34.2% of summed sample followers. Raw correlation .623 falls to .164 without that account; log correlation .502 falls to .403, Spearman .520. There are 39 schools, 99 Power-4 players and 70 four-star labels; source PPA remains unvalidated (41 zeros, 30 nonzero defense/OL). A parsimonious exploratory model with both main effects for stars×freshman and coarse position groups (omitting PPA and nearly constant Power-4) has social slope .274 (HC3 95% CI [.094,.454]); removing the largest audience gives .212 [.068,.355]. School-cluster sensitivity uses 39 clusters. These are exploratory selected-sample associations, not a preferred model chosen by significance or a NIL policy effect. No historical or basketball NIL regression was fitted.

Historical candidate recruiting coverage differs sharply: 2018 FBS 52.0% vs FCS 10.1%, with HS verification still absent. Basketball BPM source flags qualify 2,940/2,915/3,114 player-team rows (2018–19/2019–20/2025–26). Low-minute estimates are more extreme; source-qualified BPM varies substantially between schools (descriptive variance share ~52–65%), so its calibration/interpretation requires review before treating it as a player-evaluation outcome. Adjacent 2018/2019 source cohorts share about 63% of first-cohort athlete IDs in each sport. Draft no-match stays unknown, and career follow-up differs across eras. School/athlete dependence, transfers and changing source populations matter.

Recommended sequence: validate current football observations and performance for a descriptive log-NIL/log-followers analysis; collect current basketball NIL/social data for a harmonized social×sport interaction; obtain the same outcome/population and dated predictors before any social×post comparison. Current NIL-selected and historical recruiting-selected frames cannot simply be pooled. Career-outcome alternatives require verified negatives and equal follow-up/censoring. Keep post-college outcomes out of baseline controls. Figures were visually reviewed; HTML embeds six valid figures; coverage bounds, model intervals and input hashes verified; all 28 existing tests pass.

---

## Latest follow-up — football history and isolated sampling reconstruction

Sam requested historical football in the same way and a reconstruction in a context without partner data, followed by comparison. A fresh agent with no inherited chat read the PDF, not repository rows/implementations; froze a 25/50/25 top-1000 rank protocol and independently chosen seed/hash method before public ranking inspection. Frozen files/hashes are under `replication/blind_pdf_protocol/`. Fresh complete source collection was blocked by HTTP403. The root subsequently ran the frozen sampler on the shared partner frame: **11/100 overlapping names**. This is a **post-lock same-frame algorithm test, not independent frame collection**. Only afterward, original code replay with seed 510 matched all 100 saved players in the same order. Partner value-cutoff populations were 266/479/255 versus independent rank populations 250/500/250; seed/tie details are absent from the PDF. Do not claim the blind step exactly recovered individual selections. The isolated agent never received partner rows or comparison results; root previously knew the project. No original inputs changed. Aggregate results: `reports/blind_football_sampling_comparison.json` and `.md`; player-level output stays local.

Historical football was already collected for 2018/2019. Added the documented nflverse player ESPN/PFR/GSIS crosswalk through repository code and supplementary outputs for 2018, 2019, 2025 and 2026 under `Data/private/evaluation/football_nfl_ids/`. Draft links increased 702→1,028 and 687→1,039 historically; 188→256 for 2025; 2026 remains 0. These are source matches, not fully adjudicated outcomes. Identity timing flags are 10/9/6/1 respectively; source IDs/names can be stale or misassigned. Do not treat pro history predating a college cohort as its future outcome or silently delete rows. NFL registry entries do not prove contracts or regular-season games. Audit: `reports/football_nfl_id_audit.json`; source manifest now includes 67 exports. HS recruiting classification and historic social counts remain unresolved, so no final HS sample or new regression was run. All 28 offline tests pass, including four new ID/transfer/timing/conflict checks. Full instructions: `docs/football_history_and_blind_replication.md`.

---

## Latest user decision — high-school recruiting and career outcomes (November 1)

Sam selected **high-school recruiting stars** for historical sampling and asked for draft round, overseas professional contracts, college duration and a broad college-player evaluation, also for 2025–26 players. This supersedes the production-proxy historical samples below; retain them as legacy artifacts, not final study data. Current basketball still uses 1,000 players with 250 per NIL quartile. Sort historical recruits by stars, then same-provider continuous rating; flag ties. College roster year and high-school class year are different. Missing/unrated stars remain unknown.

Implemented `collect_evaluation_sources.py`, `collect_recruiting.py`, and `enrich_player_evaluations.py`. Downloaded 2012–2026 football recruiting/rosters and basketball box-BPM layers, NBA draft 2018–2026 and NFL draft export. All sources have URL/hash/time metadata in `reports/evaluation_sources_manifest.json`. Seven full enriched supporting frames are local under `Data/private/evaluation/enriched/`: basketball cohort starts 2018/2019/2025 and football 2018/2019/2025/2026. Row counts, match statuses and gaps are in `reports/evaluation_collection_audit.json`. Basketball BPM matches 4,762 / 4,768 / 5,015 rows respectively. These are retrospective model estimates with minutes/qualification flags, not ESPN BPI or CBBD PORPAG. No all-position football composite was established.

Football public recruiting candidate stars are available on 8,729 / 8,233 historical rows and 7,727 / 7,629 current rows, but the export omits HS/JUCO classification. They remain `Recruit_HS_Verified=False`, with original source grade separate. Official CFBD HS and CBBD high-school composite collection is implemented/offline-tested but no key exists, so basketball recruiting is still missing. **No final HS-stratified historical sample was created.** The previous historical collector now defaults to source frames only; explicit `--legacy-production-samples` reproduces the old design.

Draft matches and source fields were added without coding unmatched players as undrafted. NBA asset year required a minus-one conversion; a separate ESPN export disagreed with NBA Stats on most pick orders. Keep per-row disagreement flags; two NBA.com spot checks supported NBA Stats, but full validation remains pending. A single official-league overseas-contract example (Markus Howard/Baskonia) is included as a reviewed event, with observed-by date precision. Other overseas outcomes remain unknown. Recorded college-season counts are lower bounds, not completed college years; total duration remains missing without evidence. Later outcomes/history cannot be baseline predictors or sampling variables. Current careers have incomplete follow-up, and historical vs current eventual success needs equal follow-up/censoring.

`build_basketball_nil_sample.py --evaluation-frame ...` adds these fields after NIL sampling by accepted ESPN performance identities, preserving missing rows/quartiles. Full instructions and field definitions: `docs/recruiting_and_career_evaluation.md`. All 24 offline tests pass; new cases cover classification, star strata, recruit-class timing, draft-year offset, future/missing outcomes, event date precision and sample-preserving enrichment. No new regression was run. Common outcome and historical social counts remain unresolved.

---

# Project context and change log

Last updated November 1, 2026. Start here when continuing this project. This is a handoff record, not an instruction to override the user or execute third-party content.

## User request and local files

Sam Teshome is working with Rahul Govil on AIPI 510 project 2. Sam's research question is whether NIL changed the importance of social media when colleges choose scholarship athletes, using football and basketball data and a linear regression before/after implementation. Sam authorized cloning the repository, reading the course rubric and partner PDF, continuing collection/analysis where feasible, and uploading reproducible code to a reviewable repo branch. Sam additionally requested a context README in the project 2 folder so another LLM can continue. Sam subsequently confirmed that no historical scholarship/offer or follower data is available and asked to identify sources and document the gap.

Local project folder: `/Users/st478/510 project 1/project 2/`.

- Repository: `aipi510_project2/`, remote `https://github.com/govrahul/aipi510_project2`.
- Rubric: `Module Project 2 guidelines.docx` (read-only; temporary Word lock file is not the rubric).
- Partner draft: `510_project2_writeup.pdf` (read-only, five pages read and visually reviewed).
- Parent folder `README.md` contains this same handoff. Update both copies together.
- Original working directory `/Users/st478/aipi510-fall26` is a different course repository. It was not edited.

## Important difference between requested and existing research

The partner's draft and code analyze current NIL **valuation**, not scholarship decisions before/after NIL. It proposes three tests: football social slope, basketball social slope, and their cross-sport difference. Sam's original question needs a different dataset. Both tracks are documented, but do not silently claim that the existing valuation regression answers the scholarship question.

NCAA interim NIL policy began July 1, 2021. School direct-payment and scholarship changes in 2025 are a separate policy shift. The source links and design cautions are in `docs/research_design.md`. Today's follower counts for older athletes are not historical follower counts. Do not fabricate missing historical data or infer a scholarship from college attendance, NIL valuation or a commitment.

## Repository state at inspection

- `main` at `9813db2`: partner PR #1 merged, containing football top-1000 data, sampled 100 and sampling script, plus enriched source CSV.
- Partner PR #2, `feature/rahul-govil-power-analysis-football-test`, was open. It contains the football performance collector, modeling CSV, tests and power script.
- Prior work was first uploaded in [PR #3](https://github.com/govrahul/aipi510_project2/pull/3). It is now closed after the branch rename; active review is [PR #4](https://github.com/govrahul/aipi510_project2/pull/4).
- Review branch `sam/athlete-data-and-eda` (renamed from the original branch at Sam's request) starts from PR #2's head so it includes the partner's unmerged work. Its PR is intended to target the partner branch for a compact review. Merge PR #2 first and retarget the new PR to main afterward as needed. Neither partner PR #2 nor the review PR was merged by this work.
- The new branch is the intended local checkout. Check `git status`, `git remote -v` and current PR state before further work; this snapshot is not a live status query.

## Verified progress and results

1. Cloned the requested repo into the project folder and reviewed all original Python scripts, CSV schemas/content and both partner PR states.
2. Read the Word rubric: scripts rather than notebooks, hypotheses/design, justified power, assumption checks, p-values/CIs/effect sizes, raw/clean data or explanation, reproducible README, partner PR participation, written report and an eight-minute presentation on November 3.
3. Read the PDF: title/background/hypotheses/design/power and football result drafted; abstract, basketball result, cross-sport result, interpretation, limitations and conclusions incomplete. Source data for basketball is not in either branch inspected.
4. Reproduced football: N=100, R²=.321, social coefficient .2067, HC1 two-sided p=.000327052, 95% CI [.0939,.3194]. HC3 gives the same coefficient, p=.001548, CI [.0787,.3346]. These are provisional selected-sample associations. Exact code-generated tables and sensitivities are under `reports/`.
5. Audited inherited data: no duplicate player-school rows; original source fields/log transforms preserved. 41 zero PPA values, 30 nonzero PPA values on defense/OL, no saved API identities/match evidence, 99 Power-4 players and one other. Values require recollection and review. No rows were silently corrected.
6. Legacy sampling thresholds produce strata of 266/479/255 because of ties. The new sample importer uses deterministic rank strata of 250/500/250 and a seed-510 25/50/25 sample. Do not overwrite the inherited sample when reproducing the PDF.
7. Added partial-term power scenarios: with six total predictors, alpha=.05/3, power=.8, independent homoskedastic approximation needs N=527 for partial f²=.02, N=213 for .05, N=73 for .15. The old overall-R² power numbers of 41/46 do not establish adequate power for the social term/interaction.

## Changes made

| Path | Purpose |
|---|---|
| `README.md` | Setup, reproducible commands, collection instructions and limitations. |
| `PROJECT_CONTEXT.md` | This handoff; mirrored in the parent project's README. |
| `docs/historical_data_sources.md` | Follow-up source assessment: official recruiting schemas, reported-offer example, signing archives, Social Blade history, Wayback, remaining gaps and a bounded feasibility pilot. |
| `docs/basketball_collection.md` | November 1 actual basketball performance collection, fallback source rationale, data counts, cleaning, commands and pending NIL/social inputs. |
| `scripts/collect_basketball_open_stats.py` | Download/cache documented SportsDataverse ESPN exports, aggregate player-team-season statistics and join season-specific D1/conference membership. |
| `Tests/test_basketball_collection.py` | Four new offline tests for denominators, missingness, duplicate identities, timing, team membership and transfers. |
| `docs/research_design.md` | Distinguishes two questions, hypotheses/design, audit findings, source corrections, rubric gaps and ordered next steps. |
| `scripts/audit_data.py` | Recomputes the inherited football audit without modifying inputs. |
| `scripts/analyze_football.py` | Replicates HC1/HC3, adds clearly exploratory no-PPA and largest-audience sensitivity models, coefficient tables, diagnostics and plot. |
| `scripts/power_sensitivity.py` | Partial-F power for one added social or interaction term, with explicit assumptions. |
| `scripts/prepare_sample.py` | Imports an authorized CSV; parses valuations, deterministic rank strata, seeded sampling and source manifest. Not a working live Sideline scraper. |
| `scripts/collect_performance.py` | Official CFBD/CBBD requests, TLS on, local raw caches/manifests, exact identity matching, explicit review status and missing performance retained. |
| `scripts/analyze_prepost.py` | Per-sport scholarship-offer interaction workflow; checks timing, variation, identifiers, rank and cluster count. No real data/result yet. |
| `Data/templates/` | Header-only contracts for basketball enrichment and historical decisions. Not observations. |
| `Data Cleaning/football_add_stats.py` | Replaced insecure/zero-imputing implementation with compatibility wrapper to safe collector. Now needs explicit CLI season/sample/output. |
| `Tests/football_diagnostics.py` | Fixed HC3 label/code mismatch and misleading assumption claims. |
| `requirements.txt`, `.env.example`, `.gitignore` | Explicit dependencies, credential template, ignore real credentials and new licensed bulk exports. |
| `Tests/test_pipeline.py` | Seven offline tests: matching/missingness, schema, sampling, timing, outcome variation, clustered interaction and power calculation. Synthetic fixtures stay separate from evidence. |
| `reports/` | Generated aggregate audit, coefficient CSV, diagnostic JSON/PNG, results prose, power table and collection status. |

Original football CSVs and `power_analysis.py` remain unchanged. No DOCX/PDF report or presentation was edited/created, no raw social platform data was scraped, and no scholarship or basketball empirical result was invented.

## Collection status and unresolved gaps

- Sideline rankings and robots requests from HTTP returned Cloudflare denial; Chrome showed the same denial. No attempt was made to bypass it. Its published usage permits attributed class citations but restricts redistribution of bulk data. Existing committed CSV permissions/source dates are unknown. Preserve them for replication while verifying provenance with the owners; do not add more bulk data to public Git without rights.
- Sam confirmed on November 1 that no API key is available yet. No CFBD/CBBD key was configured in the project or task environment. Live performance collection could not run. Store keys locally in ignored `.env`, never in chat/code. Read the README for variable names and commands. API schemas were reviewed at the official `/api-docs.json` endpoints. CBBD season is the **ending year** (`2026`=2025–26); football year is the season year (`2025`).
- New performance collector handles both sports and caches raw responses with dates/hashes. It does not claim live validation. Offline fixtures passed. Exact name+team+position matching leaves transfers/position aliases unresolved unless reviewed. A verified `Performance College` or API ID can resolve identities; no fuzzy auto-acceptance.
- Basketball valuation/follower sample is absent. New importer and enrichment headers are ready. Basketball performance data was actually downloaded November 1 from the public SportsDataverse ESPN exports: 196,876 raw rows, aggregated to 5,680 D1 player-team records (5,677 distinct IDs) across 365 teams for 2025–26. See `docs/basketball_collection.md`. These are supplemental box-score statistics, not CBBD PORPAG. A fully validated basketball regression and cross-sport interaction analysis still need implementation after real input data and metric/control choices are established.
- Historical scholarship/offer outcomes, candidate pool, verified non-offers and pre-decision follower measures are absent. The pre/post script intentionally refuses unusable data. Finding public offers alone does not solve the negative-outcome problem. Potential sources are assessed in `docs/historical_data_sources.md`: Social Blade documents a paid Instagram history option of up to ten years when available, and Wayback is another candidate. No athlete-specific historical coverage or usable joined dataset has been established.
- Demographics beyond source-supplied grade/position/school are not collected. Do not infer sensitive traits from names or pictures.
- The draft misstates the 2021 policy as congressional legalization and misidentifies Bronny James's school as Arizona (official roster is USC). Contract/benching anecdotes and the attached Reggie Jones social post are unverified here; treat them only as leads. Source corrections are linked in the design document.

## Resume commands

From the cloned repo, activate a virtual environment with requirements installed, then:

```bash
python -m unittest discover -s Tests -v
python scripts/audit_data.py
python scripts/analyze_football.py
python scripts/power_sensitivity.py
```

To collect once a key and authorized source CSV are available, use the README's exact commands. New raw data defaults to ignored `Data/private/`. Review identities, observation dates, missingness, source value types and publication rights before modeling or uploading. The original `Data/sample_data.py` will overwrite the inherited sample if run.

Validation performed on macOS Python 3.14 with pandas 3.0.5, NumPy 2.5.2, scipy 1.18.0, statsmodels .14.6, requests 2.33.1 and matplotlib 3.11.1; seven unit tests passed and all new available-data analysis scripts ran. Synthetic pre/post fitting was tested but no real pre/post data exists. The generated football diagnostic plot was visually reviewed. Future reruns may show different summary timestamps, not different estimates.

## Follow-up source research

After Sam confirmed no historical data was available, reviewed official CFBD/CBBD recruiting documentation and schemas, an actual 247Sports high-school recruiting profile, a university signing announcement, Social Blade API history documentation, and Internet Archive API/CDX documentation. The recruiting schemas have no offer-history/date fields. Social Blade is a plausible historical-count provider but requires paid access and profile-specific coverage verification. No purchase, outreach or historical athlete download occurred. Meta's primary Insights page returned HTTP 429, so its current retention limits were not asserted. The new source assessment separates verified documentation from untested coverage and lists the conditions needed to run the pre/post model.

## November 1 basketball collection

Sam requested starting basketball collection to mirror the PDF/football workflow. Re-read the PDF and confirmed the top-1,000 NIL frame, seed/sample plan and CBBD performance source. Sam said no API key is available. Sideline HTTP still returned 403. To advance the performance layer, downloaded the documented ESPN box-score export and season-specific team membership from SportsDataverse using system curl with TLS verification enabled. Cached raw files, hashes and retrieval metadata in ignored `Data/private/basketball/`. Aggregated regular/postseason appearances into all-team and D1-only CSVs. DNP rows do not inflate denominators; no-appearance performance remains missing; IDs and historical teams stay separate. Source membership identifies 365 D1 teams. The D1 output has 5,680 rows, including 661 with no appearances and 5,019 with appearances. Two primary-source scoring spot checks passed. These data are not a NIL sample. No basketball NIL regression was run.

Extended the official CBBD/CFBD collector with `--download-only` and `--env-file` so it can collect the full performance layer once a key is available. Added pyarrow as a dependency and four meaningful aggregation tests; the full suite now has 11 passing tests. Published aggregate audit is `reports/basketball_collection_audit.json`; complete instructions are `docs/basketball_collection.md`. Reproduction code and aggregate reports are uploaded on the same review branch; raw/player-level files remain local and ignored.

## Revised November 1 sampling and social request

Sam requested Instagram follower collection options and changed new basketball work to **1,000 players, 250 from each NIL quartile**, sorted by strata. This is different from the inherited football 100-player 25/50/25 allocation. Preserve that earlier file. `sample_quartiles.py` samples from the complete supplied frame, records tie handling, population counts, probabilities and weights, and does not silently truncate to top 1,000. `build_basketball_nil_sample.py` samples by real NIL first, left-joins performance and retains missing rows. A genuine current basketball NIL frame is still absent, so that final file has not been produced.

Sam also requested 2018 and 2019 comparators for football and basketball with a standardized replacement sampling metric. Asked whether they prefer performance or recruiting strength; no answer was available at implementation time. Built **provisional** performance-based samples, not a confirmed final design or regression outcome. Season-start alignment: basketball 2018 uses ending key 2019, basketball 2019 ending key 2020; football uses starting keys 2018 and 2019. Downloaded historical box scores and season-specific memberships, plus football rosters. Four 1,000-athlete CSVs, 250 per quartile, are local under `Data/private/comparators/SPORT_YEAR/`. The metric is within-position/season percentile of recorded season points for basketball or passing/rushing/receiving yards for football. Football production coverage is restricted to QB, RB/FB, WR and TE; all other roster positions remain in the full frames with missing proxies. Unknown basketball positions remain in the full frame but are not assigned a score. Full sources, hashes and frame sizes are in `reports/historical_comparator_collection.json`.

`collect_instagram_counts.py` supports current Meta counts and authorized Social Blade response replay; historical daily counts must precede the target within a defined lag. Verified handle/evidence, timestamps/precision, status and raw hashes are retained; no handle guessing or missing-to-zero imputation. Pre-NIL rows without a target date refuse current counts. Paid live requests require an explicit operator flag and have not been executed. Meta's reference page returned 429, so live permissions/approval setup remain unverified. No Instagram credentials or verified handle file exists, and **no actual Instagram counts were collected**.

The workbook `outputs/nil-quartiles-20261101/historical_quartile_samples.xlsx` presents four provisional samples with an overview and count formulas. Exporter is in `scripts/export_cohort_workbook.mjs`, using bundled artifact-tool, with visual checks. `docs/stratification_and_instagram.md` explains all current methods and remaining limitations. New code plus existing collectors are uploaded on PR #3. Seventeen offline tests passed, including new sampling, tie, missingness, historical-date and NIL-before-performance contracts.

A standardized production proxy can organize samples but cannot replace NIL as the historical regression outcome and still test a change in the same social coefficient. Common outcome, scope and historical follower measurements remain unresolved. No causal NIL or pre/post result was run.

## Next actions in priority order

1. Review and merge partner PR #2 as appropriate; review the new PR's data/method changes separately.
2. Verify inherited performance identities and provenance; configure the API key locally and recollect performance. Do not trust the old PPA column as a validated control.
3. Obtain an authorized basketball frame, sample/enrich with timestamped social observations, join CBBD performance and audit. Then implement/run basketball and cross-sport models with justified controls and inference.
4. Follow the source assessment and bounded pilot in `docs/historical_data_sources.md` to investigate feasibility of the original historical scholarship design. If data is available, populate the template, justify sampling/power, fit per-sport interactions and run additional diagnostics. Otherwise state the original question is unanswered.
5. Finish the report and slides with audited results, accurate background, limits and reproducibility. Keep the distinction between valuation association and scholarship policy effects visible.

When updating this handoff, state actual actions/results and remaining blockers. Do not mark pending collection or unrun models as completed.
