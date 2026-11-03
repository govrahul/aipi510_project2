"""Replay reviewed public browser receipts onto the frozen top-1000 sample.

No network access, substitutions, imputation, or automatic name matching.
Receipts are keyed to a hashed frozen sample; human-reviewed handles and
identity evidence are required before counts can enter the analysis sheet.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import pandas as pd
from import_manual_basketball_followers import merge_manual

FROZEN_SHA='f0947e4377ad89c8f67d2fc07b6a6cd7356cdc932cdaa7c18598bd5936dee7e3'


def merge_receipts(sample, receipts, reviews, lookups):
    for name, data in [('sample',sample),('receipts',receipts),('reviews',reviews),('lookups',lookups)]:
        if data.Sample_Row.duplicated().any():raise ValueError('Duplicate Sample_Row in '+name)
        if not set(data.Sample_Row).issubset(set(sample.Sample_Row)):raise ValueError('Unknown sample row in '+name)
    if set(reviews.Sample_Row)!=set(sample.Sample_Row) or set(lookups.Sample_Row)!=set(sample.Sample_Row):
        raise ValueError('Review and Google lookup ledger must cover every selected player')
    if set(reviews.athlete_id)!=set(sample.athlete_id):raise ValueError('Review athlete IDs changed')
    out=sample.copy().set_index('Sample_Row',drop=False)
    receipts=receipts.set_index('Sample_Row');reviews=reviews.set_index('Sample_Row');lookups=lookups.set_index('Sample_Row')
    for col in ['Instagram_Count_Precision','Instagram_Count_Provenance','Instagram_Raw_Label',
                'Instagram_Integer_Tooltip','Instagram_Source_URL','Identity_Review_Note',
                'First_Instagram_Result_URL','Google_Observed_At']:
        out[col]=pd.Series(index=out.index,dtype='object')
    # String columns are explicitly object-typed even when the frozen CSV has only blanks.
    for col in ['Instagram_Username','Username_Verification_URL','Instagram_Observed_At']:
        out[col]=out[col].astype('object')
    for ix,row in out.iterrows():
        review=reviews.loc[ix];lookup=lookups.loc[ix]
        if row.athlete_id!=review.athlete_id:raise ValueError('Review row/athlete mismatch')
        out.loc[ix,'First_Instagram_Result_URL']=lookup.First_Instagram_Result_URL
        out.loc[ix,'Google_Observed_At']=lookup.Google_Observed_At
        out.loc[ix,'Identity_Review_Note']=review.Identity_Review_Note
        out.loc[ix,'Username_Verification_URL']=review.Identity_Evidence_URL
        if ix not in receipts.index:
            if pd.notna(review.Reviewed_Username):raise ValueError('Reviewed handle lacks a receipt')
            out.loc[ix,'Instagram_Count_Status']='unavailable_tagged_accounts'
            continue
        r=receipts.loc[ix]
        if not isinstance(r.username,str) or not re.fullmatch(r'[A-Za-z0-9_.]{1,30}',r.username):raise ValueError('Invalid Instagram handle')
        if r.username!=review.Reviewed_Username:raise ValueError('Receipt handle lacks identity review')
        n=pd.to_numeric(r.followers,errors='raise')
        if pd.isna(n) or n<0 or n!=int(n):raise ValueError('Follower count must be a nonnegative integer')
        raw=str(r.raw_label)
        if re.fullmatch(r'[\d,]+',raw) and int(raw.replace(',',''))!=n:raise ValueError('Visible integer conflicts with receipt count')
        timestamp=pd.Timestamp(r.observed_at)
        if timestamp.tzinfo is None:raise ValueError('Observation timestamp must include timezone')
        out.loc[ix,'Instagram_Username']=r.username
        out.loc[ix,'Instagram_Followers']=int(n)
        out.loc[ix,'Instagram_Followers_Approx']=None
        out.loc[ix,'Instagram_Observed_At']=r.observed_at
        out.loc[ix,'Instagram_Raw_Label']=raw
        out.loc[ix,'Instagram_Integer_Tooltip']=str(int(n))
        out.loc[ix,'Instagram_Count_Precision']='visible_followers_link_integer_tooltip'
        out.loc[ix,'Instagram_Count_Provenance']='browser_observed'
        out.loc[ix,'Instagram_Count_Status']='observed_browser_integer_tooltip'
        out.loc[ix,'Instagram_Source_URL']='https://www.instagram.com/'+r.username+'/'
    return out.reset_index(drop=True)


def finalize(root):
    d=root/'replication/basketball_top1000'
    frozen=d/'basketball_top1000_sample_100_frozen.csv'
    if hashlib.sha256(frozen.read_bytes()).hexdigest()!=FROZEN_SHA:raise ValueError('Frozen sample hash changed')
    sample=pd.read_csv(frozen,dtype={'athlete_id':str,'ESPN_Athlete_ID_Candidate':str})
    if len(sample)!=100 or sample.groupby('Quartile').size().tolist()!=[25]*4 or not sample.NIL_Global_Rank.between(1,1000).all():
        raise ValueError('Wrong sampling population or allocation')
    receipts=pd.read_csv(d/'instagram_count_receipts.csv',dtype={'raw_label':str})
    result=merge_receipts(sample,receipts,pd.read_csv(d/'identity_reviews.csv'),pd.read_csv(d/'google_lookup_receipts.csv'))
    result['Identity_Evidence_URL']=result.Username_Verification_URL
    result,manual_actions=merge_manual(result,pd.read_csv(d/'manual_count_reports.csv',dtype={'Raw_Label':str}))
    target=root/'Data/curated/basketball_top1000_instagram_100.csv'
    result.to_csv(target,index=False)
    audit=dict(sample_rows=len(result),recorded_counts=int(result.Instagram_Followers.notna().sum()),
        counts_by_quartile=result.groupby('Quartile').Instagram_Followers.count().to_dict(),
        missing_players=result.loc[result.Instagram_Followers.isna(),['Sample_Row','athlete_id','Player Name','College']].to_dict('records'),
        replacements=0,manual_counts=int(result.Instagram_Count_Provenance.eq('user_reported').sum()),
        browser_counts=int(result.Instagram_Count_Provenance.eq('browser_observed').sum()),
        provenance_by_quartile=pd.crosstab(result.Quartile,result.Instagram_Count_Provenance).to_dict(),
        manual_actions=manual_actions,frozen_sample_sha256=FROZEN_SHA,
        curated_sha256=hashlib.sha256(target.read_bytes()).hexdigest(),
        input_sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(d.glob('*.csv'))},
        collection_date='2026-11-03',nil_snapshot_date='2026-11-02',
        interpretation='Current listed top-1000 NIL population only. Membership/season not verified. Legacy basketball analyses require rerun.')
    reports=root/'reports/basketball_top1000';reports.mkdir(parents=True,exist_ok=True)
    (reports/'collection_audit.json').write_text(json.dumps(audit,indent=2)+'\n')
    return audit


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--root',type=Path,default=Path('.'))
    print(json.dumps(finalize(parser.parse_args().root),indent=2))
