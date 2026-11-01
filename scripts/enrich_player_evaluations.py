"""Add recruiting/career/evaluation fields without changing existing samples.

Final recruiting-stratified samples require verified high-school ratings. Public
football recruiting candidates remain separate until HS classification is checked.
Post-college outcomes must never enter pre-decision predictor/sampling fields.
"""
import argparse
from collections import defaultdict
import json
from pathlib import Path

import numpy as np
import pandas as pd
from collect_performance import normalize
from sample_quartiles import sample_quartiles

ROOT=Path(__file__).resolve().parents[1]
SDV='https://github.com/sportsdataverse/sportsdataverse-data/releases/download/'


def identifier(value):
    if pd.isna(value): return ''
    return str(value).removesuffix('.0')


def recruiting_sample(frame):
    """Lexicographic stars/rating order; ties split deterministically and flagged.

    Complete continuous ratings required for this design; do not let availability
    determine an undisclosed tie-break rule. Missing/unverified rows stay in frame.
    """
    eligible=frame.loc[frame.Recruit_HS_Verified.eq(True) & frame.Recruit_Stars.notna() &
                       frame.Recruit_Rating.notna()].copy()
    if eligible.athlete_id.duplicated().any():
        eligible=eligible.sort_values(['athlete_id','team_id'],kind='stable').drop_duplicates('athlete_id')
    if len(eligible) and eligible.Recruit_Provider.nunique()!=1:
        raise ValueError('One consistent recruiting provider/scale is required per sampling frame')
    if len(eligible)<1000:
        return None,dict(status='pending_insufficient_verified_HS_ratings',eligible=len(eligible),required=1000)
    # A dense rank of (stars, continuous rating) preserves both order and ties.
    pairs=sorted(set(zip(eligible.Recruit_Stars,eligible.Recruit_Rating)))
    score={pair:i+1 for i,pair in enumerate(pairs)}
    eligible['Recruit_Order_Score']=[score[x] for x in zip(eligible.Recruit_Stars,eligible.Recruit_Rating)]
    _,sample,audit=sample_quartiles(eligible,'Recruit_Order_Score',['athlete_id'])
    sample['Sampling_Design']='high_school_stars_then_same_provider_rating_rank_quartiles'
    audit.update(status='produced',eligible=len(eligible),ordering='Stars DESC, rating DESC, stable athlete ID; dense pair score is ordering only, not a regression covariate')
    return sample,audit


def recruiting_index(official, fallback):
    index=defaultdict(list)
    if official is not None:
        for row in official.to_dict('records'):
            index[(row['Sport'],normalize(row['Recruit_Name']),normalize(row.get('Recruit_College')))].append(row)
    candidates=defaultdict(list)
    for row in fallback.to_dict('records'):
        candidates[(normalize(row['player_name']),identifier(row['team_id']))].append(row)
    return index,candidates


def attach_recruit(row,sport,cohort,index,candidates):
    matches=[r for r in index.get((sport,normalize(row['Player_Name']),normalize(row['College'])),[])
             if 2007<=int(r['Recruit_Class_Year'])<=cohort]
    result=dict(Recruit_Stars=None,Recruit_Rating=None,Recruit_Class_Year=None,
        Recruit_HS_Verified=False,Recruit_Match_Status='not_available',Recruit_Source_URL=None,
        Recruit_Provider=None,Recruit_ID=None,Recruit_Source_Grade=None,
        Recruit_Timing_Status='final_class_rating_not_verified_pre_decision')
    if len(matches)==1:
        r=matches[0]
        for key in ['Recruit_Stars','Recruit_Rating','Recruit_Class_Year','Recruit_HS_Verified','Recruit_Source_URL','Recruit_Provider','Recruit_ID']:
            result[key]=r.get(key)
        result['Recruit_Match_Status']='exact_name_commitment_school_confirm_identity_before_model'
    elif len(matches)>1:
        result['Recruit_Match_Status']='ambiguous_official_identity'
    elif sport=='football':
        choices=[r for r in candidates.get((normalize(row['Player_Name']),identifier(row['team_id'])),[])
                 if int(r['season'])<=cohort]
        if len(choices)==1:
            r=choices[0]
            stars=r['stars'] if pd.notna(r['stars']) and r['stars']>0 else None
            result.update(Recruit_Stars=stars,Recruit_Class_Year=r['season'],Recruit_ID=r['recruit_id'],
                Recruit_Source_Grade=r['grade'],Recruit_Provider='SportsDataverse_247_recruit_export',
                Recruit_Source_URL=SDV+f"cfb_recruits/cfb_recruits_{int(r['season'])}.parquet",
                Recruit_Match_Status='exact_name_team_id_HS_classification_unverified')
        elif choices: result['Recruit_Match_Status']='ambiguous_public_recruit_identity'
    return result


