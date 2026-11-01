# Research design and remaining work

## What can be answered now

The available data describes a selected current football NIL valuation frame. The defensible question is whether log Instagram reach is associated with log estimated NIL valuation within that frame, conditional on specified measured covariates. The inherited regression is reproducible, but performance values have unresolved provenance. The new sensitivity models omit PPA rather than treating its values as verified.

The original user question is different: did the weight on social reach in colleges' scholarship decisions change after NIL? There are no scholarship outcomes, decision dates or historical social measurements in the existing CSVs. A sample restricted to current college athletes or high-valued NIL athletes cannot estimate selection into scholarships. Do not silently rename NIL valuation as scholarship value or treat it as confirmed NIL payment.

The course calls for a small experiment. This study is observational; there is no random assignment. Confirm that an observational policy comparison satisfies the course expectation before representing it as an experiment. None of the analyses establishes causal NIL effects or whether compensation is equitable.

## Primary before and after design

Use a defined recruit population, ideally comparable recruiting cohorts before 2021 and after 2021, with eligibility and sampling decided before examining results. For an initial design, consider 2018–2020 and 2022–2024, discuss COVID-era disruption, and exclude or separately study the transition cohort. A recruiting-class year is not an exact offer date. Obtain actual decision dates wherever possible.

The observation unit is an athlete-school decision. For each sport, fit:

```text
offer = intercept + b1*log(1+historical_followers) + b2*post
        + b3*log(1+historical_followers)*post
        + athletic_score + position controls + school controls
        + linear calendar-year trend + error
```

H0: b3=0. H1: b3≠0. The interaction measures a change in association on the probability scale. The linear probability model matches the requested linear regression; fitted probabilities can fall outside [0,1]. A logistic interaction with marginal effects is a future sensitivity check, not a completed result. Cluster at athlete for multiple school decisions; school dependence may require two-way clustering or a redesign with enough schools. Pre-register the final hypothesis family and multiplicity rule. The script uses a 95% interval per sport; adjust the family if both sport results are treated as confirmatory.

Public recruiting ratings and high-school performance can serve as athletic covariates if measured before decisions. College statistics observed afterward would leak outcomes into predictors. Recruitment stars may themselves reflect recruiting decisions, so justify their timing and interpretation. Standardize metrics within sport/cohort if scales change. Do not combine raw football PPA and basketball PORPAG into one generic numeric scale.

Collect both genuine positive and negative decisions from a defined candidate pool. Recruiting commitment and college attendance do not establish scholarship receipt. A missing offer entry is not evidence of no offer. If negatives cannot be verified, redesign the outcome (for example, a documented offer count) and state that it answers a narrower question. Current followers can be a consequence of college exposure, athletic success and NIL, so archived decision-time values are essential. The follow-up [historical source assessment](historical_data_sources.md) identifies Social Blade and archive candidates, but no athlete-specific historical coverage or usable joined dataset has been established.

The 2025 House settlement introduced another structural change affecting direct payments and scholarships. Avoid conflating that change with July 2021, or explicitly model it with sufficient data. All-schools before/after comparisons also confound NIL with time trends, transfers, COVID eligibility and platform growth. A comparison group or defensible policy exposure design is needed for a stronger causal claim.

## Existing football audit

- 1,000 frame rows, 100 sampled/enriched/modeling rows, no duplicate player-school identities and no blank modeled fields. Transformations reproduce.
- 41 PPA values equal zero. The old code uses zero for missing matches and freshmen, so zeros do not distinguish observed no contribution from unavailable performance.
- 30 nonzero PPA values belong to defense or offensive-line rows. Source IDs, matched names/teams, positions and API responses were not saved. These are review flags, not proof that each row is wrong. Recollect and validate identities before any performance-controlled substantive claim.
- 99 Power-4 players versus one other player: conference inference depends heavily on one observation. HC3 cannot create support that the sample lacks.
- The old 25/50/25 sample uses value thresholds. Valuation ties create strata of 266/479/255, not exact quarters, so the selection rates differ slightly. New rank strata fix the 250/500/250 counts for future samples. Preserve the inherited sample for replication; do not quietly replace it.
- Sampling within the top 1,000 conditions on the outcome and excludes lower-valued players. Quota allocation does not remove that selection. A simple random sample is not inherently biased merely because valuations are skewed.
- Follower observation dates, exact source URLs, source value types and performance match provenance are absent. Current methodology cannot retroactively establish how undated older values were generated.

The inherited social coefficient is 0.2067 (HC1 p=0.000327, 95% CI [0.0939,0.3194]). HC3 widens the interval to [0.0787,0.3346], p=0.00155. Exploratory models that omit unverified PPA and add recruitment-star main effects and position controls produce a social coefficient of 0.2953; removing the largest audience gives 0.2316. These are different specifications, not proof of a corrected causal estimate. Detailed outputs are generated by code in `reports/`.

## Power and reporting

The partner's R²=0.35 calculation evaluates overall model fit. It does not establish power to detect one social slope or a change in slope. Plan the tested term using partial f²=(R²full−R²reduced)/(1−R²full), separate from overall R². At alpha=.05/3 and 80% power, the independent homoskedastic partial-F approximation with six total predictors requires N=527 for partial f²=.02, N=213 for .05, and N=73 for .15. These effects are scenarios, not literature estimates or evidence of achieved power. Clustering, sparse cells, imperfect measurement and missingness generally require additional planning, preferably design-based simulation after the sampling design is specified.

