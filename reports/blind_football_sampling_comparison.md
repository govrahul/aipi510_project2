# Football sampling comparison

Frozen PDF-only protocol: `6563d747df3101fa9cf75182744b8b8ba9cee41786b4d8ff47444e2fb8ef01f0`. Independent code was frozen at 2026-11-01T21:05:08.000784+00:00 before any partner input was supplied. The isolated agent did not see partner player rows or code. The root agent had previous project knowledge, so this is operational separation, not a claim of strict preregistration.

Fresh source collection returned HTTP403. Therefore the real-data test is **post-lock sampling on the same partner frame**, not an independent collection replication. The contemporary source snapshot would also differ from the unspecified partner collection date.

Both samplers select 100 players with stated 25/50/25 quotas. The independent implementation uses rank groups 250/500/250 and its separately chosen seed 20261101 with SHA-256 priorities. The partner code uses dollar-value percentile cutoffs and seed 510; ties produce populations {'Middle_50': 479, 'Top_25': 266, 'Bottom_25': 255}. Independent nominal inclusion is 10% per rank group; partner tier probabilities are {'Middle_50': '10.44%', 'Top_25': '9.40%', 'Bottom_25': '9.80%'}.

The draws share **11 of 100 players** (Jaccard 0.058). Different randomization and boundary rules make different names expected; this is not a failure to reproduce the stated method. After unblinding, replaying the original code reproduced the saved player set: **True**; exact saved order: **True**. Original files were not modified.

The PDF supports the quota allocation but does not specify the seed or tie convention needed for exact individual reproduction. Its 25/50/25 proportional rank allocation would give equal 10% inclusion under random within-stratum sampling, not extra sampling weight to the highest quarter. The top-1000 restriction still limits population coverage. No regression result was compared or claimed.
