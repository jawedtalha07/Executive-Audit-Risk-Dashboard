DROP VIEW IF EXISTS v_agency_performance;
DROP VIEW IF EXISTS v_executive_kpi_summary;



CREATE VIEW v_agency_performance AS
WITH weekly_performance AS (
    SELECT
        f.agy_id,
        a.agy_name,
        f.week_ending,
        COUNT(DISTINCT f.cntr_id) AS active_cntrs,
        COUNT(f.timesheet_id)           AS total_timesheets,
        SUM(f.gross_billed_agency)      AS total_billed,
        SUM(f.contractor_gross_pay)     AS total_paid_contractors,
        SUM(f.total_umbrella_profit)    AS total_profit,
        SUM(f.umbrella_fixed_fee)       AS total_umbrella_fees
    FROM fact_timesheets_clean f
    JOIN dim_agency a ON f.agy_id = a.agy_id
    GROUP BY f.agy_id, a.agy_name, f.week_ending
)

SELECT
    agy_id,
    agy_name,
    week_ending,
    active_cntrs,
    total_billed,
    total_paid_contractors,
    total_profit,

    ROUND((total_profit / (total_billed + total_umbrella_fees)) * 100.0, 2) AS profit_margin_pct,
    
    ROUND(AVG(total_profit) OVER (
        PARTITION BY agy_id
        ORDER BY week_ending

        ROWS BETWEEN 3 PRECEDING AND CURRENT ROW
    ), 2) AS moving_avg_4wk_profit
FROM weekly_performance;


-- summary
CREATE VIEW v_executive_kpi_summary AS
SELECT

    COUNT(DISTINCT cntr_id)                AS total_active_contractors,
    COUNT(timesheet_id)                          AS total_clean_timesheets,
    ROUND(SUM(gross_billed_agency), 2)           AS total_gross_billed,
    ROUND(SUM(contractor_gross_pay), 2)          AS total_contractor_payouts,
    ROUND(SUM(total_umbrella_profit), 2)         AS total_retained_profit,
    
    ROUND((SUM(total_umbrella_profit) / (SUM(gross_billed_agency) + SUM(umbrella_fixed_fee))) * 100.0, 2) AS overall_margin_pct
FROM fact_timesheets_clean;
