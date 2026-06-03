import pandas as pd
import sqlite3
import os
from pathlib import Path
from sqlalchemy import create_engine, text

# ─────────────────────────────────────────────
# PATHS
# ─────────────────────────────────────────────
RAW      = Path("data/raw")
PROC     = Path("data/processed")
DB_PATH  = Path("db/bluestock_mf.db")
SQL_DIR  = Path("sql")
DOCS_DIR = Path("docs")

# ─────────────────────────────────────────────
# SECTION 1 — CLEAN NAV HISTORY
# ─────────────────────────────────────────────
print("\n[1/10] Cleaning 02_nav_history.csv ...")

nav = pd.read_csv(RAW / "02_nav_history.csv")
nav["date"] = pd.to_datetime(nav["date"])
nav = nav.sort_values(["amfi_code", "date"]).reset_index(drop=True)

before = len(nav)
nav = nav.drop_duplicates(subset=["amfi_code", "date"], keep="last")
print(f"   Duplicates removed: {before - len(nav)}")

nav_pivot = nav.pivot(index="date", columns="amfi_code", values="nav")
all_dates  = pd.date_range(nav_pivot.index.min(), nav_pivot.index.max(), freq="D")
nav_pivot  = nav_pivot.reindex(all_dates).ffill()
nav = nav_pivot.reset_index().melt(id_vars="index", var_name="amfi_code", value_name="nav")
nav.rename(columns={"index": "date"}, inplace=True)
nav = nav.dropna(subset=["nav"])

invalid_nav = nav[nav["nav"] <= 0]
print(f"   NAV <= 0 records: {len(invalid_nav)} (removed)")
nav = nav[nav["nav"] > 0]

nav["year"]  = nav["date"].dt.year
nav["month"] = nav["date"].dt.month
nav["is_weekend"] = nav["date"].dt.dayofweek >= 5

nav.to_csv(PROC / "nav_history_clean.csv", index=False)
print(f"   Saved {len(nav):,} rows -> nav_history_clean.csv")

# ─────────────────────────────────────────────
# SECTION 2 — CLEAN INVESTOR TRANSACTIONS
# ─────────────────────────────────────────────
print("\n[2/10] Cleaning 08_investor_transactions.csv ...")

txn = pd.read_csv(RAW / "08_investor_transactions.csv")

type_map = {
    "sip": "SIP", "Sip": "SIP",
    "lumpsum": "Lumpsum", "LUMPSUM": "Lumpsum",
    "redemption": "Redemption", "REDEMPTION": "Redemption",
}
txn["transaction_type"] = txn["transaction_type"].replace(type_map)

before = len(txn)
txn = txn[txn["amount_inr"] > 0]
print(f"   amount_inr <= 0 removed: {before - len(txn)}")

txn["transaction_date"] = pd.to_datetime(txn["transaction_date"], dayfirst=False)

valid_kyc = {"Verified", "Pending", "Rejected"}
bad_kyc = txn[~txn["kyc_status"].isin(valid_kyc)]
print(f"   Invalid KYC values: {len(bad_kyc)}")

txn["year"]  = txn["transaction_date"].dt.year
txn["month"] = txn["transaction_date"].dt.month

txn.to_csv(PROC / "investor_transactions_clean.csv", index=False)
print(f"   Saved {len(txn):,} rows -> investor_transactions_clean.csv")

# ─────────────────────────────────────────────
# SECTION 3 — CLEAN SCHEME PERFORMANCE
# ─────────────────────────────────────────────
print("\n[3/10] Cleaning 07_scheme_performance.csv ...")

perf = pd.read_csv(RAW / "07_scheme_performance.csv")

return_cols = ["return_1yr_pct", "return_3yr_pct", "return_5yr_pct",
               "benchmark_3yr_pct", "alpha", "beta", "sharpe_ratio",
               "sortino_ratio", "std_dev_ann_pct", "max_drawdown_pct"]

for col in return_cols:
    perf[col] = pd.to_numeric(perf[col], errors="coerce")

