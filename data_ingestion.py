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