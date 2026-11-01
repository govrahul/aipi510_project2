"""Reproducible EDA of canonical project layers; no network or input mutations.

Do not concatenate the inherited frame/sample/model as independent observations,
or count superseded production samples as additional data. No-match career
outcomes stay unknown. This is exploratory, not a pre/post or causal NIL test.
"""
import argparse
import base64
from datetime import datetime, timezone
import hashlib
import html
import json
import os
from pathlib import Path
import platform

os.environ.setdefault('MPLCONFIGDIR','/tmp/nil-eda-matplotlib')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter, NullFormatter
import numpy as np
import pandas as pd
from scipy.stats import pearsonr, spearmanr
import statsmodels
import statsmodels.formula.api as smf
from statsmodels.stats.diagnostic import het_breuschpagan
from collect_performance import normalize
from prepare_sample import parse_valuation
from enrich_player_evaluations import identifier

ROOT=Path(__file__).resolve().parents[1]
NAVY='#203c55'; TEAL='#147d80'; ORANGE='#d18739'; RED='#ae4c4c'
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,
    'axes.spines.right':False,'axes.titleweight':'bold','axes.labelcolor':NAVY,
    'text.color':NAVY,'axes.edgecolor':'#9aabb6','savefig.facecolor':'white'})


def truth(series):
    return series.astype('string').str.lower().isin(['true','1','1.0']).fillna(False)


def numeric(series): return pd.to_numeric(series,errors='raise')


def observed(series):
    if pd.api.types.is_numeric_dtype(series):
        return series.notna() & np.isfinite(series)
    return series.notna() & series.astype('string').str.strip().ne('').fillna(False)


def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def markdown(frame):
    def cell(value):
        if pd.isna(value): return '—'
        if isinstance(value,(float,np.floating)): return f'{value:,.3f}'
        return str(value).replace('|','/').replace('\n',' ')
    return '\n'.join(['| '+' | '.join(map(str,frame.columns))+' |',
        '| '+' | '.join(['---']*len(frame.columns))+' |']+
        ['| '+' | '.join(cell(x) for x in row)+' |' for row in frame.itertuples(index=False,name=None)])


def summarize_numeric(series):
    x=numeric(series).replace([np.inf,-np.inf],np.nan).dropna()
    if x.empty: return dict(n=0)
    return dict(n=len(x),mean=float(x.mean()),std=float(x.std()),minimum=float(x.min()),
        q25=float(x.quantile(.25)),median=float(x.median()),q75=float(x.quantile(.75)),
        p95=float(x.quantile(.95)),maximum=float(x.max()),zeros=int(x.eq(0).sum()))


def field_role(column):
    if column in ['athlete_id','team_id','Player_Name','Player Name','College']: return 'identity_or_membership'
    if column.startswith(('Draft_','NFL_','Overseas_')) or column in ['College_Years_Total','Observed_College_Seasons_Through_AsOf']:
        return 'career_followup_not_baseline_predictor'
    if column.startswith('Recruit_') or column=='Star Rating': return 'recruiting_covariate_needs_timing_and_identity_review'
    if column.startswith(('Source','Membership','Career_As','ESPN_Profile','Stats_Availability')): return 'provenance_or_status'
    if 'Valuation' in column or column=='raw_val': return 'valuation_or_selection_variable'
    if 'Instagram' in column: return 'social_predictor_missing_observation_time'
    return 'source_metadata_or_measure_review_dictionary'


def position_group(position):
    p=str(position).upper()
    if p=='QB': return 'Quarterback'
    if p in ['WR','RB','FB','TE']: return 'Skill offense'
    if p in ['OL','OT','OG','C','OC','IOL']: return 'Offensive line'
    if p in ['DL','DT','DE','EDGE','LB','ILB','OLB','DB','CB','S','SS','FS','SAF']: return 'Defense'
    return 'Other'


def savefig(fig,path):
    fig.savefig(path,dpi=170,bbox_inches='tight')
    plt.close(fig)


def canonical_datasets():
    specs=[dict(key='football_NIL_model',label='Football NIL sample',sport='football',cohort=None,
        unit='athlete in inherited selected sample',path=ROOT/'Data/football_modeling_data.csv')]
    for sport,years in [('basketball',[2018,2019,2025]),('football',[2018,2019,2025,2026])]:
        for year in years:
            path=(ROOT/f'Data/private/evaluation/enriched/basketball_{year}_evaluation_frame.csv' if sport=='basketball'
                  else ROOT/f'Data/private/evaluation/football_nfl_ids/football_{year}_evaluation_with_NFL_IDs.csv')
            specs.append(dict(key=f'{sport}_{year}',label=f'{sport.title()} {year}',sport=sport,cohort=year,
                              unit='athlete-team-season source row',path=path))
    return specs


