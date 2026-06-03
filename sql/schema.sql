
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
