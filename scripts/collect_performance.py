"""Cache official API responses and join only unambiguous identities.

CFBD: /ppa/players/season?year=YEAR&threshold=1
CBBD: /stats/player/season?season=YEAR (season is the ending year).
No silent zero imputation, fuzzy acceptance, or disabled TLS verification.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import unicodedata

import pandas as pd
import requests
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
OFFENSE = {'QB', 'RB', 'WR', 'TE', 'FB'}


def normalize(value):
    if pd.isna(value):
        return ''
    value = unicodedata.normalize('NFKD', str(value)).encode('ascii', 'ignore').decode()
    return re.sub(r'[^a-z0-9]', '', value.lower())


def records_to_frame(records, sport, season):
    if not isinstance(records, list) or not records:
        raise ValueError('Expected a nonempty API JSON array; no dataset was generated.')
    rows = []
    for record in records:
        required = {'name', 'team', 'position', 'season', 'id' if sport == 'football' else 'athleteId'}
        if not required.issubset(record) or record['season'] != season:
            raise ValueError('Unexpected API schema or season; inspect cached response.')
        metric = (record.get('averagePPA', {}).get('all') if sport == 'football'
                  else record.get('PORPAG'))
        rows.append(dict(api_id=str(record['id' if sport == 'football' else 'athleteId']),
                         api_name=record['name'], api_team=record['team'],
                         api_position=record['position'], performance=metric))
    frame = pd.DataFrame(rows)
    frame['performance'] = pd.to_numeric(frame.performance, errors='raise')
    return frame


def join_sample(sample, performance, sport):
    """Use API ID if provided; otherwise exact normalized name+historical team.

    A transfer can set 'Performance College' to the independently verified prior
    team. No guessed aliases. Position must also agree. Rejected candidates remain
    in the output for review; their performance stays missing.
    """
    required = {'Player Name', 'College', 'Position'}
    if sample.empty or not required.issubset(sample.columns):
        raise ValueError(f'Sample requires {sorted(required)}')
    results = []
    for _, row in sample.iterrows():
        result = row.to_dict()
        result.update(Performance=float('nan'), Performance_API_ID='',
                      Performance_Name='', Performance_Team='', Match_Status='unmatched')
        if sport == 'football' and row['Position'] not in OFFENSE:
            result['Match_Status'] = 'metric_not_applicable'
            results.append(result)
            continue
        candidates = performance
        has_id = pd.notna(row.get('Performance API ID')) and str(row.get('Performance API ID', '')).strip()
        if has_id:
            candidates = candidates[candidates.api_id.eq(str(row['Performance API ID']))]
        else:
            team = row.get('Performance College')
            if pd.isna(team) or not str(team).strip():
                team = row['College']
            candidates = candidates[
                candidates.api_name.map(normalize).eq(normalize(row['Player Name'])) &
                candidates.api_team.map(normalize).eq(normalize(team))]
        if len(candidates) > 1:
            result['Match_Status'] = 'ambiguous'
        elif len(candidates) == 1:
            candidate = candidates.iloc[0]
            result.update(Performance_API_ID=candidate.api_id, Performance_Name=candidate.api_name,
                          Performance_Team=candidate.api_team)
            same_name = normalize(candidate.api_name) == normalize(row['Player Name'])
            same_position = normalize(candidate.api_position) == normalize(row['Position'])
            # Basketball sources often use G/F/C vs PG/SG/SF/PF. Explicit review
            # is preferable to automatically assuming a role crosswalk.
            if not same_name or not same_position:
                result['Match_Status'] = 'identity_review_required'
            elif pd.isna(candidate.performance):
                result['Match_Status'] = 'metric_missing'
            else:
                result.update(Performance=candidate.performance, Match_Status='exact_id' if has_id else 'exact_name_team')
        results.append(result)
    return pd.DataFrame(results)


def collect(sport, season, raw_json=None, refresh=False, env_file=None):
    load_dotenv(env_file or ROOT / '.env')
    folder = ROOT / 'Data/private'
    path = Path(raw_json) if raw_json else folder / f'{sport}_performance_{season}.json'
    if raw_json or (path.exists() and not refresh):
        payload = path.read_bytes()
        records = json.loads(payload)
    else:
        names = (['CFBD_KEY', 'CFBD_API_KEY'] if sport == 'football'
                 else ['CBBD_API_KEY', 'CBBD_KEY', 'CFBD_KEY', 'CFBD_API_KEY'])
        key = next((os.getenv(k) for k in names if os.getenv(k)), None)
        if not key:
            raise ValueError(f'No API key configured. Set {names[0]} locally in .env; never commit it.')
        base = 'collegefootballdata' if sport == 'football' else 'collegebasketballdata'
        endpoint = '/ppa/players/season' if sport == 'football' else '/stats/player/season'
        params = {'year': season, 'threshold': 1} if sport == 'football' else {'season': season}
        url = f'https://api.{base}.com{endpoint}'
        token = key.strip().removeprefix('Bearer ').strip()
        response = requests.get(url, params=params, headers={'Authorization': f'Bearer {token}'}, timeout=45)
        if response.status_code != 200:
            raise ValueError(f'API returned HTTP {response.status_code}; no modeling output written.')
        records = response.json()
        records_to_frame(records, sport, season)  # validate before caching
        payload = json.dumps(records, indent=2).encode()
        folder.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
        metadata = dict(url=url, params=params, retrieved_at=datetime.now(timezone.utc).isoformat(),
                        sha256=hashlib.sha256(payload).hexdigest(), record_count=len(records))
        path.with_suffix('.meta.json').write_text(json.dumps(metadata, indent=2) + '\n')
    return records_to_frame(records, sport, season), hashlib.sha256(payload).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sport', choices=['football', 'basketball'], required=True)
    parser.add_argument('--season', type=int, required=True)
    parser.add_argument('--sample', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--download-only', action='store_true',
                        help='Download the full official performance layer before a NIL sample exists')
    parser.add_argument('--env-file', type=Path, help='Local credentials file, never copied to the output')
    parser.add_argument('--raw-json', type=Path)
    parser.add_argument('--refresh', action='store_true')
    args = parser.parse_args()
    if not args.download_only and args.sample is None:
        parser.error('--sample is required unless --download-only is selected')
    if args.sample is not None and args.output.resolve() == args.sample.resolve():
        parser.error('Output must not overwrite input sample')
    try:
        frame, digest = collect(args.sport, args.season, args.raw_json, args.refresh, args.env_file)
        if args.download_only:
            result = frame.copy()
        else:
            sample = pd.read_csv(args.sample, dtype={'Performance API ID': 'string'})
            result = join_sample(sample, frame, args.sport)
        result['Performance_Season'] = args.season
        result['Performance_Metric'] = 'PPA_Per_Play' if args.sport == 'football' else 'PORPAG'
        result['Performance_Response_SHA256'] = digest
        args.output.parent.mkdir(parents=True, exist_ok=True)
        result.to_csv(args.output, index=False)
        if not args.download_only:
            print(result.Match_Status.value_counts().to_string())
        print(f'Saved {args.output}. Raw download alone is not a validated NIL modeling dataset.')
    except (ValueError, requests.RequestException, OSError) as exc:
        parser.exit(1, f'Collection stopped: {exc}\n')


if __name__ == '__main__':
    main()
