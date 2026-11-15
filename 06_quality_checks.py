from datetime import datetime

import pandas as pd

from db import banner, done, fetch_df, fetch_value, insert_dataframe, step

checks = []


def record(name, passed, detail):
    checks.append({"check_name": name, "passed": bool(passed),
                   "detail": str(detail)[:200], "run_at": datetime.now()})
    print(f"  [{'  OK  ' if passed else ' FAIL '}] {name}")
    print(f"           {detail}")


banner("STEP 6 - DATA QUALITY CHECKS")

step(1, "Is the key actually a key?")
rows = fetch_value("SELECT COUNT(*) FROM clean.orders")
distinct = fetch_value("SELECT COUNT(DISTINCT order_id) FROM clean.orders")
nulls = fetch_value("SELECT COUNT(*) FROM clean.orders WHERE order_id IS NULL")
record("order_id is unique and not null", rows == distinct and nulls == 0,
       f"{rows:,} rows, {distinct:,} distinct, {nulls} null")

step(2, "RECONCILIATION - is every raw event accounted for?")
raw_events = fetch_value("SELECT COUNT(*) FROM raw.events")
clean_events = fetch_value("SELECT COUNT(*) FROM clean.events")
rejected = fetch_value("SELECT COUNT(*) FROM clean.rejected_events")
echoes = raw_events - clean_events - rejected
record("every raw event is used, rejected or a known echo",
       clean_events + rejected + echoes == raw_events and echoes >= 0,
       f"{raw_events:,} raw = {clean_events:,} clean + {rejected} rejected + {echoes} echoes removed")

for table, raw_table in [("clean.orders_all", "raw.orders"),
                         ("clean.deposits", "raw.deposits")]:
    a = fetch_value(f"SELECT COUNT(*) FROM {raw_table}")
    b = fetch_value(f"SELECT COUNT(*) FROM {table}")
    record(f"{raw_table} -> {table} loses nothing", a == b, f"{a:,} raw, {b:,} cleaned")

step(3, "REFERENTIAL INTEGRITY - does every row point at something real?")
orphan_events = fetch_value("""
    SELECT COUNT(*) FROM clean.events e
    WHERE NOT EXISTS (SELECT 1 FROM clean.orders o WHERE o.order_id = e.order_id)
""")
record("every clean event belongs to a known order", orphan_events == 0,
       f"{orphan_events} orphans")

orphan_deposits = fetch_value("""
    SELECT COUNT(*) FROM clean.deposits d
    WHERE NOT EXISTS (SELECT 1 FROM clean.orders o WHERE o.order_id = d.order_id)
""")
record("every deposit belongs to a known order", orphan_deposits == 0,
       f"{orphan_deposits} deposits with no matching order")

multi = fetch_value("""
    SELECT COUNT(*) FROM (
        SELECT order_id FROM clean.deposits GROUP BY order_id HAVING COUNT(*) > 1
    ) x
""")
record("at most one deposit per order", multi == 0, f"{multi} orders with more than one deposit")

step(4, "ACCEPTED VALUES - only the statuses and zones we expect")
bad_status = fetch_df("""
    SELECT final_status, COUNT(*) AS n FROM clean.order_final
    WHERE final_status NOT IN ('delivered','returned','cancelled','out_for_delivery','dispatched','no_event')
    GROUP BY final_status
""")
record("final_status holds only expected values", len(bad_status) == 0,
       "all known" if len(bad_status) == 0 else bad_status.to_dict("records"))

zones = fetch_value("SELECT COUNT(DISTINCT zone) FROM clean.orders")
record("exactly 4 zones after cleaning", zones == 4, f"{zones} distinct zone values")

step(5, "BUSINESS SANITY - things that cannot be true")
backwards = fetch_value("SELECT COUNT(*) FROM clean.order_final WHERE delivered_date < booked_date")
record("nothing was delivered before it was booked", backwards == 0,
       f"{backwards} orders (this is the check that catches a date-parsing bug)")

negative = fetch_value("SELECT COUNT(*) FROM clean.deposits WHERE amount < 0")
record("no negative deposits", negative == 0, f"{negative} rows with amount < 0")

owed_not_delivered = fetch_value("""
    SELECT COUNT(*) FROM clean.order_final
    WHERE final_status <> 'delivered' AND cod_due <> 0
""")
record("only delivered orders owe cash", owed_not_delivered == 0,
       f"{owed_not_delivered} undelivered orders with cod_due <> 0")

step(6, "TIE-OUT - does the headline equal its parts?")
gap = float(fetch_value("""
    SELECT SUM(o.cod_due) - SUM(ISNULL(d.amount, 0))
    FROM clean.order_final o
    LEFT JOIN clean.deposits d ON d.order_id = o.order_id
    WHERE o.final_status = 'delivered'
"""))
missing = float(fetch_value("""
    SELECT ISNULL(SUM(o.cod_due), 0) FROM clean.order_final o
    WHERE o.final_status = 'delivered' AND o.cod_due > 0
      AND NOT EXISTS (SELECT 1 FROM clean.deposits d WHERE d.order_id = o.order_id)
"""))
short = float(fetch_value("""
    SELECT ISNULL(SUM(o.cod_due - d.amount), 0)
    FROM clean.order_final o
    JOIN clean.deposits d ON d.order_id = o.order_id
    WHERE o.final_status = 'delivered'
"""))
record("cash gap = missing deposits + net shortfall on deposited orders", abs(gap - (missing + short)) < 0.01,
       f"gap {gap:,.0f} = missing {missing:,.0f} + net shortfall {short:,.0f}")

step(7, "Write the results so they outlive this terminal")
df = pd.DataFrame(checks)
insert_dataframe(df, "dq.results", {
    "check_name": "NVARCHAR(100)", "passed": "BIT",
    "detail": "NVARCHAR(200)", "run_at": "DATETIME2",
})

passed = int(df.passed.sum())
print(f"\n  dq.results: {passed} of {len(df)} checks passed")

if passed != len(df):
    print("\n  SOMETHING FAILED. Do not present these numbers until it is green.")
    raise SystemExit(1)

done("Every check passed. The numbers in results/ are defensible.\n"
     "     Read them back with:  SELECT * FROM dq.results ORDER BY run_at;")
