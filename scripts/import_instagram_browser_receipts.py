"""Import reviewed visible-DOM receipts without changing the frozen sample.

Receipts contain selected public follower fields exported from browser tool
observations, not saved HTTP bodies. Integer tooltips remain distinct from the
rounded visible labels. Newly sourced accounts require athlete-ID keyed review.
"""
import argparse
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re

import pandas as pd


def import_receipts(data, receipts, reviews):
    result=data.copy();changed=[]
    if result.athlete_id.duplicated().any() or result.Sample_Row.duplicated().any():raise ValueError('Ambiguous input identities')
    if receipts.Sample_Row.duplicated().any():raise ValueError('Duplicate receipts; explicitly resolve observation times first')
    if not reviews.empty and reviews.athlete_id.duplicated().any():raise ValueError('Conflicting account reviews')
    for r in receipts.to_dict('records'):
        match=result.index[result.Sample_Row.eq(int(r['Sample_Row']))]
        if len(match)!=1:raise ValueError('Receipt row not in frozen cohort')
        ix=match[0];player=result.loc[ix];handle=str(r['username'])
        if not re.fullmatch('[A-Za-z0-9_.]{1,30}',handle):raise ValueError('Invalid handle')
        existing=str(player.get('Instagram_Username','')).lower()==handle.lower() and pd.notna(player.get('Username_Verification_URL'))
        review=reviews.loc[reviews.athlete_id.eq(player.athlete_id)] if not reviews.empty else pd.DataFrame()
        if not existing:
            if len(review)!=1 or str(review.iloc[0].Instagram_Username).lower()!=handle.lower():
                raise ValueError(f'No account identity review for sample row {r["Sample_Row"]}')
            v=review.iloc[0]
            result.loc[ix,'Username_Verification_URL']=v.Username_Verification_URL
            result.loc[ix,'Instagram_Handle_Identity_Status']='reviewed_public_basketball_identity'
            result.loc[ix,'Instagram_Handle_Identity_Note']=v.Review_Note
        raw=str(r['integer_tooltip']);display=str(r['display_label'])
        if not re.fullmatch('[0-9][0-9,]*',raw):raise ValueError('Tooltip must be a displayed integer, not K/M')
        timestamp=datetime.fromisoformat(str(r['retrieved_at']).replace('Z','+00:00'))
        if timestamp.tzinfo is None:raise ValueError('Observation needs a timezone')
        # The title attribute on the same profile's visible followers link was
        # captured by the browser collector; it is not an inferred K/M expansion.
        evidence=json.dumps(r,sort_keys=True,default=str).encode()
        updates=dict(Instagram_Username=handle,Instagram_Followers=int(raw.replace(',','')),
            Instagram_Followers_Approx=None,Instagram_Raw_Label=display,
            Instagram_Integer_Tooltip=raw,Instagram_Count_Precision='visible_followers_link_integer_tooltip',
            Instagram_Count_Status='observed_browser_integer_tooltip',Instagram_Provider='Instagram_Chrome_visible_profile',
            Instagram_Observed_At=r['retrieved_at'],Instagram_Source_URL=f'https://www.instagram.com/{handle}/',
            Instagram_Canonical_URL=f'https://www.instagram.com/{handle}/',Instagram_Source_Reported_At=None,
            Instagram_Response_SHA256=None,Instagram_Evidence_SHA256=hashlib.sha256(evidence).hexdigest(),
            Instagram_Evidence_Format='selected_DOM_fields_exported_from_browser_tool',
            Instagram_Measurement_Note='Exact integer tooltip on visible public-profile followers label in user-authorized signed-in Chrome; no private API',
            Instagram_Collection_Note='')
        for col,value in updates.items():
            if col not in result:result[col]=None
            if result[col].dtype.kind not in 'O' and isinstance(value,str):result[col]=result[col].astype(object)
            result.loc[ix,col]=value
        changed.append(int(r['Sample_Row']))
    for col in ['Instagram_Followers','Instagram_Followers_Approx']:result[col]=pd.to_numeric(result[col],errors='raise').astype('Int64')
    missing=result.Instagram_Followers.isna() & result.Instagram_Followers_Approx.isna()
    if 'Instagram_Attempted_At' not in result:result['Instagram_Attempted_At']=None
    result.loc[missing,'Instagram_Attempted_At']=result.loc[missing,'Instagram_Observed_At']
    result.loc[missing,'Instagram_Observed_At']=None
    assert result.athlete_id.tolist()==data.athlete_id.tolist()
    assert result.Quartile.tolist()==data.Quartile.tolist()
    return result,changed


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input',type=Path,required=True);p.add_argument('--receipts',type=Path,required=True)
    p.add_argument('--reviewed',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    if a.input.resolve()==a.output.resolve():raise ValueError('Preserve the prior observation sheet')
    d=pd.read_csv(a.input);receipts=pd.read_csv(a.receipts,dtype=str)
    receipts['Sample_Row']=receipts.Sample_Row.astype(int)
    result,changed=import_receipts(d,receipts,pd.read_csv(a.reviewed));result.to_csv(a.output,index=False)
    audit=dict(rows=len(result),updated_rows=changed,exact_count_rows=int(result.Instagram_Followers.notna().sum()),
        input_sha256=hashlib.sha256(a.input.read_bytes()).hexdigest(),receipts_sha256=hashlib.sha256(a.receipts.read_bytes()).hexdigest(),
        reviews_sha256=hashlib.sha256(a.reviewed.read_bytes()).hexdigest(),output_sha256=hashlib.sha256(a.output.read_bytes()).hexdigest(),
        sample_and_strata_unchanged=True,receipt_note='Selected DOM fields exported via browser tool; no HTTP body claimed')
    a.output.with_suffix('.audit.json').write_text(json.dumps(audit,indent=2)+'\n');print(json.dumps(audit,indent=2))