def collect_inventory(specs,load,out):
    inventory=[];dictionary=[];coverage=[];frames={};auxiliary=[]
    for spec in specs:
        frame=load(spec['path']);frames[spec['key']]=frame
        ids=frame.athlete_id.map(identifier) if 'athlete_id' in frame else frame['Player Name'].map(normalize)+'|'+frame.College.map(normalize)
        duplicate_keys=int(frame.duplicated(['athlete_id','team_id']).sum()) if 'team_id' in frame else int(ids.duplicated().sum())
        r=dict(dataset=spec['key'],sport=spec['sport'],cohort_start=spec['cohort'],unit=spec['unit'],rows=len(frame),
            unique_athletes=ids.nunique(),schools=frame.College.nunique(),columns=len(frame.columns),
            duplicate_identity_team_rows=duplicate_keys,multi_team_athletes=int(ids.value_counts().gt(1).sum()),
            source_sha256=digest(spec['path']))
        if 'season' in frame:
            expected=spec['cohort']+(spec['sport']=='basketball')
            r['unexpected_season_rows']=int(numeric(frame.season).ne(expected).sum())
        inventory.append(r)
        for col in frame:
            s=frame[col];present=observed(s)
            nonfinite=int(np.isinf(s.dropna().to_numpy(dtype=float)).sum()) if pd.api.types.is_numeric_dtype(s) else 0
            dictionary.append(dict(dataset=spec['key'],column=col,dtype=str(s.dtype),rows=len(frame),nonfinite=nonfinite,
                available=int(present.sum()),missing=int((~present).sum()),missing_fraction=float((~present).mean()),
                unique_nonmissing=s.nunique(dropna=True),role=field_role(col)))
        fields={
            'NIL valuation':('Valuation',None),
            'Instagram followers':('Instagram Followers',None),
            'Recruiting stars reported':('Star Rating' if spec['cohort'] is None else 'Recruit_Stars',None),
            'Verified HS recruiting':('Recruit_HS_Verified','true'),
            'Qualified basketball BPM':('College_BPM_Qualified','true'),
            'Draft link':('Draft_Round',None),
            'Completed college years':('College_Years_Total',None)}
        for field,(column,mode) in fields.items():
            n=int((truth(frame[column]) if mode=='true' else observed(frame[column])).sum()) if column in frame else 0
            coverage.append(dict(dataset=spec['key'],field=field,rows=len(frame),column_present=column in frame,
                                 available_or_verified=n,fraction=n/len(frame),
                                 note='source-record availability, not event probability or model validity'))
    pd.DataFrame(inventory).to_csv(out/'dataset_inventory.csv',index=False)
    pd.DataFrame(dictionary).to_csv(out/'field_dictionary_and_missingness.csv',index=False)
    pd.DataFrame(coverage).to_csv(out/'coverage.csv',index=False)
    return frames,pd.DataFrame(inventory),pd.DataFrame(coverage)


def coverage_plot(coverage,specs,path):
    fields=coverage.field.drop_duplicates().tolist()
    keys=[s['key'] for s in specs]
    data=coverage.pivot(index='dataset',columns='field',values='fraction').loc[keys,fields]
    fig,ax=plt.subplots(figsize=(12.7,5.2))
    ax.imshow(data.to_numpy(),vmin=0,vmax=1,cmap='YlGnBu',aspect='auto')
    ax.set_xticks(range(len(fields)),['NIL\nvaluation','Instagram\nfollowers','Reported\nstars','Verified HS\nratings','Qualified\nbasketball BPM','Draft\nlink','Completed\ncollege years'])
    ax.set_yticks(range(len(keys)),[s['label']+(' (2018–19)' if s['key']=='basketball_2018' else ' (2019–20)' if s['key']=='basketball_2019' else ' (2025–26)' if s['key']=='basketball_2025' else '') for s in specs])
    for i,key in enumerate(keys):
        for j,field in enumerate(fields):
            v=data.loc[key,field]
            text='n/a' if field=='Qualified basketball BPM' and not key.startswith('basketball') else f'{v:.0%}'
            ax.text(j,i,text,ha='center',va='center',color='white' if v>.55 else NAVY,fontsize=10)
    ax.tick_params(length=0,pad=8)
    ax.set_title('What is observed—and what can be verified?',loc='left',pad=15)
    fig.text(.015,.015,'0% means no observed/verified records, not zero followers, zero talent or no career success. Draft links remain subject to identity review.',fontsize=9)
    fig.tight_layout(rect=(0,.05,1,1));savefig(fig,path)