def draft_index(nba,nfl):
    result=defaultdict(list)
    for r in nba.to_dict('records'):
        if r['organization_type']!='College/University': continue
        result[('basketball',normalize(r['player_name']),normalize(r['organization']))].append(dict(
            Draft_Year=r['Draft_Year'],Draft_Round=r['round_number'],Draft_Overall_Pick=r['overall_pick'],
            Draft_League='NBA',Draft_Professional_ID=identifier(r['person_id']),
            Draft_Source_URL=SDV+f"nba_stats_draft/draft_{int(r['Draft_Year'])+1}.parquet",
            Draft_Secondary_Source_Agreement=bool(r['Draft_Source_Agreement'])))
    for r in nfl.to_dict('records'):
        if int(r['season'])>2026: continue
        result[('football',normalize(r['pfr_player_name']),normalize(r['college']))].append(dict(
            Draft_Year=r['season'],Draft_Round=r['round'],Draft_Overall_Pick=r['pick'],Draft_League='NFL',
            Draft_Professional_ID=r['pfr_player_id'],
            Draft_Source_URL='https://github.com/nflverse/nflverse-data/releases/download/draft_picks/draft_picks.parquet',
            Draft_Secondary_Source_Agreement=None))
    return result


def attach_draft(row,sport,cohort,index,as_of):
    result=dict(Draft_Year=None,Draft_Round=None,Draft_Overall_Pick=None,Draft_League=None,
        Draft_Professional_ID=None,Draft_Source_URL=None,Draft_Secondary_Source_Agreement=None,
        Draft_Status='not_matched_unknown_not_a_verified_undrafted_outcome',Career_As_Of=as_of,
        Career_Followup_Status='incomplete_not_a_final_career_outcome',
        Overseas_Professional_Contract=None,Overseas_Contract_Status='not_researched_unknown',
        Overseas_Club=None,Overseas_League=None,Overseas_Contract_Date=None,Overseas_Contract_Observed_By=None,Overseas_Evidence_URL=None,
        College_Years_Total=None,College_Career_Completion_Status='not_verified')
    choices=[r for r in index.get((sport,normalize(row['Player_Name']),normalize(row['College'])),[])
             if cohort<r['Draft_Year']<=int(as_of[:4])]
    if len(choices)==1:
        result.update(choices[0])
        result['Draft_Status']='source_reported_exact_name_college_match'
        if choices[0]['Draft_Secondary_Source_Agreement'] is False:
            result['Draft_Status']='source_reported_secondary_pick_disagreement_needs_review'
    elif choices: result['Draft_Status']='ambiguous_needs_identity_review'
    return result


def observed_seasons(folder,sport,as_of):
    """Lower bounds only; no grade-based inference or absence=departure assumption."""
    records=[]
    directory='basketball_values' if sport=='basketball' else 'football_rosters'
    for path in sorted((folder/directory).glob('*.parquet')):
        year=int(path.stem.split('_')[-1])
        if year>int(as_of[:4]): continue
        frame=pd.read_parquet(path)
        if sport=='basketball':
            frame=frame.loc[frame['min']>0,['player_id','season']].rename(columns={'player_id':'athlete_id'})
            frame['Cohort_Start']=frame.season-1
        else:
            frame=frame[['athlete_id','season']].copy()
            frame['Cohort_Start']=frame.season
        frame['athlete_id']=frame.athlete_id.map(identifier)
        records.append(frame)
    return pd.concat(records,ignore_index=True).drop_duplicates(['athlete_id','Cohort_Start'])


