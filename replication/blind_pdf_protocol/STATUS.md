# Independent blind sampling deliverable

No partner player data or repository implementation was accessed. Only the supplied write-up and current public Sideline pages were consulted. This was operational separation, not a preregistered experiment. The write-up includes aggregate model results, which were not used to choose the sampler.

The sampling protocol was frozen before public player ranking inspection. It specifies a 1,000-player frame with rank strata 1-250, 251-750, 751-1,000, drawing 25/50/25 without replacement by the documented SHA-256 priority algorithm. The seed 20261101 and hashing method are explicit independent assumptions; neither is provided by the write-up.

## Collection result

No independent complete frame was collected; consequently no real-player sample was produced here. The current public football leaderboard describes season 2026, snapshot Oct 31, and 28,382 football athletes. The web reader exposes the first 25 and a client Load 50 more control. This current snapshot could support only a contemporary repeat, not an exact historical same-date replication because the partner collection date is unspecified.

Direct system curl retrieved HTTP 403 for the public football ranking at 2026-11-01T21:03:53.632976Z. The denied response and headers are preserved under raw/, with original payload hash and timestamp in provenance.jsonl. An earlier robots.txt curl attempt also returned 403; Python initially encountered sandbox DNS denial and, with escalation, a local certificate-chain error. No certificate checks were disabled. No denial was bypassed and no paid/private endpoint was used.

Public pages consulted:
- https://thesideline.co/nil-tracker/top-players/football
- https://thesideline.co/terms
- https://thesideline.co/data/usage

The web reader representation is preserved in web_source_evidence.json; it is tool-transformed text, not original HTTP bytes. The older terms page permits reasonable public-API use; the current usage page describes licensed complete files and restricts bulk redistribution. No bulk export was acquired.

## Run sampler

```sh
python3 sample_football.py complete_frame.csv sampled_football.csv
```

Default input columns: source_id, nil_value, optional source_rank. Values must be numeric in base currency units. If source_rank is present, unique ranks 1 through 1,000 are required and descending NIL order is verified. Otherwise, records are sorted by numeric NIL descending then source ID ascending. At least 1,000 unique valid records are required; extra records are truncated only after ordering. If no source ID exists, all name/school/class columns are required to form a normalized fallback ID. Column names can be mapped with --id-column, --nil-column, --rank-column, --name-column, --school-column, --class-column. To ignore an existing rank column deliberately, use --rank-column ''.

Output preserves all source columns and adds rep_source_id, rep_frame_rank, rep_stratum, rep_sample_hash. A JSON manifest accompanies it and includes input/output/protocol/sampler hashes, counts, ordering, timestamp, and limitations. Hash priorities use UTF-8 aipi510-blind-football-v1|20261101|{top,middle,bottom}|{source_id}.

A parent agent may run the locked sampler against a partner frame afterward, labeled a post-lock same-frame algorithm test. That would not be independent frame collection and should not be reported as reproducing the partner's unknown randomization.

## Verification

Synthetic data only: verified 100 unique selected records, quotas 25/50/25, invariance to input-row reversal with source ranks, and rejection of an incomplete frame, conflicting duplicate ID, and nonnumeric NIL value. CLI check verified output and manifest on a synthetic frame; no live or partner player input was used.