def football_eda(frame,topframe,out,private,figures):
    data=frame.copy()
    data['x']=np.log1p(numeric(data['Instagram Followers']))
    data['y']=np.log(numeric(data.Valuation))
    if not np.isfinite(data[['x','y']].to_numpy()).all(): raise ValueError('Nonfinite current football values')
    data['Stars_C']=numeric(data['Star Rating'])-numeric(data['Star Rating']).mean()
    data['Position_Group']=data.Position.map(position_group)
    biggest=data['Instagram Followers'].idxmax()
    metrics=dict(rows=len(data),schools=data.College.nunique(),power4=int(data.Power_4_Dummy.eq(1).sum()),
        PPA_zeros=int(data.PPA_Per_Play.eq(0).sum()),PPA_nonzero_defense_or_line=int((data.Position_Group.isin(['Defense','Offensive line'])&data.PPA_Per_Play.ne(0)).sum()),
        follower_summary=summarize_numeric(data['Instagram Followers']),valuation_summary=summarize_numeric(data.Valuation),
        largest_follower_share=float(data['Instagram Followers'].max()/data['Instagram Followers'].sum()),
        raw_pearson=float(pearsonr(data['Instagram Followers'],data.Valuation).statistic),
        log_pearson=float(pearsonr(data.x,data.y).statistic),spearman=float(spearmanr(data.x,data.y).statistic),
        raw_pearson_without_largest=float(pearsonr(data.drop(biggest)['Instagram Followers'],data.drop(biggest).Valuation).statistic),
        log_pearson_without_largest=float(pearsonr(data.drop(biggest).x,data.drop(biggest).y).statistic))
    top=topframe.Valuation.map(parse_valuation)
    metrics['frame_NIL_summary']=summarize_numeric(top)
    metrics['frame_unique_NIL_values']=int(top.nunique())
    metrics['model_unique_NIL_values']=int(data.Valuation.nunique())
    metrics['stars_counts']=data['Star Rating'].value_counts().to_dict()
    metrics['grade_counts']=data.Grade.value_counts().to_dict()
    metrics['position_groups']=data.Position_Group.value_counts().to_dict()
    pd.DataFrame([dict(variable=c,**summarize_numeric(data[c])) for c in ['Valuation','Instagram Followers','Star Rating','PPA_Per_Play']]).to_csv(out/'football_numeric_summary.csv',index=False)
    corr=data[['x','y','Star Rating','PPA_Per_Play']].corr(method='spearman')
    corr.to_csv(out/'football_spearman_correlations.csv')
    # Fixed exploratory comparisons, not a model-selection contest or p-value search.
    legacy='y ~ x + PPA_Per_Play + Freshman_Flag + Freshman_X_Stars + Power_4_Dummy + Premium_Position'
    main='y ~ x + Stars_C * Freshman_Flag + C(Position_Group)'
    fits=[('Inherited model; HC3',legacy,data,'HC3'),
          ('Main effects + position groups; HC3',main,data,'HC3'),
          ('Same model; remove largest audience',main,data.drop(biggest),'HC3'),
          ('Same model; school-clustered SE',main,data,'cluster')]
    rows=[];base=None
    for label,formula,subset,covariance in fits:
        ordinary=smf.ols(formula,subset,missing='raise').fit()
        if np.linalg.matrix_rank(ordinary.model.exog)!=ordinary.model.exog.shape[1]: raise ValueError('EDA design rank deficiency')
        fit=(ordinary.get_robustcov_results(cov_type='cluster',groups=subset.College,use_correction=True,use_t=True)
             if covariance=='cluster' else ordinary.get_robustcov_results(cov_type='HC3',use_t=False))
        ix=ordinary.model.exog_names.index('x');ci=fit.conf_int()[ix]
        rows.append(dict(model=label,n=len(subset),schools=subset.College.nunique(),formula=formula,covariance=covariance,
            social_coefficient=float(fit.params[ix]),ci95_low=float(ci[0]),ci95_high=float(ci[1]),r_squared=float(fit.rsquared),
            doubled_followers_percent_approx=100*(2**fit.params[ix]-1),
            note='exploratory selected-sample association; current performance not validated; no policy effect'))
        if label=='Main effects + position groups; HC3': base=ordinary
    models=pd.DataFrame(rows);models.to_csv(out/'football_exploratory_models.csv',index=False)
    influence=base.get_influence()
    private.mkdir(parents=True,exist_ok=True)
    pd.DataFrame(dict(Player_Name=data['Player Name'],College=data.College,followers=data['Instagram Followers'],
        NIL=data.Valuation,cooks_distance=influence.cooks_distance[0],leverage=influence.hat_matrix_diag)).to_csv(private/'football_influence_review.csv',index=False)
    loo=[float(smf.ols(main,data.drop(i),missing='raise').fit().params['x']) for i in data.index]
    metrics['diagnostics']=dict(cooks_above_4_over_n=int((influence.cooks_distance[0]>4/len(data)).sum()),
        maximum_cooks_distance=float(influence.cooks_distance[0].max()),maximum_leverage=float(influence.hat_matrix_diag.max()),
        leave_one_out_social_slope_min=min(loo),leave_one_out_social_slope_max=max(loo),
        breusch_pagan_exploratory_p=float(het_breuschpagan(base.resid,base.model.exog)[1]),
        adjusted_model_formula=main,school_clusters=data.College.nunique())
    fig,axes=plt.subplots(2,2,figsize=(11,8.1))
    for values,label,color in [(top,'Top-1,000 frame',NAVY),(data.Valuation,'Inherited sample, n=100',TEAL)]:
        x=np.sort(values);axes[0,0].step(x,np.arange(1,len(x)+1)/len(x),where='post',label=label,color=color)
    axes[0,0].set_xscale('log');axes[0,0].yaxis.set_major_formatter(PercentFormatter(1))
    axes[0,0].set_xticks([350000,500000,1000000,2000000,5000000],['$350K','$500K','$1M','$2M','$5M'])
    axes[0,0].xaxis.set_minor_formatter(NullFormatter())
    axes[0,0].set(xlabel='NIL estimate (USD, log axis)',ylabel='Cumulative share',title='Valuation-selected frame and sample')
    axes[0,0].legend(fontsize=8)
    axes[0,1].hist(np.log10(data['Instagram Followers']+1),bins=18,color=TEAL,edgecolor='white')
    axes[0,1].set(xlabel='log10(1 + Instagram followers)',ylabel='Players',title='Followers have a long right tail')
    axes[0,1].text(.98,.95,f"Median {data['Instagram Followers'].median():,.0f}\nMean {data['Instagram Followers'].mean():,.0f}",transform=axes[0,1].transAxes,ha='right',va='top',fontsize=9)
    axes[1,0].scatter(data['Instagram Followers']/1e6,data.Valuation/1e6,s=22,color=NAVY,alpha=.65)
    axes[1,0].set(xlabel='Instagram followers (millions)',ylabel='NIL estimate (USD millions)',title=f"Raw Pearson r = {metrics['raw_pearson']:.2f}")
    axes[1,1].scatter(data.x,data.y,s=22,color=TEAL,alpha=.65)
    line=np.linspace(data.x.min(),data.x.max(),100);slope,intercept=np.polyfit(data.x,data.y,1)
    axes[1,1].plot(line,intercept+slope*line,color=ORANGE,lw=2,label='Unadjusted descriptive line')
    axes[1,1].set(xlabel='ln(1 + followers)',ylabel='ln(NIL estimate)',title=f"Log Pearson r = {metrics['log_pearson']:.2f}; Spearman = {metrics['spearman']:.2f}")
    axes[1,1].legend(fontsize=8)
    fig.suptitle('Current football: preliminary associations in a selected sample',fontsize=14,fontweight='bold')
    fig.text(.02,.012,'Follower dates/identities and PPA are unverified. Neither correlation nor a log transformation establishes a NIL policy or scholarship effect.',fontsize=9)
    fig.tight_layout(rect=(0,.04,1,.96));savefig(fig,figures/'02_football_distributions.png')
    fig,axes=plt.subplots(1,2,figsize=(12,4.8),gridspec_kw={'width_ratios':[1.35,1]})
    for i,row in enumerate(models.itertuples()):
        axes[0].errorbar(row.social_coefficient,i,xerr=[[row.social_coefficient-row.ci95_low],[row.ci95_high-row.social_coefficient]],fmt='o',capsize=4,color=TEAL if i else NAVY)
    axes[0].set_yticks(range(len(models)),models.model,fontsize=9);axes[0].invert_yaxis();axes[0].axvline(0,color='#9aabb6',ls='--')
    axes[0].set(xlabel='Follower coefficient in ln(NIL) model (95% interval)',title='Exploratory model and influence checks')
    flagged=influence.cooks_distance[0]>4/len(data)
    axes[1].scatter(base.fittedvalues[~flagged],base.resid[~flagged],color=NAVY,s=24,alpha=.6,label='Other observations')
    axes[1].scatter(base.fittedvalues[flagged],base.resid[flagged],color=ORANGE,s=30,alpha=.9,label='Cook > 4/n review flag')
    axes[1].legend(fontsize=8,loc='upper left')
    axes[1].axhline(0,color='#8a8a8a',lw=1);axes[1].set(xlabel='Fitted ln(NIL)',ylabel='Residual',title='Residual spread and influential observations')
    fig.text(.02,.015,'No model is selected by significance. HC3/clustered SE address uncertainty assumptions; neither repairs selection, source errors or omitted performance.',fontsize=9)
    fig.tight_layout(rect=(0,.05,1,1));savefig(fig,figures/'03_football_model_checks.png')
    return metrics,models


