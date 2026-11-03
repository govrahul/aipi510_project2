# Corrected basketball social sample — November 3, 2026

Sam requested **top 1,000 basketball NIL listings first**, quartiles inside that
population, then Instagram collection for 25 randomly sampled players per
quartile. The previous all-5,348-frame draw was incorrect for this population.
It remains in legacy files for provenance; do not combine the samples as if
they were independent observations or reuse its model results here.

The readable spreadsheet is `Data/curated/basketball_top1000_instagram_100.xlsx`.
Its matching CSV has all provenance fields. The 1,000-row source frame is
`Data/curated/basketball_top1000_nil_frame.csv`; it has **250 per quartile**,
not 1,000 observed follower counts. The social sheet has **100 rows, 100 counts**:
99 browser observations and one user report.

| Stratum inside top 1,000 | Global source ranks | Frame | Selected | Counts |
|---|---|---:|---:|---:|
| Q4 Highest | 1–250 | 250 | 25 | 25 |
| Q3 Upper middle | 251–500 | 250 | 25 | 25 (24 browser + 1 user) |
| Q2 Lower middle | 501–750 | 250 | 25 | 25 |
| Q1 Lowest | 751–1000 | 250 | 25 | 25 |

Seed 510; sampling probability .1 and weight 10 throughout. The source ranking
was captured November 2, 2026. Exact integer follower tooltips were read through
the public profile UI November 3. Frozen source IDs, valuation, rank and draw
are unchanged after lookup. Only two players overlap the previous sample;
their counts were measured again. No old manual values were reused.

Each athlete was searched in Google in Chrome as **player name + source school
+ instagram**. The first Instagram result was opened. For school/team posts,
the named athlete's coauthor/tag links or visible Tagged users dialog resolved
nonliteral handles. Irrelevant first results were rejected rather than counted.
Examples: Duke's Brock Davis post → `brockingston`; UCLA's Eric Freeny post →
`eric_freeny`; Big 12's Abdullah Ahmed video → `bidoo_34`. Identity evidence can
come from an earlier school; it does not establish current roster membership.
Direct matching profiles were reviewed in the context of the name/school query;
this is source-based entity review, not a guarantee of account ownership.

**One manually completed count:** row 33, Alex K'Medehouto, source school Maryland,
global rank 353. A named South Plains-to-UTEP post tags
`kmedehouto_atsouvi_alexandre`; another named video tags `kmedehouto_alexandre`.
Both profile pages were unavailable. A focused Instagram surname search did
not establish another account. Sam replied **675** to the missing-account
question. His count is recorded as user reported on November 3; his handle,
actual observation time and original display precision remain unknown. The
failed-account identity evidence remains separate from the manual count source.
No player was replaced to improve coverage.

## Reproduce and review

The committed `replication/basketball_top1000/` contains the source top-1,000
extract, frozen sample, all 100 first-result Google receipts, identity reviews,
99 browser follower receipts, Sam's one manual report and sampling audit. Raw full-site HTML, unrelated comments,
credentials and browsing account data are not committed. Browser functions in
`scripts/collect_basketball_google_instagram.mjs` document the actual public-UI
method; manual identity/tag review is intentionally required. The module runs
inside an authorized CUA session with a bound tab, not as an unattended scraper.

```bash
python scripts/prepare_basketball_top1000_social.py \
  --source replication/basketball_top1000/source_top1000_snapshot.csv \
  --output-dir outputs/top1000-replay
python scripts/finalize_basketball_top1000_social.py
node scripts/build_basketball_top1000_workbook.mjs
python -m unittest discover -s Tests -p 'test_*.py'
```

Use the project Python requirements; author XLSX with the bundled artifact-tool
runtime (`node_modules` symlink to the bundled dependencies). The sampling replay
from the committed top-1,000 extract reproduces the frozen CSV byte-for-byte:
SHA256 `f0947e4377ad89c8f67d2fc07b6a6cd7356cdc932cdaa7c18598bd5936dee7e3`.
Its source hash/row count differs from the original full-frame audit because
only the 1,000-row extract is published; the draw and frame hashes match.
The finalizer rejects changed frozen data, duplicate/unknown receipt rows,
unreviewed handles, conflicting integers and mismatched reviewed athlete IDs.

## Analysis implications

Selection weights describe the listed top 1,000 only. All 100 counts are recorded,
but keep the user-report flag and include a browser-only sensitivity analysis
(99 cases, with 24 in Q3). Sam's count has unverified precision and observation
time; weights do not resolve measurement uncertainty. Rank ties across cutpoints
are flagged: 19 frame rows belong to tied prices spanning adjacent quartiles.
NIL values are rounded estimates (PUBLIC/EST labels retained), not actual deals,
scholarships or offers. `Legacy_Full_Frame_Quartile` is historical lineage only;
use `Quartile` for the corrected strata.

This is a current November 2026 listing, not a verified 2025–26 roster.
School/season and candidate ESPN IDs need validation before attaching season
performance, recruiting, draft or career outcomes. The basketball and
combined regressions, report and README were rerun on this sample on
November 3, 2026 (`scripts/make_unified_figures.py`, `BB_SAMPLE`); points per
game are joined by ESPN athlete ID, or by an exact unique name match at the
listed school when no ID is available. None of this establishes causality. Historical pre-decision social
counts and a comparable pre/post evaluation outcome are still needed to answer
the original before/after-NIL coefficient question.
