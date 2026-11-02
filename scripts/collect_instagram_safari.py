"""Read sourced public-profile follower labels in a dedicated Safari window.

The user must handle any login themselves. Stops at login/challenge screens;
never reads cookies, credentials, private APIs, feeds, or private messages.
Keeps the frozen sample, existing observations and rounded-count distinctions.
"""
import argparse
from datetime import datetime, timezone
import hashlib
from html import escape
import json
from pathlib import Path
import re
import subprocess
import time
from urllib.parse import urlparse

import pandas as pd
from collect_sideline_safari import new_window, evaluate, literal
from collect_public_instagram import parse_public_profile


SNAPSHOT='''JSON.stringify({url:location.href,title:document.title,
metadata:Array.from(document.querySelectorAll('meta[property^="og:"]')).map(m=>({property:m.getAttribute('property'),content:m.content})),
followerLinks:Array.from(document.querySelectorAll('a[href]')).filter(a=>/\\/followers\\/?$/.test(a.pathname)).map(a=>({href:a.href,text:a.innerText,title:a.title,spans:Array.from(a.querySelectorAll('[title]')).map(s=>s.title)})),
challenge:!!document.querySelector('iframe[src*="captcha"],iframe[src*="challenge"]')})'''


def parse_snapshot(snapshot, username):
    url=urlparse(snapshot['url'])
    if url.hostname not in ['www.instagram.com','instagram.com'] or url.path.strip('/').lower()!=username.lower():
        raise ValueError('Not the requested Instagram profile; login/redirect requires user review')
    if snapshot.get('challenge'):raise ValueError('Browser verification required; stopped')
    html=''.join(f'<meta property="{escape(m["property"],quote=True)}" content="{escape(m["content"],quote=True)}">' for m in snapshot['metadata'])
    try:return parse_public_profile(html,username)
    except ValueError:pass
    matches=[r for r in snapshot['followerLinks'] if urlparse(r['href']).path.strip('/').lower()==username.lower()+'/followers']
    if len(matches)!=1:raise ValueError('No unambiguous visible follower link; not inferred as zero')
    link=matches[0]
    # Full integer tooltips are accepted only on this athlete's followers link.
    titles=[x.strip() for x in [link.get('title',''),*link.get('spans',[])] if re.fullmatch(r'[0-9][0-9,]*',x.strip())]
    if titles:
        if len(set(titles))!=1:raise ValueError('Conflicting follower tooltips')
        label=titles[0]
    else:
        m=re.fullmatch(r'\s*([0-9][0-9,.]*(?:\s*[KMB])?)\s+followers\s*',link['text'],re.I)
        if not m:raise ValueError('Unsupported follower label; retained for review')
        label=m.group(1)
    fixture=f'<meta property="og:url" content="https://www.instagram.com/{username}/"><meta property="og:title" content="@{username}"><meta property="og:description" content="{label} Followers">'
    result=parse_public_profile(fixture,username)
    result['Instagram_Profile_Title']=snapshot['title']
    result['Instagram_Measurement_Note']='Visible followers-link label/tooltip in normal Safari profile DOM; retrieval time recorded'
    return result


def collect(args):
    if args.input.resolve()==args.output.resolve():raise ValueError('Keep the input observations unchanged')
    d=pd.read_csv(args.input,dtype={'athlete_id':'string'})
    if not {'Instagram_Username','Username_Verification_URL','Instagram_Followers','Instagram_Followers_Approx'}.issubset(d):
        raise ValueError('Use the sourced-handle observations sheet as input')
    raw=args.output.parent/'safari_instagram_raw';raw.mkdir(parents=True,exist_ok=True)
    results=[];window=None;calls=0;stopped=False
    for record in d.to_dict('records'):
        row=dict(record);username=str(record.get('Instagram_Username',''))
        existing=pd.notna(record.get('Instagram_Followers')) or pd.notna(record.get('Instagram_Followers_Approx'))
        if not existing and re.fullmatch('[A-Za-z0-9_.]{1,30}',username) and pd.notna(record.get('Username_Verification_URL')):
            path=raw/(username.lower()+'.json');meta_path=path.with_suffix('.meta.json')
            try:
                if path.exists() and meta_path.exists():
                    payload=path.read_bytes();meta=json.loads(meta_path.read_text())
                    if hashlib.sha256(payload).hexdigest()!=meta['sha256']:raise ValueError('Cache hash mismatch')
                elif args.offline or stopped or calls>=args.max_profiles:raise ValueError('No cached Safari observation; live collection unavailable')
                else:
                    url=f'https://www.instagram.com/{username}/'
                    if window is None:window=new_window(url)
                    else:evaluate(window,'location.href='+json.dumps(url))
                    calls+=1;time.sleep(args.delay)
                    snapshot=json.loads(evaluate(window,SNAPSHOT))
                    payload=(json.dumps(snapshot,indent=2)+'\n').encode();path.write_bytes(payload)
                    meta=dict(source_url=url,retrieved_at=datetime.now(timezone.utc).isoformat(),sha256=hashlib.sha256(payload).hexdigest())
                    meta_path.write_text(json.dumps(meta,indent=2)+'\n')
                snapshot=json.loads(payload)
                if '/accounts/' in snapshot['url'] or snapshot.get('challenge'):
                    stopped=True;raise ValueError('Safari requires login or verification; user action required, live collection stopped')
                row.update(parse_snapshot(snapshot,username))
                row.update(Instagram_Provider='Instagram_Safari_public_profile',Instagram_Source_URL=meta['source_url'],
                    Instagram_Observed_At=meta['retrieved_at'],Instagram_Response_SHA256=meta['sha256'],Instagram_Collection_Note='')
            except (ValueError,KeyError,RuntimeError,OSError,subprocess.TimeoutExpired) as exc:
                row['Instagram_Collection_Note']=str(exc)
                if isinstance(exc,(RuntimeError,subprocess.TimeoutExpired)):stopped=True
        results.append(row)
        pd.DataFrame(results).to_csv(args.output.with_suffix('.partial.csv'),index=False)
    output=pd.DataFrame(results);output.to_csv(args.output,index=False)
    report=dict(rows=len(output),live_requests=calls,stopped_for_login_or_challenge=stopped,
        direct_display_integer=int(output.Instagram_Followers.notna().sum()),direct_rounded=int(output.Instagram_Followers_Approx.notna().sum()),
        input_sha256=hashlib.sha256(args.input.read_bytes()).hexdigest())
    args.output.with_suffix('.audit.json').write_text(json.dumps(report,indent=2)+'\n');return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--max-profiles',type=int,default=100);p.add_argument('--delay',type=float,default=5)
    p.add_argument('--offline',action='store_true');a=p.parse_args()
    if a.delay<2 or not 0<=a.max_profiles<=100:p.error('Use delay >=2 seconds and request cap 0..100')
    print(json.dumps(collect(a),indent=2))
