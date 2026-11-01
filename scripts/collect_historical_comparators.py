"""Collect pre-NIL sport-season source layers; cohort year means starting year.

Basketball cohort 2018 uses ending-season key 2019, and cohort 2019 key 2020.
Football uses season keys 2018 and 2019. Historical followers are not supplied.
Default collects source frames only. Recruiting-based sampling is handled by
enrich_player_evaluations.py; --legacy-production-samples reproduces the old proxy.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess

import pandas as pd
from collect_basketball_open_stats import download, summarize
from sample_quartiles import sample_quartiles

ROOT = Path(__file__).resolve().parents[1]
BASE = 'https://github.com/sportsdataverse/sportsdataverse-data/releases/download/'


def football_frame(box, rosters, membership, cohort):
    """Retain full D1 roster; sampleable production exists only for QB/RB/WR/TE.

    Other positions remain in the source layer with missing sampling metric.
    Never impute their unmeasured production as zero.
    """
    keys = ['athlete_id', 'team_id']
    if any(set(d.season.dropna().astype(int)) != {cohort} for d in [box, rosters, membership]):
        raise ValueError('Football box, roster and membership seasons must agree')
    if box.duplicated([*keys, 'game_id', 'category']).any():
        raise ValueError('Duplicate football player-game-category records')
    if rosters.duplicated(keys).any():
        raise ValueError('Duplicate football roster identities')
    groups = membership.loc[membership.team_id_source.eq('espn') &
                            membership.subdivision_id.isin(['cfb:fbs', 'cfb:fcs'])].copy()
    groups['team_id'] = pd.to_numeric(groups.team_id, errors='raise')
    cols = ['athlete_id', 'team_id', 'athlete_display_name', 'position_abbreviation',
            'team_location', 'height', 'weight', 'experience_display_value', 'games_rostered']
    frame = rosters[cols].merge(groups[['team_id', 'subdivision_id', 'conference_id']],
                                on='team_id', how='inner', validate='many_to_one')
    frame = frame.rename(columns={'athlete_display_name': 'Player_Name', 'position_abbreviation': 'Position',
                                  'team_location': 'College', 'experience_display_value': 'Grade'})
    frame['Recorded_Production'] = float('nan')
    frame['Production_Metric'] = ''
    frame['Production_Games_Recorded'] = float('nan')
    for positions, category, column in [(['QB'], 'passing', 'passingYards'),
                                         (['RB', 'FB'], 'rushing', 'rushingYards'),
                                         (['WR', 'TE'], 'receiving', 'receivingYards')]:
        subset = box.loc[box.category.eq(category), keys + ['game_id', column]].copy()
        subset[column] = pd.to_numeric(subset[column].replace({'--': None, '': None}), errors='raise')
        grouped = subset.groupby(keys)
        totals = grouped[column].sum(min_count=1).where(grouped[column].count().eq(grouped.size()))
        mapped = pd.MultiIndex.from_frame(frame[keys])
        mask = frame.Position.isin(positions)
        frame.loc[mask, 'Recorded_Production'] = totals.reindex(mapped).to_numpy()[mask]
        frame.loc[mask, 'Production_Games_Recorded'] = grouped.game_id.nunique().reindex(mapped).to_numpy()[mask]
        frame.loc[mask, 'Production_Metric'] = column + '_season_total'
    frame['season'] = cohort
    frame['Sampling_Metric_Status'] = 'unavailable_for_position_or_no_recorded_production'
    eligible = frame.Recorded_Production.notna() & frame.Production_Metric.ne('')
    frame.loc[eligible, 'Sampling_Metric_Status'] = 'candidate_position_relative_production'
    frame['Sampling_Position_Group'] = frame.Position.replace({'FB': 'RB'})
    frame['Production_Percentile'] = frame.groupby('Sampling_Position_Group').Recorded_Production.rank(method='average', pct=True)
    return frame


def prepare_candidate_sample(frame, sport, cohort):
    data = frame.copy()
    data['Sport'], data['Cohort_Year'], data['Period'] = sport, cohort, 'Pre_NIL'
    # Use only a single primary-team record per athlete for the sampling unit.
    # The complete team-specific frame is saved independently before this step.
    eligible = data.loc[data.Production_Percentile.notna()].copy()
    sort_cols = ['athlete_id', 'Recorded_Production', 'team_id']
    eligible = eligible.sort_values(sort_cols, ascending=[True, False, True], kind='stable')
    duplicates = int(eligible.duplicated('athlete_id').sum())
    eligible = eligible.drop_duplicates('athlete_id', keep='first')
    _, sample, audit = sample_quartiles(eligible, 'Production_Percentile', ['athlete_id'])
    sample['Comparator_Status'] = 'provisional_sampling_proxy_not_a_scholarship_or_NIL_outcome'
    sample['Instagram_Username'] = None
    sample['Username_Verification_URL'] = None
    sample['Instagram_Followers'] = None
    sample['Instagram_Target_Date'] = None
    sample['Instagram_Observed_At'] = None
    sample['Instagram_Count_Status'] = 'historical_observation_missing'
    audit.update(sport=sport, cohort=cohort, candidate_frame_rows=len(eligible),
                 excluded_secondary_team_rows=duplicates,
                 secondary_team_policy='Highest recorded production, then stable team ID; full frame retains all teams',
                 proxy='Within-position/season percentile of recorded season production; provisional, no causal interpretation')
    return sample, audit


def football_download(cohort, folder, dataset):
    asset = {
        'boxscores': f'espn_cfb_player_box/player_box_{cohort}.parquet',
        'groups': f'cfb_groups/cfb_team_group_seasons_{cohort}.parquet',
        'rosters': f'espn_cfb_rosters/cfb_rosters_{cohort}.parquet',
    }[dataset]
    url = BASE + asset
    path = folder / asset.split('/')[-1]
    meta_path = path.with_suffix('.meta.json')
    folder.mkdir(parents=True, exist_ok=True)
    if path.exists():
        meta = json.loads(meta_path.read_text())
        if meta['url'] != url or hashlib.sha256(path.read_bytes()).hexdigest() != meta['sha256']:
            raise ValueError('Historical cache provenance mismatch')
        return path, meta
    temporary = path.with_suffix('.part')
    result = subprocess.run(['curl', '--fail', '--location', '--silent', '--show-error',
                             '--max-time', '60', '--output', str(temporary), url],
                            capture_output=True, text=True, timeout=65)
    if result.returncode:
        temporary.unlink(missing_ok=True)
        raise ValueError(f'HTTP download failed: {result.stderr.strip()}')
    frame = pd.read_parquet(temporary)
    if frame.empty:
        raise ValueError('Empty historical source')
    payload = temporary.read_bytes()
    temporary.replace(path)
    meta = dict(url=url, retrieved_at=datetime.now(timezone.utc).isoformat(),
                sha256=hashlib.sha256(payload).hexdigest(), bytes=len(payload), rows=len(frame),
                season=cohort, source='SportsDataverse ESPN college football export')
    meta_path.write_text(json.dumps(meta, indent=2) + '\n')
    return path, meta


def run(args):
    reports = []
    workbook_sheets = []
    for cohort in args.cohorts:
        for sport in args.sports:
            folder = args.outdir / f'{sport}_{cohort}'
            if sport == 'basketball':
                season = cohort + 1
                raw, meta = download(season, folder, transport='curl')
                groups, group_meta = download(season, folder, transport='curl', dataset='groups')
                frame, audit = summarize(pd.read_parquet(raw), pd.read_parquet(groups), season,
                                          f'{cohort + 1}-06-30')
                frame = frame.loc[frame.Division_I_Verified].copy()
                frame['Cohort_Year'] = cohort
                frame['Sport'] = sport
                frame['Source_Response_SHA256'] = meta['sha256']
                frame['Period'] = 'Pre_NIL'
                frame['Recorded_Production'] = frame.points
                frame['Production_Metric'] = 'points_season_total'
                frame['Sampling_Position_Group'] = frame.Position.map(
                    {'G':'G', 'PG':'G', 'SG':'G', 'F':'F', 'SF':'F', 'PF':'F', 'C':'C'})
                frame['Production_Percentile'] = frame.groupby('Sampling_Position_Group').Recorded_Production.rank(method='average', pct=True)
                frame.to_csv(folder / 'player_season_frame.csv', index=False)
                if args.legacy_production_samples:
                    sample, sampling_audit = prepare_candidate_sample(frame, sport, cohort)
                    sample.to_csv(folder / 'provisional_quartile_sample_1000.csv', index=False)
                else:
                    sample = None
                    sampling_audit = dict(status='source_frame_only_use_verified_HS_recruiting_pipeline',candidate_frame_rows=0,sample_rows=0)
                reports.append(dict(sport=sport, cohort=cohort, source_season=season,
                                    rows=len(frame), audit=audit, sampling=sampling_audit, sources=[meta, group_meta]))
            else:
                raw, meta = football_download(cohort, folder, 'boxscores')
                groups, group_meta = football_download(cohort, folder, 'groups')
                roster, roster_meta = football_download(cohort, folder, 'rosters')
                frame = football_frame(pd.read_parquet(raw), pd.read_parquet(roster), pd.read_parquet(groups), cohort)
                frame['Source_Response_SHA256'] = meta['sha256']
                frame.to_csv(folder / 'player_season_frame.csv', index=False)
                if args.legacy_production_samples:
                    sample, sampling_audit = prepare_candidate_sample(frame, sport, cohort)
                    sample.to_csv(folder / 'provisional_quartile_sample_1000.csv', index=False)
                else:
                    sample = None
                    sampling_audit = dict(status='source_frame_only_use_verified_HS_recruiting_pipeline',candidate_frame_rows=0,sample_rows=0)
                reports.append(dict(sport=sport, cohort=cohort, source_season=cohort,
                                    rows=len(frame), sampling=sampling_audit, sources=[meta, group_meta, roster_meta]))
            if sample is None:
                continue
            leading = ['Sample_Row', 'Quartile', 'Sport', 'Cohort_Year', 'Player_Name', 'College',
                       'Position', 'athlete_id', 'Production_Metric', 'Recorded_Production',
                       'Production_Percentile', 'Selection_Probability', 'Sampling_Weight',
                       'Instagram_Followers', 'Instagram_Count_Status']
            view = sample[leading + [c for c in sample.columns if c not in leading]]
            view.to_csv(folder / 'provisional_quartile_sample_1000.csv', index=False)
            records = json.loads(view.to_json(orient='values'))
            workbook_sheets.append(dict(name=f'{sport.title()} {cohort}', columns=view.columns.tolist(), rows=records))
    args.outdir.mkdir(parents=True, exist_ok=True)
    (args.outdir / 'collection_manifest.json').write_text(json.dumps(reports, indent=2) + '\n')
    (args.outdir / 'workbook_input.json').write_text(json.dumps(dict(sheets=workbook_sheets,
        summary=[dict(sport=r['sport'], cohort=r['cohort'], source_season=r['source_season'],
                      eligible=r['sampling']['candidate_frame_rows'], sample=r['sampling'].get('sample_rows',0)) for r in reports if r['sampling'].get('sample_rows',0)])) + '\n')
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(reports, indent=2) + '\n')
    print(json.dumps([{k: v for k, v in r.items() if k not in ['audit', 'sources']} for r in reports], indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cohorts', nargs='+', type=int, default=[2018, 2019])
    parser.add_argument('--sports', nargs='+', choices=['football', 'basketball'], default=['basketball', 'football'])
    parser.add_argument('--outdir', type=Path, default=ROOT / 'Data/private/comparators')
    parser.add_argument('--report', type=Path)
    parser.add_argument('--legacy-production-samples',action='store_true',help='Explicitly reproduce the superseded provisional production design')
    args = parser.parse_args()
    run(args)