for col in ["return_1yr_pct", "return_3yr_pct", "return_5yr_pct"]:
    anomalies = perf[(perf[col] < -30) | (perf[col] > 60)]
    print(f"   {col} anomalies: {len(anomalies)}")
    perf[f"{col}_flag"] = ((perf[col] < -30) | (perf[col] > 60))

out_of_range = perf[(perf["expense_ratio_pct"] < 0.1) | (perf["expense_ratio_pct"] > 2.5)]
print(f"   expense_ratio out of range: {len(out_of_range)}")
perf["expense_ratio_flag"] = ((perf["expense_ratio_pct"] < 0.1) | (perf["expense_ratio_pct"] > 2.5))

perf.to_csv(PROC / "scheme_performance_clean.csv", index=False)
print(f"   Saved {len(perf):,} rows -> scheme_performance_clean.csv")

# ─────────────────────────────────────────────
# SECTION 4 — CLEAN REMAINING 7 CSV FILES
# ─────────────────────────────────────────────
print("\n[4/10] Cleaning remaining CSV files ...")

remaining = {
    "01_fund_master.csv":         "fund_master_clean.csv",
    "03_aum_by_fund_house.csv":   "aum_by_fund_house_clean.csv",
    "04_monthly_sip_inflows.csv": "monthly_sip_inflows_clean.csv",
    "05_category_inflows.csv":    "category_inflows_clean.csv",
    "06_industry_folio_count.csv":"industry_folio_count_clean.csv",
    "09_portfolio_holdings.csv":  "portfolio_holdings_clean.csv",
    "10_benchmark_indices.csv":   "benchmark_indices_clean.csv",
}

date_cols_map = {
    "01_fund_master.csv":         ["launch_date"],
    "03_aum_by_fund_house.csv":   ["date"],
    "04_monthly_sip_inflows.csv": ["month"],
    "05_category_inflows.csv":    ["month"],
    "06_industry_folio_count.csv":["month"],
    "09_portfolio_holdings.csv":  ["portfolio_date"],
    "10_benchmark_indices.csv":   ["date"],
}

for src, dst in remaining.items():
    df = pd.read_csv(RAW / src)
    for col in date_cols_map.get(src, []):
        df[col] = pd.to_datetime(df[col], errors="coerce")
    df = df.drop_duplicates()
    df.to_csv(PROC / dst, index=False)
    print(f"   Saved {len(df):,} rows -> {dst}")

# ─────────────────────────────────────────────
# SECTION 5 — SQLITE STAR SCHEMA
# ─────────────────────────────────────────────
print("\n[5/10] Creating SQLite star schema ...")

DB_PATH.parent.mkdir(parents=True, exist_ok=True)
engine = create_engine(f"sqlite:///{DB_PATH}")

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS dim_fund (
    amfi_code           INTEGER PRIMARY KEY,
    fund_house          TEXT    NOT NULL,
    scheme_name         TEXT    NOT NULL,
    category            TEXT,
    sub_category        TEXT,
    plan                TEXT,
    launch_date         DATE,
    benchmark           TEXT,
    expense_ratio_pct   REAL,
    exit_load_pct       REAL,
    min_sip_amount      REAL,
    min_lumpsum_amount  REAL,
    fund_manager        TEXT,
    risk_category       TEXT,
    sebi_category_code  TEXT
);

