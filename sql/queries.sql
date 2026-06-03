
-- Q1_top5_funds_by_aum

SELECT fp.amfi_code, df.scheme_name, df.fund_house, df.category, fp.aum_crore
FROM fact_performance fp
JOIN dim_fund df ON fp.amfi_code = df.amfi_code
ORDER BY fp.aum_crore DESC
LIMIT 5;


-- Q2_avg_nav_per_month

SELECT dd.year, dd.month, dd.month_name, ROUND(AVG(fn.nav), 4) AS avg_nav
FROM fact_nav fn
JOIN dim_date dd ON fn.date_key = dd.date_key
WHERE dd.is_weekend = 0
GROUP BY dd.year, dd.month
ORDER BY dd.year, dd.month;


-- Q3_sip_yoy_growth

SELECT year, ROUND(SUM(sip_inflow_crore), 2) AS total_sip_crore
FROM (
    SELECT CAST(SUBSTR(month, 1, 4) AS INTEGER) AS year, sip_inflow_crore
    FROM fact_sip_inflows
)
GROUP BY year
ORDER BY year;


-- Q4_transactions_by_state

SELECT state, COUNT(*) AS num_transactions,
ROUND(SUM(amount_inr) / 1e7, 2) AS total_amount_crore,
ROUND(AVG(amount_inr), 2) AS avg_amount_inr
FROM fact_transactions
GROUP BY state
ORDER BY total_amount_crore DESC;


-- Q5_low_expense_funds

SELECT df.amfi_code, df.scheme_name, df.fund_house, df.plan,
fp.expense_ratio_pct, fp.return_3yr_pct, fp.sharpe_ratio
FROM fact_performance fp
JOIN dim_fund df ON fp.amfi_code = df.amfi_code
WHERE fp.expense_ratio_pct < 1.0
ORDER BY fp.return_3yr_pct DESC;


-- Q6_monthly_sip_vs_redemption

SELECT year, month,
ROUND(SUM(CASE WHEN transaction_type = 'SIP' THEN amount_inr ELSE 0 END)/1e7, 2) AS sip_crore,
ROUND(SUM(CASE WHEN transaction_type = 'Lumpsum' THEN amount_inr ELSE 0 END)/1e7, 2) AS lumpsum_crore,
ROUND(SUM(CASE WHEN transaction_type = 'Redemption' THEN amount_inr ELSE 0 END)/1e7, 2) AS redemption_crore
FROM fact_transactions
WHERE year >= 2024
GROUP BY year, month
ORDER BY year, month;


-- Q7_top_performing_funds_sharpe

SELECT df.scheme_name, df.fund_house, df.category,
fp.sharpe_ratio, fp.return_3yr_pct, fp.morningstar_rating
FROM fact_performance fp
JOIN dim_fund df ON fp.amfi_code = df.amfi_code
ORDER BY fp.sharpe_ratio DESC
LIMIT 10;


-- Q8_kyc_pending_amount

SELECT kyc_status, transaction_type,
COUNT(*) AS num_txns,
ROUND(SUM(amount_inr)/1e7, 2) AS amount_crore
FROM fact_transactions
GROUP BY kyc_status, transaction_type
ORDER BY kyc_status, transaction_type;


-- Q9_nav_52w_high_low

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


-- Q10_city_tier_investment_profile

SELECT city_tier, age_group, transaction_type,
COUNT(*) AS txn_count,
ROUND(AVG(amount_inr), 2) AS avg_amount_inr,
ROUND(SUM(amount_inr)/1e7, 2) AS total_crore
FROM fact_transactions
GROUP BY city_tier, age_group, transaction_type
ORDER BY city_tier, total_crore DESC;

