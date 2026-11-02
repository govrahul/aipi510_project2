"""Summarize frozen-sample coverage without pooling incompatible count sources."""
import argparse
import hashlib
import json
from pathlib import Path

import pandas as pd


def run(sample_dir, output_dir):
    frozen_path=sample_dir/'basketball_sideline_sample_100_frozen.csv'
    frozen=pd.read_csv(frozen_path)
    data=pd.read_csv(sample_dir/'basketball_instagram_observations_100.csv')
    sampling=json.loads((sample_dir/'sampling_audit.json').read_text())
    digest=hashlib.sha256(frozen_path.read_bytes()).hexdigest()
    if digest!=sampling['frozen_sample_sha256']:raise ValueError('Frozen sample hash changed')
    if data.athlete_id.tolist()!=frozen.athlete_id.tolist() or data.Quartile.tolist()!=frozen.Quartile.tolist():
        raise ValueError('Collection changed the sample or ordering')
    if len(frozen)!=100 or not frozen.Quartile.value_counts().eq(25).all():
        raise ValueError('Expected the frozen 100-player balanced design')
    recorded=data.Instagram_Followers.notna()|data.Instagram_Followers_Approx.notna()
    manual=data.Instagram_Count_Status.eq('user_reported_count')
    direct=recorded & ~manual
    provider=data.Opendorse_Instagram_Reach.notna()
    coverage=[]
    for quartile,group in data.groupby('Quartile',sort=True):
        ix=group.index
        coverage.append(dict(Quartile=quartile,selected=len(group),
            sourced_handles=int(group.Instagram_Username.notna().sum()),
            followers_recorded=int(recorded.loc[ix].sum()),
            user_reported=int(manual.loc[ix].sum()),
            direct_display_integer=int((group.Instagram_Followers.notna() & ~manual.loc[ix]).sum()),
            direct_rounded=int(group.Instagram_Followers_Approx.notna().sum()),
            provider_reported_integer_unknown_date=int(provider.loc[ix].sum()),
            any_source_count=int((recorded|provider).loc[ix].sum()),
            missing_follower_count=int((~recorded).loc[ix].sum()),
            missing_direct_count=int((~direct).loc[ix].sum())))
    report=dict(sampling=sampling,coverage_by_quartile=coverage,
        selected=100,sourced_handles=int(data.Instagram_Username.notna().sum()),
        follower_counts_complete=bool(recorded.all()),
        followers_recorded=int(recorded.sum()),user_reported=int(manual.sum()),
        direct_display_integer=int((data.Instagram_Followers.notna() & ~manual).sum()),
        direct_rounded=int(data.Instagram_Followers_Approx.notna().sum()),
        provider_reported_integer_unknown_date=int(provider.sum()),
        any_source_count=int((recorded|provider).sum()),missing_follower_count=int((~recorded).sum()),
        missing_direct_count=int((~direct).sum()),
        frozen_sample_sha256=digest,
        observations_sha256=hashlib.sha256((sample_dir/'basketball_instagram_observations_100.csv').read_bytes()).hexdigest(),
        analysis_ready=False,
        limitations=[
            'Missing source details remain unknown; reported counts do not establish an account handle or observation time.',
            'Rounded direct labels and provider-reported reach are separate fields; provider measurement dates are unknown.',
            'User-reported counts are labeled separately; account handles, observation times and display precision were not supplied.',
            'Observed counts are not historical pre-NIL measurements.',
            'Current Sideline listing retrieved November 2, 2026 is not established as a 2025-26 cohort.',
            'Source estimates are not verified payments, scholarship decisions, or an independent athletic evaluation.',
            'Original selection is unchanged; no replacements were used. Count completeness does not establish validity of the pre/post research design.'
        ])
    receipt_audit=sample_dir/'basketball_instagram_observations_100.audit.json'
    if receipt_audit.exists():
        provenance=json.loads(receipt_audit.read_text())
        if 'manual_input_sha256' in provenance:
            if provenance['output_sha256']!=report['observations_sha256']:raise ValueError('Manual import hash does not match main sheet')
            report['manual_completion_import']=provenance
            browser_audit=sample_dir/'basketball_instagram_browser_100.audit.json'
            if browser_audit.exists():
                browser=json.loads(browser_audit.read_text())
                if browser['output_sha256']!=provenance['source_input_sha256']:raise ValueError('Browser/manual provenance chain disagrees')
                report['browser_receipt_import']=browser
        elif 'receipts_sha256' in provenance:
            if provenance['output_sha256']!=report['observations_sha256']:raise ValueError('Browser import hash does not match main sheet')
            report['browser_receipt_import']=provenance
    output_dir.mkdir(parents=True,exist_ok=True)
    (output_dir/'collection_audit.json').write_text(json.dumps(report,indent=2)+'\n')
    table=pd.DataFrame(coverage);table.to_csv(output_dir/'coverage_by_quartile.csv',index=False)
    # Local task queue contains no inferred observations; reviewers must supply evidence.
    queue=data.loc[~recorded,['Sample_Row','athlete_id','Player Name','College','Quartile',
        'Instagram_Username','Username_Verification_URL','Instagram_Collection_Note']].copy()
    queue['Instagram_Profile_URL']=queue.Instagram_Username.map(lambda x:f'https://www.instagram.com/{x}/' if pd.notna(x) else None)
    for col in ['Reviewer','Observed_At_UTC','Raw_Follower_Label','Evidence_File','Review_Notes']:queue[col]=None
    review_file=sample_dir/'unresolved_account_reviews.csv'
    if review_file.exists():
        reviews=pd.read_csv(review_file)
        if reviews.athlete_id.duplicated().any():raise ValueError('Duplicate unresolved-account reviews')
        queue=queue.merge(reviews[['athlete_id','Review_Status','Review_Note']],on='athlete_id',how='left',validate='one_to_one',sort=False)
    queue.to_csv(sample_dir/'manual_followup_queue.csv',index=False)
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--sample-dir',type=Path,required=True);p.add_argument('--output-dir',type=Path,required=True)
    a=p.parse_args();print(json.dumps(run(a.sample_dir,a.output_dir),indent=2))
