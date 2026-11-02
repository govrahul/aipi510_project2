import os
import urllib3
import requests
import cfbd
import dotenv
import numpy as np
import pandas as pd
from thefuzz import process

"""
This script processes 'NIL and Player History Data - Football Sample.csv', pulls PPA 
from the CFBD API using direct requests with SSL bypass, applies fuzzy name matching, 
creates freshman interaction terms, log-transforms social reach and valuation, 
and outputs the final dataset to Data/football_modeling_data.csv.

Returns: Data/football_modeling_data.csv
Requires: CFBD API Key in a .env file, NIL and Player History Data - Football Sample.csv
"""

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 1. Load Environment Variables (.env file in root directory)
dotenv.load_dotenv()
cfbd_api_key = os.getenv("CFBD_KEY")

# Clean up any accidental quotes or whitespace
if cfbd_api_key:
    cfbd_api_key = cfbd_api_key.strip('"').strip("'").strip()

# 2. Configure CFBD API client and fetch player season PPA
df_ppa = pd.DataFrame(columns=["cfbd_name", "cfbd_team", "PPA_Per_Play"])

if cfbd_api_key:
    try:
        print("Fetching seasonal PPA data directly from CFBD API...")
        url = "https://api.collegefootballdata.com/ppa/players/season"
        
        # Ensure 'Bearer ' prefix is cleanly formatted
        auth_value = cfbd_api_key if cfbd_api_key.startswith("Bearer ") else f"Bearer {cfbd_api_key}"
        
        headers = {
            "Authorization": auth_value,
            "Accept": "application/json"
        }
        params = {
            "year": 2025,
            "threshold": 1
        }

        session = requests.Session()
        session.verify = False

        response = session.get(url, headers=headers, params=params, timeout=15)
        
        print(f"API Response Status Code: {response.status_code}") # Debug print

        if response.status_code == 200:
            ppa_data = response.json()
            ppa_list = []
            for p in ppa_data:
                name = p.get("name")
                team = p.get("team")
                avg_table = p.get("averagePPA", {}) or p.get("average_ppa", {}) or p.get("averageTable", {}) or p.get("average_table", {})
                all_ppa = avg_table.get("all") if isinstance(avg_table, dict) else p.get("total")
                
                ppa_list.append({
                    "cfbd_name": name,
                    "cfbd_team": team,
                    "PPA_Per_Play": all_ppa
                })
                
            df_ppa = pd.DataFrame(ppa_list)
            print(f"Successfully retrieved PPA data for {len(df_ppa)} players from API!")
        else:
            print(f"CFBD API Error Response: {response.text}")

    except Exception as e:
        print(f"Notice: Could not fetch from CFBD API ({e}).")

# 3. Load local quota sample dataset
input_path = "Data/NIL and Player History Data - Football Sample.csv"
if not os.path.exists(input_path):
    input_path = "NIL and Player History Data - Football Sample.csv"

df_sample = pd.read_csv(input_path)

# 4. Initialize modeling columns & Handle Freshmen with Fuzzy Matching
df_sample["PPA_Per_Play"] = 0.0
df_sample["Freshman_Flag"] = 0

matched_count = 0
unmatched_players = []

for idx, row in df_sample.iterrows():
    grade = str(row["Grade"]).strip()
    if "Freshman" in grade:
        df_sample.loc[idx, "Freshman_Flag"] = 1
        df_sample.loc[idx, "PPA_Per_Play"] = 0.0  # Zero out PPA for true freshmen
    else:
        player_name = str(row["Player Name"]).strip()
        if not df_ppa.empty:
            # Try exact match first
            exact_match = df_ppa[
                df_ppa["cfbd_name"].astype(str).str.lower() == player_name.lower()
            ]
            if not exact_match.empty:
                df_sample.loc[idx, "PPA_Per_Play"] = exact_match.iloc[0]["PPA_Per_Play"]
                matched_count += 1
            else:
                # Fall back to fuzzy matching (score threshold >= 85)
                cfbd_names_list = df_ppa["cfbd_name"].astype(str).tolist()
                best_match, score = process.extractOne(player_name, cfbd_names_list)
                if score >= 85:
                    matched_row = df_ppa[df_ppa["cfbd_name"] == best_match]
                    df_sample.loc[idx, "PPA_Per_Play"] = matched_row.iloc[0]["PPA_Per_Play"]
                    matched_count += 1
                else:
                    unmatched_players.append(player_name)
                    df_sample.loc[idx, "PPA_Per_Play"] = 0.0

print(f"Successfully matched {matched_count} veteran players.")
if unmatched_players:
    print(f"Unmatched players (defaulted to 0 PPA): {unmatched_players}")

# Fill any remaining missing PPA values with 0.0
df_sample["PPA_Per_Play"] = df_sample["PPA_Per_Play"].fillna(0.0)

# 5. Create Freshman Interaction Term & Log Transformations
df_sample["Freshman_X_Stars"] = (
    df_sample["Freshman_Flag"] * df_sample["Star Rating"]
)
df_sample["Log_Instagram"] = np.log1p(df_sample["Instagram Followers"])
df_sample["Log_Valuation"] = np.log(df_sample["Valuation"])

# 6. Create Control Dummies
power_4 = ["SEC", "Big Ten", "ACC", "Big 12"]
df_sample["Power_4_Dummy"] = df_sample["Conference"].isin(power_4).astype(int)

premium_positions = ["QB", "DE", "EDGE", "WR", "RB"]
df_sample["Premium_Position"] = (
    df_sample["Position"].isin(premium_positions).astype(int)
)

# 7. Ensure output directory exists and save final file
output_dir = "Data"
if not os.path.exists(output_dir):
    os.makedirs(output_dir, exist_ok=True)

output_path = os.path.join(output_dir, "football_modeling_data.csv")
df_sample.to_csv(output_path, index=False)

print(f"Successfully processed {len(df_sample)} players!")
print(f"Saved modeling-ready dataset to: {output_path}")
print(
    df_sample[
        [
            "Player Name",
            "Grade",
            "Star Rating",
            "Freshman_Flag",
            "Freshman_X_Stars",
            "Log_Instagram",
            "Log_Valuation",
        ]
    ].head()
)