def cohort_eda(frames,load,out,figures):
    basketball=[];star_coverage=[];star_links=[];overlap=[];drafts=[]
    for year in [2018,2019,2025]:
        d=frames[f'basketball_{year}'];qualified=truth(d.College_BPM_Qualified);bpm=observed(d.College_Box_BPM)
        qdata=d.loc[qualified & bpm]
        school_mean=qdata.groupby('College').College_Box_BPM.transform('mean')
        between_share=float(((school_mean-qdata.College_Box_BPM.mean())**2).sum()/((qdata.College_Box_BPM-qdata.College_Box_BPM.mean())**2).sum())
        basketball.append(dict(cohort_start=year,rows=len(d),athletes=d.athlete_id.nunique(),BPM_available=int(bpm.sum()),
            BPM_qualified=int(qualified.sum()),between_school_BPM_variance_share=between_share,no_recorded_games=int(d.Games.eq(0).sum()),
            median_games=float(d.loc[d.Games.gt(0),'Games'].median()),median_games_all_rows=float(d.Games.median()),median_PPG=float(d.Points_Per_Game.median()),
            median_BPM_all=float(d.College_Box_BPM.median()),median_BPM_qualified=float(d.loc[qualified,'College_Box_BPM'].median()),
            max_abs_BPM_all=float(d.College_Box_BPM.abs().max()),max_abs_BPM_qualified=float(d.loc[qualified,'College_Box_BPM'].abs().max()),
            qualified_PPG_BPM_spearman=float(d.loc[qualified,['Points_Per_Game','College_Box_BPM']].corr(method='spearman').iloc[0,1])))
    for year in [2018,2019,2025,2026]:
        d=frames[f'football_{year}'].copy()
        if 'subdivision_id' not in d:
            groups=load(ROOT/f'Data/private/evaluation/football_groups/cfb_team_group_seasons_{year}.parquet')
            g=groups.loc[groups.team_id_source.eq('espn')&groups.subdivision_id.isin(['cfb:fbs','cfb:fcs'])].copy()
            g['key']=g.team_id.map(identifier)
            if g.key.duplicated().any(): raise ValueError('Duplicate membership ID')
            d['subdivision_id']=d.team_id.map(identifier).map(g.set_index('key').subdivision_id)
        for name,group in d.groupby('subdivision_id',dropna=False):
            star_coverage.append(dict(cohort_start=year,subdivision=name,rows=len(group),
                stars_available=int(group.Recruit_Stars.notna().sum()),stars_fraction=float(group.Recruit_Stars.notna().mean()),
                HS_verified=int(truth(group.Recruit_HS_Verified).sum()),draft_link_fraction=float(group.Draft_Round.notna().mean())))
        for rating,group in d.groupby('Recruit_Stars',dropna=False):
            star_links.append(dict(cohort_start=year,reported_stars=rating,rows=len(group),draft_links=int(group.Draft_Round.notna().sum()),
                source_link_share=float(group.Draft_Round.notna().mean()),note='unverified recruiting and unequal follow-up; unknown outcomes not failures'))
    for key,d in frames.items():
        if key=='football_NIL_model':continue
        r=dict(dataset=key,rows=len(d),athletes=d.athlete_id.nunique(),draft_links=int(d.Draft_Round.notna().sum()),
            no_matched_draft_record=int(d.Draft_Round.isna().sum()),linked_share=float(d.Draft_Round.notna().mean()),
            median_linked_round=float(d.Draft_Round.median()) if d.Draft_Round.notna().any() else None,
            identity_timing_flags=int(d.NFL_College_Identity_Timing_Flag.notna().sum()) if 'NFL_College_Identity_Timing_Flag' in d else None,
            draft_links_secondary_disagreement=int((d.Draft_Round.notna() & d.Draft_Secondary_Source_Agreement.notna() & ~truth(d.Draft_Secondary_Source_Agreement)).sum()),
            draft_links_with_ID_support=int(d.Draft_Status.eq('exact_ESPN_ID_name_and_PFR_draft_record').sum()),
            note='link availability, NOT drafted/undrafted probability; unequal career follow-up')
        drafts.append(r)
    for sport,years in [('basketball',[2018,2019,2025]),('football',[2018,2019,2025,2026])]:
        for a in years:
            x=set(frames[f'{sport}_{a}'].athlete_id.map(identifier))
            for b in years:
                y=set(frames[f'{sport}_{b}'].athlete_id.map(identifier))
                overlap.append(dict(sport=sport,cohort_a=a,cohort_b=b,shared_athletes=len(x&y),
                    jaccard=len(x&y)/len(x|y),share_of_first=len(x&y)/len(x),note='source-ID overlap; IDs still require identity review'))
    tables=[(basketball,'basketball_distribution_summary.csv'),(star_coverage,'football_recruiting_coverage.csv'),
            (star_links,'football_draft_link_share_by_candidate_stars.csv'),(drafts,'draft_link_coverage.csv'),(overlap,'cohort_overlap.csv')]
    for rows,name in tables:pd.DataFrame(rows).to_csv(out/name,index=False)
    fig,axes=plt.subplots(2,3,figsize=(12,7.1))
    bins=np.linspace(-26,23,50)
    for k,year in enumerate([2018,2019,2025]):
        d=frames[f'basketball_{year}'];q=truth(d.College_BPM_Qualified)
        axes[0,k].hist(d.College_Box_BPM.dropna(),bins=bins,density=True,color='#bdc9d1',alpha=.7,label='All observed BPM')
        axes[0,k].hist(d.loc[q,'College_Box_BPM'],bins=bins,density=True,histtype='step',color=TEAL,lw=2,label='Provider qualified')
        axes[0,k].set(title=f'{year}–{str(year+1)[-2:]}: {int(q.sum()):,} qualified',xlabel='Box BPM',ylabel='Density')
        if k==0:axes[0,k].legend(fontsize=8)
        good=d.College_BPM_Minutes.gt(0)&d.College_Box_BPM.notna()
        axes[1,k].scatter(d.loc[good,'College_BPM_Minutes'],d.loc[good,'College_Box_BPM'],s=5,alpha=.20,color=NAVY,rasterized=True)
        axes[1,k].set(xlabel='Recorded season minutes',ylabel='Box BPM',title='Season minutes vs. BPM')
    fig.suptitle('Basketball evaluation: exposure and qualification matter',fontsize=14,fontweight='bold')
    fig.text(.02,.01,'Source model-derived values, not NIL or scholarship decisions. Cross-era calibration is unverified; 2019–20 was shortened. No low-minute rows deleted.',fontsize=9)
    fig.tight_layout(rect=(0,.04,1,.96));savefig(fig,figures/'04_basketball_evaluation.png')
    coverage=pd.DataFrame(star_coverage)
    fig,axes=plt.subplots(1,2,figsize=(11.8,4.5))
    for offset,division,color in [(-.18,'cfb:fbs',NAVY),(.18,'cfb:fcs',TEAL)]:
        sub=coverage.loc[coverage.subdivision.eq(division)].set_index('cohort_start').reindex([2018,2019,2025,2026])
        axes[0].bar(np.arange(4)+offset,sub.stars_fraction,.34,label=division.split(':')[1].upper(),color=color)
    axes[0].set_xticks(range(4),['2018','2019','2025','2026']);axes[0].yaxis.set_major_formatter(PercentFormatter(1))
    axes[0].set(ylim=(0,1),ylabel='Share with candidate recruiting stars',xlabel='Football college cohort',title='Recruiting coverage differs by subdivision');axes[0].legend()
    stars=pd.DataFrame(star_links)
    for offset,year,color in [(-.18,2018,NAVY),(.18,2019,TEAL)]:
        sub=stars.loc[stars.cohort_start.eq(year)&stars.reported_stars.notna()].set_index('reported_stars').reindex([2,3,4,5])
        axes[1].bar(np.arange(4)+offset,sub.source_link_share,.34,label=str(year),color=color)
    axes[1].set_xticks(range(4),['2','3','4','5']);axes[1].yaxis.set_major_formatter(PercentFormatter(1))
    axes[1].set(xlabel='Source-reported stars (HS classification unverified)',ylabel='Share with a linked draft record',title='Draft-link share is not a true success rate');axes[1].legend()
    fig.text(.02,.012,'Counts use athlete-team rows. Missingness may reflect source/matching coverage; no-match is unknown, not undrafted. No causal or predictive validation claimed.',fontsize=9)
    fig.tight_layout(rect=(0,.05,1,1));savefig(fig,figures/'05_football_coverage.png')
    fig,axes=plt.subplots(1,2,figsize=(10.3,4.6))
    overlaps=pd.DataFrame(overlap)
    for ax,sport,years in zip(axes,['basketball','football'],[[2018,2019,2025],[2018,2019,2025,2026]]):
        sub=overlaps.loc[overlaps.sport.eq(sport)]
        values=sub.pivot(index='cohort_a',columns='cohort_b',values='jaccard').loc[years,years]
        counts=sub.pivot(index='cohort_a',columns='cohort_b',values='shared_athletes').loc[years,years]
        ax.imshow(values,vmin=0,vmax=1,cmap='Blues')
        for i in range(len(years)):
            for j in range(len(years)):
                label='<1%' if 0<values.iloc[i,j]<.01 else f'{values.iloc[i,j]:.0%}'
                ax.text(j,i,f'{counts.iloc[i,j]:,}\n{label}',ha='center',va='center',fontsize=9,color='white' if values.iloc[i,j]>.55 else NAVY)
        ax.set_xticks(range(len(years)),years);ax.set_yticks(range(len(years)),years);ax.set_title(sport.title())
    fig.suptitle('Repeated athletes: shared IDs and Jaccard overlap',fontsize=13,fontweight='bold')
    fig.text(.02,.015,'Cells show shared athlete IDs and intersection/union. Adjacent cohorts are not independent; source identity errors may also contribute.',fontsize=9)
    fig.tight_layout(rect=(0,.06,1,.93));savefig(fig,figures/'06_cohort_overlap.png')
    return basketball,star_coverage,star_links,drafts,overlap