def enrich(frame,sport,cohort,index,candidates,drafts,history,values,as_of):
    data=frame.copy()
    data['athlete_id']=data.athlete_id.map(identifier)
    recruit=pd.DataFrame([attach_recruit(r,sport,cohort,index,candidates) for r in data.to_dict('records')])
    career=pd.DataFrame([attach_draft(r,sport,cohort,drafts,as_of) for r in data.to_dict('records')])
    for extra in [recruit,career]:
        for column in extra: data[column]=extra[column].to_numpy()
    all_counts=history.groupby('athlete_id').Cohort_Start.nunique()
    prior_counts=history.loc[history.Cohort_Start<=cohort].groupby('athlete_id').Cohort_Start.nunique()
    data['Observed_College_Seasons_Through_AsOf']=data.athlete_id.map(all_counts)
    data['Observed_College_Seasons_By_Cohort']=data.athlete_id.map(prior_counts)
    data['College_Seasons_Measure']='recorded_positive_minutes_seasons_lower_bound' if sport=='basketball' else 'recorded_roster_seasons_lower_bound'
    data['College_History_Window_Start']=2012
    data['Sport'],data['Cohort_Year']=sport,cohort
    if sport=='basketball':
        v=values.loc[values.season.eq(cohort+1)].copy()
        v['athlete_id']=v.player_id.map(identifier);v['team_id']=v.team_id.map(identifier)
        data['team_id']=data.team_id.map(identifier)
        v=v.rename(columns={'box_bpm':'College_Box_BPM','box_obpm':'College_Box_OBPM',
                            'box_dbpm':'College_Box_DBPM','qualified':'College_BPM_Qualified','min':'College_BPM_Minutes'})
        columns=['athlete_id','team_id','College_Box_BPM','College_Box_OBPM','College_Box_DBPM','College_BPM_Qualified','College_BPM_Minutes']
        data=data.merge(v[columns],on=['athlete_id','team_id'],how='left',validate='many_to_one',sort=False)
        data['College_Evaluation_Metric']='SportsDataverse_box_BPM_not_ESPN_BPI_or_CBBD_PORPAG'
        data['College_Evaluation_Source_URL']=SDV+f'mbb_player_value/mbb_player_value_{cohort+1}.parquet'
    else:
        data['College_Box_BPM']=None
        data['College_Evaluation_Metric']='no_verified_all_position_composite_collected'
    return data



def join_evaluation_to_nil(sample,evaluations):
    """Enrich final NIL sample by its accepted ESPN performance identity only."""
    data=sample.copy()
    original=data.columns.tolist()
    right=evaluations.copy()
    right['__id']=right.athlete_id.map(identifier)
    right['__team']=right.College.map(normalize)
    # Transfers and ambiguous player-team evaluations must be reviewed first.
    if right.duplicated(['__id','__team']).any(): raise ValueError('Duplicate evaluation identities')
    accepted=data.Match_Status.isin(['exact_id','exact_name_team'])
    data['__id']=data.Performance_API_ID.map(identifier).where(accepted,'')
    data['__team']=data.Performance_Team.map(normalize).where(accepted,'')
    extras=[c for c in right if c.startswith(('Recruit_','Draft_','Career_','College_','Observed_','Overseas_')) and c not in original]
    data['__order']=range(len(data))
    joined=data.merge(right[['__id','__team',*extras]],on=['__id','__team'],how='left',validate='many_to_one',sort=False)
    joined=joined.sort_values('__order',kind='stable').drop(columns=['__id','__team','__order'])
    if len(joined)!=len(sample): raise ValueError('Evaluation join changed NIL sample size')
    return joined


def apply_reviewed_events(data,events,as_of):
    if events is None: return data
    needed={'Sport','athlete_id','Event_Type','Event_Date','Evidence_URL','Identity_Verified'}
    if not needed.issubset(events): raise ValueError(f'Event file needs {sorted(needed)}')
    for event in events.to_dict('records'):
        if str(event['Identity_Verified']).lower()!='true': continue
        date=pd.Timestamp(event['Event_Date'])
        if pd.isna(date) or date>pd.Timestamp(as_of) or not str(event['Evidence_URL']).startswith('https://'):
            raise ValueError('Reviewed event needs dated evidence on/before as-of')
        mask=data.Sport.eq(event['Sport']) & data.athlete_id.eq(identifier(event['athlete_id']))
        if not mask.any(): continue
        if event['Event_Type']=='overseas_professional_contract':
            precision=event.get('Event_Date_Precision','exact_date')
            if precision not in ['exact_date','observed_by']: raise ValueError('Unsupported event date precision')
            data.loc[mask,['Overseas_Professional_Contract','Overseas_Contract_Status','Overseas_Club',
                'Overseas_League','Overseas_Contract_Date','Overseas_Contract_Observed_By','Overseas_Evidence_URL']]=[
                True,'verified_contract_announcement',event.get('Club'),event.get('League'),
                event['Event_Date'] if precision=='exact_date' else None,event['Event_Date'],event['Evidence_URL']]
        elif event['Event_Type']=='college_career_completed':
            years=float(event['College_Years_Total'])
            if not np.isfinite(years) or years<1 or years%1: raise ValueError('Career years need an evidenced positive integer')
            data.loc[mask,'College_Years_Total']=years
            data.loc[mask,'College_Career_Completion_Status']='verified_completion_evidence'
            data.loc[mask,'College_Completion_Evidence_URL']=event['Evidence_URL']
        else: raise ValueError('Unsupported career event type')
    return data


