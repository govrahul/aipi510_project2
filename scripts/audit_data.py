"""Audit inherited data without modifying it. Run from any directory."""
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def audit(root=ROOT):
    data = pd.read_csv(root / 'Data/football_modeling_data.csv')
    raw = pd.read_csv(root / 'Data/NIL and Player History Data - Football Sample.csv')
    frame = pd.read_csv(root / 'Data/football_top1000.csv')
    sample = pd.read_csv(root / 'Data/football_sample_100.csv')
    keys = ['Player Name', 'College']
    values = pd.to_numeric(frame.Valuation.str.replace('$', '', regex=False)
                           .str.replace('M', 'e6').str.replace('K', 'e3'))
    q25, q75 = values.quantile([.25, .75])
    counts = {'Top_25': int((values >= q75).sum()),
              'Middle_50': int(((values > q25) & (values < q75)).sum()),
              'Bottom_25': int((values <= q25).sum())}
    unsupported = ~data.Position.isin(['QB', 'RB', 'WR', 'TE', 'FB'])
    joined = data.merge(raw, on=keys, suffixes=('_model', '_raw'), validate='one_to_one')
    source_equal = all(joined[f'{c}_model'].equals(joined[f'{c}_raw'])
                       for c in raw.columns if c not in keys)
    return {
        'rows': {'football_frame': len(frame), 'football_sample': len(sample),
                 'football_enriched_raw': len(raw), 'football_modeling': len(data)},
        'duplicate_player_school_rows': int(data.duplicated(keys).sum()),
        'missing_by_column': data.isna().sum().to_dict(),
        'raw_fields_preserved': source_equal,
        'sample_is_subset_of_frame': set(map(tuple, sample[keys].values)).issubset(
            set(map(tuple, frame[keys].values))),
        'quota_population_counts_with_ties': counts,
        'quota_sample_counts': sample.Valuation_Tier.value_counts().to_dict(),
        'power4_counts': data.Power_4_Dummy.value_counts().to_dict(),
        'freshmen': int(data.Freshman_Flag.sum()),
        'ppa_zero_count': int(data.PPA_Per_Play.eq(0).sum()),
        'nonzero_ppa_on_defense_or_offensive_line': int(
            (unsupported & data.PPA_Per_Play.ne(0)).sum()),
        'log_instagram_max_error': float(np.max(np.abs(
            data.Log_Instagram - np.log1p(data['Instagram Followers'])))),
        'log_valuation_max_error': float(np.max(np.abs(
            data.Log_Valuation - np.log(data.Valuation)))),
        'pre_nil_observations': 'unavailable: no observation or decision dates',
        'scholarship_outcomes': 'unavailable',
        'basketball_data': 'unavailable',
        'performance_match_provenance': 'unavailable in inherited CSV',
        'source_urls_dates_and_value_types': 'unavailable in inherited CSV',
    }


if __name__ == '__main__':
    output = ROOT / 'reports/data_audit.json'
    output.parent.mkdir(exist_ok=True)
    output.write_text(json.dumps(audit(), indent=2) + '\n')
    print(output)
