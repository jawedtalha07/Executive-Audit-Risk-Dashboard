DROP TABLE IF EXISTS stg_cntrs;
DROP TABLE IF EXISTS stg_agys;
DROP TABLE IF EXISTS stg_timesheets;
DROP TABLE IF EXISTS fact_audit_exceptions;


CREATE TABLE stg_cntrs (
    cntr_id       TEXT PRIMARY KEY,
    full_name           TEXT,
    standard_hour_pay REAL,
    tax_code            TEXT,
    status              TEXT,
    agy_id           TEXT
);

CREATE TABLE stg_agys (
    agy_id          TEXT PRIMARY KEY,
    agy_name        TEXT,
    payment_terms_date INTEGER,
    umbrella_fixed_fee REAL
);

-- no primary key for error
CREATE TABLE stg_timesheets (
    timesheet_id  TEXT,
    week_ending   TEXT,
    cntr_id TEXT,
    agy_id     TEXT,
    hrs_worked  REAL,
    pay_rate      REAL,
    bill_rate     REAL
);

CREATE TABLE fact_audit_exceptions (
    exception_id  INTEGER PRIMARY KEY AUTOINCREMENT,
    timesheet_id  TEXT,
    cntr_id TEXT,
    agy_id     TEXT,
    anomaly_code  TEXT,
    severity      TEXT,

    description   TEXT,
    detected_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
