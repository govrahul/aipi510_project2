"""Run frozen PDF-only sampler, then compare against partner inputs post-lock.

This uses the partner's existing frame because independent complete collection
failed. It is a post-lock same-frame algorithm test, NOT independent collection.
The frozen agent never receives partner rows/code or comparison results.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

import numpy as np
import pandas as pd
from prepare_sample import parse_valuation
from collect_performance import normalize

ROOT=Path(__file__).resolve().parents[1]
PACKAGE=ROOT/'replication/blind_pdf_protocol'


def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()

def key(frame):
    return frame['Player Name'].map(normalize)+'|'+frame.College.map(normalize)


def rank_band(rank):
    return pd.Series(np.select([rank.le(250),rank.le(750)],['top','middle'],default='bottom'),index=rank.index)


def describe(values):
    return dict(n=len(values),minimum=float(values.min()),median=float(values.median()),
                mean=float(values.mean()),maximum=float(values.max()))


def run(args):
    lock=json.loads((PACKAGE/'deliverable_lock.json').read_text())
    for name in ['protocol_locked.md','sample_football.py','collect_public.py']:
        if digest(PACKAGE/name)!=lock['files'][name]:
            raise ValueError('Frozen independent package hash mismatch')
    before={str(path.relative_to(ROOT)):digest(path) for path in [args.frame,args.partner_sample,ROOT/'Data/sample_data.py']}
    frame=pd.read_csv(args.frame)
    partner=pd.read_csv(args.partner_sample)
    if len(frame)!=1000 or len(partner)!=100 or key(frame).duplicated().any() or key(partner).duplicated().any():
        raise ValueError('Expected unique 1000-player frame and 100-player partner sample')
    args.outdir.mkdir(parents=True,exist_ok=True)
    adapted=frame.copy()
    adapted['nil_value']=adapted.Valuation.map(parse_valuation)
    adapted['source_rank']=adapted.Rank
    input_path=args.outdir/'postlock_shared_frame.csv'
    adapted.to_csv(input_path,index=False)
    output=args.outdir/'postlock_independent_sampler_100.csv'
    result=subprocess.run([sys.executable,str(PACKAGE/'sample_football.py'),str(input_path),str(output),
        '--name-column','Player Name','--school-column','College','--class-column','Grade'],
        check=True,capture_output=True,text=True)
    independent=pd.read_csv(output)
    frame['__key']=key(frame);partner['__key']=key(partner);independent['__key']=key(independent)
    rank_lookup=frame.set_index('__key').Rank
    partner['__rank']=partner['__key'].map(rank_lookup)
    if partner['__rank'].isna().any(): raise ValueError('Partner sample has rows outside shared frame')
    overlap=set(partner['__key'])&set(independent['__key'])
    values=adapted.nil_value
    p25,p75=np.percentile(values,[25,75])
    value_tiers=pd.Series(np.select([values.ge(p75),values.le(p25)],['Top_25','Bottom_25'],default='Middle_50'))
    tier_counts=value_tiers.value_counts().to_dict()
    # Additional check ONLY AFTER lock/comparison: replay partner's original code
    # in a temporary working directory so it cannot overwrite inherited CSVs.
    with tempfile.TemporaryDirectory(prefix='aipi510-unblinded-replay-') as temporary:
        folder=Path(temporary);(folder/'Data').mkdir()
        shutil.copy2(args.frame,folder/'Data/football_top1000.csv')
        subprocess.run([sys.executable,str(ROOT/'Data/sample_data.py')],cwd=folder,check=True,capture_output=True,text=True)
        replay=pd.read_csv(folder/'Data/football_sample_100.csv')
    exact_saved_order=key(replay).tolist()==key(partner).tolist()
    for path in [args.frame,args.partner_sample,ROOT/'Data/sample_data.py']:
        if digest(path)!=before[str(path.relative_to(ROOT))]: raise ValueError('Original input changed')
    report=dict(comparison_type='post-lock_same-frame_algorithm_test_not_independent_collection',
        comparison_at_utc=datetime.now(timezone.utc).isoformat(),protocol_lock_time=lock['frozen_at_utc'],
        independent_protocol_sha256=lock['files']['protocol_locked.md'],independent_sampler_sha256=lock['files']['sample_football.py'],
        independent_agent_saw_partner_rows=False,independent_complete_frame_collected=False,
        input_hashes=before,frame_rows=1000,partner_sample_rows=100,independent_sample_rows=len(independent),
        independent_rank_stratum_populations=dict(top=250,middle=500,bottom=250),
        partner_value_stratum_populations=tier_counts,
        partner_cutoffs_USD=dict(p25=float(p25),p75=float(p75)),
        independent_rank_stratum_draws=independent.rep_stratum.value_counts().to_dict(),
        partner_saved_label_draws=partner.Valuation_Tier.value_counts().to_dict(),
        partner_draws_reexpressed_as_rank_bands=rank_band(partner.__rank).value_counts().to_dict(),
        partner_nominal_tier_inclusion_probability={tier:dict(Top_25=25,Middle_50=50,Bottom_25=25)[tier]/n for tier,n in tier_counts.items()},
        independent_nominal_rank_band_inclusion_probability=dict(top=.1,middle=.1,bottom=.1),
        common_players=len(overlap),overlap_fraction_of_100=len(overlap)/100,jaccard=len(overlap)/(200-len(overlap)),
        NIL_summary=dict(frame=describe(values),partner=describe(partner.Valuation.map(parse_valuation)),
                         independent=describe(independent.nil_value)),
        position_counts=dict(partner=partner.Position.value_counts().to_dict(),independent=independent.Position.value_counts().to_dict()),
        unblinded_original_code_replay=dict(original_seed=510,same_saved_player_set=set(key(replay))==set(key(partner)),
            same_saved_player_order=exact_saved_order,description='Post-unblinding diagnostic, not the blind reconstruction'),
        limitations=['Independent agent saw PDF aggregate model results but no partner rows or implementations.',
            'Root already had prior project knowledge; implementation isolation belongs to the fresh agent only.',
            'PDF does not specify seed, tie rule, software or collection date; seed/hash choices were independently fixed before input access.',
            'Fresh full source collection blocked by HTTP403; shared partner frame used only after protocol/code lock.',
            'Different random methods/tie rules naturally change sampled names; low overlap is not evidence of error.',
            'Top-1000 frame omits all lower-valued athletes; matching quotas cannot repair coverage bias.',
            'This replicates the legacy current-NIL sample, not historical HS-star sampling or the regression.'])
    args.report.write_text(json.dumps(report,indent=2)+'\n')
    probability_display={tier:f'{probability:.2%}' for tier,probability in report['partner_nominal_tier_inclusion_probability'].items()}
    args.report.with_suffix('.md').write_text(f'''# Football sampling comparison\n\nFrozen PDF-only protocol: `{report['independent_protocol_sha256']}`. Independent code was frozen at {report['protocol_lock_time']} before any partner input was supplied. The isolated agent did not see partner player rows or code. The root agent had previous project knowledge, so this is operational separation, not a claim of strict preregistration.\n\nFresh source collection returned HTTP403. Therefore the real-data test is **post-lock sampling on the same partner frame**, not an independent collection replication. The contemporary source snapshot would also differ from the unspecified partner collection date.\n\nBoth samplers select 100 players with stated 25/50/25 quotas. The independent implementation uses rank groups 250/500/250 and its separately chosen seed 20261101 with SHA-256 priorities. The partner code uses dollar-value percentile cutoffs and seed 510; ties produce populations {tier_counts}. Independent nominal inclusion is 10% per rank group; partner tier probabilities are {probability_display}.\n\nThe draws share **{len(overlap)} of 100 players** (Jaccard {report['jaccard']:.3f}). Different randomization and boundary rules make different names expected; this is not a failure to reproduce the stated method. After unblinding, replaying the original code reproduced the saved player set: **{report['unblinded_original_code_replay']['same_saved_player_set']}**; exact saved order: **{exact_saved_order}**. Original files were not modified.\n\nThe PDF supports the quota allocation but does not specify the seed or tie convention needed for exact individual reproduction. Its 25/50/25 proportional rank allocation would give equal 10% inclusion under random within-stratum sampling, not extra sampling weight to the highest quarter. The top-1000 restriction still limits population coverage. No regression result was compared or claimed.\n''')
    print(json.dumps({k:report[k] for k in ['comparison_type','common_players','partner_value_stratum_populations','unblinded_original_code_replay']},indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--frame',type=Path,default=ROOT/'Data/football_top1000.csv')
    p.add_argument('--partner-sample',type=Path,default=ROOT/'Data/football_sample_100.csv')
    p.add_argument('--outdir',type=Path,default=ROOT/'Data/private/replication')
    p.add_argument('--report',type=Path,default=ROOT/'reports/blind_football_sampling_comparison.json')
    run(p.parse_args())
