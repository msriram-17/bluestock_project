"""
Bluestock Mutual Fund Analytics
Master Pipeline Execution Script
"""

import subprocess

scripts = [
    "data_ingestion.py",
    "live_nav_fetch.py",
    "day2_pipeline.py"
]

for script in scripts:
    print(f"\nRunning {script}...")
    subprocess.run(["python", script])

print("\nPipeline Execution Completed Successfully!")