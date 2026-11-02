"""
    put raw CSV file in SQL and run them in order
    01_schema_setup.sql staging tables + exceptions
    CSV load in python
    02_audit_transformations.sql flag bad timesheets
    03_build_star_schema.sql dimensions +  clean fact table
    04_analytical_views.sql reporting view
    main tables are used for tableau for dashboard
"""
import sqlite3
import sys
from contextlib import closing
from pathlib import Path    

import pandas as pd
BASE_DIR = Path(__file__).resolve().parent

DATA_DIR = BASE_DIR / "data"
SQL_DIR = BASE_DIR / "sql"
DB_PATH = BASE_DIR / "data" / "contractorpay.db"

# csv file stag table where it gets loaded
STAGING_LOADS = {
    "dim_contractor_raw.csv": "stg_cntrs",
    "dim_agency_raw.csv": "stg_agys",
    "raw_timesheets.csv": "stg_timesheets",
}

TABLEAU_EXPORTS = [
    "fact_timesheets_clean",
    "fact_audit_exceptions",
    "v_agency_performance",
    "dim_agency",
    "dim_contractor",
    "v_executive_kpi_summary"
]


def run_sql_file(conn, filename):
    print(f"  running {filename}")
   # utf- 8 for pounds sign
    script = (SQL_DIR / filename).read_text(encoding="utf-8")
    conn.executescript(script)
    conn.commit()


def load_csv(conn, csv_name, table):
    df = pd.read_csv(DATA_DIR / csv_name)
    df.to_sql(table, conn, if_exists="append", index=False)
    print(f"  loaded {len(df):>5} rows into {table}")


def export_for_tableau(conn):
    for name in TABLEAU_EXPORTS:
        df = pd.read_sql_query(f"SELECT * FROM {name}", conn)
        df.to_csv(DATA_DIR / f"{name}.csv", index=False)
        print(f"  exported {name}.csv ({len(df)} rows)")


def run():
    missing = [f for f in STAGING_LOADS if not (DATA_DIR / f).exists()]
    if missing:
        sys.exit(f"Missing input file(s): {', '.join(missing)}\n"
                 "Run 01_generate_raw_data.py first.")

    with closing(sqlite3.connect(DB_PATH)) as conn:
        print("Setting up schema")
        run_sql_file(conn, "01_schema_setup.sql")

        print("Loading staging tables")
        for csv_name, table in STAGING_LOADS.items():
            load_csv(conn, csv_name, table)

        print("Running audit checks")
        run_sql_file(conn, "02_audit_transformations.sql")

        print("Building star schema")
        run_sql_file(conn, "03_build_star_schema.sql")

        print("Creating views")
        run_sql_file(conn, "04_analytical_views.sql")

        print("Exporting for Tableau")
        export_for_tableau(conn)

    print(f"\nPipeline finished. Database: {DB_PATH}")


if __name__ == "__main__":
    run()
