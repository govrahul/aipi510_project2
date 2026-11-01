# Basketball collection progress

Collected November 1, 2026. Scope: men's college basketball, 2025–26 season, performance statistics. This is a supplemental source layer awaiting the project's NIL valuation sample; it is not a completed NIL regression dataset.

## Relationship to the partner workflow

The partner PDF calls for a top-1,000 NIL valuation frame from The Sideline, a 100-player 25/50/25 valuation-tier sample, Instagram followers and recruiting ratings, and performance statistics from CollegeBasketballData. The PDF does not define the exact basketball performance metric or role-tier cutoffs. The existing official API collector extracts CBBD PORPAG, but no API key is available. Sam confirmed that they do not have a key yet.

The Sideline HTTP request still returned 403 and its structured data access is separate from citing public figures. No top-1,000 basketball valuation file or Instagram sample was acquired. This collection therefore advances the performance layer using the [documented SportsDataverse ESPN export](https://py.sportsdataverse.org/docs/mbb/reference/loaders/player), with [season-specific team membership](https://py.sportsdataverse.org/docs/mbb/reference/loaders/team). These box-score measures are not PORPAG, and they are not silently substituted into the partner's regression.

## Data actually acquired

| Item | Count or coverage |
|---|---|
| Raw player-game rows | 196,876 |
| Games in raw export | 6,300 |
| Raw game dates | November 3, 2025–April 6, 2026 |
| Raw teams, including non-D1 opponents | 727 |
| Season-specific D1 membership records | 365 |
| D1 player-team-season records | 5,680 |
| Distinct D1 athlete IDs | 5,677 |
| D1 player-team records with appearances | 5,019 |
| D1 records with no recorded appearances | 661 |

The counts describe this export's coverage, not a verified census of all players or proof of complete official season statistics. Multiple team records can share an athlete ID; they stay separate. Current NIL team assignments may differ from the team on which an athlete played in 2025–26.

Locally saved files under `Data/private/basketball/`:

- `player_box_2026.parquet`: unmodified raw player-game export.
- `mbb_team_group_seasons_2026.parquet`: season-specific membership export.
- Matching `.meta.json` files: source URLs, retrieval times, upstream last-modified values, sizes and SHA-256 hashes.
- `player_team_season_2026.csv`: all recorded team-season aggregates, including opponents outside the D1 membership table.
- `division_i_player_team_season_2026.csv`: source-confirmed D1 team membership subset, ready for identity matching to an eventual NIL sample.
- `collection_audit_2026.json`: aggregate counts and missingness. A copy is published in `reports/basketball_collection_audit.json`.

Raw and player-level files remain ignored by Git. The collector, tests, aggregate audit and these instructions are committed so Rahul can reproduce the same files. Hashes identify the exact retrieved assets; upstream releases can be revised. Preserve the local raw files for exact replay.

## Cleaning and validation

The script includes regular and postseason games through the explicit `--as-of` date. It uses source athlete/team/game IDs, rejects duplicate player-game identities, and reports exclusions. Eleven raw rows lacked identity and were excluded; all eleven were DNP placeholders. The remaining 69,333 DNP rows do not enter appearance denominators. An observed zero stays zero, while no appearance or missing statistics stay missing. Zero-minute appearances are retained because the source explicitly marks participation; rounded minutes are not used to infer absence.

One row is produced per athlete/team/season. Totals and per-game averages are calculated from appearances; if a statistic is missing in any appearance, its season total/average stays missing. Players with no recorded appearance have Games=0 and missing performance statistics. Shooting percentages are ratios of season makes/attempts and remain missing for zero attempts. Team membership is joined by ESPN team ID for season 2026; it is not inferred from a present-day team directory. The output retains conference IDs without assigning a football-style premium conference or position flag to basketball.

Spot checks against primary school sources:

- Alex Karaban: 40 games, 40 starts, 527 points, 211 rebounds and 94 assists agree with [UConn's 2025–26 cumulative table](https://uconnhuskies.com/sports/mens-basketball/stats/2025-26).
- Milan Momcilovic: the aggregate has 624 points, matching the [Iowa State season-ending report](https://cyclones.com/news/2026/3/27/mens-basketball-iowa-states-season-ends-in-sweet-16).

These limited checks do not verify every athlete. Per-game minutes in the source may be rounded and need not equal second-precision official totals. Do not treat a box-score export as an independent advanced impact model.

## Reproduce or resume

From the repository root with requirements installed:

```bash
python scripts/collect_basketball_open_stats.py --season 2026 --as-of 2026-10-31 \
  --transport curl --report reports/basketball_collection_audit.json
python -m unittest discover -s Tests -v
```

`--transport curl` uses the system certificate trust store with verification enabled. It was needed on this Mac because Python requests could not validate the download certificate chain. The default requests transport also verifies certificates; there is no insecure mode. Reruns verify cached hashes. `--refresh` requests new upstream assets.

When a CBBD key becomes available, the official collector can now collect performance before a NIL sample exists:

```bash
python scripts/collect_performance.py --sport basketball --season 2026 \
  --download-only --output Data/private/basketball_cbbd_performance_2026.csv
```

Store `CBBD_API_KEY` locally in the ignored `.env`; an explicit `--env-file /path/to/.env` is supported. No account was created and no paid access was purchased. For the official collector, configure a trusted CA bundle if the Python installation has a certificate-store problem; do not disable verification.

## Remaining steps before a NIL regression

1. Obtain a dated, source-authorized top-1,000 basketball NIL frame. Run the existing reproducible sampler for 25/50/25 observations. Do not select 100 athletes by points or followers and call it a NIL-stratified sample.
2. Add verified Instagram followers with dates/source URLs, recruiting ratings with evidence, grade/class and valuation type/date. These fields were not supplied by the downloaded box scores.
3. Resolve athlete identities and historical team assignments, especially transfers. Use verified IDs or reviewed exact name/team matches. A current Kentucky player can have prior-season Iowa State statistics; do not mark that mismatch as zero performance.
4. Choose and justify the basketball performance measure and role controls before fitting. PORPAG requires CBBD; scoring, minutes and other box-score measures are available as supplemental controls. Document any departure from the planned measure.
5. Audit the joined sample, then fit the basketball valuation model and cross-sport comparison. The original before/after scholarship analysis still needs separate historical outcome and social data.
