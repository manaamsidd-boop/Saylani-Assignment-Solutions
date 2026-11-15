import pandas as pd

from db import (banner, done, fetch_df, insert_dataframe, run_sql, step,
                table_count)

DATE_FORMATS = [
    "%Y-%m-%d",
    "%d/%m/%Y",
    "%d.%m.%Y",
]

ECHO_SECONDS = 180


def to_date(series):
    parsed = pd.Series(pd.NaT, index=series.index, dtype="datetime64[ns]")
    for fmt in DATE_FORMATS:
        still_missing = parsed.isna()
        if not still_missing.any():
            break
        parsed.loc[still_missing] = pd.to_datetime(
            series[still_missing], format=fmt, errors="coerce")
    return parsed


def to_money(series):
    stripped = series.str.replace(r"[^\d.]", "", regex=True)
    return pd.to_numeric(stripped, errors="coerce")


banner("STEP 3 - CLEANING")

step(1, "ORDERS - parse the types, normalise the zones")
orders = fetch_df("""
    SELECT order_id, booked_date, promised_date, zone, agent_id,
           cod_amount, updated_at
    FROM raw.orders
""")

orders["booked_date"] = to_date(orders.booked_date).dt.date
orders["promised_date"] = to_date(orders.promised_date).dt.date
orders["updated_at"] = pd.to_datetime(orders.updated_at, errors="coerce")
orders["cod_amount"] = pd.to_numeric(orders.cod_amount, errors="coerce")
orders["zone"] = orders.zone.str.strip().str.upper()
orders["agent_id"] = orders.agent_id.str.strip().str.upper()

unparsed = int(orders.booked_date.isna().sum() + orders.promised_date.isna().sum())
print(f"\n  dates parsed, {unparsed} unparseable")
print(f"  zones now: {sorted(orders.zone.unique())}")
if unparsed:
    raise SystemExit("  Some dates did not match any known format. Look at them first.")

insert_dataframe(orders, "clean.orders_all", {
    "order_id": "NVARCHAR(20)", "booked_date": "DATE", "promised_date": "DATE",
    "zone": "NVARCHAR(50)", "agent_id": "NVARCHAR(10)",
    "cod_amount": "DECIMAL(10,2)", "updated_at": "DATETIME2",
})

step(2, "ORDERS - the duplicates: keep the latest updated_at")
run_sql("IF OBJECT_ID('clean.orders','U') IS NOT NULL DROP TABLE clean.orders;")
run_sql("IF OBJECT_ID('clean.merge_log','U') IS NOT NULL DROP TABLE clean.merge_log;")
run_sql("""
    WITH ranked AS (
        SELECT *, ROW_NUMBER() OVER (PARTITION BY order_id
                                     ORDER BY updated_at DESC) AS rn
        FROM clean.orders_all
    )
    SELECT order_id, booked_date, promised_date, zone, agent_id,
           cod_amount, updated_at
    INTO clean.orders
    FROM ranked WHERE rn = 1;
""")
run_sql("""
    WITH ranked AS (
        SELECT *, ROW_NUMBER() OVER (PARTITION BY order_id
                                     ORDER BY updated_at DESC) AS rn
        FROM clean.orders_all
    )
    SELECT order_id, updated_at AS dropped_updated_at,
           CAST('superseded by a row with a later updated_at' AS NVARCHAR(80)) AS reason
    INTO clean.merge_log
    FROM ranked WHERE rn > 1;
""")
run_sql("ALTER TABLE clean.orders ALTER COLUMN order_id NVARCHAR(20) NOT NULL;")
run_sql("ALTER TABLE clean.orders ADD CONSTRAINT pk_clean_orders PRIMARY KEY (order_id);")

print(f"\n  {table_count('clean.orders_all'):,} rows in -> "
      f"{table_count('clean.orders'):,} orders kept, "
      f"{table_count('clean.merge_log')} logged as superseded")

step(3, "EVENTS - park the ones we cannot use")
events = fetch_df("SELECT event_id, order_id, status, event_at, agent_id FROM raw.events")
events["event_at"] = pd.to_datetime(events.event_at, errors="coerce")
events["status"] = events.status.str.strip().str.lower()
events["agent_id"] = events.agent_id.str.strip().str.upper()

insert_dataframe(events, "clean.events_all", {
    "event_id": "NVARCHAR(20)", "order_id": "NVARCHAR(20)",
    "status": "NVARCHAR(30)", "event_at": "DATETIME2", "agent_id": "NVARCHAR(10)",
})

run_sql("IF OBJECT_ID('clean.rejected_events','U') IS NOT NULL DROP TABLE clean.rejected_events;")
run_sql("""
    SELECT e.*, CAST('order_id not found in clean.orders' AS NVARCHAR(80)) AS reason
    INTO clean.rejected_events
    FROM clean.events_all e
    WHERE NOT EXISTS (SELECT 1 FROM clean.orders o WHERE o.order_id = e.order_id);
""")
print(f"\n  {table_count('clean.rejected_events')} events rejected (unknown order_id)")

step(4, f"EVENTS - the {ECHO_SECONDS // 60}-minute rule")
run_sql("IF OBJECT_ID('clean.events','U') IS NOT NULL DROP TABLE clean.events;")
run_sql(f"""
    WITH gapped AS (
        SELECT e.*,
               LAG(e.event_at) OVER (PARTITION BY e.order_id, e.status
                                     ORDER BY e.event_at) AS prev_event
        FROM clean.events_all e
        WHERE EXISTS (SELECT 1 FROM clean.orders o WHERE o.order_id = e.order_id)
    )
    SELECT event_id, order_id, status, event_at, agent_id
    INTO clean.events
    FROM gapped
    WHERE prev_event IS NULL
       OR DATEDIFF(SECOND, prev_event, event_at) > {ECHO_SECONDS};
""")

kept, total = table_count("clean.events"), table_count("clean.events_all")
rejected = table_count("clean.rejected_events")
print(f"\n  {total:,} events -> {kept:,} kept, {rejected} rejected, "
      f"{total - kept - rejected} echoes removed")

step(5, "DEPOSITS - turn the text into money")
deposits = fetch_df("SELECT deposit_id, order_id, agent_id, amount, deposited_at FROM raw.deposits")
print("\n  before:", list(deposits.amount.head(3)))
deposits["amount"] = to_money(deposits.amount)
print("  after: ", list(deposits.amount.head(3)))

deposits["deposited_at"] = pd.to_datetime(deposits.deposited_at, errors="coerce")
deposits["agent_id"] = deposits.agent_id.str.strip().str.upper()

bad = int(deposits.amount.isna().sum())
if bad:
    print(f"  WARNING: {bad} amounts could not be parsed - look at them before trusting totals")

insert_dataframe(deposits, "clean.deposits", {
    "deposit_id": "NVARCHAR(20)", "order_id": "NVARCHAR(20)",
    "agent_id": "NVARCHAR(10)", "amount": "DECIMAL(10,2)", "deposited_at": "DATETIME2",
})
total_cash = fetch_df("SELECT SUM(amount) AS t FROM clean.deposits").t[0]
print(f"\n  clean.deposits: {table_count('clean.deposits'):,} rows, total PKR {total_cash:,.0f}")

done("Four clean tables, and two tables of evidence for what we removed.\n"
     "     Next:  python 04_build_order_final.py")
