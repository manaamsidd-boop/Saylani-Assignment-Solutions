import pandas as pd

from config import DATA_DIR
from db import banner, done, step

pd.set_option("display.width", 100)
pd.set_option("display.max_columns", 20)


def read_as_text(name):
    return pd.read_csv(DATA_DIR / name, dtype=str, keep_default_na=False)


def shape_of(value):
    return "".join("9" if c.isdigit() else ("A" if c.isalpha() else c) for c in value)


banner("STEP 1 - PROFILING THE RAW FILES")
print(f"  reading from: {DATA_DIR}")

orders = read_as_text("orders.csv")
events = read_as_text("events.csv")
deposits = read_as_text("deposits.csv")

step(1, "How big is each file, and what is in it?")
for name, df in [("orders", orders), ("events", events), ("deposits", deposits)]:
    print(f"\n  {name}: {len(df):,} rows x {len(df.columns)} columns")
    print(f"    columns: {', '.join(df.columns)}")
    print(df.head(3).to_string(index=False, max_colwidth=22))

step(2, "PROBLEM 1 - duplicate orders")
total, distinct = len(orders), orders.order_id.nunique()
print(f"\n  rows: {total:,}   distinct order_id: {distinct:,}   duplicates: {total - distinct}")
repeated = orders[orders.order_id.duplicated(keep=False)].sort_values(["order_id", "updated_at"])
print("\n  the same order, twice - note which row has the later updated_at:")
print(repeated.head(4).to_string(index=False, max_colwidth=20))

step(3, "PROBLEM 2 - three date formats in one column")
print("\n  booked_date, by shape:")
print(orders.booked_date.map(shape_of).value_counts().to_string())
print("\n  examples:")
for shape, group in orders.groupby(orders.booked_date.map(shape_of)):
    print(f"    {shape:<12} e.g. {group.booked_date.iloc[0]}")

step(4, "PROBLEM 3 - zone names that do not match each other")
print(f"\n  distinct zone values as stored: {orders.zone.nunique()}")
print(orders.zone.value_counts().head(12).to_string())
cleaned_zones = orders.zone.str.strip().str.upper()
print(f"\n  after trimming and upper-casing: {cleaned_zones.nunique()}")
print(f"    -> {sorted(cleaned_zones.unique())}")

step(5, "PROBLEM 4 - money stored as text")
print("\n  amount, as delivered:")
print(deposits.amount.head(6).to_string(index=False))

step(6, "PROBLEM 5 - events for orders that do not exist")
known = set(orders.order_id)
orphans = events[~events.order_id.isin(known)]
print(f"\n  events: {len(events):,}   pointing at an unknown order: {len(orphans)}")
print(f"  examples: {', '.join(orphans.order_id.head(5))}")

step(7, "And a look at the event statuses")
print()
print(events.status.value_counts().to_string())

done("Nothing was written. You now know what you are dealing with.\n"
     "     Next:  python 02_load_raw.py")
