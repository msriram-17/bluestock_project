import pandas as pd
import os

dataset_folder = "data/raw"

print("BLUESTOCK DATA INGESTION PROJECT")
print("=" * 70)

for file in sorted(os.listdir(dataset_folder)):

    if file.endswith(".csv"):

        file_path = os.path.join(dataset_folder, file)

        try:
            df = pd.read_csv(file_path)

            print("\n" + "=" * 70)
            print(f"Dataset: {file}")

            print("\nShape:")
            print(df.shape)

            print("\nData Types:")
            print(df.dtypes)

            print("\nFirst 5 Rows:")
            print(df.head())

            print("\nMissing Values:")
            print(df.isnull().sum())

        except Exception as e:
            print(f"Error reading {file}: {e}")

print("\nAll datasets loaded successfully!")