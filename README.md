# Social Media, NIL Valuation, and College Athlete Selection

**AIPI 510 --- Module Project 2**\
**Authors:** Rahul Govil and Sam Teshome\
**Analysis snapshot:** November 2, 2026

We asked how strongly a college athlete's Instagram following is associated
with their published name, image and likeness (NIL) valuation, and whether
that association differs between men's basketball and football. The NCAA's
interim NIL policy took effect on **July 1, 2021**.

## Main findings

**Main model --- one formula, fitted separately to each sport**
(`ln NIL ~ ln(1 + followers) + performance percentile + no-stats flag + years in college`, HC3 errors; 100 players per sport, so two regressions)

| | Basketball | Football |
|---|---|---|
| Higher NIL for twice the followers | **+35%** (95% CI 18--54%, p < 0.001) | **+17%** (95% CI 7--27%, p < 0.001) |
| Followers' share of what the model explains | **64%** | **69%** |
| Last-season performance's share | 12% | 20% |
| Years in college's share | 24% | 11% |
| Model R² | 0.23 | 0.30 |
| Without the 25 highest-valued players | +1% (p = 0.86) | +4% (p = 0.05) |

Follower β: basketball 0.431 (95% CI 0.235--0.628), football 0.221
(0.093--0.350). The two slopes do not differ significantly (pooled
interaction test, p = 0.079).

