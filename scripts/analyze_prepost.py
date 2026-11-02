"""Estimate change in the social association with scholarship offers, per sport.

Real decision-time data is required. A header-only template is not evidence.
This observational model does not identify a causal policy effect.
"""
import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

CUTOFF = pd.Timestamp('2021-07-01', tz='UTC')
REQUIRED = ['athlete_id', 'sport', 'school', 'position', 'decision_date',
            'followers', 'follower_observed_at', 'athletic_score',
            'performance_observed_at', 'scholarship_offer',
            'decision_source_url', 'social_source_url', 'performance_source_url']


def validate(data):
    if not set(REQUIRED).issubset(data.columns) or data.empty:
        raise ValueError('Need real observations with all columns in Data/templates/scholarship_prepost.csv')
    data = data.copy()
    if data[REQUIRED].isna().any().any():
        raise ValueError('Missing required values; record missingness rather than inventing data')
    for c in ['athlete_id', 'school', 'position', 'sport']:
        if data[c].astype(str).str.strip().eq('').any():
            raise ValueError(f'Blank identity/control field: {c}')
    for c in ['decision_date', 'follower_observed_at', 'performance_observed_at']:
        data[c] = pd.to_datetime(data[c], utc=True, errors='raise')
    if (data.follower_observed_at > data.decision_date).any() or (data.performance_observed_at > data.decision_date).any():
        raise ValueError('Predictors observed after the decision would introduce look-ahead bias')
    for c in ['followers', 'athletic_score', 'scholarship_offer']:
        data[c] = pd.to_numeric(data[c], errors='raise')
        if not np.isfinite(data[c]).all():
            raise ValueError(f'Non-finite numeric input: {c}')
    if (data.followers < 0).any() or not data.scholarship_offer.isin([0, 1]).all():
        raise ValueError('Followers must be nonnegative and offer must be 0/1')
    for c in ['decision_source_url', 'social_source_url', 'performance_source_url']:
        if not data[c].astype(str).str.match(r'^https?://\S+$').all():
            raise ValueError(f'Need public evidence URLs in {c}')
    if data.duplicated(['athlete_id', 'school', 'decision_date']).any():
        raise ValueError('Duplicate athlete-school-decision observations')
    data['post'] = (data.decision_date >= CUTOFF).astype(int)
    if data.post.nunique() < 2:
        raise ValueError('Both pre- and post-July 1, 2021 observations are required')
    if data.groupby('post').scholarship_offer.nunique().min() < 2:
        raise ValueError('Need offered and non-offered athletes in BOTH periods')
    data['log_followers'] = np.log1p(data.followers)
    if data.groupby('post').log_followers.nunique().min() < 2:
        raise ValueError('Need follower variation within each period')
    data['year_c'] = data.decision_date.dt.year - 2021
    return data


def fit(data):
    data = validate(data)
    if data.sport.nunique() != 1:
        raise ValueError('Fit each sport separately; athletic-score scales may differ')
    formula = ('scholarship_offer ~ log_followers * post + athletic_score '
               '+ C(position) + C(school) + year_c')
    model = smf.ols(formula, data, missing='raise')
    x = model.exog
    if len(data) <= x.shape[1] + 5 or np.linalg.matrix_rank(x) < x.shape[1]:
        raise ValueError('Insufficient observations or rank-deficient controls; expand the sample')
    # Athlete clustering handles repeated applications/offers within a recruit.
    # School dependence is still a limitation; two-way inference needs enough
    # independent athlete and school clusters, not merely many rows.
    if data.athlete_id.nunique() < 30:
        raise ValueError('Fewer than 30 athlete clusters; this workflow requires more for inference')
    return model.fit(cov_type='cluster', cov_kwds={'groups': data.athlete_id}, use_t=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--sport', choices=['football', 'basketball'], required=True)
    parser.add_argument('--outdir', type=Path, default=Path(__file__).resolve().parents[1] / 'reports/prepost')
    args = parser.parse_args()
    data = pd.read_csv(args.input, dtype={'athlete_id': str})
    if 'sport' not in data:
        parser.error('Missing sport column')
    try:
        model = fit(data.loc[data.sport.eq(args.sport)])
    except ValueError as exc:
        parser.exit(1, f'Analysis stopped: {exc}\n')
    args.outdir.mkdir(parents=True, exist_ok=True)
    output = pd.DataFrame({'coefficient': model.params, 'standard_error': model.bse,
                           'p_two_sided': model.pvalues, 'ci95_low': model.conf_int()[0],
                           'ci95_high': model.conf_int()[1]})
    output.to_csv(args.outdir / f'{args.sport}_coefficients.csv')
    (args.outdir / f'{args.sport}_summary.txt').write_text(
        'OBSERVATIONAL linear probability model, athlete-clustered errors.\n'
        'log_followers:post tests a change in association, not causality.\n'
        'School dependence, period confounding and offer-reporting bias remain.\n\n' + model.summary().as_text())
    print(output.loc['log_followers:post'])
