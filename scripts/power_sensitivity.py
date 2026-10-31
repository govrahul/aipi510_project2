"""Plan power for ONE added social/interaction term, not the overall R-squared."""
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import f, ncf

ROOT = Path(__file__).resolve().parents[1]


def power(n, predictors, f2, tested=1, alpha=.05 / 3):
    """Fixed-design partial F approximation: lambda=N*f², df2=N-p-1.

    f²=(R²_full-R²_reduced)/(1-R²_full). Homoskedastic independent errors.
    This is a planning approximation, not power of an HC3/clustered Wald test.
    """
    df2 = n - predictors - 1
    if df2 <= 0:
        return np.nan
    return ncf.sf(f.isf(alpha, tested, df2), tested, df2, n * f2)


def required_n(predictors, f2, alpha=.05 / 3):
    for n in range(predictors + 3, 20001):
        if power(n, predictors, f2, alpha=alpha) >= .8:
            return n
    raise ValueError('Required sample exceeds search range')


if __name__ == '__main__':
    rows = [dict(total_predictors=p, tested_terms=1, partial_f2=effect,
                 alpha=.05 / 3, target_power=.8,
                 required_n=required_n(p, effect),
                 power_at_n100=power(100, p, effect))
            for p in [6, 8, 20] for effect in [.02, .05, .15, .35]]
    out = ROOT / 'reports/power_sensitivity.csv'
    out.parent.mkdir(exist_ok=True)
    pd.DataFrame(rows).to_csv(out, index=False)
    print(pd.DataFrame(rows).to_string(index=False))
