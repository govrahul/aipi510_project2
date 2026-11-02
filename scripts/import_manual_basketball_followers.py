"""Merge user-reported follower counts into the original basketball cohort.

Never redraw, append athletes, fabricate account URLs/observation dates, or
upgrade a manual report to a browser measurement. Matching existing values are
logged as corroboration; conflicting measurements require explicit review.
"""
import argparse
import hashlib
import json
from pathlib import Path

import pandas as pd


def merge_manual(data, manual):
    result=data.copy();actions=[]
    if result.athlete_id.duplicated().any() or manual.athlete_id.duplicated().any():
        raise ValueError('Duplicate athlete IDs')
    if 'Instagram_Count_Provenance' not in result:
        result['Instagram_Count_Provenance']=result.Instagram_Count_Status.map(
            lambda s:'browser_observed' if s=='observed_browser_integer_tooltip' else 'not_recorded')
    for col in ['Instagram_Reported_Date','Instagram_Manual_Source','Instagram_Manual_Evidence_SHA256',
                'Prior_Sourced_Instagram_Username','Prior_Username_Verification_URL']:
        if col not in result:result[col]=None
    for r in manual.to_dict('records'):
        match=result.index[result.athlete_id.eq(r['athlete_id'])]
        if len(match)!=1:raise ValueError('Manual record does not identify one sampled athlete')
        ix=match[0]
        if result.loc[ix,'Player Name']!=r['Player_Name'] or result.loc[ix,'College']!=r['College']:
            raise ValueError('Manual record name/school does not match stable athlete ID')
        value=float(r['Instagram_Followers'])
        if not value.is_integer() or value<0:raise ValueError('Follower count must be a nonnegative integer')
        prior=result.loc[ix,'Instagram_Followers']
        if pd.notna(prior):
            if int(prior)!=int(value):raise ValueError('Manual report conflicts with existing observation; review required')
            actions.append(dict(athlete_id=r['athlete_id'],Player_Name=r['Player_Name'],action='corroborates_existing_count'))
            continue
        evidence=json.dumps(r,sort_keys=True,default=str).encode()
        updates=dict(Instagram_Followers=int(value),Instagram_Followers_Approx=None,
            Instagram_Count_Provenance='user_reported',Instagram_Count_Status='user_reported_count',
            Instagram_Provider='Sam_manual_chat_submission',Instagram_Raw_Label=str(r['Raw_Label']),
            Instagram_Count_Precision='user_reported_integer_display_precision_unverified',
            Instagram_Reported_Date=r['Reported_Date'],Instagram_Manual_Source=r['Source_Reference'],
            Instagram_Manual_Evidence_SHA256=hashlib.sha256(evidence).hexdigest(),
            Instagram_Evidence_SHA256=hashlib.sha256(evidence).hexdigest(),
            Instagram_Evidence_Format='user_supplied_manual_count',
            Instagram_Measurement_Note='Reported by Sam; account handle, observation time and original display precision not supplied',
            Instagram_Collection_Note='',Instagram_Observed_At=None,Instagram_Source_Reported_At=None,
            Instagram_Source_URL=None,Instagram_Canonical_URL=None,Instagram_Response_SHA256=None,
            Instagram_Integer_Tooltip=None,Instagram_Profile_Title=None,
            Prior_Sourced_Instagram_Username=result.loc[ix,'Instagram_Username'],
            Prior_Username_Verification_URL=result.loc[ix,'Username_Verification_URL'],
            Instagram_Username=None,Username_Verification_URL=None,
            Instagram_Handle_Identity_Status='user_reported_player_match_handle_not_supplied',
            Instagram_Handle_Identity_Note='Manual report matched to sampled player name and school; no current handle supplied')
        for col,v in updates.items():
            if col not in result:result[col]=None
            if result[col].dtype.kind!='O' and isinstance(v,str):result[col]=result[col].astype(object)
            result.loc[ix,col]=v
        actions.append(dict(athlete_id=r['athlete_id'],Player_Name=r['Player_Name'],action='filled_missing_count'))
    result['Instagram_Followers']=pd.to_numeric(result.Instagram_Followers,errors='raise').astype('Int64')
    for col in ['athlete_id','Sample_Row','Quartile','Frame_Rank','NIL_Valuation_USD']:
        if result[col].tolist()!=data[col].tolist():raise ValueError(f'Merge changed {col}')
    return result,actions


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input',type=Path,required=True);p.add_argument('--manual',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);p.add_argument('--audit',type=Path,required=True);a=p.parse_args()
    if a.input.resolve()==a.output.resolve():raise ValueError('Preserve the pre-manual sheet')
    result,actions=merge_manual(pd.read_csv(a.input),pd.read_csv(a.manual,dtype={'Raw_Label':str}))
    a.output.parent.mkdir(parents=True,exist_ok=True);result.to_csv(a.output,index=False)
    audit=dict(rows=len(result),counts_recorded=int(result.Instagram_Followers.notna().sum()),
        missing_counts=int(result.Instagram_Followers.isna().sum()),
        provenance_counts=result.Instagram_Count_Provenance.value_counts().to_dict(),
        rows_per_quartile=result.Quartile.value_counts().to_dict(),actions=actions,
        source_input_sha256=hashlib.sha256(a.input.read_bytes()).hexdigest(),
        manual_input_sha256=hashlib.sha256(a.manual.read_bytes()).hexdigest(),
        output_sha256=hashlib.sha256(a.output.read_bytes()).hexdigest(),
        original_sample_unchanged=True,replacements_used=0,
        manual_policy='Report date is not an observed-at timestamp; no profile URL or display precision inferred')
    a.audit.parent.mkdir(parents=True,exist_ok=True);a.audit.write_text(json.dumps(audit,indent=2)+'\n')
    print(json.dumps({k:v for k,v in audit.items() if k!='actions'},indent=2))
