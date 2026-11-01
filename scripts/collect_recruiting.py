"""Collect official high-school recruiting records, with offline JSON replay.

Football explicitly requests classification=HighSchool. Basketball's documented
high-school composite endpoint is used. Source athlete IDs are not assumed to
share the ESPN namespace. Never use a recruit class as the college cohort year.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path

import pandas as pd
import requests
from dotenv import load_dotenv

ROOT=Path(__file__).resolve().parents[1]


def normalize_recruits(records, sport, year):
    if not isinstance(records,list) or not records:
        raise ValueError('Expected nonempty recruiting JSON array')
    rows=[]
    for r in records:
        if r.get('year') != year or not {'id','name','stars','rating'}.issubset(r):
            raise ValueError('Recruiting schema/class mismatch')
        if sport=='football' and r.get('recruitType')!='HighSchool':
            continue
        team=r.get('committedTo')
        if isinstance(team,dict): team=team.get('name')
        stars=r.get('stars')
        if stars is not None and (isinstance(stars,bool) or stars not in [0,1,2,3,4,5]):
            raise ValueError('Unexpected star scale')
        rows.append(dict(Sport=sport,Recruit_ID=str(r['id']),Recruit_Name=r['name'],
            Recruit_Class_Year=year,Recruit_College=team,Recruit_Position=r.get('position'),
            Recruit_Stars=stars if stars and stars>0 else None,Recruit_Rating=r.get('rating'),
            Recruit_National_Rank=r.get('ranking'),Recruit_High_School=r.get('school'),
            Recruit_Source_Athlete_ID=r.get('athleteId'),Recruit_HS_Verified=True,
            Recruit_Provider='CFBD_HighSchool' if sport=='football' else 'CBBD_HighSchool_Composite'))
    return pd.DataFrame(rows)


def collect(sport,year,folder,raw_json=None,env_file=None):
    load_dotenv(env_file or ROOT/'.env')
    host='collegefootballdata' if sport=='football' else 'collegebasketballdata'
    url=f'https://api.{host}.com/recruiting/players'
    params={'year':year}
    if sport=='football': params['classification']='HighSchool'
    path=raw_json or folder/f'{sport}_hs_recruits_{year}.json'
    meta_path=path.with_suffix('.meta.json')
    if path.exists():
        payload=path.read_bytes()
        if not meta_path.exists():
            raise ValueError('Replay requires source .meta.json with URL, params, retrieved_at, sha256')
        meta=json.loads(meta_path.read_text())
        if meta['url']!=url or meta['params']!=params or meta['sha256']!=hashlib.sha256(payload).hexdigest():
            raise ValueError('Recruit cache provenance mismatch')
    else:
        if raw_json: raise ValueError('Replay file does not exist')
        names=['CFBD_API_KEY','CFBD_KEY'] if sport=='football' else ['CBBD_API_KEY','CBBD_KEY','CFBD_API_KEY','CFBD_KEY']
        key=next((os.getenv(k) for k in names if os.getenv(k)),None)
        if not key: raise ValueError('No local API key; configure ignored .env. No request made.')
        response=requests.get(url,params=params,headers={'Authorization':'Bearer '+key.removeprefix('Bearer ').strip()},timeout=45)
        if response.status_code!=200: raise ValueError(f'Recruit API HTTP {response.status_code}')
        payload=response.content
        normalize_recruits(json.loads(payload),sport,year)
        folder.mkdir(parents=True,exist_ok=True)
        path.write_bytes(payload)
        meta=dict(url=url,params=params,retrieved_at=datetime.now(timezone.utc).isoformat(),sha256=hashlib.sha256(payload).hexdigest())
        meta_path.write_text(json.dumps(meta,indent=2)+'\n')
    frame=normalize_recruits(json.loads(payload),sport,year)
    for column,value in [('Recruit_Source_URL',url),('Recruit_Retrieved_At',meta['retrieved_at']),('Recruit_Response_SHA256',meta['sha256'])]:
        frame[column]=value
    return frame


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--sport',choices=['football','basketball'],required=True)
    p.add_argument('--years',nargs='+',type=int,required=True)
    p.add_argument('--raw-json',type=Path,help='Single-year authorized response with provenance sidecar')
    p.add_argument('--env-file',type=Path)
    p.add_argument('--outdir',type=Path,default=ROOT/'Data/private/evaluation/official_recruiting')
    a=p.parse_args()
    if a.raw_json and len(a.years)!=1: p.error('--raw-json requires exactly one year')
    try:
        frames=[collect(a.sport,y,a.outdir,a.raw_json,a.env_file) for y in a.years]
        a.outdir.mkdir(parents=True,exist_ok=True)
        out=a.outdir/f'{a.sport}_hs_recruits.csv'
        pd.concat(frames,ignore_index=True).to_csv(out,index=False)
        print(f'Saved {sum(len(f) for f in frames)} records to {out}')
    except (ValueError,OSError,requests.RequestException) as e:
        p.exit(1,'Recruiting stopped: '+(str(e) if isinstance(e,ValueError) else type(e).__name__)+'\n')
