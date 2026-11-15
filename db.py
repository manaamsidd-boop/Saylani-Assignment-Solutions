import re
import warnings
from pathlib import Path

import pandas as pd
import pyodbc

from config import CONNECTION_STRING

warnings.filterwarnings("ignore", message="pandas only supports SQLAlchemy connectable")


def get_connection(autocommit=False):
    return pyodbc.connect(CONNECTION_STRING, autocommit=autocommit)


def run_sql(sql, params=()):
    with get_connection(autocommit=True) as conn:
        conn.cursor().execute(sql, params)


def fetch_df(sql, params=()):
    with get_connection() as conn:
        return pd.read_sql(sql, conn, params=params)


def fetch_value(sql, params=()):
    with get_connection() as conn:
        return conn.cursor().execute(sql, params).fetchone()[0]


def table_count(table):
    return fetch_value(f"SELECT COUNT(*) FROM {table}")


def table_exists(table):
    return fetch_value("SELECT COUNT(*) FROM sys.objects WHERE object_id = OBJECT_ID(?)", (table,)) > 0


def run_sql_script(path):
    sql = Path(path).read_text(encoding="utf-8")
    chunks = [c.strip() for c in re.split(r"(?mi)^\s*GO\s*$", sql) if c.strip()]
    with get_connection(autocommit=True) as conn:
        cursor = conn.cursor()
        for chunk in chunks:
            cursor.execute(chunk)


def insert_dataframe(df, table, column_types, chunk_size=5000):
    columns = list(column_types.keys())
    column_defs = ", ".join(f"[{c}] {column_types[c]}" for c in columns)
    data = df[columns].astype(object).where(pd.notna(df[columns]), None)
    rows = data.values.tolist()
    placeholders = ", ".join("?" for _ in columns)
    column_list = ", ".join(f"[{c}]" for c in columns)
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(f"IF OBJECT_ID('{table}','U') IS NOT NULL DROP TABLE {table};")
        cursor.execute(f"CREATE TABLE {table} ({column_defs});")
        cursor.fast_executemany = True
        sql = f"INSERT INTO {table} ({column_list}) VALUES ({placeholders})"
        for start in range(0, len(rows), chunk_size):
            cursor.executemany(sql, rows[start:start + chunk_size])
        conn.commit()
    return len(rows)


def banner(title):
    print()
    print("=" * 72)
    print(f" {title}")
    print("=" * 72)


def step(number, title):
    print(f"\n  STEP {number}: {title}")


def done(message):
    print(f"\n  >> {message}")
