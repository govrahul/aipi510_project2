"""Fetch one explicitly public URL; preserve HTTP bytes/headers/provenance.

Uses system curl's certificate validation. Does not authenticate, retry denials,
solve challenges, guess private endpoints, or make paid requests. Caller must
provide a URL discovered from the public source. HTTP 4xx/5xx are recorded,
not treated as data. No automatic pagination because none is documented yet.
"""
import hashlib,json,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parent
RAW=ROOT/'raw'; RAW.mkdir(exist_ok=True)
def fetch(url,label):
    if not label.replace('-','').replace('_','').isalnum():
        raise ValueError('Use an alphanumeric label with hyphens/underscores.')
    started=datetime.now(timezone.utc).isoformat()
    body=RAW/(label+'.bin'); headers=RAW/(label+'.headers.txt')
    cmd=['curl','--silent','--show-error','--location','--max-time','45',
         '--dump-header',str(headers),'--output',str(body),
         '--write-out','%{http_code}\n%{url_effective}\n',url]
    p=subprocess.run(cmd,capture_output=True,text=True)
    status=p.stdout.splitlines()
    rec={'url':url,'final_url':status[1] if len(status)>1 else None,
         'retrieved_at_utc':started,'completed_at_utc':datetime.now(timezone.utc).isoformat(),
         'status_code':int(status[0]) if status and status[0].isdigit() else None,
         'curl_exit_code':p.returncode,'curl_stderr':p.stderr.strip(),
         'path':str(body.relative_to(ROOT)),'headers_path':str(headers.relative_to(ROOT)),
         'bytes':body.stat().st_size if body.exists() else None,
         'sha256':hashlib.sha256(body.read_bytes()).hexdigest() if body.exists() else None}
    with (ROOT/'provenance.jsonl').open('a') as f:
        f.write(json.dumps(rec,sort_keys=True)+'\n')
    print(json.dumps(rec))
    if p.returncode or not rec['status_code'] or rec['status_code']>=400:
        sys.exit(1)
if __name__=='__main__': fetch(sys.argv[1],sys.argv[2])
