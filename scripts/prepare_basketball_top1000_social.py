"""Cut the NIL ranking to its top 1,000 FIRST, then draw 25 per quartile.

This supersedes the legacy all-5,348-frame design. Selection is locked before
Google/Instagram lookup. Source display ties use the existing stable rank/ID
order; no player is substituted for an unavailable social account.
"""
import argparse
import hashlib
import json
from pathlib import Path
from urllib.parse import quote
import pandas as pd
from sample_quartiles import sample_quartiles


def prepare(source,output_dir,seed=510):
    raw=pd.read_csv(source,dtype={'athlete_id':'string','ESPN_Athlete_ID_Candidate':'string'})
    if len(raw)<1000 or raw.athlete_id.duplicated().any():raise ValueError('Need at least 1,000 uniquely identified listings')
    if not raw.Frame_Rank.is_unique or raw.NIL_Valuation_USD.isna().any():raise ValueError('Ranking or valuation incomplete')
    raw=raw.sort_values('Frame_Rank',kind='stable')
    if raw.Frame_Rank.iloc[:1000].tolist()!=list(range(1,1001)):raise ValueError('Top ranks are incomplete')
    top=raw.iloc[:1000].copy()
    if not top.NIL_Valuation_USD.is_monotonic_decreasing:raise ValueError('Source ranking not descending by NIL')
    top['NIL_Global_Rank']=top.Frame_Rank
    top['Legacy_Full_Frame_Quartile']=top.Quartile
    top=top.drop(columns=['Quartile','Stratification_Value','Stratification_Metric','Stratum_Population_N',
        'Selection_Probability','Sampling_Weight','Metric_Tie_Crosses_Quartile','Frame_Rank'],errors='ignore')
    frame,sample,audit=sample_quartiles(top,'NIL_Valuation_USD',['athlete_id'],per_quartile=25,seed=seed)
    if not frame.NIL_Global_Rank.tolist()==frame.Frame_Rank.tolist():raise ValueError('Stable source order changed at a tie')
    for d in [frame,sample]:
        d['Sampling_Frame']='Top 1000 Sideline basketball listings, ranked by NIL; November 2 2026 source snapshot'
        d['Sport']='basketball'
    for col in ['Instagram_Username','Username_Verification_URL','Instagram_Followers','Instagram_Followers_Approx','Instagram_Observed_At']:
        sample[col]=None
    sample['Instagram_Count_Status']='not_collected'
    sample['Lookup_Query']=sample['Player Name']+' '+sample.College+' instagram'
    sample['Google_Search_URL']=sample.Lookup_Query.map(lambda q:'https://www.google.com/search?q='+quote(q))
    output_dir.mkdir(parents=True,exist_ok=True)
    frame.to_csv(output_dir/'basketball_top1000_nil_frame.csv',index=False)
    sample.to_csv(output_dir/'basketball_top1000_sample_100_frozen.csv',index=False)
    audit.update(source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),source_rows=len(raw),
        frame_definition='Source global ranks 1 through 1000, then rank quartiles of 250 each',
        quartile_global_rank_ranges={q:[int(g.NIL_Global_Rank.min()),int(g.NIL_Global_Rank.max())] for q,g in frame.groupby('Quartile')},
        frame_sha256=hashlib.sha256((output_dir/'basketball_top1000_nil_frame.csv').read_bytes()).hexdigest(),
        frozen_sample_sha256=hashlib.sha256((output_dir/'basketball_top1000_sample_100_frozen.csv').read_bytes()).hexdigest(),
        source_snapshot_retrieved='2026-11-02',correction_date='2026-11-03',
        replaces='Legacy 100-player sample drawn from all 5348 listings; not the requested population',
        follower_lookup='Google: player name + college + instagram; first Instagram result; inspect school-post athlete tags where needed')
    (output_dir/'sampling_audit.json').write_text(json.dumps(audit,indent=2)+'\n');return audit


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True);p.add_argument('--output-dir',type=Path,required=True)
    p.add_argument('--seed',type=int,default=510);a=p.parse_args();print(json.dumps(prepare(a.source,a.output_dir,a.seed),indent=2))
