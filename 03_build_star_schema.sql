    DROP TABLE IF EXISTS dim_agency;
    DROP TABLE IF EXISTS dim_contractor;
    DROP TABLE IF EXISTS fact_timesheets_clean;

    CREATE TABLE dim_agency AS SELECT * FROM stg_agys;
    CREATE TABLE dim_contractor AS SELECT * FROM stg_cntrs;

    CREATE TABLE fact_timesheets_clean AS
    SELECT
        t.timesheet_id,
        t.week_ending,
        t.cntr_id,
        t.agy_id,
        t.hrs_worked,
        t.pay_rate,
        t.bill_rate,
        a.umbrella_fixed_fee,
        ROUND(t.hrs_worked * t.bill_rate, 2)                  AS gross_billed_agency,
        ROUND(t.hrs_worked * t.pay_rate, 2)                   AS contractor_gross_pay,
        
        -- bill pay X hour margin for full timesheet
        ROUND((t.bill_rate - t.pay_rate) * t.hrs_worked, 2)   AS gross_margin,
        ROUND(((t.bill_rate - t.pay_rate) * t.hrs_worked) + a.umbrella_fixed_fee, 2) AS total_umbrella_profit
    FROM stg_timesheets t
    INNER JOIN dim_agency a ON t.agy_id = a.agy_id
    WHERE t.timesheet_id NOT IN (
        SELECT DISTINCT timesheet_id FROM fact_audit_exceptions
    );
