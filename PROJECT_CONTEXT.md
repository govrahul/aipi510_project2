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
- New work is uploaded in [PR #3](https://github.com/govrahul/aipi510_project2/pull/3), open for review.
- New branch `codex/basketball-data-and-analysis` starts from PR #2's head so it includes the partner's unmerged work. Its PR is intended to target the partner branch for a compact review. Merge PR #2 first and retarget the new PR to main afterward as needed. Neither was merged by this work.
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

## Next actions in priority order

1. Review and merge partner PR #2 as appropriate; review the new PR's data/method changes separately.
2. Verify inherited performance identities and provenance; configure the API key locally and recollect performance. Do not trust the old PPA column as a validated control.
3. Obtain an authorized basketball frame, sample/enrich with timestamped social observations, join CBBD performance and audit. Then implement/run basketball and cross-sport models with justified controls and inference.
4. Follow the source assessment and bounded pilot in `docs/historical_data_sources.md` to investigate feasibility of the original historical scholarship design. If data is available, populate the template, justify sampling/power, fit per-sport interactions and run additional diagnostics. Otherwise state the original question is unanswered.
5. Finish the report and slides with audited results, accurate background, limits and reproducibility. Keep the distinction between valuation association and scholarship policy effects visible.

When updating this handoff, state actual actions/results and remaining blockers. Do not mark pending collection or unrun models as completed.