def run(args):
    source=args.sources
    fallback=pd.concat([pd.read_parquet(p) for p in sorted((source/'football_recruits').glob('*.parquet'))],ignore_index=True)
    official=pd.read_csv(args.official_recruits) if args.official_recruits else None
    index,candidates=recruiting_index(official,fallback)
    drafts=draft_index(pd.read_csv(source/'nba_draft_normalized.csv'),pd.read_parquet(source/'nfl_draft/draft_picks.parquet'))
    histories={s:observed_seasons(source,s,args.as_of) for s in ['basketball','football']}
    values=pd.concat([pd.read_parquet(p) for p in (source/'basketball_values').glob('*.parquet')],ignore_index=True)
    events=pd.read_csv(args.reviewed_events,dtype={'athlete_id':'string'}) if args.reviewed_events else None
    specs=[]
    for year in [2018,2019]:
        for sport in ['basketball','football']:
            specs.append((sport,year,pd.read_csv(ROOT/f'Data/private/comparators/{sport}_{year}/player_season_frame.csv')))
    specs.append(('basketball',2025,pd.read_csv(ROOT/'Data/private/basketball/division_i_player_team_season_2026.csv')))
    for year in [2025,2026]:
        frame=pd.read_parquet(source/f'football_rosters/cfb_rosters_{year}.parquet')
        groups=pd.read_parquet(source/f'football_groups/cfb_team_group_seasons_{year}.parquet')
        groups=groups.loc[groups.team_id_source.eq('espn') & groups.subdivision_id.isin(['cfb:fbs','cfb:fcs'])]
        allowed=set(groups.team_id.map(identifier))
        frame=frame.loc[frame.team_id.map(identifier).isin(allowed)].copy()
        frame=frame.rename(columns={'athlete_display_name':'Player_Name','team_location':'College','position_abbreviation':'Position'})
        specs.append(('football',year,frame))
    if args.input:
        if args.sport is None or args.cohort_start is None: raise ValueError('--input needs --sport and --cohort-start')
        frame=pd.read_csv(args.input).rename(columns={'Player Name':'Player_Name'})
        if not {'athlete_id','team_id','Player_Name','College'}.issubset(frame):
            raise ValueError('Enrichment input needs verified ESPN athlete_id, team_id, Player_Name, College')
        specs=[(args.sport,args.cohort_start,frame)]
    args.outdir.mkdir(parents=True,exist_ok=True)
    audit=[]
    for sport,cohort,frame in specs:
        data=enrich(frame,sport,cohort,index,candidates,drafts,histories[sport],values,args.as_of)
        data=apply_reviewed_events(data,events,args.as_of)
        data.to_csv(args.outdir/f'{sport}_{cohort}_evaluation_frame.csv',index=False)
        sample,sampling=recruiting_sample(data)
        if sample is not None: sample.to_csv(args.outdir/f'{sport}_{cohort}_HS_quartiles_1000.csv',index=False)
        audit.append(dict(sport=sport,cohort_start=cohort,rows=len(data),unique_athletes=data.athlete_id.nunique(),
            recruiting_stars_available=int(data.Recruit_Stars.notna().sum()),verified_HS_ratings=int(data.Recruit_HS_Verified.eq(True).sum()),
            recruiting_status=data.Recruit_Match_Status.value_counts().to_dict(),
            draft_status=data.Draft_Status.value_counts().to_dict(),draft_round_available=int(data.Draft_Round.notna().sum()),
            college_BPM_available=int(data.College_Box_BPM.notna().sum()),
            overseas_contract_verified=int(data.Overseas_Professional_Contract.eq(True).sum()),sampling=sampling))
    report=dict(as_of=args.as_of,cohorts=audit,source_manifest='Data/private/evaluation/collection_manifest.json',
        note='Previous production-based samples are superseded provisional artifacts. No final HS-stratified sample without sufficient verified HS ratings. No future outcomes imputed.')
    (args.outdir/'evaluation_audit.json').write_text(json.dumps(report,indent=2)+'\n')
    if args.report: args.report.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--sources',type=Path,default=ROOT/'Data/private/evaluation')
    p.add_argument('--outdir',type=Path,default=ROOT/'Data/private/evaluation/enriched')
    p.add_argument('--as-of',default='2026-11-01')
    p.add_argument('--input',type=Path,help='Optional verified ESPN-ID sample; preserve its row/quartile order')
    p.add_argument('--sport',choices=['football','basketball'])
    p.add_argument('--cohort-start',type=int)
    p.add_argument('--official-recruits',type=Path)
    p.add_argument('--reviewed-events',type=Path)
    p.add_argument('--report',type=Path,default=ROOT/'reports/evaluation_collection_audit.json')
    a=p.parse_args()
    if a.as_of!='2026-11-01': p.error('This reviewed source snapshot uses 2026-11-01; revise event-date handling before another as-of date')
    run(a)
