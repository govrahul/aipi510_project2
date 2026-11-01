"""Supplement historical/current football outcomes using nflverse ESPN/PFR IDs.

No fuzzy name matching. Source IDs plus exact normalized name identify candidate
records; disagreement/duplicate identities remain review flags. NFL registration
is distinct from a signed contract or playing a regular-season game. Outcomes
predating the college cohort flag possible stale/misattributed college identities.
"""
import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path

import pandas as pd
from collect_performance import normalize
from enrich_player_evaluations import identifier

ROOT=Path(__file__).resolve().parents[1]
URL='https://github.com/nflverse/nflverse-data/releases/download/players/players.parquet'


def supplement(frame, players, picks, cohort):
    indexed=defaultdict(list)
    for r in players.to_dict('records'):
        key=identifier(r['espn_id'])
        if key: indexed[key].append(r)
    by_pfr=defaultdict(list)
    for r in picks.to_dict('records'):
        key=identifier(r['pfr_player_id'])
        if key: by_pfr[key].append(r)
    rows=[]
    for original in frame.to_dict('records'):
        row=original.copy()
        row.update(NFL_ID_Match_Status='not_matched_unknown',NFL_Pro_Player_Record=None,
            NFL_GSIS_ID=None,NFL_PFR_ID=None,NFL_Rookie_Season=None,NFL_Last_Recorded_Season=None,
            NFL_ID_Source_URL=URL,NFL_College_Identity_Timing_Flag=None,
            NFL_Crosswalk_Draft_Year=None,NFL_Crosswalk_Draft_Round=None,NFL_Crosswalk_Draft_Pick=None)
        choices=indexed.get(identifier(row['athlete_id']),[])
        if len(choices)>1:
            row['NFL_ID_Match_Status']='duplicate_crosswalk_ID_needs_review'
        elif len(choices)==1:
            player=choices[0]
            if normalize(player['display_name'])!=normalize(row['Player_Name']):
                row['NFL_ID_Match_Status']='ESPN_ID_name_disagreement_needs_review'
            else:
                row.update(NFL_ID_Match_Status='exact_ESPN_ID_and_name',NFL_Pro_Player_Record=True,
                    NFL_GSIS_ID=player['gsis_id'],NFL_PFR_ID=player['pfr_id'],
                    NFL_Rookie_Season=player['rookie_season'],NFL_Last_Recorded_Season=player['last_season'],
                    NFL_Crosswalk_Draft_Year=player['draft_year'],NFL_Crosswalk_Draft_Round=player['draft_round'],
                    NFL_Crosswalk_Draft_Pick=player['draft_pick'])
                # A draft/rookie year before the college season is a source anomaly,
                # not evidence that a new college athlete already succeeded/failed.
                timing=[int(player[k]) for k in ['draft_year','rookie_season'] if pd.notna(player[k])]
                if timing and min(timing)<=cohort:
                    row['NFL_College_Identity_Timing_Flag']='pro_history_on_or_before_college_cohort_review_identity'
                linked=by_pfr.get(identifier(player['pfr_id']),[])
                if len(linked)==1:
                    pick=linked[0]
                    if pd.notna(player['draft_year']) and (int(pick['season'])!=int(player['draft_year']) or
                        pd.isna(player['draft_round']) or int(pick['round'])!=int(player['draft_round']) or
                        pd.isna(player['draft_pick']) or int(pick['pick'])!=int(player['draft_pick'])):
                        row['NFL_ID_Match_Status']='crosswalk_draft_record_disagreement_needs_review'
                        row['Draft_Status']='conflicting_outcome_sources_needs_review'
                    elif cohort<int(pick['season'])<=2026 and not row['NFL_College_Identity_Timing_Flag']:
                        previous=row.get('Draft_Year')
                        if pd.notna(previous) and (int(previous)!=int(pick['season']) or
                            int(row['Draft_Round'])!=int(pick['round']) or int(row['Draft_Overall_Pick'])!=int(pick['pick'])):
                            row['NFL_ID_Match_Status']='existing_draft_outcome_disagreement_needs_review'
                            row['Draft_Status']='conflicting_outcome_sources_needs_review'
                        else:
                            row.update(Draft_Year=pick['season'],Draft_Round=pick['round'],Draft_Overall_Pick=pick['pick'],
                                Draft_League='NFL',Draft_Professional_ID=pick['pfr_player_id'],
                                Draft_Status='exact_ESPN_ID_name_and_PFR_draft_record',
                                Draft_Source_URL='https://github.com/nflverse/nflverse-data/releases/download/draft_picks/draft_picks.parquet')
                elif len(linked)>1: row['NFL_ID_Match_Status']='multiple_PFR_draft_records_needs_review'
        rows.append(row)
    return pd.DataFrame(rows)


def run(args):
    source=args.sources
    players=pd.read_parquet(source/'nfl_players/players.parquet')
    picks=pd.read_parquet(source/'nfl_draft/draft_picks.parquet')
    audit=[]
    for cohort in [2018,2019,2025,2026]:
        path=args.frames/f'football_{cohort}_evaluation_frame.csv'
        frame=pd.read_csv(path,low_memory=False)
        before=int(frame.Draft_Round.notna().sum())
        result=supplement(frame,players,picks,cohort)
        output=args.outdir/f'football_{cohort}_evaluation_with_NFL_IDs.csv'
        output.parent.mkdir(parents=True,exist_ok=True)
        result.to_csv(output,index=False)
        audit.append(dict(cohort=cohort,rows=len(result),draft_matches_before=before,
            draft_matches_after=int(result.Draft_Round.notna().sum()),
            NFL_ID_status=result.NFL_ID_Match_Status.value_counts().to_dict(),
            timing_flags=int(result.NFL_College_Identity_Timing_Flag.notna().sum()),
            source_frame_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
            output_sha256=hashlib.sha256(output.read_bytes()).hexdigest()))
    report=dict(as_of='2026-11-01',sources=[URL,
        'https://github.com/nflverse/nflverse-data/releases/download/draft_picks/draft_picks.parquet'],
        crosswalk_sha256=hashlib.sha256((source/'nfl_players/players.parquet').read_bytes()).hexdigest(),
        cohorts=audit,limits=['NFL player record is not a signed-contract or regular-season appearance observation.',
            'Same ESPN ID/name can still be source errors; timing anomalies are flagged, not silently corrected.',
            'No match remains unknown. Historical HS recruitment, social counts and final duration remain incomplete.'])
    args.report.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--sources',type=Path,default=ROOT/'Data/private/evaluation')
    p.add_argument('--frames',type=Path,default=ROOT/'Data/private/evaluation/enriched')
    p.add_argument('--outdir',type=Path,default=ROOT/'Data/private/evaluation/football_nfl_ids')
    p.add_argument('--report',type=Path,default=ROOT/'reports/football_nfl_id_audit.json')
    run(p.parse_args())
