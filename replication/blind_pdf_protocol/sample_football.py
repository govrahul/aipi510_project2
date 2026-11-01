#!/usr/bin/env python3
"""Independent PDF-only football sampler. Standard library; no network access.

Input CSV columns default to source_id, nil_value, and optional source_rank.
At least 1,000 unique complete records are required. source_rank is the
sport-specific descending NIL order (1 is highest); it must be unambiguous.
If no rank column is available, sort numeric NIL descending then identifier.
All extra input columns are preserved. No downstream completeness filters.
"""
import argparse,csv,hashlib,json,sys,unicodedata
from datetime import datetime,timezone
from decimal import Decimal,InvalidOperation
from pathlib import Path
SEED='20261101'
PREFIX='aipi510-blind-football-v1'
QUOTAS=(('top',0,250,25),('middle',250,750,50),('bottom',750,1000,25))

def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def norm(value):
    text=unicodedata.normalize('NFKD',value).casefold()
    return ' '.join(''.join(c if c.isalnum() else ' ' for c in text if not unicodedata.combining(c)).split())
def numeric(value):
    try: result=Decimal(str(value).strip())
    except InvalidOperation as e: raise ValueError(f'Nonnumeric NIL value: {value!r}') from e
    if not result.is_finite() or result<0: raise ValueError(f'Invalid NIL value: {value!r}')
    return result

def prepare(rows,fieldnames,id_column='source_id',nil_column='nil_value',rank_column='source_rank',name_column='name',school_column='school',class_column='class'):
    if nil_column not in fieldnames: raise ValueError(f'Missing NIL column {nil_column!r}')
    has_id=id_column in fieldnames
    if not has_id and not all(c in fieldnames for c in (name_column,school_column,class_column)):
        raise ValueError('Need a source ID, or all name/school/class fields for fallback ID.')
    has_rank=bool(rank_column and rank_column in fieldnames)
    unique={}; duplicates=0
    for row in rows:
        source_id=row[id_column].strip() if has_id else '|'.join(norm(row[c]) for c in (name_column,school_column,class_column))
        if not source_id or (not has_id and not norm(row[name_column])): raise ValueError('Empty source identifier/name')
        value=numeric(row[nil_column])
        rank=None
        if has_rank:
            try:
                rank=int(row[rank_column])
                if str(rank)!=str(row[rank_column]).strip() or rank<=0: raise ValueError()
            except (ValueError,TypeError) as e: raise ValueError('Ranks must be positive integers.') from e
        if source_id in unique:
            if unique[source_id]['row'] != row: raise ValueError(f'Conflicting duplicate identifier: {source_id!r}')
            duplicates+=1; continue
        unique[source_id]={'id':source_id,'value':value,'source_rank':rank,'row':row}
    records=list(unique.values())
    if len(records)<1000: raise ValueError(f'Incomplete frame: {len(records)} unique records, need at least 1000.')
    if has_rank:
        if len({r['source_rank'] for r in records})!=len(records):
            raise ValueError('Tied source ranks are ambiguous; provide unique stable source order.')
        records.sort(key=lambda r:r['source_rank'])
        if [r['source_rank'] for r in records[:1000]]!=list(range(1,1001)):
            raise ValueError('Source ranks 1-1000 must all be present exactly once.')
        if any(a['value']<b['value'] for a,b in zip(records,records[1:])):
            raise ValueError('Source rank is not descending numeric NIL order.')
        ordering='source_rank ascending; unique ranks 1-1000 required'
    else:
        records.sort(key=lambda r:(-r['value'],r['id']))
        ordering='numeric NIL descending; stable identifier ascending'
    frame=records[:1000]
    for rank,r in enumerate(frame,1): r['frame_rank']=rank
    return frame,{'ordering':ordering,'input_unique_count':len(records),'exact_duplicates_removed':duplicates,
                  'excluded_below_rank_1000':len(records)-1000,'nil_at_rank_1000':str(frame[-1]['value']),
                  'ties_at_cutoff_in_supplied_input':sum(r['value']==frame[-1]['value'] for r in records)}

def select(frame):
    selected=[]
    for label,start,end,n in QUOTAS:
        for r in frame[start:end]:
            r['stratum']=label
            r['sample_hash']=hashlib.sha256(f'{PREFIX}|{SEED}|{label}|{r["id"]}'.encode('utf-8')).hexdigest()
        selected.extend(sorted(frame[start:end],key=lambda r:(r['sample_hash'],r['id']))[:n])
    return sorted(selected,key=lambda r:r['frame_rank'])

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('input_csv',type=Path); p.add_argument('output_csv',type=Path)
    for arg,default in [('id','source_id'),('nil','nil_value'),('rank','source_rank'),('name','name'),('school','school'),('class','class')]:
        p.add_argument('--'+arg+'-column',default=default)
    args=p.parse_args()
    if args.input_csv.resolve()==args.output_csv.resolve(): raise ValueError('Output cannot overwrite input.')
    with args.input_csv.open(newline='',encoding='utf-8-sig') as f:
        reader=csv.DictReader(f); fields=reader.fieldnames or []; rows=list(reader)
    reserved=['rep_source_id','rep_frame_rank','rep_stratum','rep_sample_hash']
    if any(x in fields for x in reserved): raise ValueError('Input contains reserved rep_ output columns.')
    frame,details=prepare(rows,fields,**{x+'_column':getattr(args,x+'_column') for x in ('id','nil','rank','name','school','class')})
    chosen=select(frame)
    with args.output_csv.open('w',newline='',encoding='utf-8') as f:
        writer=csv.DictWriter(f,fieldnames=fields+reserved); writer.writeheader()
        for r in chosen:
            writer.writerow({**r['row'],'rep_source_id':r['id'],'rep_frame_rank':r['frame_rank'],'rep_stratum':r['stratum'],'rep_sample_hash':r['sample_hash']})
    protocol=Path(__file__).with_name('protocol_locked.md')
    manifest={'created_at_utc':datetime.now(timezone.utc).isoformat(),'algorithm':PREFIX,'seed':SEED,
              'input_path':str(args.input_csv.resolve()),'input_sha256':sha(args.input_csv),
              'output_path':str(args.output_csv.resolve()),'output_sha256':sha(args.output_csv),
              'sampler_sha256':sha(__file__),'protocol_sha256':sha(protocol),
              'frame_size':len(frame),'sample_size':len(chosen),'quota_counts':{s:sum(r['stratum']==s for r in chosen) for s,*_ in QUOTAS},
              'column_mapping':{x:getattr(args,x+'_column') for x in ('id','nil','rank','name','school','class')},**details,
              'limitation':'This is an independent deterministic implementation of an underspecified PDF protocol. A contemporary frame is not a same-date historical replication. A partner frame supplied after lock is a post-lock same-frame algorithm test, not independent frame collection.'}
    manifest_path=args.output_csv.with_suffix(args.output_csv.suffix+'.manifest.json')
    manifest_path.write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'output':str(args.output_csv),'manifest':str(manifest_path),'counts':manifest['quota_counts'],'output_sha256':manifest['output_sha256']}))
if __name__=='__main__':
    try: main()
    except (ValueError,OSError) as e: sys.exit(str(e))