CREATE TABLE IF NOT EXISTS dim_date (
    date_key    TEXT    PRIMARY KEY,
    year        INTEGER NOT NULL,
    quarter     INTEGER NOT NULL,
    month       INTEGER NOT NULL,
    month_name  TEXT    NOT NULL,
    week        INTEGER NOT NULL,
    day         INTEGER NOT NULL,
    day_name    TEXT    NOT NULL,
    is_weekend  INTEGER NOT NULL DEFAULT 0,
    is_month_end INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS fact_nav (
    nav_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    amfi_code   INTEGER NOT NULL REFERENCES dim_fund(amfi_code),
    date_key    TEXT    NOT NULL REFERENCES dim_date(date_key),
    nav         REAL    NOT NULL,
    is_weekend  INTEGER NOT NULL DEFAULT 0,
    UNIQUE(amfi_code, date_key)
);

CREATE TABLE IF NOT EXISTS fact_transactions (
    txn_id              INTEGER PRIMARY KEY AUTOINCREMENT,
    investor_id         TEXT    NOT NULL,
    transaction_date    TEXT    NOT NULL,
    amfi_code           INTEGER NOT NULL REFERENCES dim_fund(amfi_code),
    transaction_type    TEXT    NOT NULL,
    amount_inr          REAL    NOT NULL,
    state               TEXT,
    city                TEXT,
    city_tier           TEXT,
    age_group           TEXT,
    gender              TEXT,
    annual_income_lakh  REAL,
    payment_mode        TEXT,
    kyc_status          TEXT,
    year                INTEGER,
    month               INTEGER
);

CREATE TABLE IF NOT EXISTS fact_performance (
    perf_id             INTEGER PRIMARY KEY AUTOINCREMENT,
    amfi_code           INTEGER NOT NULL REFERENCES dim_fund(amfi_code),
    return_1yr_pct      REAL,
    return_3yr_pct      REAL,
    return_5yr_pct      REAL,
    benchmark_3yr_pct   REAL,
    alpha               REAL,
    beta                REAL,
    sharpe_ratio        REAL,
    sortino_ratio       REAL,
    std_dev_ann_pct     REAL,
    max_drawdown_pct    REAL,
    aum_crore           REAL,
    expense_ratio_pct   REAL,
    morningstar_rating  INTEGER,
    risk_grade          TEXT
);

CREATE TABLE IF NOT EXISTS fact_aum (
    aum_id          INTEGER PRIMARY KEY AUTOINCREMENT,
    date_key        TEXT    NOT NULL,
    fund_house      TEXT    NOT NULL,
    aum_lakh_crore  REAL,
    aum_crore       REAL,
    num_schemes     INTEGER
);

CREATE TABLE IF NOT EXISTS fact_sip_inflows (
    sip_id                    INTEGER PRIMARY KEY AUTOINCREMENT,
    month                     TEXT    NOT NULL,
    sip_inflow_crore          REAL,
    active_sip_accounts_crore REAL,
    new_sip_accounts_lakh     REAL,
    sip_aum_lakh_crore        REAL,
    yoy_growth_pct            REAL
);

CREATE TABLE IF NOT EXISTS dim_benchmark (
    bench_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    date_key    TEXT    NOT NULL,
    index_name  TEXT    NOT NULL,
    close_value REAL    NOT NULL
);
"""

with engine.connect() as conn:
    for stmt in SCHEMA_SQL.strip().split(";"):
        stmt = stmt.strip()
        if stmt:
            conn.execute(text(stmt))
    conn.commit()

with open(SQL_DIR / "schema.sql", "w") as f:
    f.write(SCHEMA_SQL)

print("   All tables created successfully!")
print("   schema.sql saved!")

# ─────────────────────────────────────────────
# SECTION 6 — BUILD dim_date
# ─────────────────────────────────────────────
print("\n[6/10] Building dim_date ...")

dates = pd.date_range("2022-01-01", "2026-12-31", freq="D")
dim_date = pd.DataFrame({
    "date_key":    dates.strftime("%Y-%m-%d"),
    "year":        dates.year,
    "quarter":     dates.quarter,
    "month":       dates.month,
    "month_name":  dates.strftime("%B"),
    "week":        dates.isocalendar().week.astype(int),
    "day":         dates.day,
    "day_name":    dates.strftime("%A"),
    "is_weekend":  (dates.dayofweek >= 5).astype(int),
    "is_month_end":(dates == dates.to_period("M").to_timestamp("M")).astype(int),
})

dim_date.to_sql("dim_date", engine, if_exists="replace", index=False)
print(f"   dim_date: {len(dim_date):,} rows loaded!")

# ─────────────────────────────────────────────
# SECTION 7 — LOAD ALL DATA INTO SQLITE
# ─────────────────────────────────────────────
print("\n[7/10] Loading all cleaned data into SQLite ...")

# dim_fund
fund = pd.read_csv(PROC / "fund_master_clean.csv")
fund.to_sql("dim_fund", engine, if_exists="replace", index=False)
print(f"   dim_fund: {len(fund):,} rows")

# fact_nav
nav_clean = pd.read_csv(PROC / "nav_history_clean.csv", parse_dates=["date"])
nav_clean["date_key"] = nav_clean["date"].dt.strftime("%Y-%m-%d")
fact_nav = nav_clean[["amfi_code", "date_key", "nav", "is_weekend"]].copy()
fact_nav = fact_nav.dropna(subset=["amfi_code", "date_key", "nav"])
fact_nav.to_sql("fact_nav", engine, if_exists="replace", index=False)
print(f"   fact_nav: {len(fact_nav):,} rows")

# fact_transactions
txn_clean = pd.read_csv(PROC / "investor_transactions_clean.csv", parse_dates=["transaction_date"])
txn_clean["transaction_date"] = txn_clean["transaction_date"].dt.strftime("%Y-%m-%d")
txn_clean.to_sql("fact_transactions", engine, if_exists="replace", index=False)
print(f"   fact_transactions: {len(txn_clean):,} rows")

# fact_performance
perf_clean = pd.read_csv(PROC / "scheme_performance_clean.csv")
perf_clean.to_sql("fact_performance", engine, if_exists="replace", index=False)
print(f"   fact_performance: {len(perf_clean):,} rows")

# fact_aum
aum = pd.read_csv(PROC / "aum_by_fund_house_clean.csv", parse_dates=["date"])
aum["date_key"] = aum["date"].dt.strftime("%Y-%m-%d")
aum.drop(columns=["date"], inplace=True)
aum.to_sql("fact_aum", engine, if_exists="replace", index=False)
print(f"   fact_aum: {len(aum):,} rows")

# fact_sip_inflows
sip = pd.read_csv(PROC / "monthly_sip_inflows_clean.csv", parse_dates=["month"])
sip["month"] = sip["month"].dt.strftime("%Y-%m-%d")
sip.to_sql("fact_sip_inflows", engine, if_exists="replace", index=False)
print(f"   fact_sip_inflows: {len(sip):,} rows")

# dim_benchmark
bench = pd.read_csv(PROC / "benchmark_indices_clean.csv", parse_dates=["date"])
bench["date_key"] = bench["date"].dt.strftime("%Y-%m-%d")
bench.drop(columns=["date"], inplace=True)
bench.to_sql("dim_benchmark", engine, if_exists="replace", index=False)
print(f"   dim_benchmark: {len(bench):,} rows")

# ─────────────────────────────────────────────
# SECTION 8 — 10 ANALYTICAL SQL QUERIES
# ─────────────────────────────────────────────
print("\n[8/10] Running 10 analytical queries ...")

QUERIES = {

"Q1_top5_funds_by_aum": """
SELECT fp.amfi_code, df.scheme_name, df.fund_house, df.category, fp.aum_crore
FROM fact_performance fp
JOIN dim_fund df ON fp.amfi_code = df.amfi_code
ORDER BY fp.aum_crore DESC
LIMIT 5;
""",

"Q2_avg_nav_per_month": """
SELECT dd.year, dd.month, dd.month_name, ROUND(AVG(fn.nav), 4) AS avg_nav
FROM fact_nav fn
JOIN dim_date dd ON fn.date_key = dd.date_key
WHERE dd.is_weekend = 0
GROUP BY dd.year, dd.month
ORDER BY dd.year, dd.month;
""",

"Q3_sip_yoy_growth": """
SELECT year, ROUND(SUM(sip_inflow_crore), 2) AS total_sip_crore
FROM (
    SELECT CAST(SUBSTR(month, 1, 4) AS INTEGER) AS year, sip_inflow_crore
    FROM fact_sip_inflows
)
GROUP BY year
ORDER BY year;
""",

"Q4_transactions_by_state": """
SELECT state, COUNT(*) AS num_transactions,
ROUND(SUM(amount_inr) / 1e7, 2) AS total_amount_crore,
ROUND(AVG(amount_inr), 2) AS avg_amount_inr
FROM fact_transactions
GROUP BY state
ORDER BY total_amount_crore DESC;
""",

"Q5_low_expense_funds": """
SELECT df.amfi_code, df.scheme_name, df.fund_house, df.plan,
fp.expense_ratio_pct, fp.return_3yr_pct, fp.sharpe_ratio
FROM fact_performance fp
JOIN dim_fund df ON fp.amfi_code = df.amfi_code
WHERE fp.expense_ratio_pct < 1.0
ORDER BY fp.return_3yr_pct DESC;
""",

"Q6_monthly_sip_vs_redemption": """
SELECT year, month,
ROUND(SUM(CASE WHEN transaction_type = 'SIP' THEN amount_inr ELSE 0 END)/1e7, 2) AS sip_crore,
ROUND(SUM(CASE WHEN transaction_type = 'Lumpsum' THEN amount_inr ELSE 0 END)/1e7, 2) AS lumpsum_crore,
ROUND(SUM(CASE WHEN transaction_type = 'Redemption' THEN amount_inr ELSE 0 END)/1e7, 2) AS redemption_crore
FROM fact_transactions
WHERE year >= 2024
GROUP BY year, month
ORDER BY year, month;
""",

"Q7_top_performing_funds_sharpe": """
SELECT df.scheme_name, df.fund_house, df.category,
fp.sharpe_ratio, fp.return_3yr_pct, fp.morningstar_rating
FROM fact_performance fp
JOIN dim_fund df ON fp.amfi_code = df.amfi_code
ORDER BY fp.sharpe_ratio DESC
LIMIT 10;
""",

"Q8_kyc_pending_amount": """
SELECT kyc_status, transaction_type,
COUNT(*) AS num_txns,
ROUND(SUM(amount_inr)/1e7, 2) AS amount_crore
FROM fact_transactions
GROUP BY kyc_status, transaction_type
ORDER BY kyc_status, transaction_type;
""",

"Q9_nav_52w_high_low": """
SELECT fn.amfi_code, df.scheme_name, df.category,
ROUND(MAX(fn.nav), 4) AS nav_52w_high,
ROUND(MIN(fn.nav), 4) AS nav_52w_low,
ROUND((MAX(fn.nav) - MIN(fn.nav)) / MIN(fn.nav) * 100, 2) AS range_pct
FROM fact_nav fn
JOIN dim_fund df ON fn.amfi_code = df.amfi_code
WHERE fn.date_key >= DATE('now', '-365 days')
AND fn.is_weekend = 0
GROUP BY fn.amfi_code
ORDER BY range_pct DESC;
""",

"Q10_city_tier_investment_profile": """
SELECT city_tier, age_group, transaction_type,
COUNT(*) AS txn_count,
ROUND(AVG(amount_inr), 2) AS avg_amount_inr,
ROUND(SUM(amount_inr)/1e7, 2) AS total_crore
FROM fact_transactions
GROUP BY city_tier, age_group, transaction_type
ORDER BY city_tier, total_crore DESC;
""",
}

all_queries_sql = ""
with engine.connect() as conn:
    for name, sql in QUERIES.items():
        df = pd.read_sql(text(sql), conn)
        all_queries_sql += f"\n-- {name}\n{sql}\n"
        print(f"\n   {name}")
        print(df.to_string(index=False))

with open(SQL_DIR / "queries.sql", "w") as f:
    f.write(all_queries_sql)

print("\n   queries.sql saved!")

print("\n" + "="*50)
print("DAY 2 COMPLETE!")
print(f"   Database : {DB_PATH}")
print(f"   Schema   : {SQL_DIR}/schema.sql")
print(f"   Queries  : {SQL_DIR}/queries.sql")
print(f"   Processed: {PROC}")
print("="*50)