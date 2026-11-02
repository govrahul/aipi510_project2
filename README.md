# Social Media, NIL Valuation, and College Athlete Selection

**AIPI 510 --- Module Project 2**\
**Authors:** Rahul Govil and Sam Teshome\
**Analysis snapshot:** November 1, 2026

**Collection update (November 2):** Safari collection now supplies the full
5,348-listing Sideline basketball frame and a frozen 100-player social-data
substudy with 25 per NIL quartile. **All 100 original sampled players now have
Instagram follower counts**: 80 browser observations and 20 manually reported
by Sam. Each NIL quartile has 25 populated counts, with no replacements.
The completed [CSV](Data/curated/basketball_instagram_100.csv) and
[Excel view](Data/curated/basketball_instagram_100.xlsx) are committed for review.
Manual source labels preserve unknown account handles, observation dates and
original display precision. Collection
code, local-data paths and reproduction steps are in
[the collection notes](docs/basketball_instagram_100.md); aggregate coverage is
in [the audit](reports/basketball_instagram_100/collection_audit.json).

This project examines the relationship between college athletes'
social-media reach and reported name, image, and likeness (NIL)
valuation. It also documents the data needed to investigate whether the
relationship between social reach and college selection changed after
the NCAA's interim NIL policy took effect on **July 1, 2021**.

> **Main takeaway:** In a selected sample of 100 college football
> players, Instagram following is positively associated with reported
> NIL valuation after adjustment for the covariates in the replication
> model. This is an observational association---not evidence that
> followers cause higher NIL compensation, influence scholarship offers,
> or that NIL policy changed college recruiting.

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
completed analysis addresses the first question for a selected football
sample. The second question remains unestimated because comparable
historical follower measurements and verified decision outcomes are not
available.

## 2. What this project does

-   Reproduces a football NIL valuation analysis using a supplied
    top-1,000 valuation frame and a 100-player sample.
-   Models the relationship between log NIL valuation and log Instagram
    followers.
-   Reports heteroskedasticity-robust (HC3) uncertainty and sensitivity
    checks, including a school-clustered specification.
-   Audits source coverage, missingness, identity matching, and the
    limitations of the inherited data.
-   Collects supporting football and basketball roster/performance
    source layers and documents what is still needed for cross-sport and
    historical comparisons.
-   Provides scripts, aggregate outputs, input hashes, and offline tests
    so the available analysis can be reviewed and rerun.

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
player-team-season records across 365 teams. This is a supporting
performance layer only: a paired basketball NIL valuation frame and
dated Instagram follower sample were not obtained, so no basketball NIL
regression was fit.

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
```

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

The primary completed analysis uses ordinary least squares (OLS) with:

-   **Outcome:** natural log of positive reported NIL valuation in U.S.
    dollars.
-   **Social predictor:** natural log of one plus Instagram followers,
    `log(1 + followers)`.
-   **Replication controls:** PPA per play, freshman status,
    freshman-by-stars interaction, Power 4 indicator, and
    premium-position indicator.
-   **Inference:** HC3 heteroskedasticity-robust standard errors, with
    additional sensitivity checks.

The replication model preserves the inherited specification. Because the
inherited PPA values have unresolved provenance and applicability,
exploratory alternatives omit PPA and cannot be described as controlling
for validated college performance. Alternative specifications also
examine centered recruiting-star ratings, freshman status and its main
effects/interaction, position groups, the largest-audience observation,
and school-clustered uncertainty.

The report uses a three-test Bonferroni family threshold of
`alpha = 0.0167` for the planned football, basketball, and cross-sport
tests. Only the football slope has completed data; basketball and the
cross-sport interaction remain untested.

## 6. Results

### 6.1 Primary football result

The replicated football model estimates a positive association between
Instagram following and reported NIL valuation:

  --------------------------------------------------------------------------------
  Model                     N        Social          95%    Two-sided           R²
                                coefficient   confidence      p-value 
                                                interval              
  -------------- ------------ ------------- ------------ ------------ ------------
  Replication,            100         0.207     \[0.079,      0.00155        0.321
  HC3                                            0.335\]              

  --------------------------------------------------------------------------------

At sufficiently large follower counts, the coefficient corresponds to
approximately **15.4% higher modeled NIL valuation for a doubling of
followers**, with an approximate 95% interval of **5.6% to 26.1%**,
conditional on the included controls.

This is a conditional association in the selected sample. It should not
be interpreted as the expected return from gaining followers or as
evidence that followers cause a change in valuation.

### 6.2 Sensitivity checks reported in the project report

  ------------------------------------------------------------------------------
  Model                           N         Social 95% confidence      Two-sided
                                       coefficient       interval        p-value
  ------------------ -------------- -------------- -------------- --------------
  Position groups,              100          0.274       \[0.094,        0.00282
  HC3                                                     0.454\] 

  Largest audience               99          0.212       \[0.068,        0.00388
  omitted, HC3                                            0.355\] 

  School-clustered              100          0.274       \[0.121,        0.00086
                                                          0.427\] 
  ------------------------------------------------------------------------------

The positive coefficient persists across these specified checks, but
model specification, influential observations, and uncertainty affect
its magnitude. These sensitivity models are exploratory and are not
additional confirmatory discoveries.

The repository also contains analysis outputs generated as the code
evolved. For the exact results from the currently checked-in scripts,
rerun `scripts/analyze_football.py` and consult the generated files
under `reports/`; do not assume every historical report table represents
the same model specification.

### 6.3 Diagnostics and interpretation

-   The exploratory Breusch--Pagan tests indicate heteroskedasticity,
    motivating robust uncertainty estimates.
-   The inherited model has substantial collinearity involving freshman
    status and its interaction with uncentered stars.
-   Influence checks flag observations for review; flagged players are
    not automatically removed from the primary model.
-   The sample has limited conference variation (99 of 100 players are
    from Power 4 schools).
-   The largest account has substantial influence on the raw follower
    correlation.
-   HC3 and school-clustered standard errors change uncertainty; they do
    not correct selection bias, confounding, source errors, or reverse
    causation.

### 6.4 Analyses not completed

  -----------------------------------------------------------------------
  Research question       Status                  Why it remains
                                                  unanswered
  ----------------------- ----------------------- -----------------------
  Football followers and  **Completed**           A 100-player selected
  NIL valuation                                   football sample
                                                  contains both measures.

  Basketball followers    **Not run**             No paired basketball
  and NIL valuation                               NIL valuation frame and
                                                  dated follower
                                                  measurements.

  Football vs. basketball **Not run**             Requires comparable
  social-slope comparison                         paired NIL and follower
                                                  data in both sports.

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
6.  **Limited coverage:** The sample has little non-Power-4 variation.
    Basketball and historical source layers do not yet contain the
    paired measurements needed for the planned regressions.
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

  `deliverables/`                     Report, presentation, and
                                      submission materials.

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
