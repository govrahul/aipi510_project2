"""Build the requested 1,000-player NIL sample before collecting social counts.

Requires a real source-authorized NIL frame. Exactly 250 per full-frame rank
quartile; performance/social missingness never changes which players are drawn.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re

import pandas as pd
from collect_performance import join_sample
from prepare_sample import parse_valuation
from sample_quartiles import sample_quartiles

ROOT = Path(__file__).resolve().parents[1]


def build(nil_data, performance):
    required = {'Player Name', 'College', 'Position', 'Valuation'}
    if not required.issubset(nil_data.columns):
        raise ValueError(f'NIL input needs {sorted(required)}')
    if nil_data[list(required)].isna().any().any():
        raise ValueError('NIL identity, position and valuation fields must be populated')
    data = nil_data.copy()
    def parse_sampling_value(value):
        cleaned = str(value).strip().upper().replace('$', '').replace(',', '')
        # A source-reported zero belongs in the sampling frame; unknown is not zero.
        if re.fullmatch(r'0(?:\.0+)?\s*[KM]?', cleaned):
            return 0.0
        return parse_valuation(value)
    data['NIL_Valuation_USD'] = data.Valuation.map(parse_sampling_value)
    if 'athlete_id' not in data:
        # Internal stable frame key, explicitly NOT a verified external athlete ID.
        data['athlete_id'] = ['frame:' + hashlib.sha256(f'{name}|{school}'.encode()).hexdigest()[:20]
                              for name, school in data[['Player Name', 'College']].itertuples(index=False, name=None)]
        data['Athlete_ID_Type'] = 'internal_name_school_key_requires_identity_verification'
    else:
        data['Athlete_ID_Type'] = 'source_provided_verify_id_namespace_before_join'
    _, sample, audit = sample_quartiles(data, 'NIL_Valuation_USD', ['athlete_id'])
    # Only exact name/historical-team/position matches are automatically accepted.
    frame = performance.rename(columns={'athlete_id': 'api_id', 'Player_Name': 'api_name',
                                       'College': 'api_team', 'Position': 'api_position',
                                       'Points_Per_Game': 'performance'})
    frame['api_id'] = frame.api_id.astype(str)
    result = join_sample(sample, frame, 'basketball')
    result['Performance_Metric'] = 'ESPN_Points_Per_Game_supplemental_not_PORPAG'
    for column in ['Instagram_Username', 'Username_Verification_URL', 'Instagram_Followers', 'Instagram_Observed_At']:
        if column not in result:
            result[column] = None
    result['Instagram_Count_Status'] = 'not_collected'
    result['Sport'] = 'basketball'
    audit['performance_matches'] = result.Match_Status.value_counts().to_dict()
    audit['sampling_order'] = 'Sample by NIL first; left-join performance; retain every selected player'
    return result, audit


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--nil-frame', type=Path, required=True)
    parser.add_argument('--performance', type=Path,
        default=ROOT / 'Data/private/basketball/division_i_player_team_season_2026.csv')
    parser.add_argument('--output', type=Path,
        default=ROOT / 'Data/private/basketball/basketball_nil_quartiles_1000.csv')
    parser.add_argument('--source-url', required=True)
    parser.add_argument('--nil-observed-at', required=True)
    args = parser.parse_args()
    if args.output.resolve() in [args.nil_frame.resolve(), args.performance.resolve()]:
        parser.error('Output must not overwrite a source')
    try:
        datetime.fromisoformat(args.nil_observed_at)
        result, audit = build(pd.read_csv(args.nil_frame, dtype={'athlete_id': 'string'}),
                              pd.read_csv(args.performance, dtype={'athlete_id': 'string'}))
        result['NIL_Source_URL'], result['NIL_Observed_At'] = args.source_url, args.nil_observed_at
        audit.update(nil_source_url=args.source_url, nil_observed_at=args.nil_observed_at,
                     input_sha256=hashlib.sha256(args.nil_frame.read_bytes()).hexdigest(),
                     generated_at=datetime.now(timezone.utc).isoformat())
        args.output.parent.mkdir(parents=True, exist_ok=True)
        result.to_csv(args.output, index=False)
        args.output.with_suffix('.meta.json').write_text(json.dumps(audit, indent=2) + '\n')
        print(json.dumps(audit, indent=2))
    except (ValueError, OSError) as exc:
        parser.exit(1, f'Build stopped: {exc}\n')
