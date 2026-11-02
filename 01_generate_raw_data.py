## make 3 fake data set
## dim_contractor_raw.csv, dim_agency_raw.csv, raw_timesheets.csv
## fix data every run for tableau
## make bad rows for sql to check
import os
from datetime import date, timedelta

import numpy as np
import pandas as pd

DATA_DIR = "data"
SEED = 42

N_CNTRS = 120
N_AGYS = 10
N_ACTIVE_POOL = 100               # only first 100 timesheet
WEEKLY_HEADCOUNT = 75             # contractors submitting any weel
N_WEEKS = 18                      # one more than the 17week WTD window
FIRST_WEEK_ENDING = date(2026, 6, 7)   # Sunday


def make_cntrs(rng):
    ids = [f"CNT{1000 + i}" for i in range(N_CNTRS)]
    first_names = ["James", "Sarah", "Alex", "Emily", "David",
                   "Priya", "Liam", "Chloe", "Mohamed", "Elena"]
    last_names = ["Smith", "Patel", "Taylor", "Brown", "Wilson",
                  "Davies", "Evans", "Thomas", "Johnson", "Roberts"]
    
    names = [
        f"{rng.choice(first_names)} {rng.choice(last_names)}"
        for _ in ids
    ]

    return pd.DataFrame({
        "cntr_id": ids,
        "full_name": names,
        # we use random here to show the hourly pay rate
        "standard_hour_pay": rng.choice(    
            [25.0, 32.5, 45.0, 55.0, 70.0, 85.0], size=N_CNTRS),
        "tax_code": rng.choice(
            ["1257L", "BR", "0T", "D0"], size=N_CNTRS,
            p=[0.75, 0.15, 0.05, 0.05]),
        "status": rng.choice(
            ["Active", "Suspended"], size=N_CNTRS, p=[0.95, 0.05]),
        "agy_id": rng.choice([f"AGY{100 + i}" for i in range(N_AGYS)], size= N_CNTRS),
    })


def make_agys():
    # made up agency name
    return pd.DataFrame({
        "agy_id": [f"AGY{100 + i}" for i in range(N_AGYS)],
        "agy_name": [
            "Northgate Recruitment", "Pembroke Talent", "Calder & Finch",
            "Brightwell Tech Staffing", "Marlow Resourcing", "Ashdown Partners",
            "Fenwick Search", "Harcourt Associates", "Kestrel Consulting",
            "Ventry Group",
        ],
        "payment_terms_date": [14, 30, 30, 45, 30, 14, 30, 60, 30, 14],
        "umbrella_fixed_fee": [25.0, 20.0, 30.0, 22.5, 25.0, 30.0, 20.0, 35.0, 25.0, 20.0],
    })


def make_timesheets(cntrs, agys,rng):
    pay_by_cntr = dict(zip(cntrs["cntr_id"],
                                 cntrs["standard_hour_pay"]))
    agy_by_cntrs = dict(zip(cntrs["cntr_id"],
                                    cntrs["agy_id"]))
    ## earlier made a mistake by just putting a range 10 that would crash the 
    # system as number of agencies might change 
    #agency_ids = agencies["agency_id"].tolist()
    pool = cntrs["cntr_id"].tolist()[:N_ACTIVE_POOL]

    week_endings = [FIRST_WEEK_ENDING + timedelta(weeks=i) for i in range(N_WEEKS)]

    rows = []
    for week in week_endings:
        submitters = rng.choice(pool, size=WEEKLY_HEADCOUNT, replace=False)

        for cntr_id in submitters:
            cntr_id = str(cntr_id)
            pay_rate = pay_by_cntr[cntr_id]
            ## error from above
            ##agency_id = str(np.random.choice(agency_ids))
            agy_id = agy_by_cntrs[cntr_id]
            # agencies bill 20 to 40 above what the contractor is paid
            bill_rate = round(pay_rate * rng.uniform(1.20, 1.40), 2)

            # nearly a standard week rounded off to the nearest half of hour
            hrs = rng.normal(loc=37.5, scale=5.0)
            hrs = float(np.clip(np.round(hrs * 2) / 2, 15.0, 60.0))

            rows.append({
                "timesheet_id": f"TS-{len(rows) + 1:05d}",
                "week_ending": week.isoformat(),
                "cntr_id": cntr_id,
                "agy_id": agy_id,
                "hrs_worked": hrs,
                "pay_rate": pay_rate,
                "bill_rate": bill_rate,
            })

    return pd.DataFrame(rows)


def add_bad_row(ts):
    """breaking few rows so that audit can catch them"""
    # bill rate or below the pay rate so the agency loses money
    safe_indices = [i for i in [20,85,210] if i < len(ts)]
    for idx in safe_indices:
        ts.loc[idx, "bill_rate"] = ts.loc[idx, "pay_rate"]-5.00

    # one contractor who logs 56 hrs every week they appear
    if "CNT1005" in ts["cntr_id"].values:
        ts.loc[ts["cntr_id"] == "CNT1005", "hrs_worked"] = 56.0

    # same timesheet under different ids
    if len(ts) > 45:
        dup = ts.iloc[[45]].copy()
        dup["timesheet_id"] = "TS-DUP999"
        return pd.concat([ts, dup], ignore_index=True)
    return ts


def main():
    rng = np.random.default_rng(SEED)
    os.makedirs(DATA_DIR, exist_ok=True)

    cntrs = make_cntrs(rng)
    agys = make_agys()
    timesheets = add_bad_row(make_timesheets(cntrs, agys,rng))

    cntrs.to_csv(f"{DATA_DIR}/dim_contractor_raw.csv", index=False)
    agys.to_csv(f"{DATA_DIR}/dim_agency_raw.csv", index=False)
    timesheets.to_csv(f"{DATA_DIR}/raw_timesheets.csv", index=False)

    print(f"Wrote {len(cntrs)} cntrs, {len(agys)} agys "
          f"and {len(timesheets)} timesheets to {DATA_DIR}/")


if __name__ == "__main__":
    main()
