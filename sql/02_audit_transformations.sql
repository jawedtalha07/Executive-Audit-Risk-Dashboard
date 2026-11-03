-- 3 check audit tool
-- if we catch anything we will get it in fact audit exception file
-- timesheet weill show there more than one time if it does not follow more than one rule


-- bill rate <= below pay rate money loss
INSERT INTO fact_audit_exceptions
    (timesheet_id, cntr_id, agy_id, anomaly_code, severity, description)
SELECT
    t.timesheet_id,
    t.cntr_id,
    t.agy_id,
    'ERR_MARGIN_DEFICIT',
    'CRITICAL',
    -- check error in profit loss in main
    'Pay rate (£' || PRINTF('%.2f', t.pay_rate) || ') >= Bill rate (£' || PRINTF('%.2f', t.bill_rate) || ')'
FROM stg_timesheets t
WHERE t.bill_rate <= t.pay_rate;

-- match between contractor and week more than once = flag in both original duplicate
WITH duplicate_detection AS (
    SELECT
        timesheet_id,
        cntr_id,
        agy_id,
        week_ending,
        -- main logic
        ROW_NUMBER() OVER (PARTITION BY cntr_id, week_ending
        ORDER BY timesheet_id ASC) AS submission_rank
        FROM stg_timesheets
        
)
INSERT INTO fact_audit_exceptions
    (timesheet_id, cntr_id, agy_id, anomaly_code, severity, description)
SELECT
    timesheet_id,
    cntr_id,
    agy_id,
    'ERR_DUPLICATE_TIMESHEET',
    'HIGH',
    'Multiple timesheets submitted for contractor in week ending ' || week_ending
FROM duplicate_detection
WHERE submission_rank > 1;

-- 3. UK Working Time Directive: average over a 17-week window must not pass 48 hrs
--    Note: the window is the contractor's last 17 timesheets (ROWS, not a date range),
--    which is the same thing as long as they don't skip many weeks.
WITH rolling_hours_calc AS (
    SELECT
        timesheet_id,
        cntr_id,
        agy_id,
        week_ending,
        hrs_worked,
        AVG(hrs_worked) OVER (
            PARTITION BY cntr_id
            ORDER BY week_ending
            ROWS BETWEEN 16 PRECEDING AND CURRENT ROW
        ) AS rolling_17wk_avg_hours
    FROM stg_timesheets
)
INSERT INTO fact_audit_exceptions
    (timesheet_id, cntr_id, agy_id, anomaly_code, severity, description)
SELECT
    timesheet_id,
    cntr_id,
    agy_id,
    'ERR_WTD_BREACH',
    'HIGH',
    'Rolling 17-week average hours (' || ROUND(rolling_17wk_avg_hours, 1) || ' hrs) exceeds 48-hour statutory cap'
FROM rolling_hours_calc
WHERE rolling_17wk_avg_hours > 48.0;
