# Basketball Instagram collection — November 2, 2026

The public Sideline ranking was collected successfully through normal Safari
after Sam changed the local network setup. The collector expanded all public
"Load more" controls: **5,348 listings**, not just the first page. A frozen
100-player follow-up sample contains **25 per NIL rank quartile**, seed 510.
This is the requested 100-player social-data substudy; it does not replace the
planned 1,000-player main basketball dataset or reconstruct the partner's football
sample. No selected player was replaced because their followers were unavailable.

## Observed coverage

| NIL quartile | Selected | Sourced handles | Direct Instagram counts | Additional Opendorse counts |
|---|---:|---:|---:|---:|
| Highest | 25 | 17 | 4 | 1 |
| Upper middle | 25 | 13 | 0 | 3 |
| Lower middle | 25 | 10 | 0 | 2 |
| Lowest | 25 | 8 | 0 | 2 |
| Total | 100 | 48 | 4 | 8 |

Of the four direct observations, one is an unabbreviated displayed integer and
three are rounded K/M labels. Opendorse's eight positive integer reach values
have **unknown underlying measurement dates**. These are separate fields and
are not substituted for current direct Instagram observations. There are 12
players with a count from either source, not 100 complete observations.

Instagram returned login shells with HTTP 200 for many profiles, including a
normal Safari inspection. The updated collector stops live retrieval at these
shells as well as HTTP 403/429. It does not solve verification, log in, change
settings, read credentials/cookies, or call private APIs. On November 2, Sam
explicitly chose **keep the collection logged out**. Use only unauthenticated
public sources; no signed-in collection is authorized. The optional Safari
Instagram collector has offline parser checks and stops at login; it has not
collected observations in a signed-in session.

## Files and source decisions

The working data live under `Data/private/basketball_instagram_100/` (ignored).

- `safari/sideline_safari_page_107.json`: fully expanded public DOM snapshot;
  `safari_collection_status.json` records the 108 saved pagination snapshots.
- `sample/basketball_sideline_full_frame.csv`: all 5,348 ranking listings.
- `sample/basketball_sideline_sample_100_frozen.csv`: selection locked before
  follower availability was investigated. SHA256
  `9cd7286551e1f7d1de3e32df37e1aaa29729dc51a503454b8e488464a2e3afab`.
- `sample/basketball_with_handles_100.csv`: all 100 selected rows and sourced
  handles; no counts inferred from a name, school account or search snippet.
- `sample/basketball_instagram_observations_100.csv`: current main collection
  sheet, with direct counts, rounded labels, separate provider reach, timestamps,
  source URLs, statuses and source hashes. All 100 selected rows remain ordered
  by NIL stratum/rank.
- `sample/manual_followup_queue.csv`: 96 rows missing a direct count, with
  profile links where sourced and blank reviewer/evidence fields.
- `sample/opendorse_raw/`, `sample/public_instagram_raw/`,
  `profile_evidence_raw/`: cached public source HTML with metadata and hashes.

Code and aggregate audits are committed. Raw market data and bulk source HTML
remain local rather than being redistributed. Five additional source-reviewed
handle mappings are under `replication/basketball_social/`; the larger local
lookup manifest is `profile_lookup_candidates.csv`. Preserve the local source
caches when handing off this collection.

Identity checks use named basketball biographies and athlete-specific social
links, plus Opendorse name/sport/school checks. Team navigation/footer accounts,
same-name football players and unverified school mismatches are rejected. Some
biographies describe an earlier school: an account link establishes source
evidence, not proof the athlete still uses that account. Review stale aliases
before analysis. Opendorse checks 100 candidate public slugs, which are lookup
attempts rather than identities. The primary-profile manifest contains 82 URLs
for 64 sampled players. Exact-name school history helps resolve transfers; a
candidate Sideline numeric ID is not itself a validated ESPN crosswalk.

## Sampling and analysis limits

