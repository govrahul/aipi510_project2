# Basketball Instagram collection — November 2, 2026

> **Superseded November 3:** This is the legacy sample drawn from all 5,348
> listings. Sam clarified that only the top 1,000 should form the sampling
> population. Use [the corrected top-1,000 dataset and notes](basketball_top1000_social.md)
> for new basketball work. The 100-count completion described below is historical.

The public Sideline ranking was collected successfully through normal Safari
after Sam changed the local network setup. The collector expanded all public
"Load more" controls: **5,348 listings**, not just the first page. A frozen
100-player follow-up sample contains **25 per NIL rank quartile**, seed 510.
This is the requested 100-player social-data substudy; it does not replace the
planned 1,000-player main basketball dataset or reconstruct the partner's football
sample. No selected player was replaced because their followers were unavailable.

## Observed coverage

| NIL quartile | Selected | Browser counts | User-reported counts | Recorded counts | Missing counts |
|---|---:|---:|---:|---:|---:|
| Highest | 25 | 25 | 0 | 25 | 0 |
| Upper middle | 25 | 20 | 5 | 25 | 0 |
| Lower middle | 25 | 19 | 6 | 25 | 0 |
| Lowest | 25 | 16 | 9 | 25 | 0 |
| Total | 100 | 80 | 20 | 100 | 0 |

Sam supplied the 20 remaining counts through chat annotations and a
semicolon-separated list. The completed original cohort is committed as
`Data/curated/basketball_instagram_100.csv`, with a readable Excel view at
`Data/curated/basketball_instagram_100.xlsx`. The 21-record manual receipt CSV
includes Ali Diouf's existing 971 as corroboration, not an additional athlete.
`Instagram_Count_Provenance` distinguishes 80 `browser_observed` observations
from 20 `user_reported` entries. Manual account handles, observation timestamps
and original display precision were not supplied. The report date is November
2, 2026, not an invented measurement date. No replacements were used; the
replacement exploration was stopped before adoption.

After the first logged-out pass returned four observations, Sam signed into
Instagram and explicitly authorized another browser pass in Chrome or Safari.
That newer authorization supersedes the earlier logged-out-only preference.
Using normal signed-in Chrome, **80 exact integer counts** were read from the
title attributes (tooltips) on the visible followers links. Rounded visible
labels are retained alongside the integer tooltip, not expanded to invent a
count. For example, Myles Colvin displayed 13.4K with tooltip 13,472. The earlier
three rounded-only observations now have integer tooltip observations.

Opendorse's eight positive reach values remain in separate columns with
**unknown underlying measurement dates**. All eight now overlap directly
observed players, so they do not add observations. Before the manual reports,
one formerly sourced handle exposed no usable count and 19 other accounts were
unresolved. The user reports filled those 20 count gaps. Same-name actors, a rugby player, a tree-care
business, unrelated students and fan pages were excluded from account matches.

Instagram returned login shells with HTTP 200 for many profiles, including a
normal Safari inspection. The updated collector stops live retrieval at these
shells as well as HTTP 403/429. It does not solve verification, log in, change
settings, read credentials/cookies, or call private APIs. The later Chrome pass
used the session Sam had already signed into; there was no automated login.
It read public athlete profile fields, not private messages, feeds or follower
lists. The optional Safari collector was not used for this pass. A browser
challenge, login redirect or security warning remains a stop condition.

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
- `sample/manual_followup_queue.csv`: now empty of missing-count rows.
- `sample/unresolved_account_reviews.csv`: historical browser-only account
  review notes; these are not current missing-count indicators.
- `sample/basketball_instagram_observations_100_before_browser.csv`: preserved
  first-pass source sheet. `sample/basketball_instagram_browser_100.csv` is the
  reviewed browser-import output copied to the main collection sheet.
- `browser_dom_receipts_80.csv`: selected DOM fields exported from browser-tool
  observations, with row, username, UTC time, rounded/display label and integer
  tooltip. This is a local evidence ledger, not a saved HTTP-response body.
- `sample/opendorse_raw/`, `sample/public_instagram_raw/`,
  `profile_evidence_raw/`: cached public source HTML with metadata and hashes.

