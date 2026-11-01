# Historical football and isolated sampling reconstruction

Updated November 1, 2026 following Sam's request to obtain historical football data in the same way and reconstruct the partner's sampling in a context without his data before comparing.

## Football history collected and strengthened

Historical 2018 and 2019 Division I football frames contain 23,755 and 23,985 player-team rows, respectively. These were previously collected from ESPN/SportsDataverse. New work downloads the documented [nflverse player crosswalk](https://nflreadr.nflverse.com/reference/load_players.html) and joins ESPN ID + exact normalized name, then PFR ID to draft picks. It also applies the same fields to 2025/2026 football.

| College cohort | Source-frame rows | Prior name+college draft links | Links after ID supplement | Pro-history timing flags |
|---|---:|---:|---:|---:|
| 2018 | 23,755 | 702 | 1,028 | 10 |
| 2019 | 23,985 | 687 | 1,039 | 9 |
| 2025 | 26,327 | 188 | 256 | 6 |
| 2026 | 26,094 | 0 | 0 | 1 |

These are source-reported candidate links, not fully adjudicated outcomes. Exact IDs can be misassigned upstream; a matching name alone does not resolve that. Timing flags identify cases where pro history is on/before the supposed college season. For example, a 2025 Texas Tech roster row with the ESPN ID associated with a 2021 NFL draftee requires identity review; it is not silently treated as that college athlete's future outcome. Possible reinstatement/re-enrollment also requires evidence, so timing flags are not automatic deletions. Name/ID disagreements and source conflicts remain explicit.

The supplemented outputs are `Data/private/evaluation/football_nfl_ids/football_YEAR_evaluation_with_NFL_IDs.csv`. Originals are retained. Added fields include NFL ESPN/PFR/GSIS matching status, rookie/last-recorded seasons, crosswalk draft fields, and timing flags. A player record does not establish a paid contract, NFL regular-season appearance, or completed career. No-match is unknown. The full 2012–2026 recruiting/history layers remain available; high-school classification, historical social counts, verified total years and broad pro-contract coverage are still incomplete. Final HS-star-stratified samples were not fabricated, and no all-position football composite was found.

Source URLs and hashes are in `reports/evaluation_sources_manifest.json`; match coverage and output hashes are in `reports/football_nfl_id_audit.json`. Reproduce with:

```bash
python scripts/collect_evaluation_sources.py
python scripts/enrich_player_evaluations.py --reviewed-events Data/curated/reviewed_career_events.csv
python scripts/enrich_football_nfl_ids.py
```

## Isolated reconstruction and comparison

A fresh agent received no chat history and was barred from the partner's CSVs, implementation, README, reports and context files. The PDF itself contains aggregate model results, so this is an operationally blinded sampling reconstruction, not a preregistered or fully outcome-blind experiment. The root agent's previous project knowledge was not erased.

Before looking at public ranking rows, the agent froze its PDF-derived protocol: top 1,000 by NIL, rank groups of 250/500/250, and draws of 25/50/25. It independently fixed seed 20261101 and SHA-256 priorities because the PDF supplies no seed or within-quota randomization. Protocol SHA-256: `6563d747df3101fa9cf75182744b8b8ba9cee41786b4d8ff47444e2fb8ef01f0`. The frozen package is under `replication/blind_pdf_protocol/`.

A complete fresh Sideline frame could not be collected because the source returned HTTP403. The independent agent did not substitute incomplete rows or another ranking source. Its source-check evidence is saved locally. The current source snapshot also would not prove same-date replication of the partner's undated scrape.

After the protocol/code lock, the root ran the independent sampler against the shared 1,000-player partner frame, then opened the saved sample/code to compare. **This is a post-lock same-frame algorithm test, not independent data collection.** The isolated agent never received partner rows or comparison results.

| Check | Result |
|---|---|
| PDF allocation recovered | 25 / 50 / 25, sample size 100 |
| Independent rank stratum populations | 250 / 500 / 250 |
| Partner dollar-cutoff populations (top/middle/bottom) | 266 / 479 / 255 because of ties |
| Shared selected players | 11 of 100 |
| Post-unblinding original-script replay | All 100 players and their order reproduced |
| Original input modification | None; hashes checked before/after |

Different randomization/seeds and boundary rules make different selected names expected. The overlap does not show one implementation is better or wrong. The write-up supports the broad allocation but lacks enough detail to reproduce individuals without the original code/data. Its rank-proportional 25/50/25 design gives nominal 10% inclusion per group under random within-group selection; it does not oversample the highest quarter. Restricting to the top 1,000 still excludes lower-valued athletes.

Comparison commands and outputs:

```bash
python scripts/compare_blind_football_sample.py
python -m unittest discover -s Tests -v
```

Read `reports/blind_football_sampling_comparison.md` and its JSON for hashes, dates, cutoff/probability details, descriptive distributions and limitations. The new 100-player sample is local at `Data/private/replication/postlock_independent_sampler_100.csv`; it does not replace the inherited sample or the new 1,000-player historical HS design. No regression was rerun as part of this sampling comparison.