Quartiles use the full frame: 1,337 listings each. Source bands are $13.3K–$42.8K,
$42.8K–$75K, $75K–$261K and $261K–$6M. Stable ID ordering breaks rounded-value
ties; 28 full-frame rows belong to ties that cross quartile boundaries. These
are rank quartiles, not disjoint strict value cutoffs. Within-frame inclusion
probability is 25/1,337 and weight 53.48. Weights do not repair source omissions
or follower nonresponse. The frame has no duplicate profile URLs but includes
24 duplicate-name groups across schools (28 excess rows); they require ID/transfer review before
treating all listings as distinct people. Do not deduplicate by name alone.

This is a **current listing retrieved November 2, 2026**, not an established
2025–26 membership snapshot. Source valuation measurement dates are unavailable.
Do not merge current school blindly with last season's performance. Displayed
NIL estimates are rounded model outputs, not verified payments, scholarships,
or a common pre/post athletic-evaluation outcome. The 407 nonnumeric official
school profile IDs are retained; numeric IDs are only crosswalk candidates.

The four direct observations all fall in the highest quartile. A complete-case
regression now would destroy the balanced design and substantially change the
target population. No basketball regression is fitted from this collection.
Finish identity/count review across strata, validate season and metric definitions,
then examine nonresponse before selecting a model. This collection supplies no
2018–2019 followers and does not resolve the common-outcome requirement for a
pre/post policy comparison.

## Reproduce

Run from the repository root with Python 3 and `requirements.txt` installed.
Source observations and extraction times are cached so offline replay does not
silently replace them with newer counts. Never regenerate the frozen sample in
its existing directory from a newer source snapshot.

```sh
# macOS Safari; user handles OS authorization and any browser verification.
python3 scripts/collect_sideline_safari.py --output-dir Data/private/basketball_instagram_100/safari_new

# Replay the original complete snapshot into a NEW directory.
python3 scripts/prepare_basketball_social_sample.py --snapshot Data/private/basketball_instagram_100/safari/sideline_safari_page_107.json --output-dir /tmp/basketball_sample_replay

# Public Opendorse profiles: --offline reuses the recorded source responses.
python3 scripts/collect_opendorse_instagram.py --input Data/private/basketball_instagram_100/sample/basketball_sideline_sample_100_frozen.csv --performance Data/private/evaluation/enriched/basketball_2025_evaluation_frame.csv --output Data/private/basketball_instagram_100/sample/basketball_opendorse_instagram_100.csv --offline

# Replay the explicitly sourced public profile URLs; candidates require review.
python3 scripts/collect_profile_handle_evidence.py --input Data/private/basketball_instagram_100/profile_lookup_candidates.csv --output Data/private/basketball_instagram_100/profile_handle_evidence.json --offline

python3 scripts/build_basketball_handle_inputs.py --sample Data/private/basketball_instagram_100/sample/basketball_sideline_sample_100_frozen.csv --opendorse Data/private/basketball_instagram_100/sample/basketball_opendorse_instagram_100.csv --evidence Data/private/basketball_instagram_100/profile_handle_evidence.json --reviewed replication/basketball_social/reviewed_handle_sources.csv --output Data/private/basketball_instagram_100/sample/basketball_with_handles_100.csv

python3 scripts/collect_public_instagram.py --input Data/private/basketball_instagram_100/sample/basketball_with_handles_100.csv --output Data/private/basketball_instagram_100/sample/basketball_instagram_observations_100.csv --offline

python3 scripts/audit_basketball_social_collection.py --sample-dir Data/private/basketball_instagram_100/sample --output-dir reports/basketball_instagram_100

python3 -m unittest discover -s Tests -p 'test_*.py'
```

Without `--offline`, collectors make bounded public requests with delays and
stop on access restrictions. Sam chose logged-out collection, so do not run a
signed-in browser pass or request login again. The existing Safari helper is
retained for code review, not as an instruction to authenticate. Further work
can use unauthenticated public sources and identity-reviewed source evidence;
leave unavailable counts missing and retain the frozen selection.

Primary public sources: [Sideline basketball ranking](https://thesideline.co/nil-tracker/top-players/basketball),
[Opendorse](https://opendorse.com/), and the named official biographies recorded
per row. Aggregate evidence: `reports/basketball_instagram_100/collection_audit.json`
and `coverage_by_quartile.csv`. Login failures, missing counts and incomplete
career follow-up are unknowns, never zeros.
