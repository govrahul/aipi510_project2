"""
This file pulls the top 1000 for a given sport and quota samples it.

Returns: CSV with 100 sampled players
Requires: file in Data/ with top 1000 players
"""

import pandas as pd
import numpy as np

RANDOM_SEED = 510

def assign_tier_and_sample(data, random_seed, sport, valuation_col='Valuation'):
    # clean valuation to actual numbers
    cleaned = (
        data[valuation_col].str.replace("$", "", regex=False).str.strip().str.upper()
    )

    # Use regex to extract the number and the suffix separately
    # r'^([\d\.]+)([KM]?)$' matches:
    # Group 1: digits and decimal points ([\d\.]+)
    # Group 2: optional letter K, M at the end ([KM]?)
    extracted = cleaned.str.extract(r"^([\d\.]+)([KM]?)$")

    # Convert numbers to float and map multipliers
    nums = extracted[0].astype(float)
    multipliers = extracted[1].map({"K": 1e3, "M": 1e6}).fillna(1)

    # Calculate raw value and assign to new column
    data["raw_val"] = nums * multipliers
    
    p75 = np.percentile(data['raw_val'], 75)
    p25 = np.percentile(data['raw_val'], 25)

    print(f"Top 25% cutoff: ${p75:,.2f}")
    print(f"Bottom 25% cutoff: ${p25:,.2f}")

    def assign_tier(val):
        if val >= p75:
            return "Top_25"
        elif val <= p25:
            return "Bottom_25"
        else:
            return "Middle_50"


    data["Valuation_Tier"] = data['raw_val'].apply(assign_tier)

    np.random.seed(random_seed)

    sample_top = data[data["Valuation_Tier"] == "Top_25"].sample(n=25)
    sample_mid = data[data["Valuation_Tier"] == "Middle_50"].sample(n=50)
    sample_bot = data[data["Valuation_Tier"] == "Bottom_25"].sample(n=25)

    # Combine into final N=100 evaluation dataset
    df_sample_100 = (
        pd.concat([sample_top, sample_mid, sample_bot])
        .reset_index(drop=True)
    )

    df_sample_100 = pd.DataFrame(df_sample_100)
    df_sample_100.to_csv(f"Data/{sport}_sample_100.csv")

    print(f"Saved sampled data to Data/{sport}_sample_100.csv")

if __name__ == "__main__":
    SPORT = "football" # change with sport you want to sample
    data = pd.read_csv(f"Data/{SPORT}_top1000.csv")

    assign_tier_and_sample(data=data, random_seed=RANDOM_SEED, sport=SPORT)