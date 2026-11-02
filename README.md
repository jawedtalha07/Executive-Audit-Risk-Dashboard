# Executive-Audit-Risk-Dashboard
ContractorPay Sentinel

A small data-engineering project that generates a fake contractor-payroll dataset, loads it into SQLite, audits it with SQL, builds a star schema, and exports clean tables for Tableau dashboards.

The dataset is synthetic. Some rows are deliberately broken ("planted") so the SQL audit has real problems to catch, similar to a real-world timesheet feed.

Pipeline overview
01_generate_raw_data.py  ->  3 raw CSVs (with planted bad rows)
02_run_pipeline.py       ->  loads CSVs into SQLite, runs the SQL files, exports CSVs for Tableau
03_run_tests.py          ->  sanity checks on the finished warehouse
Project structure
contractorpay-sentinel/
├── 01_generate_raw_data.py
├── 02_run_pipeline.py
├── 03_run_tests.py
├── sql/
│   ├── 01_schema_setup.sql          staging tables + exceptions log
│   ├── 02_audit_transformations.sql flags bad timesheets
│   ├── 03_build_star_schema.sql     dimensions + clean fact table
│   └── 04_analytical_views.sql      reporting views
└── data/                            created when the scripts run
    ├── dim_contractor_raw.csv
    ├── dim_agency_raw.csv
    ├── raw_timesheets.csv
    ├── contractorpay.db             SQLite database
    ├── fact_timesheets_clean.csv    exported for Tableau
    ├── fact_audit_exceptions.csv    exported for Tableau
    └── v_agency_performance.csv     exported for Tableau
Requirements
Python 3.10+
numpy and pandas (pip install numpy pandas)
SQLite (the sqlite3 module ships with Python)
Tableau (Desktop or Public) for the dashboards
How to run

Always run the scripts from the project root. The scripts use relative paths (data/, sql/), so running them from inside sql/ fails or creates a stray sql/data/ folder.

bash
cd contractorpay-sentinel
python3 01_generate_raw_data.py
python3 02_run_pipeline.py
python3 03_run_tests.py

Expected results:

Generator: Wrote 120 cntrs, 10 agys and 1351 timesheets
Pipeline: staging loads of 120 / 10 / 1351 rows, then three CSV exports
Tests: all three checks pass, with 1331 clean + 20 flagged = 1351 staged

The generated data is the same on every run (fixed seed), so Tableau results stay stable.

The data
Table	Rows	Description
Contractors	120	id, name, hourly pay, tax code, status (Active/Suspended), and the one agency that places them
Agencies	10	id, name, payment terms (days), umbrella fixed fee
Timesheets	1,351	18 weeks of timesheets: 75 contractors per week, drawn from the first 100 contractors. Each has hours, pay rate and bill rate

Design choices:

Each contractor belongs to one agency for all weeks, as in real life. The agency is assigned once per contractor, and timesheets look it up.
Bill rate is 20% to 40% above the pay rate, so the agency normally makes a margin.
Hours are roughly normal around 37.5 per week, rounded to half hours and clipped to 15 to 60.
18 weeks is one more than the 17-week window used by the Working Time Directive check.
Randomness comes from one seeded generator (np.random.default_rng(42)) created in main() and passed into each function.
Planted problems

01_generate_raw_data.py deliberately breaks these rows (row numbers are arbitrary; any row would do):

Problem	Where	Expected audit result
Bill rate below pay rate	rows 20 and 85	ERR_MARGIN_DEFICIT
Bill rate equal to pay rate	row 210	ERR_MARGIN_DEFICIT
Contractor CNT1005 logs 56 hours every week	all their rows	ERR_WTD_BREACH
Duplicate timesheet under a new id (TS-DUP999)	copy of row 45	ERR_DUPLICATE_TIMESHEET on both rows
SQL layers
01_schema_setup.sql drops and recreates the staging tables (stg_cntrs, stg_agys, stg_timesheets) and the fact_audit_exceptions log. stg_timesheets has no primary key on purpose, so bad and duplicate rows can load.
02_audit_transformations.sql runs three checks and writes every hit to fact_audit_exceptions:
ERR_MARGIN_DEFICIT: bill rate at or below pay rate
ERR_DUPLICATE_TIMESHEET: the same contractor and week submitted more than once (flags both copies)
ERR_WTD_BREACH: rolling 17-timesheet average above 48 hours (UK Working Time Directive). The window is the last 17 rows per contractor, not a date range, which is equivalent as long as they don't skip many weeks
03_build_star_schema.sql copies the staging tables into dim_agency and dim_contractor, then builds fact_timesheets_clean. The fact table keeps only timesheets not in the exceptions log, and adds gross_billed_agency, contractor_gross_pay, gross_margin and total_umbrella_profit.
04_analytical_views.sql creates:
v_agency_performance: weekly billed, paid and profit per agency, margin %, and a 4-week moving average of profit
v_executive_kpi_summary: one-row dashboard summary
Tests

03_run_tests.py checks that:

No zero or negative margins reach fact_timesheets_clean.
Every staged timesheet is either clean or flagged (clean + flagged = staged), so none go missing.
At least one Working Time Directive breach is found.
Tableau

Connect Tableau to the exported CSVs in data/:

fact_timesheets_clean.csv
fact_audit_exceptions.csv
v_agency_performance.csv

After re-running the pipeline, refresh the data source (Data menu > your source > Refresh). Make sure the connection points to the CSVs in the project's data/ folder and not an old copy.

Lessons learned and bugs fixed
Invisible whitespace broke a join. A trailing space in generated agency ids ("AGY102 " vs "AGY102") meant timesheets matched no agency. fact_timesheets_clean came out empty while the pipeline still "succeeded". Test 2 (row counts must reconcile) caught it.
Renaming a column means renaming it everywhere. A column name is shared by the CSV headers, staging tables, audit SQL, fact table, views and Tableau. Partial renames caused no column named ... errors until every file matched.
Working directory matters. Running from sql/ made the scripts look for sql/sql/... and write data to a stray folder.
Known limitations and next steps
Suspended contractors still submit timesheets. The status column is not used when generating timesheets. This could become a fourth audit check (ERR_SUSPENDED_CONTRACTOR).
payment_terms_date holds a number of days, not a date, so payment_terms_days would be a clearer name.
Planted rows are chosen by row number. Choosing them by condition, or writing a log of what was planted, would make audit results easier to verify.
The audit does not yet check that each contractor maps to exactly one agency in the fact table.
Paths are relative to the working directory. Building them from Path(__file__).parent would remove the run-from-root requirement.