def write_report(out,html_out,figures,inventory,coverage,football,models,basketball,star_coverage,drafts,overlap,manifest):
    f=football;b=pd.DataFrame(basketball);sc=pd.DataFrame(star_coverage)
    overlap_table=pd.DataFrame(overlap);adjacent=overlap_table.loc[overlap_table.cohort_a.eq(2018)&overlap_table.cohort_b.eq(2019)]
    inventory_view=inventory[['dataset','rows','unique_athletes','schools','multi_team_athletes']]
    fbs=sc.loc[sc.cohort_start.eq(2018)&sc.subdivision.eq('cfb:fbs')].iloc[0]
    fcs=sc.loc[sc.cohort_start.eq(2018)&sc.subdivision.eq('cfb:fcs')].iloc[0]
    lines=['# Exploratory data analysis','',
        'Exploratory snapshot of the available source layers; no new source collection, confirmatory hypothesis test or NIL policy-effect claim. '
        'This report distinguishes a current valuation association from the still-unanswered scholarship/pre-post question. Player-level outputs stay local; code, aggregate tables and figures are reviewable.','',
        'Source layers: inherited football CSVs attributed to The Sideline by the partner write-up (original snapshot and valuation type unverified), ESPN/SportsDataverse performance and roster exports, SportsDataverse model-derived basketball BPM, and nflverse career crosswalks. Exact input hashes are in the manifest; collection provenance is in the existing source audits. NIL figures are estimates, not verified compensation.','',
        '## Main findings','',
        f"- Only the inherited football model file has both NIL and followers (n={f['rows']}); it is drawn from a top-1,000 valuation frame, not the full college-athlete population. Historical and basketball layers have no social measurements or NIL valuations. Verified HS recruiting is absent in the new frames.",
        f"- Current football followers are highly skewed: median {f['follower_summary']['median']:,.0f}, mean {f['follower_summary']['mean']:,.0f}, maximum {f['follower_summary']['maximum']:,.0f}. The largest account contributes {f['largest_follower_share']:.1%} of summed followers in this sample.",
        f"- The selected-sample association is positive: raw Pearson r={f['raw_pearson']:.3f}, log-scale Pearson r={f['log_pearson']:.3f}, Spearman rho={f['spearman']:.3f}. Removing the largest account changes raw r to {f['raw_pearson_without_largest']:.3f} and log r to {f['log_pearson_without_largest']:.3f}. These are descriptive, not causal or independent validation of the input observations.",
        f"- Conference variation is nearly absent ({f['power4']}/100 Power-4); {f['stars_counts'].get(4,0)}/{f['rows']} have four-star labels. There are {f['schools']} schools, with repeated players per school. Avoid treating the Power-4 coefficient as a stable conference effect.",
        f"- PPA needs recollection: {f['PPA_zeros']} zeros and {f['PPA_nonzero_defense_or_line']} nonzero values on defense/offensive line, where this collected offensive metric is not applicable. These are audit flags, not proof of exact row corrections.",
        f"- Football recruiting availability is selective: in 2018, {fbs.stars_fraction:.1%} of FBS rows versus {fcs.stars_fraction:.1%} of FCS rows have candidate stars. Complete-case restriction would change the target population. These are not yet verified high-school ratings.",
        '- Basketball BPM is broadly observed, but roughly half of roster rows satisfy the provider qualification flag. Unqualified/low-minute rows have wider extremes. Compare exposure and source qualification before ranking players.',
        '- Adjacent seasons reuse many athlete IDs; player-team rows, distinct athletes, and sampling units differ. Historical cohorts have much longer career follow-up. Draft no-match remains unknown, so observed link shares are not draft probabilities.','',
        '## Data structure and coverage','',markdown(inventory_view),'',
        'The three inherited football files are nested layers (frame → sampled players → enriched/model records), not three independent samples. The seven cohort files are supporting source frames, not final stratified samples or proof of complete national coverage. Football school coverage changes across years, so a change in source population can mimic a trend. Superseded production samples are intentionally excluded. Basketball cohort starts 2018/2019/2025 mean 2018–19/2019–20/2025–26; football uses fall-start seasons. Fall 2026 is ongoing.','',
        '![Coverage](figures/01_coverage.png)','',
        'All-zero verification coverage differs from an observed numerical zero. The field dictionary records absent columns, missing observations, uniqueness and suggested roles. The cohort files currently lack the social columns entirely, rather than containing verified zero followers.','',
        '## Current football: distributions and preliminary relationships','',
        '![Football distributions](figures/02_football_distributions.png)','',
        f"The top-1,000 frame has only {f['frame_unique_NIL_values']} distinct reported valuations, so ties and rounded price bands matter. The sample minimum of ${f['valuation_summary']['minimum']:,.0f} reflects valuation selection. Modeling only this range cannot identify scholarship selection or associations for lower-valued/unvalued athletes. Sampling weights target the supplied frame; they cannot recover athletes excluded below the cutoff.",'',
        '## Exploratory model checks','',
        markdown(models[['model','n','social_coefficient','ci95_low','ci95_high','r_squared']]),'',
        'The inherited model is retained only as a replication benchmark. The alternative omits unverified PPA and the nearly constant Power-4 indicator, includes both main effects for the stars×freshman interaction, and groups positions to avoid sparse single-position cells. It still lacks a validated college-performance control. The largest-audience deletion is a sensitivity check, not a new preferred sample. No model is chosen by its p-value or R².','',
        '![Model checks](figures/03_football_model_checks.png)','',
        f"The alternative model has {f['diagnostics']['cooks_above_4_over_n']} observations above the descriptive Cook's-distance 4/n flag. Leave-one-out follower slopes range from {f['diagnostics']['leave_one_out_social_slope_min']:.3f} to {f['diagnostics']['leave_one_out_social_slope_max']:.3f}. Flags prompt review rather than automatic deletion. The school-clustered calculation uses {f['diagnostics']['school_clusters']} clusters and a small-sample correction; sparse/unbalanced clusters still limit precision.",'',
        'HC3 and cluster covariance calculations follow [statsmodels robust covariance documentation](https://www.statsmodels.org/stable/generated/statsmodels.regression.linear_model.RegressionResults.get_robustcov_results.html). These change uncertainty estimates; they do not repair input validity, outcome-based selection, reverse causation or confounding. Influence/residual checks follow [statsmodels diagnostics](https://www.statsmodels.org/stable/examples/notebooks/generated/regression_diagnostics.html).','',
        '## Basketball: comparable exposure before comparable outcomes','',
        markdown(b[['cohort_start','rows','BPM_available','BPM_qualified','median_games','median_PPG','median_BPM_qualified']]),'',
        markdown(b[['cohort_start','qualified_PPG_BPM_spearman','between_school_BPM_variance_share']]),'',
        'Among provider-qualified players, the descriptive between-school share of BPM variation is about 52–65%, and PPG/BPM rank correlation is only about .12–.16. This is compatible with a measure that captures substantial team context rather than scoring alone; it is not validation of player ability. Review construction/calibration before using BPM as a replacement evaluation outcome. The variance decomposition is descriptive, not a causal school effect.','',
        '![Basketball evaluation](figures/04_basketball_evaluation.png)','',
        'Source BPM combines model-derived efficiency information and is not NIL valuation, scholarship evaluation or a prospective real-time ranking. Differences across seasons may reflect exposure, population, model calibration and source coverage. Game medians use rows with at least one recorded appearance; PPG summaries use nonmissing observations. The 2019–20 season has fewer recorded games; season point totals should not be compared as though opportunities were equal. Qualification/minutes restrictions change the estimand to qualifying/active players, so retain the full frame and report exclusions. Do not infer the effect of NIL from a shift in these distributions.','',
        '## Football: missingness and draft ascertainment','',
        '![Football coverage](figures/05_football_coverage.png)','',
        markdown(pd.DataFrame(drafts)[['dataset','rows','draft_links','no_matched_draft_record','identity_timing_flags']]),'',
        'Many basketball draft links have a secondary-source disagreement flag; the draft coverage CSV records those counts separately from ID-supported football links. Resolve these disagreements before outcome modeling.','',
        'The plotted higher-star draft-link pattern is descriptive and mixes unverified ratings, differential identity coverage and subsequent opportunities. Unmatched players may be drafted under another identity/school, undrafted, still eligible, playing abroad, or simply missing. No binary success/failure or logistic regression was constructed from these unknowns. Career duration is not the number of source seasons observed, and a pro registry entry is not a contract.','',
        '## Dependence, repeated athletes and follow-up','',
        markdown(adjacent[['sport','cohort_a','cohort_b','shared_athletes','jaccard','share_of_first']]),'',
        '![Cohort overlap](figures/06_cohort_overlap.png)','',
        'Use a documented athlete-season or athlete-school-decision unit. For transfers, retain team records for source audit and define one athlete-season measurement before modeling, rather than arbitrarily duplicating the outcome. Repeated athletes require dependence-aware inference; school clustering may also matter. Train/test splits, if prediction becomes a goal, must group by athlete and respect chronology. Do not compare eight years of historical career follow-up with incomplete current careers.','',
        '## Analysis plan supported by this EDA','',
        '1. **Available now: selected-sample valuation association.** After validating follower identities/dates and recollecting performance, use ln(NIL) against ln(1+followers), with justified baseline stars, experience and position controls. This log-outcome model describes positive valuations; pre-specify how genuine zero valuations will be handled in future frames, without turning unknown valuations into zeros or silently excluding source-reported zeros. Include constituent main effects for interactions. Inspect nonlinear patterns and influential cases; report HC3 plus a school-cluster sensitivity. Effects are associations within the defined valuation frame. The current 100 observations and limited covariate variation constrain complexity.',
        '2. **Basketball/cross-sport NIL extension: pending inputs.** Obtain the real NIL frame, apply the pre-specified 250-per-quartile sample before enrichment, collect contemporaneous followers and verify covariates. Then compare social slopes with a pooled social×sport interaction and its confidence interval. Harmonize measurement timing and inclusion criteria; do not compare raw PPA and BPM as the same scale. Neither separately significant slopes nor different signs establish a slope difference.',
        '3. **Original before/after scholarship question: not estimable yet.** Define a common outcome (verified offers/award or another explicitly redesigned evaluation measure), dated predictors and a consistent eligible population in both eras. The present historical frames have neither social counts nor scholarship decisions. Current NIL-selected and historical recruiting-selected samples target different populations and cannot simply be pooled. Pre-specify a common sampling frame/weights and timing policy. A social×post interaction estimates a change in association, not automatically a causal effect of NIL; calendar/platform/COVID/policy changes remain confounded.',
        '4. **Career evaluation alternative: redesign before fitting.** Keep draft/contract outcomes separate; establish verified positives, trustworthy negatives and a common follow-up horizon or a censoring-aware design. Draft round is conditional on draft selection and differs by league. An ordinal/selection or time-to-event model may be justified after the observation process is resolved; do not assign undrafted players round zero. Years in college has no monotonic quality interpretation.',
        '5. **Finish coverage and power before adding complexity.** Verify HS classes, preserve missingness and map source/identity failures by sport, tier, position and subdivision. Do not impute structural missingness such as nonexistent historical NIL values or unknown future outcomes. Use the existing partial-term power script for the planned interaction and revise for clustering/design. Pre-specify the primary model before collecting/inspecting further effect estimates.','',
        'The field dictionary tags later career outcomes and source metadata so they are not accidentally treated as pre-decision predictors. Also verify whether valuation estimates already use the proposed predictors; formula-generated outcomes can build associations into the data.','',
        '## Reproduction and artifacts','',
        '```bash','python scripts/run_eda.py','```','',
        'Tables/figures: `reports/eda/`. Standalone visual report: `outputs/eda-20261101/eda_report.html`. Private influence rows: `Data/private/eda/`. Input hashes, software versions and exclusions: `reports/eda/manifest.json`. Raw and enriched inputs are read-only; no live requests or synthetic observations enter the EDA. All intervals and sensitivity fits are exploratory.']
    (out/'README.md').write_text('\n'.join(lines)+'\n')
    # Standalone, dependency-free visual report; only aggregate tables/unnamed plots.
    sections=[]
    cards=[('Current paired social + NIL',f"{f['rows']} football players"),('Unobserved social counts','All historical/basketball frames'),('Largest account share',f"{f['largest_follower_share']:.1%} of sampled followers"),('Current log correlation',f"r = {f['log_pearson']:.2f}")]
    sections.append('<div class="cards">'+''.join(f'<article><small>{html.escape(a)}</small><strong>{html.escape(b)}</strong></article>' for a,b in cards)+'</div>')
    sections.append('<div class="notice">Exploratory source-data snapshot. Historical/basketball social measurements and scholarship outcomes are absent. No pre/post NIL effect is estimated.</div>')
    sections.append('<h2>Data layers and units</h2>'+inventory_view.to_html(index=False,border=0))
    titles=['Coverage and verification','Current football patterns','Model sensitivity','Basketball exposure and evaluation','Football recruiting coverage','Repeated athletes']
    captions=['No observed value is different from a verified zero. Draft availability is not success probability.',
        f"Raw r={f['raw_pearson']:.2f}, log r={f['log_pearson']:.2f}; removing the largest audience gives raw r={f['raw_pearson_without_largest']:.2f}. Selected and unverified input data limit interpretation.",
        'Exploratory comparisons only. Source validity and selection are unresolved even where intervals exclude zero.',
        'Low-minute estimates are more extreme. Qualification flags and exposure rules matter; calibration across eras is unverified.',
        'Complete-case analysis changes the population. Draft no-match stays unknown.',
        'Adjacent cohorts contain repeated athlete IDs; career follow-up windows also differ.']
    for filename,title,caption in zip(sorted(figures.glob('*.png')),titles,captions):
        encoded=base64.b64encode(filename.read_bytes()).decode()
        sections.append(f'<section><h2>{html.escape(title)}</h2><img alt="{html.escape(title)}" src="data:image/png;base64,{encoded}"><p>{html.escape(caption)}</p></section>')
    sections.append('<h2>What to analyze next</h2><ol><li>Validate and analyze the current football valuation association.</li><li>Collect current basketball NIL/social inputs before a cross-sport interaction.</li><li>Define the same outcome, population and dated social predictor before any before/after comparison.</li><li>Resolve unknown negatives and unequal follow-up before career-outcome modeling.</li></ol>')
    sections.append('<p>Full interpretation, formulas, limitations and commands are in reports/eda/README.md. This HTML embeds all figures and works offline.</p>')
    html_out.parent.mkdir(parents=True,exist_ok=True)
    html_out.write_text('<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>NIL project EDA</title><style>body{font:16px/1.55 system-ui,sans-serif;color:#203c55;background:#f4f6f7;margin:0}main{max-width:1200px;margin:auto;padding:36px 28px}h1{font-size:36px;margin-bottom:8px}h2{margin-top:38px}small{display:block;color:#536d7a}.cards{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin:25px 0}article,section{background:white;padding:18px;border:1px solid #d9e2e5;border-radius:10px}strong{display:block;font-size:21px;margin-top:8px}.notice{padding:17px;background:#fff4df;border-left:4px solid #d18739}img{width:100%;height:auto}table{border-collapse:collapse;background:white;font-size:13px;display:block;overflow-x:auto}td,th{padding:9px 12px;border-bottom:1px solid #d9e2e5;text-align:left}th{background:#203c55;color:white}@media(max-width:800px){.cards{grid-template-columns:1fr 1fr}main{padding:20px}h1{font-size:29px}}</style><main><small>AIPI 510 · descriptive analysis · source snapshot November 2026</small><h1>What the NIL data can tell us</h1><p>Structure, coverage, preliminary relationships and an analysis plan.</p><p>Sources: inherited Sideline-attributed NIL estimates, ESPN/SportsDataverse exports and nflverse. Original observation dates and measurement validity remain under review.</p>'+''.join(sections)+'</main></html>')