**Sport-specific models** (each sport on its own, adding variables only
that sport has; [section 6.2](#62-sport-specific-models)):

| | Added variables | Twice the followers | R² |
|---|---|---|---|
| Football | recruiting stars, freshman, stars × freshman, position group | **+21%** (β 0.274, p = 0.003) | 0.36 |
| Basketball | points per game, freshman, big conference, forward/center | **+9%** (β 0.124, p = 0.32, not significant) | 0.54 |

In basketball, playing in one of the five largest conferences (ACC, Big Ten,
Big 12, SEC, Big East) goes with about **+509%** NIL value (p < 0.001) and
explains half the variation by itself.

In plain terms:

1. In the main model, Instagram following is the strongest factor we
   measured in both sports, accounting for about two thirds of what the
   model explains.
2. The sport-specific models qualify that. Football's follower effect holds
   after adding recruiting stars and position. In basketball, conference
   matters far more, and big-conference players also have more followers,
   so much of basketball's follower effect reflects conference.
3. The effect is concentrated at the top of the market: without the
   highest-valued quarter of players it nearly disappears.
4. The basketball slope is larger, but the difference between sports is not
   statistically significant (p = 0.079), so we do not claim one sport
   rewards followers more.
5. This is an observational, single-snapshot association. It does not show
   that followers cause higher NIL value or that NIL changed recruiting.

## Where to find everything

| What | Where |
|---|---|
| Written report (PDF / editable Word) | [`deliverables/project2_report.pdf`](deliverables/project2_report.pdf), [`deliverables/project2_report.docx`](deliverables/project2_report.docx) |
| Presentation (8 min) and speaking script | [`deliverables/project2_presentation.pptx`](deliverables/project2_presentation.pptx), [`deliverables/presentation_script.md`](deliverables/presentation_script.md) |
| Rubric checklist | [`deliverables/submission_checklist.md`](deliverables/submission_checklist.md) |
| Final figures (bar charts) and the tables behind them | [`figures/`](figures/) ([guide](figures/README.md)), [`figures/figure_data/`](figures/figure_data/) |
| Main model code and results | [`scripts/make_unified_figures.py`](scripts/make_unified_figures.py) → [`unified_model_results.json`](figures/figure_data/unified_model_results.json), [`unified_model_diagnostics.json`](figures/figure_data/unified_model_diagnostics.json) |
| Basketball-specific model | [`scripts/make_unified_figures.py`](scripts/make_unified_figures.py) → [`basketball_only_model.json`](figures/figure_data/basketball_only_model.json) |
| Football-specific model and football robustness fits | [`scripts/summarize_deliverable_results.py`](scripts/summarize_deliverable_results.py) → [`reports/deliverables/model_statistics.json`](reports/deliverables/model_statistics.json) |
| Power analysis | [`scripts/power_sensitivity.py`](scripts/power_sensitivity.py), partner's original in [`power_analysis.py`](power_analysis.py) |
| Cleaned analysis data | [`Data/football_modeling_data.csv`](Data/football_modeling_data.csv), [`Data/curated/basketball_instagram_100.csv`](Data/curated/basketball_instagram_100.csv) |
| Raw data and how each file was made | [section 3.4](#34-raw-and-cleaned-data) |
| Collection and cleaning scripts | [`scripts/`](scripts/) (`collect_*`, `prepare_*`, `import_*`), [`Data Cleaning/`](Data%20Cleaning/) |
| Supplementary models (football replication, robustness, EDA) | [section 6.3](#63-supplementary-football-replication-and-robustness), [`reports/eda/`](reports/eda/), [`Tests/football_test.py`](Tests/football_test.py) |

## Reproduce the final analysis (run order)

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

python -m unittest discover -s Tests -v          # offline tests
python scripts/summarize_deliverable_results.py  # football-specific model and football robustness fits
python scripts/power_sensitivity.py              # power analysis
python scripts/make_manuscript_figures.py        # figures 1-6 and the transfer-trend table
python scripts/make_unified_figures.py           # main model, basketball-specific model, post hoc tests, figures 7-11
python scripts/build_project_report.py           # rebuilds deliverables/project2_report.docx
```

The football steps run from checked-in data. The two figure scripts also
read basketball box scores from `Data/private/basketball/`, which is not in
Git (size and source terms) and is rebuilt with
`scripts/collect_basketball_open_stats.py`. Full details are in
[section 4](#4-reproducibility).

------------------------------------------------------------------------

## 1. The problem

The NCAA's interim NIL policy, effective July 1, 2021, changed the
environment in which college athletes could receive compensation for the
use of their name, image, and likeness \[1\]. Social-media audiences may
create commercial opportunities, but they may also reflect athletic
success, visibility, school exposure, and other factors.

This creates two related---but distinct---research questions:

1.  **Current NIL valuation:** Among college athletes with reported NIL
    valuations, is a larger social-media audience associated with a
    higher estimated NIL valuation?
2.  **College selection before and after NIL:** Did the relationship
    between social-media reach and college scholarship or recruiting
    decisions change after NIL implementation?

These questions require different outcomes and data. A reported NIL
valuation is an estimate of commercial value; it is **not necessarily a
verified payment, scholarship offer, or recruiting decision**. The
completed analysis addresses the first question in samples of 100
basketball and 100 football players. The second question remains unestimated because comparable
historical follower measurements and verified decision outcomes are not
available.

## 2. What this project does

-   Collects a 100-player men's basketball sample (25 per NIL quartile of
    all 5,348 Sideline listings) with Instagram follower counts and
    last-season points per game.
-   Reuses the partner's 100-player football sample, with an audit of its
    sources and performance field.
-   Fits one main model (the same formula in each sport), with HC3 errors,
    dominance analysis, assumption checks and post hoc tests.
-   Fits a sport-specific model for each sport that adds variables only
    that sport has.
-   Keeps the partner's original football model and several robustness
    fits as clearly labelled supplementary results.
-   Provides scripts (no notebooks), aggregate outputs, input hashes and
    offline tests so every number can be rerun.

## 3. Data collection and sources

The project combines inherited NIL/social-media data with public roster,
performance, recruiting, and career-source layers. The source files are
not all equivalent: some are inputs to the completed regression, while
others are supporting data collected to assess whether future
comparisons are feasible.

### 3.1 Completed football valuation sample

The inherited football data are attributed by the partner collection to
**The Sideline NIL tracker** \[2\]. The available files form nested
layers:

1.  A ranked frame of 1,000 football players.
2.  A 100-player sample drawn from that frame.
3.  Enriched/model records for those same sampled players.

The three layers are not independent samples and should not be
concatenated as 1,200 observations. The partner sampling code uses seed
`510` and valuation tiers to select 25, 50, and 25 players. Because
valuation ties affect the tier boundaries, the resulting tier
populations are 266, 479, and 255; this is close to proportional
allocation, not deliberate oversampling of the top tier.

The modeled sample contains 100 players across 39 schools, including 99
Power 4 players. Reported NIL estimates range from \$350,000 to
\$5,000,000.

**Important provenance limitations:**

-   The original bulk snapshot date and valuation methodology have not
    been independently verified.
-   The original follower observation dates and some follower/player
    identity evidence are unavailable.
-   The Sideline source could not be freshly retrieved during the later
    collection work (HTTP 403), so the project did not replace it with
    an unrelated or incomplete source.
-   The NIL values are estimates, not confirmed athlete compensation.

The inherited files and their hashes are preserved for replication. The
football input SHA-256 reported in the project report is:

``` text
82e228c40758266338aee4e58a44c55f0217e0355b0490e871b5ae9f05a2c6f7
```

### 3.2 Public roster and performance data

Additional collection scripts use public ESPN/SportsDataverse data
releases and related sport-specific repositories \[3--5\]. These sources
support roster, game, recruiting-candidate, and performance data
collection. Source identifiers, request metadata, and SHA-256 hashes are
retained in collection manifests and audit outputs.

Examples of supporting data layers include:

-   Football player/team/season roster and performance exports.
-   Basketball player-game and team-membership exports.
-   Recruiting candidate information, where available.
-   Basketball model-derived performance metrics and football
    performance measures.
-   Player crosswalks and draft-source links for exploratory
    career-history auditing.

These data layers do **not** automatically become valid NIL or
scholarship outcomes. Matching is based on accepted source IDs or
reviewed identity evidence; ambiguous matches and unsupported values are
kept missing rather than silently filled.

For the 2025--26 men's basketball performance collection, the
ESPN/SportsDataverse export was aggregated to 5,680 Division I
player-team-season records across 365 teams. Points per game from this
layer is the basketball performance measure in the two-sport model.

### 3.2a Basketball NIL and Instagram sample

`scripts/collect_sideline_safari.py` collected the full Sideline men's
basketball listing (5,348 players, retrieved November 2, 2026) through
normal Safari browsing and saved 108 hashed page snapshots.
`scripts/prepare_basketball_social_sample.py` then froze 100 players, 25 at
random from each NIL quartile of the full listing (seed 510), *before* any
follower counts were looked up. Eighty follower counts were read directly
from public Instagram profiles (`scripts/collect_instagram_browser.mjs`,
`scripts/import_instagram_browser_receipts.py`) and the other 20 were
supplied by Sam from manual checks
(`scripts/import_manual_basketball_followers.py`); the
`Instagram_Count_Provenance` column records which is which. See
[`docs/basketball_instagram_100.md`](docs/basketball_instagram_100.md).

### 3.3 Missingness and data-quality rules

The collection and analysis workflow follows several rules:

-   Missing, unknown, and observed-zero values are distinct. A missing
    performance value is not automatically converted to zero.
-   The inherited football performance field (PPA) has audit flags: 41
    zero values and 30 nonzero values on defensive/offensive-line
    players, where the collected offensive metric may not apply. These
    values are not treated as validated performance measurements.
-   Ambiguous player matches remain unresolved rather than being
    accepted from a name-only match.
-   A missing draft crosswalk is unknown; it is not proof that a player
    was undrafted.
-   Historical NIL and follower values are not imputed as zero when the
    source data do not exist.
-   Demographic characteristics are not inferred from names or
    photographs.
-   Newly collected player-level files and credentials are kept
    local/ignored by Git where required; aggregate audits, scripts, and
    source descriptions are available for review.

### 3.4 Raw and cleaned data

  -----------------------------------------------------------------------
  File                                         Stage     Contents
  -------------------------------------------- --------- ----------------
  `Data/football_top1000.csv`                  Raw       Top 1,000 football
                                                         NIL valuations
                                                         (partner pull)

  `Data/football_sample_100.csv`               Raw       100-player
                                                         stratified sample
                                                         (seed 510)

  `Data/NIL and Player History Data -          Raw       Partner enrichment
  Football Sample.csv`                                   of the sample

  `Data/football_modeling_data.csv`            Cleaned   Football analysis
                                                         file used by every
                                                         football model

  `Data/private/basketball_instagram_100/`     Raw,      Full 5,348-player
                                               local     listing, page
                                                         snapshots and
                                                         browser receipts

  `Data/private/basketball/`                   Raw,      ESPN/SportsDataverse
                                               local     box scores and
                                                         rosters by season

  `Data/curated/basketball_instagram_100.csv`  Cleaned   Basketball analysis
                                                         file (100 players,
                                                         NIL, followers,
                                                         provenance)

  `figures/figure_data/`                       Derived   Aggregate tables
                                                         behind every figure
                                                         and the model
                                                         results (JSON)
  -----------------------------------------------------------------------

`Data/private/` is ignored by Git because of file size and source terms.
It is rebuilt by the collection scripts in section 4.4; its hashes are in
the collection manifests under `reports/`.

See [`reports/eda/README.md`](reports/eda/README.md),
[`docs/basketball_collection.md`](docs/basketball_collection.md), and
the source manifests under `reports/` for more detail.

## 4. Reproducibility

### 4.1 Requirements

-   Python 3.11 or newer
-   Packages listed in [`requirements.txt`](requirements.txt)
-   Git

### 4.2 Set up the environment

Run the following commands from the repository root:

``` bash
git clone https://github.com/govrahul/aipi510_project2.git
cd aipi510_project2

python3 -m venv .venv
source .venv/bin/activate

python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

On Windows, activate the environment with:

``` powershell
.venv\Scripts\activate
```

### 4.3 Run the offline tests and football analysis

``` bash
# Run the offline test suite
python -m unittest discover -s Tests -v

# Audit the available input data
python scripts/audit_data.py

# Reproduce the football regression and diagnostics
python scripts/analyze_football.py

# Reproduce the partial-term power sensitivity calculations
python scripts/power_sensitivity.py

# Reproduce the exploratory data analysis and aggregate figures
python scripts/run_eda.py

# Football model statistics used in the report (writes reports/deliverables/model_statistics.json)
python scripts/summarize_deliverable_results.py

# Report figures 1-6 and the roster/transfer trend table
python scripts/make_manuscript_figures.py

# Two-sport model, dominance shares, assumption checks and post hoc tests (figures 7-11)
# Add --cached to redraw the figures without rerunning the 1,000-draw bootstrap.
python scripts/make_unified_figures.py

# Rebuild the written report (deliverables/project2_report.docx and reports/deliverables/project2_report.md)
python scripts/build_project_report.py
```

`make_manuscript_figures.py` and `make_unified_figures.py` also read the
local basketball box-score files under `Data/private/basketball/`, which
come from `scripts/collect_basketball_open_stats.py` (section 4.4). The
football-only steps run from checked-in files.

The scripts write aggregate tables, diagnostics, figures, and reports
under `reports/`. The EDA script also documents a standalone report at
`outputs/eda-20261101/eda_report.html` when generated locally. The
checked-in inputs are treated as read-only by the analysis workflow.

The original partner replication can also be run with:

``` bash
python Tests/football_test.py
```

The legacy `Data/sample_data.py` script can overwrite the inherited
sample. Do not run it unless intentionally rebuilding that input. For
additional data, use the newer import/collection scripts and preserve
the original inputs.

### 4.4 Reproduce supporting collection layers

Some collection steps require external access or credentials and are not
needed to rerun the checked-in football analysis.

**Basketball performance export:**

``` bash
python scripts/collect_basketball_open_stats.py \
  --season 2026 \
  --as-of 2026-10-31 \
  --transport curl \
  --report reports/basketball_collection_audit.json
```

**Collect/refresh football or basketball performance through the
configured provider workflow:**

``` bash
cp .env.example .env
# Add any required API credentials locally to .env.
# Do not commit .env or share API keys.

python scripts/collect_performance.py \
  --sport basketball \
  --season 2026 \
  --sample Data/private/basketball_enriched.csv \
  --output Data/private/basketball_performance_joined.csv
```

Use the appropriate season and input file for the sport being collected.
The repository's collection guides explain source-specific fields,
matching rules, and required credentials. Basketball uses the ending
year for its season label (for example, `2026` represents 2025--26);
football uses the calendar year of the football season.

For a new, source-authorized basketball NIL frame, the repository
includes a revised 1,000-player design with 250 players selected from
each full-frame NIL quartile. The actual source frame is required before
that sample can be created. Do not substitute a performance ranking or
follower ranking for NIL-based stratification.

### 4.5 Reproducibility boundaries

The checked-in football analysis is reproducible from the inherited
inputs. Reproducing new external collection may require network access,
provider credentials, and access to the same upstream source versions.
The project records hashes and metadata to identify retrieved assets,
but upstream providers can revise their data.

Offline tests use synthetic fixtures to test pipeline behavior; they are
**not research observations**. Some larger newly collected player-level
files are intentionally kept local and are not distributed in the
repository. Their collection scripts, aggregate audits, and source
descriptions are provided where possible.

## 5. Statistical approach

All models are ordinary least squares on the natural log of NIL valuation,
with `log(1 + Instagram followers)` as the predictor of interest and HC3
heteroskedasticity-robust standard errors. On this scale, twice the
followers multiplies valuation by `2^β`, so effects are reported as
`100 × (2^β − 1)` percent.

-   **Main model (fitted to each sport separately):** followers, last-season performance
    percentile within sport (basketball points per game; football PPA per
    play with zeros treated as missing), a flag for no college stats last
    season, and years in college. The sport difference (H3) is tested with
    a pooled model that interacts sport with every term. General dominance
    analysis with 1,000 bootstrap draws splits R² among the factors.
-   **Football-specific model:** followers, centered recruiting stars,
    freshman status, stars × freshman, and four position groups. It drops
    the partner's PPA measure (unverified values) and the Power 4 flag
    (99 of 100 players are Power 4).
-   **Basketball-specific model:** followers, points per game (per 5),
    no-stats flag, freshman, big conference (ACC, Big Ten, Big 12, SEC,
    Big East) and forward-or-center.
-   **Post hoc:** Kruskal--Wallis tests across four equal follower groups
    and across recruiting-star groups, followed by Holm-corrected pairwise
    Mann--Whitney tests.
-   **Multiple testing:** football, basketball and sport-difference tests
    form one family with a Bonferroni threshold of `alpha = 0.0167`.

## 6. Results

### 6.1 Main model: one formula fitted to each sport

Both sports were fitted with the same model:
`ln(NIL) ~ ln(1 + followers) + last-season performance percentile + no-stats flag + years in college`,
with HC3 robust standard errors. Performance is ranked within each sport
(basketball points per game; football PPA per play with zeros treated as
missing).

  ------------------------------------------------------------------------
  Result                                  Basketball        Football
  -------------------------------------- ----------------- -----------------
  Higher NIL per doubling of followers    +35% (18--54%)    +17% (7--27%)

  p-value (follower slope)                0.00002           0.0007

  Partial f² for followers                0.18              0.25

  Share of explained R²: followers        64%               69%

  Share: last-season performance          12%               20%

  Share: years in college                 24%               11%

  Model R²                                0.23              0.30

  Without the 25 highest-valued players   +1% (p = 0.86)    +4% (p = 0.05)
  ------------------------------------------------------------------------

The sport difference in follower slopes is not significant (pooled
interaction, p = 0.079). Post hoc Kruskal--Wallis tests on four equal
follower groups agree (basketball p = 0.006, football p < 0.001), and
Holm-corrected Mann--Whitney pairs show the gap is mainly between the
most-followed group and the rest. Results:
[`unified_model_results.json`](figures/figure_data/unified_model_results.json)
and [`unified_model_diagnostics.json`](figures/figure_data/unified_model_diagnostics.json).

### 6.2 Sport-specific models

**Football** (position groups, HC3): β = 0.274, 95% CI 0.094--0.454,
p = 0.0028, about **+21% NIL for twice the followers** (95% CI 7--37%),
R² = 0.355. Recruiting stars: valuations differ across 3-, 4- and 5-star
players (Kruskal--Wallis p = 0.001), but the Holm-corrected pairs show the
difference is 5-star versus 4-star only (p = 0.002).

**Basketball** (HC3, R² = 0.54):

  -----------------------------------------------------------------------
  Term                              Effect on NIL      95% CI          p
  -------------------------------- --------------- --------------- -------
  Twice the followers                    +9%        −8% to +29%      0.32

  +5 points per game                     +8%        −22% to +49%     0.66

  Freshman                              −37%        −60% to −1%      0.045

  Big conference                       +509%       +295% to +840%   <0.001

  Forward or center (vs guard)           −2%        −29% to +35%     0.89
  -----------------------------------------------------------------------

The 19 big-conference players have a median NIL value of \$413K against
\$55K for the rest, and more followers (median 5,754 against 2,198).
Conference alone explains 50% of the variation in basketball NIL value, so
much of the follower association in the main model reflects conference.
Football cannot be checked this way because 99 of its 100 players are in
Power 4 conferences.

### 6.3 Supplementary: football replication and robustness

These were run to check that the football results do not depend on one
modelling choice. They are not headline findings and were not selected by
p-value.

  ------------------------------------------------------------------------------
  Model                           N      β      95% CI          p        Role
  ---------------------------- ---- ------ -------------- -------- -------------
  Partner's original model,     100  0.207  0.079 to 0.335  0.00155  Replication
  HC3

  Partner's model, largest       99  0.212  0.068 to 0.355  0.00388  Influence
  account removed                                                    check

  Football-specific model with  100  0.274  0.121 to 0.427  0.00086  Dependence
  school-clustered errors                                            check
  ------------------------------------------------------------------------------

All are positive and below the 0.0167 threshold. The partner's model
gives about 15% higher NIL per doubling of followers (95% CI 6--26%).
Figure `fig3_followers_vs_valuation` shows these side by side, and the
exploratory analysis in [`reports/eda/`](reports/eda/) and the partner's
original test in [`Tests/football_test.py`](Tests/football_test.py) are
also supplementary.

### 6.4 Diagnostics

-   The exploratory Breusch--Pagan tests indicate heteroskedasticity,
    motivating robust uncertainty estimates.
-   The inherited model has substantial collinearity involving freshman
    status and its interaction with uncentered stars.
-   Influence checks flag observations for review; flagged players are
    not automatically removed from the models.
-   The sample has limited conference variation (99 of 100 players are
    from Power 4 schools).
-   The largest account has substantial influence on the raw follower
    correlation.
-   HC3 and school-clustered standard errors change uncertainty; they do
    not correct selection bias, confounding, source errors, or reverse
    causation.

### 6.5 Status of each research question

  -----------------------------------------------------------------------
  Research question       Status                  Why it remains
                                                  unanswered
  ----------------------- ----------------------- -----------------------
  Football followers and  **Completed**           A 100-player selected
  NIL valuation                                   football sample
                                                  contains both measures.

  Basketball followers    **Completed**           100-player basketball
  and NIL valuation                               sample, 25 per NIL
                                                  quartile (section 6.1).

  Football vs. basketball **Completed**           Same model in both
  social-slope comparison (exploratory)           sports; slope
                                                  difference p = 0.079.
                                                  Sport main effect not
                                                  testable because the
                                                  football sample covers
                                                  only the top 1,000.

  Pre-/post-NIL change in **Not run**             Historical follower
  scholarship association                         counts and comparable,
                                                  verified
                                                  scholarship/decision
                                                  outcomes are missing.
  -----------------------------------------------------------------------

A valid pre/post analysis would need the same outcome and eligible
population in both eras, follower counts measured before the relevant
decision, verified positive and negative decisions, and inference that
accounts for repeated athletes and schools. A model would test the
`social_media × post-NIL` interaction directly; a difference in
significance between two separate models is not itself evidence of a
difference in slopes.

## 7. Limitations

The results should be interpreted with the following limitations in
mind:

1.  **Outcome-based selection:** The football sample is drawn from a
    top-1,000 NIL valuation frame. Athletes below the frame cutoff are
    excluded, so the result does not generalize automatically to all
    college athletes or prospects.
2.  **Valuation measurement:** NIL values are estimates, and the
    original valuation formula is not verified. If the formula already
    incorporates audience size, part of the association may be built
    into the outcome.
3.  **Follower timing and identity:** Follower counts are not fully
    validated against athlete identity and measurement date.
    Contemporaneous or later follower counts may not precede valuation
    or recruiting decisions.
4.  **Performance controls:** PPA has unresolved missingness and
    position-applicability issues. Exploratory alternatives omit it and
    therefore do not control for validated college performance.
5.  **Confounding and reverse causation:** Athletic performance, school
    exposure, media visibility, and NIL valuation may all influence
    follower counts and valuation.
6.  **Limited coverage:** The football sample has little non-Power-4
    variation and covers only valuations of \$350,000 and up, while the
    basketball sample covers the whole market, so the two cannot be
    pooled to test sport itself. Twenty basketball follower counts were
    reported manually without a measurement date. Historical source
    layers do not contain the follower counts needed for a pre/post test.
7.  **Observational design:** No NIL exposure, follower count, or
    college decision was randomized. The analysis does not establish a
    causal policy effect or whether NIL changed scholarship decisions.

## 8. Repository guide

  -----------------------------------------------------------------------
  Path                                Purpose
  ----------------------------------- -----------------------------------
  `Data/`                             Inherited project inputs and
                                      templates; sensitive/new
                                      player-level data may be excluded
                                      or kept local.

  `Data Cleaning/`                    Data-cleaning and preparation
                                      materials.

  `Tests/`                            Offline unit tests and partner
                                      replication checks.

  `scripts/`                          Collection, audit, sampling,
                                      analysis, and reporting scripts.

  `docs/`                             Research design, source collection
                                      notes, and methodological
                                      documentation.

  `reports/`                          Aggregate model outputs, data
                                      audits, manifests, and EDA
                                      artifacts.

  `figures/`                          Project figures and visual outputs.

  `deliverables/`                     Written report (PDF and Word),
                                      8-minute presentation and speaking
                                      script, model-explainer slide,
                                      submission checklist.

  `PROJECT_CONTEXT.md`                Project handoff, current status,
                                      and known issues.

  `requirements.txt`                  Python dependencies.

  `.env.example`                      Example local environment
                                      configuration; never commit real
                                      credentials.
  -----------------------------------------------------------------------

Useful documentation:

-   [Project context and handoff](PROJECT_CONTEXT.md)
-   [Research design and remaining work](docs/research_design.md)
-   [Exploratory data analysis](reports/eda/README.md)
-   [Football results](reports/football_results.md)
-   [Basketball collection notes](docs/basketball_collection.md)
-   [Historical football and blind sampling
    reconstruction](docs/football_history_and_blind_replication.md)

## 9. References and data sources

1.  **NCAA.** *The History of the NCAA.* The June 30, 2021 entry
    describes the interim NIL policy effective July 1, 2021.\
    https://www.ncaa.org/about-us/history/

2.  **The Sideline.** *NIL Tracker.* Source attribution for the
    inherited football NIL valuation frame follows the partner
    collection/report. The original bulk snapshot date and valuation
    methodology remain unverified; fresh access was not available during
    later collection.\
    https://thesideline.co/

3.  **SportsDataverse.** *SportsDataverse data releases.* Public
    sports-data repositories used for roster, game, and performance
    collection.\
    https://github.com/sportsdataverse/sportsdataverse-data

4.  **SportsDataverse.** *hoopR data.* Basketball data resources used in
    the supporting collection workflow.\
    https://github.com/sportsdataverse/hoopR-data

5.  **SportsDataverse.** *College Football data.* Football data
    resources used in the supporting collection workflow.\
    https://github.com/sportsdataverse/cfb-data

6.  **SportsDataverse Python documentation.** ESPN-derived data export
    documentation and season/team membership resources used in the
    basketball collection workflow.\
    https://py.sportsdataverse.org/

7.  **nflverse.** *nflverse-data.* Supplementary player crosswalk and
    draft-source data used for football career-history auditing. A
    crosswalk match is not, by itself, evidence of a professional
    contract.\
    https://github.com/nflverse/nflverse-data

8.  **statsmodels.** *RegressionResults.get_robustcov_results.*
    Documentation for robust covariance estimators used in the
    regression workflow.\
    https://www.statsmodels.org/stable/generated/statsmodels.regression.linear_model.RegressionResults.get_robustcov_results.html

9.  **statsmodels.** *Regression diagnostics example.* Reference for
    regression diagnostic procedures.\
    https://www.statsmodels.org/stable/examples/notebooks/generated/regression_diagnostics.html

10. **Govil, R., & Teshome, S.** *Social media following and college
    athlete NIL valuation.* AIPI 510 Module Project 2 report, November
    1, 2026. The report and analysis evidence are maintained in this
    repository's `deliverables/` and `reports/` directories.

11. **Govil, R., & Teshome, S.** *AIPI 510 Project 2 repository.* Source
    code, inherited inputs, collection scripts, audits, aggregate
    analysis outputs, and documentation.\
    https://github.com/govrahul/aipi510_project2

------------------------------------------------------------------------

## Authors

**Rahul Govil** and **Sam Teshome**\
AIPI 510 --- Module Project 2\
November 2026
