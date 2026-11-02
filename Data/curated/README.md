# Curated research data

- `basketball_instagram_100.csv`: completed original 100-player basketball
  follow-up cohort, ordered by frozen NIL stratum/rank. All 100 have follower
  counts, with 25 players per full-frame NIL quartile. Full provenance columns
  remain in this CSV.
- `basketball_instagram_100.xlsx`: readable 24-column Excel view of those same
  100 records, including numeric counts/NIL estimates, stable IDs and sources.
- `basketball_manual_followers_20261102.csv`: 21 user reports supplied by Sam
  on November 2, 2026. Twenty fill missing counts; Ali Diouf's 971 corroborates
  the existing browser observation and does not create a duplicate.
- `reviewed_career_events.csv`: previously reviewed career-event evidence.

`Instagram_Count_Provenance` distinguishes `browser_observed` (80) from
`user_reported` (20). Manual report dates are submission dates, not measurement
dates. The user did not supply manual account handles, observation timestamps
or original display precision; those remain unknown. Existing browser records
are preserved. No missing source field is converted to zero.

Reproduction and source limitations are in `docs/basketball_instagram_100.md`;
completion hashes and checks are in
`reports/basketball_instagram_100/manual_completion_audit.json`. The full
5,348-listing source frame and bulk HTML remain local under `Data/private/`.
This 100-player study extract is committed at Sam's explicit request. It is a
current November 2026 listing, not an established 2025–26 membership snapshot.
