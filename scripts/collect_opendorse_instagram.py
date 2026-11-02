"""Collect public Opendorse profile Instagram reach for a frozen player sample.

Name slugs are lookup candidates, not proof of identity. Require exact normalized
name, men's basketball, and current school or a supplied verified prior school.
No authentication/private API; parses the data delivered with public profiles.
Reported positive reach has unknown underlying measurement freshness. Defaults
and zero placeholders never become observed zero followers. Preserve all rows.
"""
import argparse
from datetime import datetime,timezone
import hashlib
from html import unescape
import json
from pathlib import Path
import re
import subprocess
import time
import unicodedata
from urllib.parse import urlparse

import pandas as pd


def normalize(s):return re.sub('[^a-z0-9]','',unicodedata.normalize('NFKD',str(s)).encode('ascii','ignore').decode().lower())
def slug(s):return re.sub('[^a-z0-9]+','-',unicodedata.normalize('NFKD',str(s)).encode('ascii','ignore').decode().lower()).strip('-')

ALIASES={'uconn':['Connecticut'],'usc':['Southern California'],'loyolachicago':['Loyola Chicago','Loyola (IL)'],
 'loyolamarymount':['Loyola Marymount','LMU'],'calstatenorthridge':['Cal State Northridge','CSUN'],
 'californiabaptist':['California Baptist','Cal Baptist'],'seMissouristate'.lower():['Southeast Missouri'],
 'arkansaspinebluff':['Arkansas Pine Bluff','UAPB'],'easttexasam':['East Texas A&M','Texas A&M Commerce'],
 'umasslowell':['UMass Lowell','Massachusetts Lowell'],'texasam':['Texas A&M']}


def school_matches(school,teams):
    targets=[school,*ALIASES.get(normalize(school),[])]
    return any((normalize(name) in normalize(team) if len(normalize(name))>=4 else
        bool(re.match(r'^'+re.escape(str(name))+r'\b',str(team),re.I)))
        for name in targets for team in teams if len(normalize(name))>=2)


def parse_profile(html,record,prior_schools=()):
    m=re.search(r'<script\b[^>]*\bid="__NEXT_DATA__"[^>]*>(.*?)</script>',html,re.S)
    if not m:raise ValueError('No public profile payload (unavailable/login/challenge)')
    d=json.loads(m.group(1))['props']['pageProps']['initialState']['profile']['profileData']
    if not d:raise ValueError('Public athlete profile not found')
    name=' '.join([d.get('firstName',''),d.get('lastName','')]).strip()
    names={normalize(name),normalize((d.get('nickname') or '')+' '+(d.get('lastName') or ''))}
    if normalize(record['Player Name']) not in names:raise ValueError('Profile name does not match selected athlete')
    if "Men's Basketball" not in d.get('sports',[]):raise ValueError('Profile is not a men basketball athlete')
    teams=d.get('currentTeams',[])+d.get('previousTeams',[])
    if school_matches(record['College'],teams):identity='exact_name_sport_school'
    elif any(school_matches(s,teams) for s in prior_schools):identity='exact_name_sport_verified_prior_school'
    else:raise ValueError('Name/sport candidate needs school/identity review; no count accepted')
    link=d.get('instagramUrl') or ''
    if not link.startswith('http'):link='https://'+link
    u=urlparse(link);handle=u.path.strip('/')
    if u.hostname not in ['instagram.com','www.instagram.com'] or not re.fullmatch('[A-Za-z0-9_.]{1,30}',handle):raise ValueError('No valid source-linked Instagram handle')
    count=d.get('instagramReach')
    valid_count=not isinstance(count,bool) and isinstance(count,(int,float)) and count>0 and int(count)==count
    return dict(Instagram_Username=handle,Instagram_Profile_URL=f'https://www.instagram.com/{handle}/',
       Instagram_Followers=int(count) if valid_count else None,
       Instagram_Count_Status='observed_opendorse_reported_integer' if valid_count else 'handle_observed_count_missing',
       Instagram_Count_Precision='provider_reported_integer',Instagram_Provider='Opendorse_public_profile',
       Instagram_Identity_Status=identity,Instagram_Source_Athlete_Name=name,
       Instagram_Source_School_Affiliations=' | '.join(teams),Instagram_Source_Reported_At=None,
       Instagram_Measurement_Note='Public provider-reported Instagram reach; retrieval time is known, underlying count measurement date is not supplied')