Code, aggregate audits and the completed 100-row study extract are committed
at Sam's explicit request. The full source frame and bulk HTML remain local.
Five initial source-reviewed
handle mappings and 33 new browser identity reviews are under
`replication/basketball_social/`; the larger local
lookup manifest is `profile_lookup_candidates.csv`. Preserve the local source
caches when handing off this collection.

Identity checks use named basketball biographies, athlete-specific social
links, Opendorse name/sport/school checks, and matching athlete-name/college
basketball tags in public Instagram biographies. The Jarin Stevenson handle
was also confirmed in official UNC game notes. Team navigation/footer accounts,
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

Browser-observed coverage is 100%, 80%, 76% and 64% from the highest to lowest
quartile; manually reported counts bring recorded coverage to 100% in every
quartile. Keep these source distinctions in any sensitivity analysis, rather
than claiming 100 exact browser measurements. No basketball regression is
fitted from this collection. Validate season, source quality and metric
definitions before choosing the analysis. This collection supplies no
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

python3 scripts/collect_public_instagram.py --input Data/private/basketball_instagram_100/sample/basketball_with_handles_100.csv --output Data/private/basketball_instagram_100/sample/basketball_logged_out_replay.csv --offline

# Replay reviewed browser observations without using a browser or overwriting
# the main collection sheet. Receipt ledgers are local, ignored evidence.
python3 scripts/import_instagram_browser_receipts.py --input Data/private/basketball_instagram_100/sample/basketball_instagram_observations_100_before_browser.csv --receipts Data/private/basketball_instagram_100/browser_dom_receipts_80.csv --reviewed replication/basketball_social/browser_reviewed_handle_sources.csv --output /tmp/basketball_browser_replay_100.csv

# Apply the committed manual source reports to the preserved browser sheet.
python3 scripts/import_manual_basketball_followers.py --input Data/private/basketball_instagram_100/sample/basketball_instagram_browser_100.csv --manual Data/curated/basketball_manual_followers_20261102.csv --output /tmp/basketball_manual_replay_100.csv --audit /tmp/basketball_manual_replay_audit.json

python3 scripts/audit_basketball_social_collection.py --sample-dir Data/private/basketball_instagram_100/sample --output-dir reports/basketball_instagram_100

python3 -m unittest discover -s Tests -p 'test_*.py'
```

`scripts/build_basketball_followers_workbook.mjs` builds the Excel view from the
completed CSV using the bundled `@oai/artifact-tool` runtime. It retains all 100
records, typed numeric counts and separate source/report/observation fields;
the CSV retains the complete provenance schema. The manual import rejects
conflicting existing counts and mismatched athlete IDs/names/schools. The
completion audit reports 20 filled gaps, one corroboration, 100 populated
counts, unchanged IDs/strata/NIL values and zero replacements.

Without `--offline`, HTTP collectors make bounded public requests with delays
and stop on access restrictions. `scripts/collect_instagram_browser.mjs` contains
the Chrome CUA extraction and receipt-export functions used for the authorized
browser pass. In the Codex CUA runtime, bind a dedicated Instagram tab in the
user-authorized browser, then call `collectProfileBatch(tab, jobs)` with sourced
`[Sample_Row, username]` pairs. Export `receiptsCsv(observations)` into a local
ledger and import it with the Python command above. Browser bindings are supplied
by Codex; this module is not a standalone headless browser or credential loader.
Inspect newly discovered account identities before importing their counts.

Instagram search was used for all 52 initially unmatched names. Results were
candidates only; the 33 newly accepted accounts required school basketball
affiliation or explicit official-source evidence. Counts from unresolved
candidates were not attached to study rows. The importer checks reviewed
athlete IDs, handle matches, integer tooltips, UTC timestamps and unchanged
sample ordering. Receipt hashes cover the selected-field ledger and per-record
evidence; no HTTP-response hash is claimed for Chrome DOM observations.

Primary public sources: [Sideline basketball ranking](https://thesideline.co/nil-tracker/top-players/basketball),
[Opendorse](https://opendorse.com/), and the named official biographies recorded
per row. Aggregate evidence: `reports/basketball_instagram_100/collection_audit.json`
and `coverage_by_quartile.csv`. Login failures, missing counts and incomplete
career follow-up are unknowns, never zeros.
