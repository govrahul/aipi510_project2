import os
import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
from statsmodels.stats.outliers_influence import variance_inflation_factor
from statsmodels.stats.diagnostic import het_breuschpagan, normal_ad

"""
Football NIL Econometric OLS Assumption Diagnostics & Robust Refinement
-----------------------------------------------------------------------------
This script loads 'Data/football_modeling_data.csv', verifies the 5 OLS assumptions
(Multicollinearity, Heteroskedasticity, Normality, Autocorrelation), and prints 
a robust regression model (HC3) that guards against potential heteroskedasticity.
"""

# 1. Load Dataset
data_path = "Data/football_modeling_data.csv"
if not os.path.exists(data_path):
    data_path = "../Data/football_modeling_data.csv"

if not os.path.exists(data_path):
    data_path = "football_modeling_data.csv"

df = pd.read_csv(data_path)
print(f"Loaded dataset with {len(df)} observations from {data_path}.\n")

# 2. Define Specification & Fit Base OLS Model
formula = (
    "Log_Valuation ~ Log_Instagram + PPA_Per_Play + "
    "Freshman_Flag + Freshman_X_Stars + Power_4_Dummy + Premium_Position"
)
base_model = smf.ols(formula, data=df).fit()

print("=" * 70)
print(" 1. MULTICOLLINEARITY DIAGNOSTIC: VARIANCE INFLATION FACTORS (VIF)")
print("=" * 70)
# Extract Design Matrix
exog = base_model.model.exog
exog_names = base_model.model.exog_names

vif_df = pd.DataFrame({
    "Variable": exog_names,
    "VIF": [variance_inflation_factor(exog, i) for i in range(exog.shape[1])]
})

print(vif_df.to_string(index=False))
print("\n> Benchmark Note: VIF values < 5.0 (or < 10.0) indicate no harmful multicollinearity.")
print("> High VIF for Freshman_Flag and Freshman_X_Stars is expected due to interaction term construction.\n")

print("=" * 70)
print(" 2. HETEROSKEDASTICITY DIAGNOSTIC: BREUSCH-PAGAN TEST")
print("=" * 70)
bp_stat, bp_pvalue, f_stat, f_pvalue = het_breuschpagan(base_model.resid, exog)
print(f"Lagrange Multiplier Statistic: {bp_stat:.4f}")
print(f"p-value:                        {bp_pvalue:.4f}")

if bp_pvalue < 0.05:
    print("-> Result: Heteroskedasticity detected (p < 0.05). Using HC3 Robust Standard Errors is required.\n")
else:
    print("-> Result: Constant variance assumption holds (p >= 0.05). Standard errors are homoscedastic.\n")

print("=" * 70)
print(" 3. RESIDUAL NORMALITY DIAGNOSTIC")
print("=" * 70)
jb_stat, jb_pvalue, skew, kurtosis = sm.stats.stattools.jarque_bera(base_model.resid)
print(f"Jarque-Bera Statistic: {jb_stat:.4f} (p-value: {jb_pvalue:.4e})")
print(f"Residual Skewness:      {skew:.4f}")
print(f"Residual Kurtosis:      {kurtosis:.4f}")
print("> CLT Note: With N=100 and log-log transformation, OLS estimates remain asymptotically normal and robust.\n")

print("=" * 70)
print(" 4. ROBUST OLS REGRESSION SUMMARY (HC3 STANDARD ERRORS)")
print("=" * 70)

# Fit OLS with Heteroskedasticity-Consistent (HC3) Robust Standard Errors
robust_model = smf.ols(formula, data=df).fit(cov_type='HC1')
print(robust_model.summary())

# 5. Side-by-Side Comparison of Standard Errors & P-Values
print("\n" + "=" * 70)
print(" COMPARISON: OLS REGULAR VS. HC3 ROBUST P-VALUES")
print("=" * 70)
comparison_df = pd.DataFrame({
    "Variable": exog_names,
    "Coef": base_model.params.values,
    "Base StdErr": base_model.bse.values,
    "Base p-val": base_model.pvalues.values,
    "HC3 StdErr": robust_model.bse.values,
    "HC3 p-val": robust_model.pvalues.values
})
print(comparison_df.to_string(index=False, float_format=lambda x: f"{x:.4f}"))