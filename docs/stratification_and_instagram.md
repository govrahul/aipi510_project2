> **Latest basketball design, November 3:** Restrict to top 1,000 NIL listings
> FIRST, make four rank quartiles of 250 within those 1,000, then select 25 per
> quartile for Instagram collection. This replaces the full-frame design below.
> See [the corrected collection](basketball_top1000_social.md). For historical
> comparators, Sam chose high-school recruiting stars; the production-quartile
> comparator samples below remain provisional legacy artifacts. See
> [recruiting and career evaluation](recruiting_and_career_evaluation.md).

# Revised sampling and Instagram collection

Updated November 1, 2026. Sam revised the intended final basketball sample to **1,000 athletes, 250 per NIL valuation quartile**, sorted by stratum. This supersedes the earlier 100-player 25/50/25 plan for new basketball work. The inherited football sample is still 100 players with the old allocation; it was not silently changed.

## What the new sampler does

`scripts/sample_quartiles.py` uses the full eligible input pool, orders descending by the selected metric, splits it into four nearly equal rank quartiles, and samples 250 without replacement from each using seed 510. It does not first truncate to the highest 1,000. For a pool of exactly 1,000, all rows are retained. The quarter labels are Q4_Highest, Q3_Upper_Middle, Q2_Lower_Middle and Q1_Lowest. Rows stay in that order and descending metric order within each stratum.

The files include the original metric, frame rank, stratum population, sampling probability and inverse-probability weight. Weights describe the supplied frame only. With equally sized population quartiles and equal draws, selection probabilities are equal; unequal prices or a skewed dollar distribution do not justify oversampling a lower tier. If the frame already consists only of top-valued players, it still excludes everyone below that cutoff.

To make exactly four equally sized groups when prices tie, the code uses stable ID ordering and records `Metric_Tie_Crosses_Quartile`. A tied dollar value may appear in two adjacent strata. This is a rank-based quartile design, not four strictly disjoint price intervals. It refuses duplicate IDs, missing metrics or fewer than 250 eligible players in any quartile. It does not replace missing data with zero.

## Current basketball final file

`scripts/build_basketball_nil_sample.py` implements the full 1,000-player design. It samples by NIL **before** left-joining supplemental performance. Missing performance or followers never causes a selected player to be dropped or replaced. Source-reported $0 valuations are retained for sampling, while unknown valuations stop the build. A later regression must explicitly address zeros and the chosen transformation; the sampler does not silently discard them.

```bash
python scripts/build_basketball_nil_sample.py \
  --nil-frame /path/to/authorized_full_basketball_nil_frame.csv \
  --source-url https://thesideline.co/nil-tracker/top-players \
  --nil-observed-at YYYY-MM-DD
```

Inputs require Player Name, College, Position and Valuation. The frame should have one current row per athlete with documented eligibility and dates; source-provided IDs are preferred. Otherwise an explicitly labeled internal name-school key is created, not a purported verified ESPN identifier. Exact historical team/name/position joins can leave transfers unmatched; a reviewed Performance College or Performance API ID can resolve those identities. A current NIL roster should not be joined to prior-season statistics solely by current school.

The intended output is `Data/private/basketball/basketball_nil_quartiles_1000.csv`. **It has not been produced from real basketball NIL observations**, because the NIL frame remains unavailable. The 5,680-row performance file is a supporting source layer, not the final sample. Synthetic unit tests verify the final builder's 1,000/250 structure and preservation of unmatched rows, but are not empirical basketball data.

## Ways to obtain Instagram counts

