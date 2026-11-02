"""Recompute aggregate statistics for the rubric deliverables without live requests.

Uses the four fixed exploratory comparisons from run_eda.py. No source mutation,
automatic outlier removal, model search, or new confirmatory test is performed.
"""
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
from statsmodels.stats.diagnostic import het_breuschpagan
from statsmodels.stats.outliers_influence import variance_inflation_factor
from power_sensitivity import required_n, power
from run_eda import position_group

ROOT = Path(__file__).resolve().parents[1]


def run():
    source = ROOT / 'Data/football_modeling_data.csv'
    initial = hashlib.sha256(source.read_bytes()).hexdigest()
    d = pd.read_csv(source)
    d['x'] = np.log1p(d['Instagram Followers'])
    d['y'] = np.log(d.Valuation)
    d['Stars_C'] = d['Star Rating'] - d['Star Rating'].mean()
    d['Position_Group'] = d.Position.map(position_group)
    legacy = 'y ~ x + PPA_Per_Play + Freshman_Flag + Freshman_X_Stars + Power_4_Dummy + Premium_Position'
    alternative = 'y ~ x + Stars_C * Freshman_Flag + C(Position_Group)'
    specs = [('Inherited model HC1', legacy, d, 'HC1'),
             ('Inherited model HC3', legacy, d, 'HC3'),
             ('Position groups HC3', alternative, d, 'HC3'),
             ('Largest audience omitted HC3', alternative, d.drop(d['Instagram Followers'].idxmax()), 'HC3'),
             ('Position groups school clustered', alternative, d, 'cluster')]
    rows = []
    for label, formula, subset, covariance in specs:
        model = smf.ols(formula, subset, missing='raise').fit()
        if np.linalg.matrix_rank(model.model.exog) != model.model.exog.shape[1]:
            raise ValueError('Rank deficient model')
        robust = (model.get_robustcov_results(cov_type='cluster', groups=subset.College,
                   use_correction=True, use_t=True) if covariance == 'cluster' else
                  model.get_robustcov_results(cov_type=covariance, use_t=False))
        i = model.model.exog_names.index('x')
        ci95, cifamily = robust.conf_int()[i], robust.conf_int(alpha=.05/3)[i]
        jb, jbp, skew, kurtosis = sm.stats.jarque_bera(model.resid)
        reduced = smf.ols(formula.replace('x + ', ''), subset, missing='raise').fit()
        rows.append(dict(model=label, formula=formula, n=int(model.nobs), schools=subset.College.nunique(),
            coefficient=float(robust.params[i]), standard_error=float(robust.bse[i]),
            p_two_sided=float(robust.pvalues[i]), ci95=list(map(float,ci95)),
            ci9833=list(map(float,cifamily)), r_squared=float(model.rsquared),
            doubled_followers_percent=100*(2**robust.params[i]-1),
            doubled_followers_ci95_percent=[100*(2**v-1) for v in ci95],
            observed_partial_f2=float((model.rsquared-reduced.rsquared)/(1-model.rsquared)),
            breusch_pagan_p=float(het_breuschpagan(model.resid,model.model.exog)[1]),
            jarque_bera_p=float(jbp),
            cooks_above_4_over_n=int((model.get_influence().cooks_distance[0]>4/model.nobs).sum()),
            vif={name:float(variance_inflation_factor(model.model.exog,j)) for j,name in enumerate(model.model.exog_names)}))
    evidence = dict(as_of='2026-11-01', source_sha256=initial,
        status='exploratory associations; no basketball, cross-sport or pre/post effect test',
        alpha_family=.05/3, models=rows,
        power=[dict(partial_f2=f2,total_predictors=8,tested_terms=1,
                    required_n=required_n(8,f2),power_at_100=power(100,8,f2)) for f2 in [.02,.05,.15]],
        references={'NCAA':'https://www.ncaa.org/about-us/history/',
                    'robust_covariance':'https://www.statsmodels.org/stable/generated/statsmodels.regression.linear_model.RegressionResults.get_robustcov_results.html'})
    assert hashlib.sha256(source.read_bytes()).hexdigest() == initial
    out=ROOT/'reports/deliverables';out.mkdir(parents=True,exist_ok=True)
    (out/'model_statistics.json').write_text(json.dumps(evidence,indent=2)+'\n')
    print(pd.DataFrame(rows)[['model','coefficient','p_two_sided','ci9833','r_squared']].to_string(index=False))


if __name__ == '__main__':
    run()
