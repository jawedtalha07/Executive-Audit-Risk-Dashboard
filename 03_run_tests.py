"""
Sanity checks on the warehouse after the pipeline has run
Run it with: python3 03_run_tests.py
"""
import sqlite3
import sys
from contextlib import closing
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_PATH  = BASE_DIR / "data" / "contractorpay.db"


def scalar(cur, query):
    return cur.execute(query).fetchone()[0]


def run_tests():
    if not DB_PATH.exists():
        sys.exit(f"{DB_PATH} not found. Run 02_run_pipeline.py first.")

    with closing(sqlite3.connect(DB_PATH)) as conn:
        cur = conn.cursor()
        print("Running warehouse checks...\n")

        # no loss making should be in clean table
        bad_margins = scalar(
            cur, "SELECT COUNT(*) FROM fact_timesheets_clean WHERE gross_margin <= 0")
        assert bad_margins == 0, \
            f"FAILED: {bad_margins} zero/negative margins in fact_timesheets_clean"
        print("[PASS] 1. No zero or negative margins in fact_timesheets_clean")

        # every timesheet should be checked
        staged = scalar(cur, "SELECT COUNT(*) FROM stg_timesheets")
        clean = scalar(cur, "SELECT COUNT(*) FROM fact_timesheets_clean")
        flagged = scalar(
            cur, "SELECT COUNT(DISTINCT timesheet_id) FROM fact_audit_exceptions")
        assert clean + flagged == staged, \
            f"FAILED: {clean} clean + {flagged} flagged != {staged} staged"
        print(f"[PASS] 2. Row counts reconcile ({clean} clean + {flagged} flagged = {staged} staged)")

        # over working contract flag here
        wtd = scalar(
            cur, "SELECT COUNT(*) FROM fact_audit_exceptions WHERE anomaly_code = 'ERR_WTD_BREACH'")
        assert wtd > 0, "FAILED: no Working Time Directive breaches found"
        print(f"[PASS] 3. Found {wtd} Working Time Directive breaches")

    print("\nAll checks passed.")


if __name__ == "__main__":
    run_tests()
