"""Read public Instagram profile metadata for already sourced athlete handles.

No login, cookies, private API, paid request, or access-control bypass. Preserves
rounded K/M labels separately from exact displayed integers. Keeps every input
row and stops live retrieval after a rate-limit/block response. Raw HTML remains
local; aggregate provenance and parser code can be shared for review.
"""
import argparse
from datetime import datetime, timezone
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import subprocess
import time
from urllib.parse import urlparse

import pandas as pd


class Metadata(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True); self.values={}
    def handle_starttag(self,tag,attrs):
        if tag.lower()=='meta':
            a=dict(attrs); key=a.get('property') or a.get('name')
            if key and 'content' in a:self.values[key]=a['content']


def login_required(html):
    parser=Metadata();parser.feed(html)
    return (parser.values.get('og:title','').strip().lower()=='instagram' and
            'log in to instagram' in parser.values.get('description','').lower())


def parse_public_profile(html, username):
    parser=Metadata();parser.feed(html);m=parser.values
    url=m.get('og:url','');title=m.get('og:title','')
    host=urlparse(url).hostname
    returned=urlparse(url).path.strip('/').lower()
    if host not in ['instagram.com','www.instagram.com'] or returned!=username.lower():
        raise ValueError('Missing/mismatched canonical Instagram profile; login or unavailable page')
    if '@'+username.lower() not in title.lower():raise ValueError('Profile title handle does not match')
    description=m.get('og:description','')
    match=re.match(r'^([0-9][0-9,.]*(?:\s*[KMB])?)\s+Followers\b',description,re.I)
    if not match:raise ValueError('No supported public follower label; do not infer zero')
    label=match.group(1).replace(' ','');suffix=label[-1].upper()
    abbreviated=suffix in 'KMB'
    number=label[:-1] if abbreviated else label
    number=number.replace(',','')
    value=float(number)*({'K':1000,'M':1000000,'B':1000000000}[suffix] if abbreviated else 1)
    if not abbreviated and not value.is_integer():raise ValueError('Noninteger unabbreviated follower label')
    return dict(Instagram_Followers=None if abbreviated else int(value),
        Instagram_Followers_Approx=int(round(value)) if abbreviated else None,
        Instagram_Raw_Label=label,
        Instagram_Count_Status='observed_public_rounded' if abbreviated else 'observed_public_display_integer',
        Instagram_Count_Precision='abbreviated_label_rounding_rule_unknown' if abbreviated else 'displayed_integer',
        Instagram_Canonical_URL=url,Instagram_Profile_Title=title,
        Instagram_Source_Reported_At=None,
        Instagram_Measurement_Note='Metadata retrieved at observation time; platform count freshness is not independently established')


def collect(args):
    if args.input.resolve()==args.output.resolve():raise ValueError('Do not overwrite the frozen sample')
    d=pd.read_csv(args.input,dtype={'athlete_id':'string'})
    required={'Instagram_Username','Username_Verification_URL'}
    if not required.issubset(d):raise ValueError(f'Need {required}')
    if args.delay<1:raise ValueError('Delay must be at least one second')
    raw=args.output.parent/'public_instagram_raw';raw.mkdir(parents=True,exist_ok=True)
    result=[];audit=[];calls=0;blocked=False
    for record in d.to_dict('records'):
        row={**record,'Instagram_Followers':None,'Instagram_Followers_Approx':None,
             'Instagram_Count_Status':'not_collected','Instagram_Provider':'Instagram_public_profile_metadata',
             'Instagram_Observed_At':None,'Instagram_Response_SHA256':None,'Instagram_Collection_Note':''}
        username=str(record.get('Instagram_Username','')).strip().lstrip('@')
        evidence=record.get('Username_Verification_URL')
        try:
            if not re.fullmatch('[A-Za-z0-9_.]{1,30}',username) or pd.isna(evidence) or not str(evidence).startswith('https://'):
                raise ValueError('Missing verified handle/source evidence')
            path=raw/(username.lower()+'.html');meta_path=path.with_suffix('.meta.json')
            if path.exists() and meta_path.exists():
                payload=path.read_bytes();meta=json.loads(meta_path.read_text())
                if hashlib.sha256(payload).hexdigest()!=meta['sha256']:raise ValueError('Cache hash mismatch')
                if meta['username'].lower()!=username.lower():raise ValueError('Cache username mismatch')
            elif args.offline:raise ValueError('No cached public snapshot')
            elif blocked:raise ValueError('Live collection stopped after a block/rate limit; row retained')
            elif calls>=args.max_profiles:raise ValueError('Live request cap reached; row retained')
            else:
                if calls:time.sleep(args.delay)
                calls+=1;url=f'https://www.instagram.com/{username}/'
                response=subprocess.run(['curl','-L','--max-time','35','-sS','-w','%{http_code}','-o',str(path),url],capture_output=True,text=True)
                code=int(response.stdout) if response.stdout.isdigit() else 0
                payload=path.read_bytes() if path.exists() else b''
                meta=dict(username=username,provider='Instagram_public_profile_metadata',source_url=url,
                    retrieved_at=datetime.now(timezone.utc).isoformat(),http_status=code,
                    sha256=hashlib.sha256(payload).hexdigest())
                meta_path.write_text(json.dumps(meta,indent=2)+'\n')
                if code in [403,429]:blocked=True
            row.update(Instagram_Observed_At=meta['retrieved_at'],Instagram_Response_SHA256=meta['sha256'],Instagram_Source_URL=meta['source_url'])
            if meta['http_status']!=200:raise ValueError(f"Public source returned HTTP {meta['http_status']}")
            html=payload.decode('utf-8',errors='replace')
            if login_required(html):
                blocked=True
                raise ValueError('Public source requires login; stopped live collection, row retained')
            row.update(parse_public_profile(html,username))
        except (ValueError,OSError,KeyError) as exc:row['Instagram_Collection_Note']=str(exc)
        result.append(row)
        audit.append({k:row.get(k) for k in ['Instagram_Count_Status','Instagram_Count_Precision']})
        print(f"{len(result)}/{len(d)} {row['Instagram_Count_Status']}",flush=True)
    output=pd.DataFrame(result);args.output.parent.mkdir(parents=True,exist_ok=True);output.to_csv(args.output,index=False)
    summary=dict(input_rows=len(d),output_rows=len(output),live_requests=calls,
        status_counts=output.Instagram_Count_Status.value_counts().to_dict(),stopped_for_block=blocked,
        input_sha256=hashlib.sha256(args.input.read_bytes()).hexdigest(),
        exact_column_policy='Instagram_Followers contains only unabbreviated displayed integers; K/M labels use separate approximate field',
        identity_policy='handle comes from input source evidence; canonical URL and returned handle must agree; athlete identity still requires source review')
    args.output.with_suffix('.audit.json').write_text(json.dumps(summary,indent=2)+'\n')
    return summary


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--input',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--max-profiles',type=int,default=100);p.add_argument('--delay',type=float,default=1.5);p.add_argument('--offline',action='store_true')
    print(json.dumps(collect(p.parse_args()),indent=2))
