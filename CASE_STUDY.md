# QuickCart Mini-Sprint: Where Did the Cash Go?

**45 minutes · solo or pairs · Python + SQL Server**

## The scenario

QuickCart (fictional) is a Karachi marketplace. 30 delivery agents serve 4 zones. Most orders are **COD**: the agent collects cash at the door and deposits it at the office the same night.

October's cash book is short. Operations says every order was delivered. Finance says the cash never arrived. Both are reading different exports.

**Your mission:** load three messy exports, clean them, and tell Finance how much cash is missing and who is holding it.

## Setup

```powershell
pip install -r requirements.txt
Copy-Item .env.example .env
python make_data.py
python 00_test_connection.py
```

Run `setup.sql` if you prefer to create the database and schemas by hand. If your class shares one server, set `SQL_DATABASE=quickcart_yourname` in `.env`.

## The data

| File | Rows | What's messy |
|---|---|---|
| `orders.csv` | ~1,555 | 55 duplicate `order_id` (keep latest `updated_at`), three date formats, zone names in mixed case with stray spaces |
| `events.csv` | ~4,740 | Duplicate events seconds apart, events for order IDs that do not exist |
| `deposits.csv` | ~935 | Amounts as text (`PKR 1,250`, `1250.00`, `" 1250 "`), deposits for orders never delivered |

## Business rules

1. If an `order_id` appears twice in `orders.csv`, keep the row with the latest `updated_at`.
2. Two events for the same order with the same `status` within **3 minutes** count as one.
3. An order's **final status** is the status of its latest event.
4. `cod_due` = the order's `cod_amount` **only if** final status is `delivered`. Otherwise 0.
5. **On time** = delivered on or before `promised_date`. `days_late` counts days past the promise.
6. **Shortfall** = `cod_due` - total deposited for that order. Negative shortfall (over-deposited) is still a finding.

## Stages

**Stage 1 - Load.** Load all three CSVs into `raw.orders`, `raw.events`, `raw.deposits`, every column `NVARCHAR(200)`, read with `dtype=str`. Re-running must not duplicate rows. Print row counts per file and per table; they must match.

**Stage 2 - Clean.** Build `clean.orders`, `clean.events`, `clean.deposits` with real types. Dedupe orders by rule 1 and keep `clean.merge_log`. Parse all three date formats. Normalise zones. Drop duplicate events by rule 2. Send events with an unknown `order_id` to `clean.rejected_events` with a reason. Parse money to `DECIMAL(10,2)`. Build `clean.order_final` with a primary key on `order_id`.

**Stage 3 - Answer.** One `.sql` file per question in `queries/`, results saved as CSV in `results/`.

1. Order count by zone and final status.
2. On-time delivery rate by zone.
3. Top 5 agents by total COD shortfall.
4. Orders with a deposit but a final status that is **not** `delivered`.
5. Delivered COD orders with **no** deposit: count and total rupees at risk.

**Data quality.** Write at least three checks into `dq.results` (`check_name`, `passed`, `detail`, `run_at`):

- `order_id` is unique and not null in `clean.orders`
- `raw.events` count = `clean.events` + duplicates removed + `clean.rejected_events`
- No order has `delivered_date` before its `booked_date`

## Deliverables

```
README.md      how to run, one line per cleaning decision
setup.sql      database and schemas
0x_*.py        the pipeline steps
queries/       q1..q5.sql
results/       q1..q5.csv
findings.md    3 bullets: the number, the query, the action
```

## Rules

- Do not edit the CSVs by hand. Every fix lives in code.
- Every number comes from a `.sql` file in the repo.
- You must be able to explain any line you submit.

## Scoring (50 points)

| Criterion | Points |
|---|---|
| Correct answers to Q1-Q5 | 20 |
| Cleaning: every planted issue found and fixed in code | 15 |
| Data quality checks run and reconcile | 5 |
| Findings: three numbers with actions | 10 |

## Hints

- Profile first. Five minutes here saves twenty later.
- Dates are the trap. `21/10/2026` and `21.10.2026` are day-first, `2026-10-21` is ISO. Do not use `pd.to_datetime(col, format="mixed", dayfirst=True)`; pass each format explicitly, or use `COALESCE` over `TRY_CONVERT` styles `23`, `103` and `104`. Add a check that no delivery precedes its booking.
- Money: strip everything except digits and the dot before converting.
- Echo events: `LAG()` over `(order_id, status) ORDER BY event_at`, keep rows where the gap is over 180 seconds.
- Final status: `ROW_NUMBER() OVER (PARTITION BY order_id ORDER BY event_at DESC) = 1`.
- The story is in Q3, Q4 and Q5.
