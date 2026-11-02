"""Replay sourced profile URLs and extract Instagram link candidates for review.

Inputs are explicit public profile URLs discovered in source searches, never
guessed Instagram handles. Candidate links are NOT accepted athlete identities.
Raw profiles stay local; review account context before adding a handle to the
frozen sample. No login or access-control bypass; blocked hosts are skipped.
"""
import argparse
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess
import time
from urllib.parse import urlparse

import pandas as pd
from bs4 import BeautifulSoup


def run(args):
    data=pd.read_csv(args.input);raw=args.output.parent/'profile_evidence_raw';raw.mkdir(parents=True,exist_ok=True)
    records=[];blocked=set();calls=0
    for row in data.to_dict('records'):
        url=row['url'];host=urlparse(url).hostname
        digest=hashlib.sha256(url.encode()).hexdigest()[:20];path=raw/(digest+'.html');meta_path=path.with_suffix('.meta.json')
        record={**row,'Instagram_Link_Candidates':[],'status':'not_collected'}
        try:
            if path.exists() and meta_path.exists():
                meta=json.loads(meta_path.read_text());payload=path.read_bytes()
                if hashlib.sha256(payload).hexdigest()!=meta['sha256']:raise ValueError('Cache hash mismatch')
            elif args.offline:raise ValueError('No cached profile')
            elif host in blocked:raise ValueError('Host blocked/rate-limited; no further requests')
            elif calls>=args.max_profiles:raise ValueError('Request cap reached')
            else:
                if calls:time.sleep(args.delay)
                calls+=1
                r=subprocess.run(['curl','-L','--max-time','25','-sS','-w','%{http_code}','-o',str(path),url],capture_output=True,text=True)
                code=int(r.stdout) if r.stdout.isdigit() else 0;payload=path.read_bytes() if path.exists() else b''
                meta=dict(source_url=url,http_status=code,retrieved_at=datetime.now(timezone.utc).isoformat(),sha256=hashlib.sha256(payload).hexdigest())
                meta_path.write_text(json.dumps(meta,indent=2)+'\n')
                if code in [403,429]:blocked.add(host)
            record.update(source_sha256=meta['sha256'],retrieved_at=meta['retrieved_at'])
            if meta['http_status']!=200:raise ValueError(f"HTTP {meta['http_status']}")
            soup=BeautifulSoup(payload,'html.parser');record['title']=soup.title.get_text(' ',strip=True) if soup.title else ''
            candidates={}
            for a in soup.find_all('a',href=True):
                u=urlparse(a['href']);handle=u.path.strip('/')
                if u.hostname in ['www.instagram.com','instagram.com'] and re.fullmatch('[A-Za-z0-9_.]{1,30}',handle):
                    # Preserve nearby source context to distinguish athlete and team/footer links.
                    parent=a.parent
                    candidates.setdefault(handle,dict(username=handle,url=f'https://www.instagram.com/{handle}/',
                        anchor_text=a.get_text(' ',strip=True),parent_class=parent.get('class',[]),
                        context=parent.get_text(' ',strip=True)[:280]))
            record['Instagram_Link_Candidates']=list(candidates.values());record['status']='profile_read_candidates_need_review'
        except (ValueError,OSError,KeyError) as exc:record['error']=str(exc)
        records.append(record)
        args.output.write_text(json.dumps(records,indent=2)+'\n')
        print(f"{len(records)}/{len(data)} candidates={len(record['Instagram_Link_Candidates'])}",flush=True)
    return dict(rows=len(records),requests=calls,rows_with_candidates=sum(bool(x['Instagram_Link_Candidates']) for x in records))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--input',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--max-profiles',type=int,default=150);p.add_argument('--delay',type=float,default=1);p.add_argument('--offline',action='store_true')
    a=p.parse_args()
    if a.delay<1:p.error('Use at least one second between requests')
    print(json.dumps(run(a),indent=2))
