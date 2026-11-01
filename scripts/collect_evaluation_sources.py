"""Download documented public recruiting, draft, roster and basketball-value layers.

No credentials or paid calls. Cached bytes, URLs and hashes make reruns auditable.
NBA Stats asset ending year is one greater than draft year; audit picks
against a separate ESPN export; disagreements remain explicit review flags.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess

import pandas as pd
from collect_performance import normalize

ROOT = Path(__file__).resolve().parents[1]
SDV = 'https://github.com/sportsdataverse/sportsdataverse-data/releases/download/'


def fetch_asset(task):
    url, path = task
    path.parent.mkdir(parents=True, exist_ok=True)
    meta_path = path.with_suffix('.meta.json')
    if path.exists() and meta_path.exists():
        meta = json.loads(meta_path.read_text())
        if meta['url'] != url or meta['sha256'] != hashlib.sha256(path.read_bytes()).hexdigest():
            raise ValueError(f'Cache provenance mismatch: {path.name}')
        return meta
    temporary = path.with_suffix('.part')
    result = subprocess.run(['curl', '--fail', '--location', '--silent', '--show-error',
        '--max-time', '60', '--output', str(temporary), url], capture_output=True, text=True, timeout=65)
    if result.returncode:
        temporary.unlink(missing_ok=True)
        raise ValueError(f'Download failed for {path.name}: {result.stderr.strip()}')
    frame = pd.read_parquet(temporary)
    if frame.empty:
        raise ValueError(f'Empty source: {path.name}')
    payload = temporary.read_bytes()
    temporary.replace(path)
    meta = dict(url=url, file=str(path.relative_to(path.parents[1])), rows=len(frame),
                bytes=len(payload), sha256=hashlib.sha256(payload).hexdigest(),
                retrieved_at=datetime.now(timezone.utc).isoformat())
    meta_path.write_text(json.dumps(meta, indent=2)+'\n')
    return meta


def normalize_nba_draft(stats, espn, draft_year):
    """Retain NBA Stats values and flag secondary-export disagreement for review."""
    if set(stats.season.astype(int)) != {draft_year + 1} or set(espn.season.astype(int)) != {draft_year}:
        raise ValueError('Unexpected NBA source season labels')
    a, b = stats.copy(), espn.copy()
    a['Name_Key'] = a.player_name.map(normalize)
    b['Name_Key'] = b.athlete_display_name.map(normalize)
    keys = ['Name_Key', 'overall_pick']
    if a.duplicated(keys).any() or b.duplicated(keys).any():
        raise ValueError('Duplicate NBA draft identity/pick')
    merged = a.merge(b[['Name_Key', 'overall_pick', 'round']], on=keys, how='left', validate='one_to_one')
    merged['Draft_Source_Agreement'] = merged.round_number.eq(merged['round'])
    merged['Draft_Year'] = draft_year
    return merged


def run(args):
    folder = args.outdir
    tasks = []
    def add(tag, filename, subfolder):
        tasks.append((SDV + tag + '/' + filename, folder/subfolder/filename))
    for year in range(args.start_year, args.end_year+1):
        add('cfb_recruits', f'cfb_recruits_{year}.parquet', 'football_recruits')
        add('espn_cfb_rosters', f'cfb_rosters_{year}.parquet', 'football_rosters')
        add('mbb_player_value', f'mbb_player_value_{year}.parquet', 'basketball_values')
    for year in range(2018, args.end_year+1):
        add('nba_stats_draft', f'draft_{year+1}.parquet', 'nba_stats_draft')
        add('espn_nba_draft', f'draft_{year}.parquet', 'espn_nba_draft')
    for year in [2025, 2026]:
        add('cfb_groups', f'cfb_team_group_seasons_{year}.parquet', 'football_groups')
    tasks.append(('https://github.com/nflverse/nflverse-data/releases/download/draft_picks/draft_picks.parquet',
                  folder/'nfl_draft/draft_picks.parquet'))
    tasks.append(('https://github.com/nflverse/nflverse-data/releases/download/players/players.parquet',
                  folder/'nfl_players/players.parquet'))
    with ThreadPoolExecutor(max_workers=4) as pool:
        metadata = list(pool.map(fetch_asset, tasks))
    drafts = []
    for year in range(2018, args.end_year+1):
        frame = normalize_nba_draft(pd.read_parquet(folder/f'nba_stats_draft/draft_{year+1}.parquet'),
                                   pd.read_parquet(folder/f'espn_nba_draft/draft_{year}.parquet'), year)
        drafts.append(frame)
    nba = pd.concat(drafts, ignore_index=True)
    nba.to_csv(folder/'nba_draft_normalized.csv', index=False)
    manifest = dict(sources=metadata, requested_window=[args.start_year,args.end_year],
        nba_draft_rows=len(nba), nba_draft_agreement=int(nba.Draft_Source_Agreement.sum()),
        limits=['Football recruit export does not retain HS/JUCO classification; not verified HS ratings.',
                'Observed college seasons are lower bounds, not confirmed career duration.',
                'NBA draft no-match is not a verified undrafted outcome.',
                'Secondary ESPN export disagrees frequently on pick order; NBA Stats values retained with review flags.'])
    (folder/'collection_manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
    print(json.dumps({k:v for k,v in manifest.items() if k!='sources'}, indent=2))


if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--outdir',type=Path,default=ROOT/'Data/private/evaluation')
    p.add_argument('--start-year',type=int,default=2012)
    p.add_argument('--end-year',type=int,default=2026)
    a=p.parse_args()
    if not 2006 <= a.start_year <= 2018 or a.end_year != 2026:
        p.error('This reviewed source plan requires start 2006–2018 and end 2026; revise deliberately for later seasons.')
    run(a)
