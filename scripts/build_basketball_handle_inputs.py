"""Attach reviewed account evidence to a frozen NIL sample, without redrawing.

Accept athlete-specific links from a named men's-basketball roster or public
On3 basketball profile, plus identity-checked Opendorse rows and an optional
reviewed source CSV. Team navigation/footer links are never accepted. Conflicting
handles are retained for review instead of selecting the easiest account.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
from urllib.parse import urlparse

from bs4 import BeautifulSoup
import pandas as pd
from collect_opendorse_instagram import normalize


def accepted_profile_links(evidence,record,raw_dir):
    title=evidence.get('title','');name=record['Player Name']
    if normalize(name) not in normalize(title):return []
    url=evidence['url'];host=urlparse(url).hostname
    basketball=('basketball' in title.lower() and 'women' not in title.lower())
    if host in ['on3.com','www.on3.com']:
        path=raw_dir/(hashlib.sha256(url.encode()).hexdigest()[:20]+'.html')
        try:
            soup=BeautifulSoup(path.read_bytes(),'html.parser');tag=soup.find('script',id='__NEXT_DATA__')
            player=json.loads(tag.get_text())['props']['pageProps']['player']
            basketball=player.get('defaultSport',{}).get('name')=='Basketball' and normalize(player.get('name'))==normalize(name)
        except (OSError,KeyError,AttributeError,TypeError,ValueError):return []
    if not basketball:return []
    out=[]
    for c in evidence['Instagram_Link_Candidates']:
        classes=' '.join(c['parent_class']).lower()
        athlete_specific=('rosterbio__player__socialicons' in classes or
            'contacts-module' in classes or 'sidearm-roster-player-social' in classes or
            ('social-item' in classes and 'for ' not in c['context'].lower()))
        if athlete_specific:
            out.append(dict(username=c['username'],url=url,status='public_named_basketball_profile_link',note='Source profile identifies the athlete; school may be an earlier affiliation'))
    return out


def run(args):
    frozen=pd.read_csv(args.sample,dtype={'athlete_id':'string'});d=frozen.copy()
    op=pd.read_csv(args.opendorse,dtype={'athlete_id':'string'}) if args.opendorse else pd.DataFrame()
    evidences=json.loads(args.evidence.read_text()) if args.evidence else []
    reviewed=pd.read_csv(args.reviewed) if args.reviewed else pd.DataFrame()
    if not reviewed.empty:
        if 'athlete_id' not in reviewed:raise ValueError('Reviewed sources need frozen athlete_id, not row number alone')
        if reviewed.athlete_id.duplicated().any():raise ValueError('Duplicate reviewed athlete IDs')
        if not set(reviewed.athlete_id).issubset(set(frozen.athlete_id)):raise ValueError('Reviewed sources do not match this frozen sample')
    rows=[];issues=[]
    for record in frozen.to_dict('records'):
        options=[];oprow=op.loc[op.athlete_id.eq(record['athlete_id'])] if not op.empty else pd.DataFrame()
        if len(oprow)==1:
            o=oprow.iloc[0]
            if pd.notna(o.get('Instagram_Username')) and pd.notna(o.get('Instagram_Identity_Status')):
                options.append(dict(username=o.Instagram_Username,url=o.Username_Verification_URL,status=o.Instagram_Identity_Status,note='Opendorse name/sport/school identity check'))
            record['Opendorse_Instagram_Reach']=o.get('Instagram_Followers')
            record['Opendorse_Retrieved_At']=o.get('Instagram_Observed_At')
            record['Opendorse_Source_URL']=o.get('Instagram_Source_URL')
            record['Opendorse_Reach_AsOf']=None
        for evidence in evidences:
            if (evidence['Sample_Row']==record['Sample_Row'] and
                normalize(evidence.get('Player Name'))==normalize(record['Player Name']) and
                normalize(evidence.get('College'))==normalize(record['College'])):
                options.extend(accepted_profile_links(evidence,record,args.evidence.parent/'profile_evidence_raw'))
        custom=reviewed.loc[reviewed.athlete_id.eq(record['athlete_id'])] if not reviewed.empty else pd.DataFrame()
        if not custom.empty:
            # Explicit reviewed evidence can resolve a conflict; preserve its stated basis.
            options=[dict(username=r['Instagram_Username'],url=r['Username_Verification_URL'],status='reviewed_public_source',note=r['Review_Note']) for r in custom.to_dict('records')]
        unique={str(o['username']).lower():o for o in options}
        record.update(Instagram_Username=None,Username_Verification_URL=None,Instagram_Followers=None,Instagram_Followers_Approx=None,
                      Instagram_Count_Status='not_collected',Instagram_Handle_Identity_Status='no_verified_handle')
        if len(unique)==1:
            o=next(iter(unique.values()));record.update(Instagram_Username=o['username'],Username_Verification_URL=o['url'],
                Instagram_Handle_Identity_Status=o['status'],Instagram_Handle_Identity_Note=o['note'])
        elif len(unique)>1:
            record['Instagram_Handle_Identity_Status']='conflicting_handle_sources_needs_review'
            issues.append(dict(Sample_Row=record['Sample_Row'],options=options))
        rows.append(record)
    result=pd.DataFrame(rows)
    assert result.athlete_id.tolist()==frozen.athlete_id.tolist()
    assert result.Quartile.tolist()==frozen.Quartile.tolist()
    result.to_csv(args.output,index=False)
    audit=dict(rows=len(result),verified_handles=int(result.Instagram_Username.notna().sum()),
       identity_status=result.Instagram_Handle_Identity_Status.value_counts().to_dict(),conflicts=issues,
       frozen_sample_sha256=hashlib.sha256(args.sample.read_bytes()).hexdigest(),
       no_replacement=True,opendorse_count_note='Supplementary provider integer; measurement date unknown, not substituted for a new Instagram snapshot')
    args.output.with_suffix('.audit.json').write_text(json.dumps(audit,indent=2)+'\n');return audit


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--sample',type=Path,required=True);p.add_argument('--opendorse',type=Path)
    p.add_argument('--evidence',type=Path);p.add_argument('--reviewed',type=Path);p.add_argument('--output',type=Path,required=True)
    print(json.dumps(run(p.parse_args()),indent=2))
