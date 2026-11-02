"""Sample exactly 250 rows per rank quartile from an explicitly defined frame.

Quartiles describe the FULL eligible input frame, not an implicit top-1000 cut.
Ties are ordered by stable IDs and flagged; equal-valued players may cross strata.
Original source files and the older 100-player sampler are never overwritten.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

LABELS = ['Q4_Highest', 'Q3_Upper_Middle', 'Q2_Lower_Middle', 'Q1_Lowest']


def sample_quartiles(data, metric, ids, per_quartile=250, seed=510):
    required = [metric, *ids]
    if any(c not in data for c in required) or data.empty:
        raise ValueError(f'Need a nonempty frame containing {required}')
    if data[required].isna().any().any() or data.duplicated(ids).any():
        raise ValueError('Frame IDs and stratification metric must be complete and unique')
    result = data.copy()
    result['Stratification_Value'] = pd.to_numeric(result[metric], errors='raise')
    if not np.isfinite(result.Stratification_Value).all():
        raise ValueError('Non-finite stratification values')
    # Sorting IDs as strings keeps the random draw independent of input row order.
    tie_keys = []
    for i, col in enumerate(ids):
        key = f'__tie_{i}'
        result[key] = result[col].astype(str)
        tie_keys.append(key)
    result = result.sort_values(['Stratification_Value', *tie_keys],
                                ascending=[False, *([True] * len(tie_keys))], kind='stable').reset_index(drop=True)
    result['Frame_Rank'] = np.arange(1, len(result) + 1)
    result['Quartile'] = [LABELS[min(3, i * 4 // len(result))] for i in range(len(result))]
    result['Stratification_Metric'] = metric
    counts = result.Quartile.value_counts()
    if any(counts.get(label, 0) < per_quartile for label in LABELS):
        raise ValueError(f'Need >= {per_quartile} eligible rows in every quartile; counts={counts.to_dict()}')
    result['Stratum_Population_N'] = result.Quartile.map(counts).astype(int)
    result['Selection_Probability'] = per_quartile / result.Stratum_Population_N
    result['Sampling_Weight'] = 1 / result.Selection_Probability
    crossed_values = result.groupby('Stratification_Value').Quartile.nunique()
    result['Metric_Tie_Crosses_Quartile'] = result.Stratification_Value.isin(crossed_values[crossed_values > 1].index)
    rng = np.random.default_rng(seed)
    sampled = pd.concat([result.loc[rng.choice(result.index[result.Quartile.eq(label)], per_quartile,
                                              replace=False)] for label in LABELS])
    sampled = sampled.sort_values('Frame_Rank').drop(columns=tie_keys).reset_index(drop=True)
    sampled.insert(0, 'Sample_Row', np.arange(1, len(sampled) + 1))
    result = result.drop(columns=tie_keys)
    audit = dict(seed=seed, input_frame_rows=len(result), sample_rows=len(sampled),
                 sample_per_quartile=sampled.Quartile.value_counts().to_dict(),
                 population_per_quartile=counts.to_dict(), metric=metric,
                 tie_policy='Descending metric, stable string IDs; rank quartiles, not strict value bins',
                 rows_in_ties_crossing_quartiles=int(result.Metric_Tie_Crosses_Quartile.sum()),
                 stratum_ranges={label: dict(min=float(group.Stratification_Value.min()),
                                            max=float(group.Stratification_Value.max()))
                                 for label, group in result.groupby('Quartile')},
                 note='Weights target this input frame only; do not repair exclusions outside it')
    return result, sampled, audit


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--metric', required=True)
    parser.add_argument('--id-columns', nargs='+', required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--frame-description', required=True)
    parser.add_argument('--seed', type=int, default=510)
    args = parser.parse_args()
    if args.output.resolve() == args.input.resolve():
        parser.error('Sample must not overwrite the input frame')
    try:
        data = pd.read_csv(args.input, dtype={c: 'string' for c in args.id_columns})
        _, sample, audit = sample_quartiles(data, args.metric, args.id_columns, seed=args.seed)
        audit.update(frame_description=args.frame_description, input_sha256=hashlib.sha256(args.input.read_bytes()).hexdigest(),
                     generated_at=datetime.now(timezone.utc).isoformat())
        args.output.parent.mkdir(parents=True, exist_ok=True)
        sample.to_csv(args.output, index=False)
        args.output.with_suffix('.meta.json').write_text(json.dumps(audit, indent=2) + '\n')
        print(json.dumps(audit, indent=2))
    except (ValueError, OSError) as exc:
        parser.exit(1, f'Sampling stopped: {exc}\n')
