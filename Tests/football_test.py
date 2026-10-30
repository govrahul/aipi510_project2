import os
import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf

"""
Football NIL Econometric OLS Regression Analysis
-----------------------------------------------------------------------------
Model Specification:
    Log(Valuation) = B0 
                   + B1 * Log(Instagram Followers) 
                   + B2 * PPA Per Play 
                   + B3 * Freshman Flag 
                   + B4 * (Freshman Flag * Star Rating) 
                   + B5 * Power 4 Conference Dummy 
                   + B6 * Premium Position Dummy 
                   + e
"""

# 1. Load Modeling Dataset
data_path = "Data/football_modeling_data.csv"
if not os.path.exists(data_path):
    data_path = "../Data/football_modeling_data.csv"

if not os.path.exists(data_path):
    raise FileNotFoundError(
        f"Could not locate modeling dataset at {data_path}. "
        "Please run your 'football_add_stats.py' script first."
    )

df = pd.read_csv(data_path)
print(f"Successfully loaded dataset from {data_path} with {len(df)} observations.")

# 2. Define the OLS Regression Formula
formula = (
    "Log_Valuation ~ Log_Instagram + PPA_Per_Play + "
    "Freshman_Flag + Freshman_X_Stars + Power_4_Dummy + Premium_Position"
)

# 3. Fit the Ordinary Least Squares (OLS) Model
model = smf.ols(formula, data=df).fit()

# 4. Print Full Regression Results Summary
print("\n" + "=" * 75)
print(" FOOTBALL NIL IMPACT: SOCIAL REACH VS. ON-FIELD PERFORMANCE (OLS)")
print("=" * 75)
print(model.summary())

# 5. Print Key Economic Takeaways & Fit Metrics
print("\n" + "-" * 75)
print(f"Model Summary Statistics:")
print(f" * Number of Observations (N): {int(model.nobs)}")
print(f" * R-squared ($R^2$):           {model.rsquared:.4f}")
print(f" * Adjusted $R^2$:              {model.rsquared_adj:.4f}")
print(f" * F-statistic:                {model.fvalue:.4f} (p-value: {model.f_pvalue:.4e})")
print("-" * 75)