import hashlib
from datetime import datetime

import pandas as pd

from config import DATA_DIR, SQL_DATABASE
from db import banner, done, insert_dataframe, run_sql, step, table_count

FILES = [
    ("orders.csv", "raw.orders"),
    ("events.csv", "raw.events"),
    ("deposits.csv", "raw.deposits"),
]


def read_as_text(path):
    return pd.read_csv(path, dtype=str, keep_default_na=False)


def add_tracking_columns(df, filename):
    joined = df.astype(str).agg("|".join, axis=1)
    df = df.copy()
    df["_source_file"] = filename
    df["_loaded_at"] = datetime.now()
    df["_row_hash"] = joined.map(lambda row: hashlib.md5(row.encode()).hexdigest())
    return df


banner("STEP 2 - LOADING THE RAW FILES INTO SQL SERVER")
print(f"  database: {SQL_DATABASE}")
print(f"  reading from: {DATA_DIR}")

step(1, "Make sure the schemas exist")
for schema in ("raw", "clean", "dq"):
    run_sql(f"IF SCHEMA_ID('{schema}') IS NULL EXEC('CREATE SCHEMA {schema}');")
print("\n  schemas ready: raw, clean, dq")

step(2, "Load each file")
counts = []
for filename, table in FILES:
    df = read_as_text(DATA_DIR / filename)
    rows_in_file = len(df)
    df = add_tracking_columns(df, filename)
    column_types = {c: "NVARCHAR(200)" for c in df.columns}
    column_types["_loaded_at"] = "DATETIME2"
    column_types["_row_hash"] = "CHAR(32)"
    rows_written = insert_dataframe(df, table, column_types)
    counts.append((filename, table, rows_in_file, rows_written))
    print(f"  {filename:<18} -> {table:<14} {rows_written:>6,} rows")

step(3, "RECONCILE - does the database hold what the files held?")
print()
print(f"  {'file':<18} {'in file':>9} {'in table':>10}   match")
all_match = True
for filename, table, rows_in_file, _ in counts:
    in_table = table_count(table)
    ok = in_table == rows_in_file
    all_match &= ok
    print(f"  {filename:<18} {rows_in_file:>9,} {in_table:>10,}   {'yes' if ok else 'NO'}")

if not all_match:
    raise SystemExit("\n  ROW COUNTS DO NOT MATCH. Stop and find out why before going on.")

done("Every row in every file is now in SQL Server, untouched.\n"
     "     Next:  python 03_clean_tables.py")