def run(args):
    out=args.outdir;figures=out/'figures';figures.mkdir(parents=True,exist_ok=True)
    inputs={}
    def load(path):
        if not path.exists(): raise ValueError(f'Missing input {path}; reproduce collection first')
        inputs[str(path.relative_to(ROOT))]=digest(path)
        return pd.read_parquet(path) if path.suffix=='.parquet' else pd.read_csv(path,low_memory=False)
    specs=canonical_datasets()
    frames,inventory,coverage=collect_inventory(specs,load,out)
    top=load(ROOT/'Data/football_top1000.csv')
    coverage_plot(coverage,specs,figures/'01_coverage.png')
    football,models=football_eda(frames['football_NIL_model'],top,out,ROOT/'Data/private/eda',figures)
    basketball,star_coverage,star_links,drafts,overlap=cohort_eda(frames,load,out,figures)
    pd.DataFrame([
        dict(question='Current football NIL/social association',status='exploratory_only',next_dependency='Validate identities/dates and performance; define selected-frame estimand'),
        dict(question='Current basketball/cross-sport NIL slope',status='missing_key_inputs',next_dependency='Real basketball NIL valuations and dated follower counts'),
        dict(question='Before/after scholarship decision slope',status='not_estimable',next_dependency='Same decision outcome/population and pre-decision social measures in both eras'),
        dict(question='Career evaluation across eras',status='descriptive_links_only',next_dependency='Verified negatives, identity resolution and equal follow-up/censoring design')
    ]).to_csv(out/'analysis_readiness.csv',index=False)
    manifest=dict(generated_at=datetime.now(timezone.utc).isoformat(),source_career_as_of='2026-11-01',
        inputs=inputs,script_sha256=digest(Path(__file__)),versions=dict(python=platform.python_version(),pandas=pd.__version__,numpy=np.__version__,statsmodels=statsmodels.__version__,matplotlib=matplotlib.__version__),
        included_units='one inherited football model plus seven canonical cohort frames; nested frame/sample not pooled',
        excluded_layers=['superseded production-quartile samples','duplicate pre-NFL-ID football versions','header-only templates','synthetic fixtures'],
        no_match_policy='Missing draft/contract record is unknown, never a verified negative',football=football,
        basketball=basketball,notes=['All results are exploratory','No outcome or predictor imputation','No pre/post model fitted'])
    write_report(out,args.html_output,figures,inventory,coverage,football,models,basketball,star_coverage,drafts,overlap,manifest)
    for relative,expected in inputs.items():
        if digest(ROOT/relative)!=expected: raise ValueError(f'EDA input changed: {relative}')
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2,allow_nan=False)+'\n')
    print(json.dumps(dict(report=str(out/'README.md'),visual_report=str(args.html_output),
        figures=len(list(figures.glob('*.png'))),football_correlations={k:football[k] for k in ['raw_pearson','log_pearson','spearman','raw_pearson_without_largest']},models=models[['model','social_coefficient']].to_dict('records')),indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--outdir',type=Path,default=ROOT/'reports/eda')
    parser.add_argument('--html-output',type=Path,default=ROOT/'outputs/eda-20261101/eda_report.html')
    args=parser.parse_args()
    run(args)
