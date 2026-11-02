"""Prepare a reproducible top-1000 frame and stratified sample from an authorized CSV.

This imports a CSV export; it does not circumvent source access restrictions.
Ties are broken by player name and college so strata contain 250/500/250 rows.
Outputs default to ignored local storage because source redistribution rights vary.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def parse_valuation(value):
    text = str(value).strip().upper().replace('$', '').replace(',', '')
    match = re.fullmatch(r'(\d+(?:\.\d+)?)\s*([KM]?)', text)
    if not match:
        raise ValueError(f'Invalid valuation: {value!r}; missing is not zero.')
    result = float(match[1]) * {'': 1, 'K': 1000, 'M': 1000000}[match[2]]
    if result <= 0:
        raise ValueError('Valuation must be positive')
    return result


def prepare(data, seed=510):
    required = {'Player Name', 'College', 'Position', 'Conference', 'Grade', 'Valuation'}
    if not required.issubset(data.columns):
        raise ValueError(f'Required columns: {sorted(required)}')
    if len(data) < 1000 or data.duplicated(['Player Name', 'College']).any():
        raise ValueError('Need at least 1000 distinct player-school rows')
    if data[list(required)].isna().any().any():
        raise ValueError('Missing required frame fields')
    data = data.copy()
    data['raw_val'] = data.Valuation.map(parse_valuation)
    data = data.sort_values(['raw_val', 'Player Name', 'College'],
                            ascending=[False, True, True], kind='stable').head(1000).reset_index(drop=True)
    data['Rank'] = np.arange(1, 1001)
    data['Valuation_Tier'] = np.repeat(['Top_25', 'Middle_50', 'Bottom_25'], [250, 500, 250])
    rng = np.random.default_rng(seed)
    sample = pd.concat([data.loc[rng.choice(data.index[data.Valuation_Tier.eq(tier)], n, replace=False)]
                        for tier, n in [('Top_25', 25), ('Middle_50', 50), ('Bottom_25', 25)]], ignore_index=True)
    return data, sample


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--sport', choices=['football', 'basketball'], required=True)
    parser.add_argument('--source-url', required=True)
    parser.add_argument('--observed-at', required=True, help='Actual source snapshot date, ISO 8601')
    parser.add_argument('--outdir', type=Path, default=ROOT / 'Data/private')
    args = parser.parse_args()
    datetime.fromisoformat(args.observed_at)
    frame, sample = prepare(pd.read_csv(args.input))
    args.outdir.mkdir(parents=True, exist_ok=True)
    frame.to_csv(args.outdir / f'{args.sport}_top1000.csv', index=False)
    sample.to_csv(args.outdir / f'{args.sport}_sample_100.csv', index=False)
    metadata = dict(source_url=args.source_url, observed_at=args.observed_at,
                    imported_at=datetime.now(timezone.utc).isoformat(), seed=510,
                    input_sha256=hashlib.sha256(args.input.read_bytes()).hexdigest(),
                    sample_design='25/50/25 simple random draws within rank strata; deterministic tie breaking')
    (args.outdir / f'{args.sport}_sample.meta.json').write_text(json.dumps(metadata, indent=2) + '\n')
    print('Saved frame, sample and provenance. Confirm source rights before uploading data.')
