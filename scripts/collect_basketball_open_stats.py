"""Collect published ESPN men's college basketball box scores via SportsDataverse.

Supplemental performance source while CBBD credentials are unavailable. This is
not a NIL-ranked sample, a follower dataset, or a replacement for CBBD PORPAG.
Official loader/asset reference:
https://py.sportsdataverse.org/docs/mbb/reference/loaders/player
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess

import numpy as np
import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
BASE = 'https://github.com/sportsdataverse/sportsdataverse-data/releases/download/'
ASSETS = {
    'boxscores': ('espn_mens_college_basketball_player_boxscores/player_box_{season}.parquet', 'player'),
    'groups': ('mbb_groups/mbb_team_group_seasons_{season}.parquet', 'team'),
}
STATS = ['minutes', 'points', 'rebounds', 'assists', 'steals', 'blocks', 'turnovers',
         'field_goals_made', 'field_goals_attempted', 'three_point_field_goals_made',
         'three_point_field_goals_attempted', 'free_throws_made', 'free_throws_attempted']


def download(season, folder, refresh=False, transport='requests', dataset='boxscores'):
    folder.mkdir(parents=True, exist_ok=True)
    asset, documentation = ASSETS[dataset]
    url = BASE + asset.format(season=season)
    label = ('ESPN player-game box scores published by SportsDataverse' if dataset == 'boxscores'
             else 'Season-specific ESPN team membership published by SportsDataverse')
    path = folder / asset.format(season=season).split('/')[-1]
    manifest = path.with_suffix('.meta.json')
    if path.exists() and not refresh:
        if not manifest.exists():
            raise ValueError(f'Cache lacks provenance: {path}; use --refresh')
        metadata = json.loads(manifest.read_text())
        if metadata.get('url') != url or metadata.get('season') != season:
            raise ValueError('Cached provenance refers to another asset or season')
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if metadata['sha256'] != digest:
            raise ValueError('Cached file hash mismatch; inspect file before refreshing')
        if metadata['source'] != label:
            metadata['source'] = label
            manifest.write_text(json.dumps(metadata, indent=2) + '\n')
        return path, metadata
    if transport == 'curl':
        # macOS curl uses the platform trust store. Certificate checking stays on;
        # this option handles a Python installation with an incomplete CA store.
        temporary = path.with_suffix('.part')
        result = subprocess.run(['curl', '--fail', '--location', '--silent', '--show-error',
                                 '--max-time', '60', '--dump-header', '-', '--output',
                                 str(temporary), url], capture_output=True, text=True, timeout=65)
        if result.returncode:
            temporary.unlink(missing_ok=True)
            raise ValueError(f'curl download failed: {result.stderr.strip()}')
        payload = temporary.read_bytes()
        modified = [line.split(':', 1)[1].strip() for line in result.stdout.splitlines()
                    if line.lower().startswith('last-modified:')]
        last_modified = modified[-1] if modified else None
    else:
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        payload = response.content
        last_modified = response.headers.get('Last-Modified')
    if not (payload.startswith(b'PAR1') and payload.endswith(b'PAR1')):
        raise ValueError('Response is not Parquet; refusing to save an error page')
    temporary = path.with_suffix('.part')
    temporary.write_bytes(payload)
    frame = pd.read_parquet(temporary)
    if frame.empty or 'season' not in frame or set(frame.season.dropna().astype(int)) != {season}:
        temporary.unlink()
        raise ValueError('Empty or unexpected-season response')
    temporary.replace(path)
    metadata = dict(source=label, url=url,
                    source_documentation=f'https://py.sportsdataverse.org/docs/mbb/reference/loaders/{documentation}',
                    retrieved_at=datetime.now(timezone.utc).isoformat(),
                    last_modified=last_modified,
                    sha256=hashlib.sha256(payload).hexdigest(), bytes=len(payload),
                    rows=len(frame), season=season,
                    caveat='Public performance export; not NIL sample, followers or PORPAG')
    manifest.write_text(json.dumps(metadata, indent=2) + '\n')
    return path, metadata


def summarize(box, membership, season, as_of):
    """One row per athlete/team/season; DNP rows never inflate games played.

    Missing statistics remain missing, including players with no appearances.
    An athlete with two teams retains two rows; no name-only or transfer pooling.
    """
    required = {'season', 'season_type', 'game_date', 'game_id', 'athlete_id', 'team_id',
                'athlete_display_name', 'team_location', 'athlete_position_abbreviation',
                'did_not_play', 'starter', *STATS}
    if not required.issubset(box.columns) or box.empty:
        raise ValueError(f'Unexpected box-score schema; missing {sorted(required - set(box.columns))}')
    if set(box.season.dropna().astype(int)) != {season}:
        raise ValueError('Box scores contain another season')
    group_required = {'league', 'season', 'team_id', 'team_id_source', 'subdivision_id', 'conference_id'}
    if not group_required.issubset(membership.columns):
        raise ValueError('Unexpected team-membership schema')
    if set(membership.season.dropna().astype(int)) != {season}:
        raise ValueError('Membership and box-score seasons differ')
    data = box.copy()
    data['game_date'] = pd.to_datetime(data.game_date, utc=True, errors='raise')
    cutoff = pd.Timestamp(as_of, tz='UTC')
    eligible = data.season_type.isin([2, 3]) & data.game_date.le(cutoff)
    audit = dict(season=season, as_of=as_of, raw_rows=len(data),
                 raw_games=int(data.game_id.nunique()), raw_athletes=int(data.athlete_id.nunique()),
                 raw_teams=int(data.team_id.nunique()),
                 first_game_date=str(data.game_date.min().date()),
                 last_game_date=str(data.game_date.max().date()),
                 excluded_by_date_or_season_type=int((~eligible).sum()))
    data = data.loc[eligible].copy()
    missing_identity = data[['athlete_id', 'team_id', 'game_id', 'athlete_display_name']].isna().any(axis=1)
    audit['excluded_missing_identity_rows'] = int(missing_identity.sum())
    data = data.loc[~missing_identity].copy()
    if data.empty:
        raise ValueError('No eligible player observations')
    for c in ['athlete_id', 'team_id', 'game_id']:
        numeric = pd.to_numeric(data[c], errors='raise')
        if not np.isfinite(numeric).all() or numeric.mod(1).ne(0).any():
            raise ValueError(f'Non-integer source identifier in {c}')
        data[c] = numeric.astype('int64')
    if data.duplicated(['game_id', 'team_id', 'athlete_id']).any():
        raise ValueError('Duplicate player-game identity; inspect source before aggregation')
    for c in ['did_not_play', 'starter']:
        if not data[c].isin([True, False]).all():
            raise ValueError(f'Unknown participation flag: {c}')
        data[c] = data[c].astype(bool)
    for c in STATS:
        data[c] = pd.to_numeric(data[c], errors='raise')
        if ((data[c].notna() & ~np.isfinite(data[c])) | data[c].lt(0)).any():
            raise ValueError(f'Invalid negative or non-finite statistic: {c}')
    audit['dnp_rows_excluded_from_game_denominators'] = int(data.did_not_play.sum())
    played = data.loc[~data.did_not_play].copy()
    audit['appearance_rows'] = len(played)
    audit['zero_minute_appearances_retained'] = int(played.minutes.eq(0).sum())
    audit['missing_appearance_stats'] = played[STATS].isna().sum().to_dict()
    keys = ['season', 'athlete_id', 'team_id']
    grouped = played.groupby(keys)
    games = grouped.size().rename('Games')
    totals = grouped[STATS].sum(min_count=1)
    # If one appearance lacks a stat, do not call its partial sum a season total.
    totals = totals.where(grouped[STATS].count().eq(games, axis=0))
    identity = data.sort_values('game_date').groupby(keys).agg(
        Player_Name=('athlete_display_name', 'last'),
        College=('team_location', 'last'),
        Position=('athlete_position_abbreviation', lambda x: '/'.join(sorted(set(x.dropna())))),
        Name_Variants=('athlete_display_name', 'nunique'),
        First_Recorded_Game=('game_date', 'min'), Last_Recorded_Game=('game_date', 'max'))
    result = identity.join(games).join(grouped.starter.sum().rename('Starts')).join(totals)
    result['Games'] = result.Games.fillna(0).astype(int)
    result['Starts'] = result.Starts.fillna(0).astype(int)
    for stat in ['minutes', 'points', 'rebounds', 'assists', 'steals', 'blocks', 'turnovers']:
        result[f'{stat.title()}_Per_Game'] = result[stat] / result.Games.replace(0, np.nan)
    for prefix, made, attempted in [
        ('FG', 'field_goals_made', 'field_goals_attempted'),
        ('Three_Point', 'three_point_field_goals_made', 'three_point_field_goals_attempted'),
        ('FT', 'free_throws_made', 'free_throws_attempted')]:
        result[f'{prefix}_Pct'] = result[made] / result[attempted].replace(0, np.nan)
    result['Stats_Availability'] = np.where(result.Games.eq(0), 'no_recorded_appearances',
                                           np.where(result[STATS].isna().any(axis=1),
                                                    'incomplete_appearance_statistics', 'complete_recorded_appearances'))
    result = result.reset_index()
    result['team_id'] = result.team_id.astype(str)
    groups = membership.loc[membership.league.eq('mbb') & membership.team_id_source.eq('espn'),
                            ['season', 'team_id', 'subdivision_id', 'conference_id']].copy()
    groups['team_id'] = groups.team_id.astype(str)
    if groups.duplicated(['season', 'team_id']).any():
        raise ValueError('Ambiguous team-season membership')
    result = result.merge(groups, on=['season', 'team_id'], how='left', validate='many_to_one')
    result['Division_I_Verified'] = result.subdivision_id.eq('mbb:d1').fillna(False)
    result['ESPN_Profile_URL'] = ('https://www.espn.com/mens-college-basketball/player/_/id/'
                                  + result.athlete_id.astype(str))
    for c in ['First_Recorded_Game', 'Last_Recorded_Game']:
        result[c] = result[c].dt.strftime('%Y-%m-%d')
    audit.update(player_team_season_rows=len(result),
                 division_i_player_team_rows=int(result.Division_I_Verified.sum()),
                 division_i_teams=int(result.loc[result.Division_I_Verified, 'team_id'].nunique()),
                 division_i_athletes=int(result.loc[result.Division_I_Verified, 'athlete_id'].nunique()),
                 no_appearance_player_team_rows=int(result.Games.eq(0).sum()),
                 athlete_ids_on_multiple_teams=int((result.groupby('athlete_id').team_id.nunique() > 1).sum()),
                 availability=result.Stats_Availability.value_counts().to_dict(),
                 identity_name_variant_rows=int(result.Name_Variants.gt(1).sum()),
                 scope='All recorded regular/postseason games, including games against non-D1 opponents',
                 limitation='Recorded export coverage is not proof of complete official season statistics')
    return result.sort_values(['athlete_id', 'team_id']), audit


def run(args):
    raw, raw_meta = download(args.season, args.outdir, args.refresh, args.transport)
    groups, group_meta = download(args.season, args.outdir, args.refresh, args.transport, 'groups')
    result, audit = summarize(pd.read_parquet(raw), pd.read_parquet(groups), args.season, args.as_of)
    result['Source_Response_SHA256'] = raw_meta['sha256']
    result['Membership_Response_SHA256'] = group_meta['sha256']
    result['Source'] = 'ESPN via SportsDataverse; supplemental box-score statistics'
    result.to_csv(args.outdir / f'player_team_season_{args.season}.csv', index=False)
    result.loc[result.Division_I_Verified].to_csv(
        args.outdir / f'division_i_player_team_season_{args.season}.csv', index=False)
    audit['source_manifests'] = [raw_meta, group_meta]
    audit['not_collected'] = ['NIL valuations', 'Instagram followers', 'recruiting star ratings', 'CBBD PORPAG']
    report = args.outdir / f'collection_audit_{args.season}.json'
    report.write_text(json.dumps(audit, indent=2) + '\n')
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(audit, indent=2) + '\n')
    print(json.dumps(audit, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--season', type=int, default=2026, help='Ending year: 2026 means 2025–26')
    parser.add_argument('--outdir', type=Path, default=ROOT / 'Data/private/basketball')
    parser.add_argument('--refresh', action='store_true')
    parser.add_argument('--transport', choices=['requests', 'curl'], default='requests')
    parser.add_argument('--as-of', default='2026-10-31', help='Last eligible game date, YYYY-MM-DD')
    parser.add_argument('--report', type=Path, help='Optional aggregate audit to publish in reports/')
    args = parser.parse_args()
    try:
        run(args)
    except (requests.RequestException, ValueError, OSError) as exc:
        parser.exit(1, f'Collection stopped: {exc}\n')
