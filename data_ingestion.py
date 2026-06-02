import requests
import pandas as pd

# Fetch fund master data from mfapi.in
url = "https://api.mfapi.in/mf"
response = requests.get(url)
data = response.json()

# Convert to DataFrame
df = pd.DataFrame(data)
print("Shape:", df.shape)
print("\nColumns:", df.columns.tolist())
print("\nFirst 5 rows:")
print(df.head())

# Print unique scheme names
print("\nTotal Schemes:", df['schemeName'].nunique())

# Save as raw CSV
df.to_csv('data/raw/fund_master.csv', index=False)
print("\nFund master saved successfully!")
# Task 7 - Validate AMFI codes
# Load fund master and nav history
fund_master = pd.read_csv('data/raw/fund_master.csv')

# Load one of the nav files we already have
nav_history = pd.read_csv('data/raw/SBI_Bluechip_nav.csv')

# Get all scheme codes from fund master
fund_master_codes = set(fund_master['schemeCode'].astype(str))

print("\n--- Data Quality Summary ---")
print(f"Total schemes in fund master: {len(fund_master)}")
print(f"Total NAV records in SBI Bluechip: {len(nav_history)}")
print(f"Sample NAV data:")
print(nav_history.head())
print("\nData quality check complete!")
import os

# Task 3 - Load all 10 CSV files
print("\n--- Loading all 10 CSV datasets ---")
csv_folder = 'data/raw'
csv_files = os.listdir(csv_folder)

for file in csv_files:
    if file.endswith('.csv'):
        df = pd.read_csv(f'{csv_folder}/{file}')
        print(f"\n📂 File: {file}")
        print(f"Shape: {df.shape}")
        print(f"Dtypes:\n{df.dtypes}")
        print(f"Head:\n{df.head()}")
        print("-"*50)
# Task 6 - Explore fund master properly
print("\n--- Fund Master Exploration ---")
fund_df = pd.read_csv('data/raw/fund_master.csv')

# Print unique fund houses from scheme names
print(f"Total Schemes: {len(fund_df)}")
print(f"\nSample Scheme Names:")
print(fund_df['schemeName'].head(10).tolist())

# Extract fund houses from scheme names
print(f"\nTotal Unique Scheme Codes: {fund_df['schemeCode'].nunique()}")
print(f"\nISIN Growth - Null count: {fund_df['isinGrowth'].isna().sum()}")
print(f"ISIN DivReinvestment - Null count: {fund_df['isinDivReinvestment'].isna().sum()}")

# Task 7 - Validate AMFI codes properly
print("\n--- AMFI Code Validation ---")
fund_codes = set(fund_df['schemeCode'].astype(str))

# Our fetched scheme codes
fetched_codes = {'119551', '120503', '118632', '119092', '120841', '125497', '118834', '119364'}

# Check if all fetched codes exist in fund master
print("\nValidating fetched scheme codes against fund master:")
for code in fetched_codes:
    if code in fund_codes:
        print(f"✅ Scheme {code} exists in fund master")
    else:
        print(f"❌ Scheme {code} NOT found in fund master")

print("\n--- Data Quality Summary ---")
print(f"Total schemes in fund master: {len(fund_df)}")
print(f"Total fetched NAV schemes: {len(fetched_codes)}")
print(f"All codes validated: {fetched_codes.issubset(fund_codes)}")
print(f"Missing ISIN Growth: {fund_df['isinGrowth'].isna().sum()}")
print(f"Missing ISIN DivReinvestment: {fund_df['isinDivReinvestment'].isna().sum()}")