"""Collect the public Sideline basketball ranking through the user's Safari.

Uses AppleScript and ordinary page controls in one dedicated Safari window.
Does not log in, solve verification, change browser security settings, spoof a
browser, or use private endpoints. Pauses on a challenge or disabled Apple
Events JavaScript. Requires macOS Safari and user-enabled JavaScript from Apple
Events. Local raw page snapshots remain ignored. Use --window-id to resume.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
URL='https://thesideline.co/nil-tracker/top-players/basketball'


def literal(text):
    return '"'+str(text).replace('\\','\\\\').replace('"','\\"').replace('\n','\\n').replace('\r','\\r')+'"'


def apple(script):
    p=subprocess.run(['osascript','-'],input=script,capture_output=True,text=True,timeout=25)
    if p.returncode:raise RuntimeError(p.stderr.strip())
    return p.stdout.strip()


def evaluate(window_id, javascript):
    return apple(f'tell application "Safari"\nreturn do JavaScript {literal(javascript)} in current tab of window id {int(window_id)}\nend tell')


def new_window(url=URL):
    # Safari may leave the old window frontmost briefly after creating a document.
    # Identify the new window by ID rather than navigating an unrelated front tab.
    return int(apple('tell application "Safari"\n'
        'set previousIDs to id of every window\n'
        'make new document with properties {URL:'+literal(url)+'}\n'
        'repeat 50 times\nrepeat with candidateWindow in windows\n'
        'if (id of candidateWindow) is not in previousIDs then return id of candidateWindow\n'
        'end repeat\ndelay 0.2\nend repeat\n'
        'error "Could not identify the dedicated new Safari window"\nend tell'))


SNAPSHOT="""JSON.stringify({url:location.href,title:document.title,
text:document.body?document.body.innerText:'',
tables:Array.from(document.querySelectorAll('table')).map(t=>({headers:Array.from(t.querySelectorAll('thead th')).map(x=>x.innerText),rows:Array.from(t.querySelectorAll('tbody tr')).map(r=>({text:r.innerText,cells:Array.from(r.querySelectorAll('td')).map(c=>c.innerText),links:Array.from(r.querySelectorAll('a[href]')).map(a=>({text:a.innerText,href:a.href}))}))})),
buttons:Array.from(document.querySelectorAll('button')).map(b=>({text:b.innerText,disabled:b.disabled})),
selects:Array.from(document.querySelectorAll('select')).map(s=>({value:s.value,options:Array.from(s.options).map(o=>({text:o.text,value:o.value}))})),
rankingRows:Array.from(document.querySelectorAll('.nil-player-row')).map(r=>({rank:r.querySelector('.nil-row-rank')?.innerText,name:r.querySelector('.nil-row-name')?.innerText,position:r.querySelector('.nil-player-meta em')?.innerText,college:r.querySelector('.nil-player-meta b')?.innerText,conference:r.querySelector('.nil-row-conf')?.innerText,grade:r.querySelector('.nil-player-class')?.innerText,value:r.querySelector('.nil-row-value')?.innerText,profile_url:r.querySelector('a.nil-player-id')?.href,source_label:r.querySelector('.nil-player-src')?.innerText})),
playerLinks:Array.from(document.querySelectorAll('a[href*="/players/"]')).map(a=>({text:a.innerText,href:a.href}))})""".replace('\n','')


def blocked(snapshot):
    text=(snapshot.get('title','')+' '+snapshot.get('text','')[:4000]).lower()
    return any(t in text for t in ['sorry, you have been blocked','verify you are human','checking your browser',
        'just a moment','attention required','enable javascript and cookies to continue','captcha'])


def run(args):
    out=args.output_dir;out.mkdir(parents=True,exist_ok=True)
    window=args.window_id
    if window is None:
        window=new_window()
        print('Safari window ID:',window,flush=True)
    status=dict(window_id=window,requested_url=URL,generated_at=datetime.now(timezone.utc).isoformat(),
                status='started',snapshots=[])
    status_path=out/'safari_collection_status.json'
    def save():status_path.write_text(json.dumps(status,indent=2)+'\n')
    save()
    try:
        last_rows=-1
        for i in range(args.max_pages):
            # Short readiness polling; no browser fingerprint or security changes.
            snapshot=None
            for _ in range(30):
                raw=evaluate(window,SNAPSHOT)
                if raw and raw!='missing value':
                    candidate=json.loads(raw)
                    if candidate.get('url')!='about:blank' and candidate.get('text','').strip():
                        snapshot=candidate;break
                time.sleep(1)
            if snapshot is None:raise ValueError('Safari page did not become readable within the readiness window')
            path=out/f'sideline_safari_page_{i:03d}.json';path.write_text(json.dumps(snapshot,indent=2)+'\n')
            status['snapshots'].append(dict(path=path.name,sha256=hashlib.sha256(path.read_bytes()).hexdigest(),url=snapshot['url']))
            if blocked(snapshot):
                status.update(status='needs_user_browser_verification',note='Safari shows an access/verification page. Collector paused without interacting with it.');save();return status
            if 'thesideline.co' not in snapshot.get('url',''):raise ValueError('Safari left the requested site; collector paused')
            count=len(snapshot.get('rankingRows',[]));status['visible_player_link_count']=len(snapshot['playerLinks']);status['ranking_rows']=count
            print(f'Page {i+1}: {count} public player links',flush=True)
            if args.inspect_only:status['status']='inspection_saved';save();return status
            controls=[b for b in snapshot['buttons'] if 'load' in b['text'].lower() and 'more' in b['text'].lower() and not b['disabled']]
            if not controls:status['status']='public_controls_exhausted';save();return status
            if count<=last_rows:status['status']='no_new_rows_after_public_control';save();return status
            last_rows=count
            # Only the visible "Load ... more" control, never hidden API calls.
            text=controls[0]['text']
            click='(()=>{const b=Array.from(document.querySelectorAll("button")).find(b=>b.innerText==='+json.dumps(text)+');if(!b||b.disabled)return "unavailable";b.click();return "clicked"})()'
            if evaluate(window,click)!='clicked':raise ValueError('Public load-more control unavailable')
            time.sleep(args.delay)
        status['status']='page_cap_reached';save();return status
    except (RuntimeError,ValueError,json.JSONDecodeError,subprocess.TimeoutExpired) as exc:
        status.update(status='paused',error=str(exc));save();return status


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--window-id',type=int);p.add_argument('--inspect-only',action='store_true')
    p.add_argument('--max-pages',type=int,default=120);p.add_argument('--delay',type=float,default=2)
    p.add_argument('--output-dir',type=Path,default=ROOT/'Data/private/basketball_instagram_100/safari')
    a=p.parse_args()
    if a.max_pages<1 or a.delay<1:p.error('Use a positive page cap and a delay of at least one second')
    result=run(a);print(json.dumps({k:v for k,v in result.items() if k!='snapshots'},indent=2));sys.exit(0 if result['status'] in ['inspection_saved','public_controls_exhausted'] else 2)