def collect(args):
    d=pd.read_csv(args.input,dtype={'athlete_id':'string','ESPN_Athlete_ID_Candidate':'string'})
    if args.output.resolve()==args.input.resolve():raise ValueError('Never overwrite frozen sample')
    history={}
    if args.performance:
        p=pd.read_csv(args.performance,dtype={'athlete_id':'string'})
        for row in p.to_dict('records'):
            history.setdefault((str(row['athlete_id']),normalize(row['Player_Name'])),set()).add(row['College'])
    raw=args.output.parent/'opendorse_raw';raw.mkdir(parents=True,exist_ok=True)
    rows=[];calls=0;blocked=False
    for rec in d.to_dict('records'):
        row={**rec,'Instagram_Followers':None,'Instagram_Count_Status':'not_collected',
             'Instagram_Collection_Note':'','Instagram_Provider':'Opendorse_public_profile'}
        candidate=slug(rec['Player Name']);path=raw/(candidate+'.html');meta_path=path.with_suffix('.meta.json')
        try:
            if path.exists() and meta_path.exists():
                payload=path.read_bytes();meta=json.loads(meta_path.read_text())
                if hashlib.sha256(payload).hexdigest()!=meta['sha256']:raise ValueError('Source cache hash mismatch')
            elif args.offline:raise ValueError('No cached public profile')
            elif blocked:raise ValueError('Collection stopped for rate limit/block')
            elif calls>=args.max_profiles:raise ValueError('Live request cap reached')
            else:
                if calls:time.sleep(args.delay)
                calls+=1;url='https://opendorse.com/profile/'+candidate
                r=subprocess.run(['curl','-L','--max-time','30','-sS','-w','%{http_code}','-o',str(path),url],capture_output=True,text=True)
                code=int(r.stdout) if r.stdout.isdigit() else 0;payload=path.read_bytes() if path.exists() else b''
                meta=dict(source_url=url,http_status=code,retrieved_at=datetime.now(timezone.utc).isoformat(),sha256=hashlib.sha256(payload).hexdigest())
                meta_path.write_text(json.dumps(meta,indent=2)+'\n')
                if code in [403,429]:blocked=True
            row.update(Instagram_Source_URL=meta['source_url'],Username_Verification_URL=meta['source_url'],
                       Instagram_Observed_At=meta['retrieved_at'],Instagram_Response_SHA256=meta['sha256'])
            if meta['http_status']!=200:raise ValueError(f"Public profile HTTP {meta['http_status']}")
            prior=history.get((str(rec.get('ESPN_Athlete_ID_Candidate')),normalize(rec['Player Name'])),set())
            row.update(parse_profile(payload.decode('utf-8',errors='replace'),rec,prior))
        except (ValueError,KeyError,OSError,TypeError) as exc:row['Instagram_Collection_Note']=str(exc)
        rows.append(row);print(f"{len(rows)}/{len(d)} {row['Instagram_Count_Status']}",flush=True)
        # Checkpoint after each public request so an interruption loses no rows.
        pd.DataFrame(rows).to_csv(args.output.with_suffix('.partial.csv'),index=False)
    result=pd.DataFrame(rows);result.to_csv(args.output,index=False)
    audit=dict(input_rows=len(d),output_rows=len(result),status_counts=result.Instagram_Count_Status.value_counts().to_dict(),
      live_requests=calls,source='public Opendorse profile HTML and serialized page data',
      source_count_date_policy='Underlying measurement date unavailable; retrieval timestamp is not proof of contemporaneous measurement',
      input_sha256=hashlib.sha256(args.input.read_bytes()).hexdigest())
    args.output.with_suffix('.audit.json').write_text(json.dumps(audit,indent=2)+'\n');return audit


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--input',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--performance',type=Path);p.add_argument('--max-profiles',type=int,default=100);p.add_argument('--delay',type=float,default=1.5);p.add_argument('--offline',action='store_true')
    a=p.parse_args()
    if a.delay<1 or a.max_profiles<0:p.error('Use >=1 second delay and a nonnegative request cap')
    print(json.dumps(collect(a),indent=2))
