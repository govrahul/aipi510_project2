"""Collect/normalize follower counts for verified athlete handles, preserving rows.

No name-to-handle guessing. Meta supplies current professional-account counts,
not arbitrary historical snapshots. Social Blade requests can consume credits and
are disabled unless --allow-paid-requests is explicitly provided by the operator.
Use --responses-dir to replay source JSON without any network request.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import time

import pandas as pd
import requests
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]


def exact_count(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or pd.isna(value) or value < 0 or value % 1:
        raise ValueError('Follower count must be an exact nonnegative integer, not a rounded K/M label')
    return int(value)


def parse_response(payload, provider, username, retrieved_at, target_date=None, max_lag_days=30):
    if provider == 'meta':
        if target_date:
            raise ValueError('Meta current-count response cannot supply a historical target date')
        data = payload.get('business_discovery', {})
        if str(data.get('username', '')).lower() != username.lower():
            raise ValueError('Returned Instagram username differs from the verified input')
        return dict(Instagram_Followers=exact_count(data.get('followers_count')),
                    Instagram_Observed_At=retrieved_at, Instagram_Account_ID=str(data.get('id', '')),
                    Instagram_Count_Status='observed_current', Instagram_Observation_Precision='retrieval_timestamp')
    if not payload.get('status', {}).get('success'):
        raise ValueError('Provider did not return a successful profile response')
    data = payload.get('data', {})
    if str(data.get('id', {}).get('username', '')).lower() != username.lower():
        raise ValueError('Returned Instagram username differs from the verified input')
    if target_date:
        target = pd.Timestamp(target_date, tz='UTC')
        candidates = []
        for record in data.get('daily', []):
            observed = pd.to_datetime(record.get('date'), utc=True, errors='raise')
            if pd.isna(observed):
                continue
            if observed <= target and (target - observed).days <= max_lag_days:
                candidates.append((observed, exact_count(record.get('followers'))))
        if not candidates:
            raise ValueError('No historical count on/before target within the permitted lag')
        observed, count = max(candidates, key=lambda x: x[0])
        return dict(Instagram_Followers=count, Instagram_Observed_At=observed.strftime('%Y-%m-%d'),
                    Instagram_Account_ID=str(data.get('id', {}).get('id', '')),
                    Instagram_Count_Status='observed_historical', Instagram_Lag_Days=(target-observed).days,
                    Instagram_Observation_Precision='provider_calendar_day')
    return dict(Instagram_Followers=exact_count(data.get('statistics', {}).get('total', {}).get('followers')),
                Instagram_Observed_At=retrieved_at, Instagram_Account_ID=str(data.get('id', {}).get('id', '')),
                Instagram_Count_Status='observed_current', Instagram_Observation_Precision='retrieval_timestamp')


def run(args):
    load_dotenv(args.env_file or ROOT / '.env')
    data = pd.read_csv(args.input, dtype={'athlete_id': 'string'})
    required = {'athlete_id', 'Instagram_Username', 'Username_Verification_URL'}
    if not required.issubset(data.columns):
        raise ValueError(f'Input must contain {sorted(required)}')
    if args.output.resolve() == args.input.resolve():
        raise ValueError('Output must not overwrite the sampling file')
    if not args.responses_dir and args.provider == 'socialblade' and not args.allow_paid_requests:
        raise ValueError('Paid provider requests are disabled. Replay authorized exports or explicitly authorize them at the CLI.')
    if not args.responses_dir:
        names = (['META_ACCESS_TOKEN', 'META_IG_USER_ID', 'META_API_VERSION'] if args.provider == 'meta'
                 else ['SOCIALBLADE_CLIENT_ID', 'SOCIALBLADE_TOKEN'])
        if not all(os.getenv(name) for name in names):
            raise ValueError(f'Missing local credential/configuration variables: {names}')
    if args.max_profiles < 1:
        raise ValueError('Set a positive --max-profiles request cap')
    rows, calls = [], 0
    raw_dir = args.output.parent / 'instagram_responses'
    raw_dir.mkdir(parents=True, exist_ok=True)
    for _, record in data.iterrows():
        row = record.to_dict()
        row.update(Instagram_Followers=None, Instagram_Observed_At=None,
                   Instagram_Count_Status='not_collected', Instagram_Provider=args.provider,
                   Instagram_Response_SHA256=None, Instagram_Collection_Note='')
        username = str(record.get('Instagram_Username', '')).strip().lstrip('@')
        verified = str(record.get('Username_Verification_URL', ''))
        target = record.get('Instagram_Target_Date')
        target = str(target) if pd.notna(target) and str(target).strip() else None
        try:
            if not re.fullmatch(r'[A-Za-z0-9_.]{1,30}', username) or not re.match(r'^https?://\S+$', verified):
                raise ValueError('Missing valid handle or evidence linking it to this athlete')
            historical = str(record.get('Period', '')) == 'Pre_NIL'
            if historical and not target:
                raise ValueError('Historical cohort requires an explicit Instagram_Target_Date; current count refused')
            if args.provider == 'meta' and target:
                raise ValueError('Meta cannot supply the requested historical follower snapshot')
            if args.responses_dir:
                path = args.responses_dir / f'{username}.json'
                metadata = json.loads(path.with_suffix('.meta.json').read_text())
                payload = path.read_bytes()
                if hashlib.sha256(payload).hexdigest() != metadata['sha256']:
                    raise ValueError('Response provenance hash mismatch')
                if metadata.get('provider') != args.provider or metadata.get('username', '').lower() != username.lower():
                    raise ValueError('Cached provider/username does not match input')
                retrieved = metadata['retrieved_at']
            else:
                if calls >= args.max_profiles:
                    raise ValueError('Request cap reached; row retained for a later batch')
                calls += 1
                if args.provider == 'meta':
                    version, caller = os.environ['META_API_VERSION'], os.environ['META_IG_USER_ID']
                    if not re.fullmatch(r'v\d+\.\d+', version) or not caller.isdigit():
                        raise ValueError('Invalid Meta API version or caller ID configuration')
                    response = requests.get(f'https://graph.facebook.com/{version}/{caller}',
                        params={'fields': f'business_discovery.username({username}){{id,username,followers_count}}'},
                        headers={'Authorization': f"Bearer {os.environ['META_ACCESS_TOKEN']}"}, timeout=30)
                else:
                    response = requests.get('https://matrix.sbapis.com/b/instagram/statistics',
                        params={'query': username, 'history': 'vault' if target else 'default'},
                        headers={'clientid': os.environ['SOCIALBLADE_CLIENT_ID'],
                                 'token': os.environ['SOCIALBLADE_TOKEN']}, timeout=30)
                if response.status_code != 200:
                    raise ValueError(f'Provider returned HTTP {response.status_code}; no count recorded')
                payload = response.content
                retrieved = datetime.now(timezone.utc).isoformat()
                path = raw_dir / f'{username}.json'
                path.write_bytes(payload)
                path.with_suffix('.meta.json').write_text(json.dumps(dict(provider=args.provider, username=username,
                    retrieved_at=retrieved, sha256=hashlib.sha256(payload).hexdigest()), indent=2) + '\n')
                time.sleep(1)
            row.update(parse_response(json.loads(payload), args.provider, username, retrieved, target, args.max_lag_days))
            row['Instagram_Response_SHA256'] = hashlib.sha256(payload).hexdigest()
        except (ValueError, OSError, requests.RequestException, KeyError) as exc:
            row['Instagram_Count_Status'] = 'missing_or_needs_review'
            # Do not print request URLs/headers or an exception that might expose credentials.
            row['Instagram_Collection_Note'] = str(exc) if isinstance(exc, (ValueError, KeyError)) else type(exc).__name__
        rows.append(row)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(args.output, index=False)
    print(pd.DataFrame(rows).Instagram_Count_Status.value_counts().to_string())


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--provider', choices=['meta', 'socialblade'], required=True)
    parser.add_argument('--env-file', type=Path)
    parser.add_argument('--responses-dir', type=Path)
    parser.add_argument('--max-profiles', type=int, default=10)
    parser.add_argument('--max-lag-days', type=int, default=30)
    parser.add_argument('--allow-paid-requests', action='store_true')
    args = parser.parse_args()
    try:
        run(args)
    except (ValueError, OSError) as exc:
        parser.exit(1, f'Collection stopped: {exc}\n')