| Method | Suitable use | Requirements and limits |
|---|---|---|
| Manual public-profile snapshot | Current count for a verified athlete handle | Record observation date and evidence URL. Preserve a displayed rounded label as rounded; do not present 12.3K as an exact 12,300 observation. A profile captured today is not historical evidence. |
| [Meta Business Discovery](https://developers.facebook.com/docs/instagram-platform/instagram-api-with-facebook-login/business-discovery) | Current aggregate count for supported professional accounts | Requires an appropriately configured Meta app, token and caller account. Target professional/personal account coverage and permissions must be checked. The official page returned 429 during review; no live Meta request was tested, so exact current app approval requirements are not claimed here. This is not a general historical count endpoint. |
| [Social Blade Instagram API](https://socialblade.com/developers/docs) | Current or archived daily counts, if the athlete was tracked | Documented daily history can extend up to ten years in the vault tier, with automatic downgrades where unavailable. Normal athlete queries require credentials and prepaid credits; vault is documented at five credits/profile. Account-specific 2018/2019 coverage is unverified. No purchase or paid query was made. |
| [Internet Archive](https://archive.org/help/wayback_api.php), dated reporting or athlete-provided historical export | Potential historical evidence | Inspect the actual captured count and date. A capture index alone is not a follower observation. Coverage may be sparse and biased toward famous players. Record changes of username/account and observation precision. |

An unofficial scraper can encounter logins, rate limits, blocked responses and rounded counts. It is not a reliable credential-free substitute for an arbitrary 1,000-account historical panel. This repo uses source APIs/authorized response files and does not bypass those controls. Select athletes by NIL first; do not keep only those whose Instagram data is easiest to collect.

## Collection code and record structure

`scripts/collect_instagram_counts.py` preserves every input row and quartile order. It requires a verified username and a URL linking the account to the athlete; names are never guessed into handles. Counts, provider, observation date, account ID where available, precision, status, lag and response hash are recorded. Failures remain missing with a reason. A real zero is retained.

The header contract is `Data/templates/instagram_counts_input.csv`. For historical rows, retain `Period=Pre_NIL` and provide an explicit `Instagram_Target_Date` after the research measurement date is defined. Historical rows without a target date are refused rather than receiving today's count. Daily provider data has day precision, not a verified intraday timestamp; a same-day snapshot cannot by itself establish that it preceded a scholarship decision.

Meta configuration is local: META_ACCESS_TOKEN, META_IG_USER_ID and META_API_VERSION in ignored `.env`. Current-count collection example:

```bash
python scripts/collect_instagram_counts.py --provider meta \
  --input Data/private/basketball/basketball_nil_quartiles_1000.csv \
  --output Data/private/basketball/basketball_with_instagram.csv --max-profiles 10
```

Do not run until the input contains verified usernames and the app is authorized. The request cap bounds the batch. No token is placed in a URL or committed. Network API calls require valid TLS; correct the local trust configuration rather than disabling verification.

For already authorized Social Blade exports, supply a folder containing `USERNAME.json` and `USERNAME.meta.json`. Metadata records provider (`socialblade`), username, retrieved_at and sha256. The script verifies these before parsing. This offline replay is the default documented path; it incurs no requests:

```bash
python scripts/collect_instagram_counts.py --provider socialblade \
  --input Data/private/comparators/basketball_2018/provisional_quartile_sample_1000.csv \
  --responses-dir /path/to/authorized_responses \
  --output Data/private/comparators/basketball_2018/with_instagram.csv --max-lag-days 30
```

The parser selects the latest daily observation on/before the target, within the explicitly recorded maximum lag. No future observation or interpolation from current counts is accepted. Paid live requests are disabled unless the operator explicitly supplies `--allow-paid-requests`; no such requests were executed in this work. Credentials, authorized bulk responses and player-level outputs stay local and ignored.

## Historical comparator files actually produced

`scripts/collect_historical_comparators.py` downloaded documented SportsDataverse exports for both sports and two season-start cohorts. The raw caches, hashes and full frames are saved separately. Four provisional samples were produced, **1,000 athletes each and 250 per quartile**, plus a readable workbook at `outputs/nil-quartiles-20261101/historical_quartile_samples.xlsx`.

- Basketball 2018 = 2018–19, ending-season key 2019.
- Basketball 2019 = 2019–20, ending-season key 2020. COVID shortened this season.
- Football 2018/2019 = fall-start seasons 2018/2019, including their bowl cycles.

The provisional sampling metric is average-rank percentile of recorded season production within sport/position/year. Basketball uses points, grouping G/PG/SG as guards and F/SF/PF as forwards, with centers separate; unknown/ambiguous roles are retained in the full frame but not assigned a proxy. Football uses passing yards for QBs, rushing yards for RB/FB and receiving yards for WR/TE, with FB grouped with RB for ranking. These are transparent production proxies, not validated all-sport talent scores.

**Football coverage restriction:** the sampled comparator currently covers those offensive positions only. The full D1 roster frames retain other positions with missing production proxies. Defensive box-score coverage in these older exports is sparse and offensive-line production is unavailable, so neither was falsely converted to zero. A comparison to the partner's all-position football sample would require aligning scopes or adopting another justified metric.

Athletes with no measured production are excluded from the eligible proxy-sampling frame and remain in the full source file. One athlete with multiple recorded teams is represented by the team with highest recorded production (stable team-ID tie break); the complete source frame retains every team. Sampling weights apply only to this eligible production frame. The samples are provisional because the historical replacement metric has not been confirmed by Sam.

Historical follower counts and scholarship outcomes remain missing. **Changing the regression outcome from current NIL valuation to historical production would not test whether the same social-media coefficient changed sign.** The proxy can organize sampling, but an interpretable before/after comparison still needs a common outcome, consistent scope and historical predictor measurements. No such regression was run.

Reproduce the source collection and samples:

```bash
python scripts/collect_historical_comparators.py --legacy-production-samples --report reports/historical_comparator_collection.json
python -m unittest discover -s Tests -v
```

The workbook builder is `scripts/export_cohort_workbook.mjs`. Run it with `@oai/artifact-tool` available through the bundled Codex workspace runtime (or an authorized installation), passing the generated `Data/private/comparators/workbook_input.json` and an output directory. It verifies 1,000/250 counts before export. The CSVs are the statistical inputs; the workbook is a readable presentation of those samples.
