"""Freeze a 100-player draw from the fully expanded Safari NIL ranking.

25 per full-frame rank quartile, seed 510, before observing follower coverage.
Only source-provided displayed valuation labels are parsed; no missing-to-zero.
"""
import argparse
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import re

import pandas as pd
from sample_quartiles import sample_quartiles
from prepare_sample import parse_valuation


def prepare(snapshot_path,output_dir):
    snapshot=json.loads(snapshot_path.read_text());rows=snapshot.get('rankingRows',[])
    match=re.search(r'Showing\s+[\d,]+\s+of\s+([\d,]+)\s+athletes',snapshot['text'])
    if not match:raise ValueError('No source total to verify frame completeness')
    expected=int(match.group(1).replace(',',''))
    if len(rows)!=expected:raise ValueError(f'Incomplete frame: {len(rows)} of {expected}; finish public pagination first')
    retrieved_at=snapshot.get('retrieved_at') or datetime.fromtimestamp(snapshot_path.stat().st_mtime,tz=timezone.utc).isoformat()
    data=[]
    for row in rows:
        m=re.search(r'/players/(b-(\d+))-',row.get('profile_url',''))
        slug=row.get('profile_url','').split('/players/')[-1]
        if not slug.startswith('b-') or not row.get('name') or not row.get('college') or not row.get('value'):raise ValueError('Missing source identity, college or valuation')
        data.append({'athlete_id':'sideline:'+slug,'ESPN_Athlete_ID_Candidate':m.group(2) if m else None,'Player Name':row['name'],'College':row['college'],
          'Position':row.get('position'),'Conference':row.get('conference'),'Grade':row.get('grade'),
          'Valuation':row['value'],'NIL_Valuation_USD':0.0 if re.fullmatch(r'\$?0(?:\.0+)?[KM]?',row['value'].strip()) else parse_valuation(row['value']),
          'Sideline_Profile_URL':row['profile_url'],'NIL_Evidence_Label':row.get('source_label'),
          'NIL_Source_URL':snapshot['url'],'NIL_Retrieved_At':retrieved_at,
          'NIL_Source_Snapshot_Date':None,'NIL_Value_Precision':'source_displayed_rounded_label',
          'Cohort':f'Sideline current listing retrieved {retrieved_at[:10]}; verify season and roster snapshot before joining performance'})
    full,sample,audit=sample_quartiles(pd.DataFrame(data),'NIL_Valuation_USD',['athlete_id'],per_quartile=25,seed=510)
    for col in ['Instagram_Username','Username_Verification_URL','Instagram_Followers','Instagram_Followers_Approx','Instagram_Observed_At']:
        sample[col]=None
    sample['Instagram_Count_Status']='not_collected'
    audit.update(snapshot_sha256=hashlib.sha256(snapshot_path.read_bytes()).hexdigest(),source_url=snapshot['url'],
       source_total=expected,sampling_order='Frozen NIL quartiles first; no replacement for unavailable followers',
       value_policy='Displayed rounded source estimates, not verified payments; no inferred source snapshot date')
    output_dir.mkdir(parents=True,exist_ok=True)
    full.to_csv(output_dir/'basketball_sideline_full_frame.csv',index=False)
    sample.to_csv(output_dir/'basketball_sideline_sample_100_frozen.csv',index=False)
    audit['frozen_sample_sha256']=hashlib.sha256((output_dir/'basketball_sideline_sample_100_frozen.csv').read_bytes()).hexdigest()
    (output_dir/'sampling_audit.json').write_text(json.dumps(audit,indent=2)+'\n')
    return audit


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--snapshot',type=Path,required=True);p.add_argument('--output-dir',type=Path,required=True)
    a=p.parse_args();print(json.dumps(prepare(a.snapshot,a.output_dir),indent=2))
