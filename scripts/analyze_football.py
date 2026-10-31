"""Reproduce the partner model and report explicitly exploratory sensitivities."""
import json
import os
from pathlib import Path

os.environ.setdefault('MPLCONFIGDIR', '/tmp/nil-matplotlib')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
from statsmodels.stats.diagnostic import het_breuschpagan
from statsmodels.stats.outliers_influence import variance_inflation_factor

ROOT = Path(__file__).resolve().parents[1]
LEGACY = ('Log_Valuation ~ Log_Instagram + PPA_Per_Play + Freshman_Flag + '
          'Freshman_X_Stars + Power_4_Dummy + Premium_Position')
# Excludes unverified PPA entirely; cannot claim to control for college performance.
EXPLORATORY = ('Log_Valuation ~ Log_Instagram + Stars_C * Freshman_Flag '
               '+ C(Position)')


def fit_checked(formula, data, covariance):
    model = smf.ols(formula, data=data, missing='raise').fit(cov_type=covariance)
    if np.linalg.matrix_rank(model.model.exog) != model.model.exog.shape[1]:
        raise ValueError('Rank-deficient design matrix; revise controls.')
    return model


def run():
    out = ROOT / 'reports'
    out.mkdir(exist_ok=True)
    df = pd.read_csv(ROOT / 'Data/football_modeling_data.csv')
    # Recompute rather than trust inherited transformations.
    numeric = ['Valuation', 'Instagram Followers', 'Star Rating', 'PPA_Per_Play']
    if not np.isfinite(df[numeric].to_numpy()).all():
        raise ValueError('Non-finite modeling inputs')
    if (df.Valuation <= 0).any() or (df['Instagram Followers'] < 0).any():
        raise ValueError('Valuations must be positive and followers nonnegative')
    df['Log_Valuation'] = np.log(df.Valuation)
    df['Log_Instagram'] = np.log1p(df['Instagram Followers'])
    df['Stars_C'] = df['Star Rating'] - df['Star Rating'].mean()
    models = {
        'partner_replication_HC1': fit_checked(LEGACY, df, 'HC1'),
        'partner_replication_HC3': fit_checked(LEGACY, df, 'HC3'),
        'without_unverified_PPA_HC3': fit_checked(EXPLORATORY, df, 'HC3'),
        'without_unverified_PPA_or_largest_audience_HC3': fit_checked(
            EXPLORATORY, df.drop(df['Instagram Followers'].idxmax()), 'HC3'),
    }
    rows = []
    for label, model in models.items():
        for term in model.params.index:
            ci = model.conf_int().loc[term]
            adjusted = model.conf_int(alpha=.05 / 3).loc[term]
            rows.append(dict(model=label, term=term, coefficient=model.params[term],
                             standard_error=model.bse[term], p_two_sided=model.pvalues[term],
                             ci95_low=ci[0], ci95_high=ci[1],
                             ci9833_low=adjusted[0], ci9833_high=adjusted[1],
                             n=int(model.nobs), r_squared=model.rsquared))
    table = pd.DataFrame(rows)
    table.to_csv(out / 'football_coefficients.csv', index=False)
    base = smf.ols(LEGACY, data=df).fit()
    influence = base.get_influence()
    diagnostics = dict(
        breusch_pagan_lm_p=float(het_breuschpagan(base.resid, base.model.exog)[1]),
        jarque_bera_p=float(sm.stats.jarque_bera(base.resid)[1]),
        max_cooks_distance=float(influence.cooks_distance[0].max()),
        observations_above_cooks_4_over_n=int((influence.cooks_distance[0] > 4 / len(df)).sum()),
        vif={name: float(variance_inflation_factor(base.model.exog, i))
             for i, name in enumerate(base.model.exog_names)})
    (out / 'football_diagnostics.json').write_text(json.dumps(diagnostics, indent=2) + '\n')
    focus = table.loc[table.term.eq('Log_Instagram')]
    lines = ['# Football analysis', '',
             'Exploratory associations in the inherited selected top-1000 frame. '
             'No model here estimates a pre/post NIL effect or a scholarship effect.', '',
             'The partner models retain unverified PPA solely for replication. '
             'The other models omit PPA and cannot control for college performance. '
             'HC3 uses a normal-reference Wald test; no one-sided test is claimed.', '',
             '| Model | N | Social coefficient | 95% CI | Two-sided p | R² |',
             '|---|---:|---:|---|---:|---:|']
    for row in focus.itertuples():
        lines.append(f'| {row.model} | {row.n} | {row.coefficient:.4f} | '
                     f'[{row.ci95_low:.4f}, {row.ci95_high:.4f}] | '
                     f'{row.p_two_sided:.6g} | {row.r_squared:.3f} |')
    beta = models['partner_replication_HC1'].params['Log_Instagram']
    lines += ['', f'The replicated coefficient corresponds approximately to '
              f'{100 * (2 ** beta - 1):.1f}% higher modeled valuation for twice the '
              'followers at sufficiently large follower counts, conditional on included controls. '
              'This is an association, not a causal effect.', '',
              'The coefficient CSV also reports 98.33% intervals for the write-up’s '
              'three-test Bonferroni family. Sensitivity models are exploratory, '
              'not additional confirmatory discoveries.', '',
              'Missing data provenance, possible mismatches, selection on valuation, '
              'contemporaneous follower measurement, school clustering and sparse '
              'conference variation limit inference. HC3 does not fix these problems. '
              'Normality tests do not establish independence or causality.']
    (out / 'football_results.md').write_text('\n'.join(lines) + '\n')
    fig, axes = plt.subplots(1, 3, figsize=(13, 3.8))
    axes[0].scatter(df.Log_Instagram, df.Log_Valuation, alpha=.65, s=18)
    axes[0].set(xlabel='log(1 + Instagram followers)', ylabel='log(NIL valuation)',
                title='Inherited football sample (n=100)')
    axes[1].scatter(base.fittedvalues, base.resid, alpha=.65, s=18)
    axes[1].axhline(0, color='gray', linewidth=1)
    axes[1].set(xlabel='Fitted log valuation', ylabel='Residual', title='Partner model residuals')
    sm.qqplot(base.resid, line='s', ax=axes[2], markersize=3)
    axes[2].set_title('Partner model normal Q-Q')
    fig.tight_layout()
    fig.savefig(out / 'football_diagnostics.png', dpi=160)
    plt.close(fig)
    print('\n'.join(lines))


if __name__ == '__main__':
    run()
