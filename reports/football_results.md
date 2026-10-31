# Football analysis

Exploratory associations in the inherited selected top-1000 frame. No model here estimates a pre/post NIL effect or a scholarship effect.

The partner models retain unverified PPA solely for replication. The other models omit PPA and cannot control for college performance. HC3 uses a normal-reference Wald test; no one-sided test is claimed.

| Model | N | Social coefficient | 95% CI | Two-sided p | R² |
|---|---:|---:|---|---:|---:|
| partner_replication_HC1 | 100 | 0.2067 | [0.0939, 0.3194] | 0.000327052 | 0.321 |
| partner_replication_HC3 | 100 | 0.2067 | [0.0787, 0.3346] | 0.00154806 | 0.321 |
| without_unverified_PPA_HC3 | 100 | 0.2953 | [0.1016, 0.4889] | 0.00280408 | 0.407 |
| without_unverified_PPA_or_largest_audience_HC3 | 99 | 0.2316 | [0.0705, 0.3927] | 0.00484227 | 0.364 |

The replicated coefficient corresponds approximately to 15.4% higher modeled valuation for twice the followers at sufficiently large follower counts, conditional on included controls. This is an association, not a causal effect.

The coefficient CSV also reports 98.33% intervals for the write-up’s three-test Bonferroni family. Sensitivity models are exploratory, not additional confirmatory discoveries.

Missing data provenance, possible mismatches, selection on valuation, contemporaneous follower measurement, school clustering and sparse conference variation limit inference. HC3 does not fix these problems. Normality tests do not establish independence or causality.