Report exact nonzero p-values, effect sizes and confidence intervals. The existing statsmodels summaries use two-sided tests; the PDF describes directional alternatives. Choose and document a consistent hypothesis before seeing new results. Do not halve p-values after inspecting signs. For a three-test Bonferroni family, .0167 tests correspond to 98.33% two-sided intervals; conventional 95% intervals can also be shown if labeled. A normality test or n=100 does not establish all OLS assumptions. HC3 addresses a variance problem under other assumptions, not data errors or dependence.

## Historical source assessment

Sam confirmed there is no existing historical dataset. See [historical_data_sources.md](historical_data_sources.md) for verified provider capabilities, access requirements, gaps and a proposed coverage pilot. The documented recruiting APIs provide covariates and commitments rather than complete dated offer histories. No paid data was purchased or athlete history acquired.

## Collection priority and sources

1. Verify football source dates and the API identities behind inherited performance values. Configure a local API key and replay the new collector. No API key was available in this session.
2. Obtain a source-authorized basketball valuation frame and provenance. Python and browser access to Sideline rankings returned a Cloudflare denial. No new basketball player dataset was acquired or fabricated.
3. Use `prepare_sample.py`, then collect Instagram observations, date/evidence and recruitment ratings. Do not fill missing follower counts with zero. Obtain and review CBBD season statistics with `collect_performance.py`.
4. Fit basketball and a cross-sport social-slope comparison only after the input audit passes. A full new basketball/cross-sport analysis is not yet implemented or run. Account for sport-specific performance/position definitions, roster selection, school dependence and comparable valuation dates/types. Do not simply copy football's premium-position list or Power-4 basketball assumptions.
5. Independently investigate historical scholarship decisions and archived social metrics. If feasible, populate the pre/post template and run the per-sport interaction model. If unavailable, transparently present the current-valuation study as the narrower result and the original policy question as unresolved.

Official references reviewed October 31, 2026:

- [NCAA policy history](https://www.ncaa.org/about-us/history/): July 1, 2021 policy implementation. The PDF's statement that Congress legalized NIL in 2021 should be replaced with a sourced description of the NCAA interim policy and state-law context.
- [NCAA 2025 roster and scholarship changes](https://www.ncaa.org/news/media-center-di-board-of-directors-formally-adopts-changes-to-roster-limits/): a separate policy change, effective July 2025.
- [Sideline methodology](https://thesideline.co/data/how-we-estimate): distinguishes estimates, published benchmarks and deals. Its current allocator uses position, class and recruiting ratings; game stats/followers are not inputs to that allocator. Published benchmarks may follow other providers' methods; check their provenance separately.
- [Sideline usage](https://thesideline.co/data/usage): class projects may cite individual figures with attribution; bulk redistribution is restricted. Existing CSV rights have not been verified. Do not add new bulk exports to public Git by default.
- [CBBD getting started](https://api.collegebasketballdata.com/getting-started), [stats API](https://api.collegebasketballdata.com/api/stats), [season conventions](https://api.collegebasketballdata.com/data-availability): requires bearer authentication; `season=2026` means 2025–26. Schema reviewed at `/api-docs.json`.
- [CFBD API schema](https://api.collegefootballdata.com/api-docs.json): `/ppa/players/season`, `year`, player ID, position and average PPA.
- [statsmodels power implementation](https://www.statsmodels.org/stable/_modules/statsmodels/stats/power.html): noncentral-F planning conventions. New partial-term calculation is cross-checked against FTestPowerF2 in offline tests.
- [USC Bronny James roster](https://usctrojans.com/sports/mens-basketball/roster/bronny-james/15863): the PDF incorrectly identifies his college as Arizona. The Underwood contract/benching and valuation anecdotes are unverified here; remove them or replace them with dated primary evidence. The attached Reggie Jones social post is motivation, not verified analytical data.

## Rubric status

| Requirement | Status and next action |
|---|---|
| Title, abstract, background | Partner PDF has title/background; abstract empty. Correct factual errors and align title with actual outcome. |
| Hypotheses and design | Current NIL hypotheses exist; original pre/post design documented separately. Explain observational design and controls. |
| Power analysis | Original overall-model calculation reproduced; new term-specific sensitivity table generated. Final design-specific justification still needed. |
| Collection and cleaning scripts | Football source data present; safe performance collector/importer and audit added. Basketball and historical data still missing. |
| Tests, assumptions, effect sizes, p, CI | Football replication and sensitivity outputs generated. Basketball and pre/post empirical results unavailable. |
| Interpretation, limitations, conclusion | Blank sections in PDF; use audited findings and the distinctions above. Do not claim a NIL policy effect. |
| References | Existing references plus primary corrections above; verify any anecdote used. |
| Repo reproducibility, raw/clean data | README, scripts, requirements, tests, generated reports. Exact original collection cannot be reproduced without source provenance. |
| Collaboration | Partner PR #1 merged; PR #2 open at inspection. New work stays on its own review branch. |
| Presentation | Rubric specifies maximum 8 minutes, November 3. No deck was requested or created in this work. |

## November 1 collection update

Basketball performance data has now been collected from a documented SportsDataverse ESPN export as a supplemental source while Sam has no CBBD key. [Collection details](basketball_collection.md) report 5,680 D1 player-team records across 365 teams for 2025–26, source hashes, cleaning and spot checks. The statements above about missing basketball data apply to the NIL/follower sample and CBBD performance collection; those remain missing. No basketball NIL or cross-sport regression has run.
