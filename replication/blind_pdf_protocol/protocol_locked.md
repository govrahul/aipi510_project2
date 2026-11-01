# Operationally blinded football sampling replication

Recorded before collecting any player frame or accessing any partner player data. This is operational separation of collection/implementation, not a preregistered experiment or a claim of strict historical blindness. The write-up itself includes aggregate analysis results; those do not determine the sampling rules below.

## Permitted source read

`/Users/st478/510 project 1/project 2/510_project2_writeup.pdf`, five pages; SHA-256 `fe6fda5a651d9766de3008a9df76f446d1a738aa5f35c27a5e8e1c740eba9705`. Page 3 was also rendered and visually inspected. No repository CSVs, implementation scripts, reports, README, or PROJECT_CONTEXT read.

## Extracted stated protocol (page 3)

- Source: The Sideline, https://thesideline.co, for NIL valuation and player metadata.
- Frame: top 1,000 players in each sport by NIL valuation, collected because of practical collection limitations.
- Football sample: 100 players via quotas: 25 from highest 25%, 50 from middle 50%, 25 from lowest 25% of that 1,000-player frame.
- Statistics are merged afterward by exact and fuzzy player-name matching. Players who did not play last season or were in high school receive zero statistics. This implies high-school players are not automatically excluded from the source frame.

## Not specified

Collection date/time; the exact ranking page, filters, year, and athlete eligibility; tie resolution; treatment of missing or nonnumeric NIL valuations; deduplication; whether quartiles are rank-based or monetary value-based; within-quota selection method; seed or software; replacement policy; treatment of insufficient strata; source pagination and truncation behavior; whether the football frame contains all football players or only college players; whether sample selection occurs before or after matching/statistical completeness checks.

## Deterministic implementation assumptions fixed before collection

1. Collect the current publicly available Sideline football NIL ranking, record retrieval timestamps, original URLs, response metadata, raw payload hashes, and any filters. Do not use partner data, private/paid APIs, or bypass access controls.
2. Use source rank if a descending numeric NIL ranking can be verified. Otherwise sort valid numeric valuations descending, then stable source athlete identifier ascending (fallback: normalized player name + school + class). Keep one record per source identifier, failing on irreconcilable duplicates. Keep the source's football eligibility as supplied, without excluding high-school players by inference.
3. Do not proceed as an exact protocol replication unless a complete 1,000-player ranked frame with numeric NIL values is available. Report an incomplete frame; do not silently sample a smaller population or replace it with another source.
4. Interpret percentages as rank strata: ranks 1-250, 251-750, 751-1,000. This gives exactly 250/500/250 records and resolves rank-boundary value ties through the source's stable ordering. Preserve source ties/ranks and report how the top-1,000 cutoff was resolved.
5. Select without replacement within each stratum using a stable pseudorandom SHA-256 priority: hash UTF-8 `aipi510-blind-football-v1|20261101|{stratum}|{source_id}`; choose the 25/50/25 smallest hexadecimal hashes, breaking an impossible hash tie by source ID. This algorithm is portable and deterministic. `20261101` is an explicitly chosen independent seed, not asserted to be the partner's seed.
6. Preserve output in original rank order, with source ID, source rank, stratum, NIL value, sample hash, and available metadata. Do not filter based on later performance data availability.
7. Compare with partner data only after explicit unblinding. A mismatch is not evidence of implementation error because the date, randomization, and seed were unspecified.

## Statistical implication of stated allocation

The quota allocation is proportional: 25/250 = 50/500 = 25/250 = 10%. Under independent uniform random selection within strata, every frame member has the same 10% marginal inclusion probability. Therefore it ensures the three rank-band counts, but it does not disproportionally oversample the highest-valued quarter. It also cannot address coverage bias from omitting all players outside the top 1,000. Random selection within quotas is an assumption, not established by the term quota sampling.
