# QuickCart - a 45-minute data engineering sprint

The brief is in `CASE_STUDY.md`. Stack: Python (pandas + pyodbc) and Microsoft SQL Server.

## Run order

```powershell
pip install -r requirements.txt
Copy-Item .env.example .env
python make_data.py
python 00_test_connection.py
python run_all.py
```

`python run_all.py --from 3` restarts at step 3. `--quiet` trims the output. Every step is safe to re-run.

Connection: `config.py` builds the string from `.env` (`SQL_SERVER`, `SQL_DATABASE`, `SQL_DRIVER`, optional `SQL_USER` and `SQL_PASSWORD`). With no user it uses Windows authentication. `setup.sql` creates the database and schemas by hand if you want it.

## Steps

| Script | What it does |
|---|---|
| `make_data.py` | Writes `data/*.csv` (`--check` asserts every planted issue) |
| `00_test_connection.py` | Setup checks with a FIX line for each failure |
| `01_profile_the_data.py` | Shows the planted problems. Writes nothing |
| `02_load_raw.py` | Loads the three files into `raw.*` as text and reconciles counts |
| `03_clean_tables.py` | Types, dedupe, echo removal, money parsing into `clean.*` |
| `04_build_order_final.py` | One row per order |
| `05_answer_the_questions.py` | Runs `queries/q1..q6.sql` into `results/q1..q6.csv` |
| `06_quality_checks.py` | 13 checks into `dq.results` |

## Cleaning decisions

- Duplicate orders: keep the latest `updated_at`; losers go to `clean.merge_log`
- Dates: each of the three formats is tried explicitly, never guessed; unparseable dates stop the step
- Zones and agent IDs: trimmed and upper-cased, so `DHA`, `dha` and `  DHA ` become one value
- Events for unknown orders: moved to `clean.rejected_events` with a reason, never dropped silently
- Echo events: same order and status within 180 seconds count as one
- Deposit amounts: everything except digits and the dot is stripped, then cast to `DECIMAL(10,2)`
- Final status: latest event wins, so delivered-then-returned is returned
- `cod_due`: only delivered orders owe cash
- Primary keys on `clean.orders` and `clean.order_final` so the database enforces uniqueness

## Schemas

```
raw.orders, raw.events, raw.deposits     untouched copies, every column text
clean.orders_all / clean.orders          typed, then deduplicated
clean.merge_log                          the 55 superseded order rows
clean.events_all / clean.events          typed, then echoes removed
clean.rejected_events                    the 25 events for unknown orders
clean.deposits                           amount as DECIMAL
clean.order_final                        one row per order
dq.results                               pass/fail with detail
```

## Expected answers (seed 7)

| | |
|---|---|
| Cash due on delivered orders | PKR 9,473,780 |
| Cash collected against them | PKR 8,252,700 |
| **Gap** | **PKR 1,221,080** |
| Delivered, no deposit at all | 114 orders, PKR 1,102,440 |
| Net shortfall on deposited orders | PKR 118,640 (agents A03, A07, A20, A23, A18) |
| Deposits against undelivered orders | 20, PKR 122,000 |
| Orders / clean events / rejected / echoes | 1,500 / 4,309 / 25 / 407 |
| Final statuses | 1,185 delivered, 130 out_for_delivery, 124 returned, 61 cancelled |
