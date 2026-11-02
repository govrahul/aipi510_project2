import numpy as np
from statsmodels.stats.power import FTestPowerF2

# ==========================================
# GLOBAL HYPERPARAMETERS & ASSUMPTIONS
# ==========================================
ALPHA = 0.05 / 3  # Significance level (Type I error rate)
POWER = 0.80  # Target statistical power (1 - Type II error rate)
EXPECTED_R2 = 0.35  # Empirical literature benchmark for NIL OLS models

# Convert R-squared to Cohen's f-squared: f^2 = R^2 / (1 - R^2)
f2_effect = EXPECTED_R2 / (1 - EXPECTED_R2)  # f^2 ~ 0.5385 (Large Effect Size)


def calculate_sample_size(num_predictors, test_name):
    """Calculates denominator degrees of freedom and total required sample size N.

    Formula: N = df_denom + u + 1
    """
    # 1. Solve for denominator degrees of freedom (df_denom)
    df_denom = FTestPowerF2().solve_power(
        effect_size=f2_effect, df_num=num_predictors, alpha=ALPHA, power=POWER
    )

    # 2. Total N calculation
    total_N = df_denom + num_predictors + 1
    rounded_N = int(np.ceil(total_N))

    print(f"=== {test_name} ===")
    print(f"Predictors (u): {num_predictors}")
    print(f"Cohen's f^2: {f2_effect:.4f} (Derived from target R^2 = {EXPECTED_R2})")
    print(f"Residual Degrees of Freedom (df_denom): {df_denom:.2f}")
    print(f"Minimum Required Sample Size (N): {rounded_N} players\n")

    return rounded_N


# ==========================================
# EXECUTE POWER ANALYSIS FOR ALL 3 TESTS
# ==========================================

# Test 1: Football Model (6 predictors: Social Reach, Performance, Freshman Flag, Freshman*Stars Interaction, Premium Position, Conference)
n_football = calculate_sample_size(
    num_predictors=6, test_name="Test 1: Football OLS Model"
)

# Test 2: Basketball Model (6 predictors: Social Reach, Performance, Freshman Flag, Freshman*Stars Interaction, Role Tier, Conference)
n_basketball = calculate_sample_size(
    num_predictors=6, test_name="Test 2: Basketball OLS Model"
)

# Test 3: Comparison Interaction Model (8 predictors: Social, Sport Dummy, Interaction, Perf, Freshman Flag, Freshman*Stars Interaction, Role/Pos, Conference)
n_interaction = calculate_sample_size(
    num_predictors=8, test_name="Test 3: Cross-Sport Interaction Model"
)