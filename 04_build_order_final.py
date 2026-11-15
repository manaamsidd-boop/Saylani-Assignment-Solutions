from db import banner, done, fetch_df, run_sql, step, table_count

banner("STEP 4 - BUILDING clean.order_final")

step(1, "Find each order's LAST event")
run_sql("IF OBJECT_ID('clean.order_final','U') IS NOT NULL DROP TABLE clean.order_final;")
run_sql("""
    WITH last_event AS (
        SELECT order_id, status, event_at,
               ROW_NUMBER() OVER (PARTITION BY order_id
                                  ORDER BY event_at DESC) AS rn
        FROM clean.events
    )
    SELECT
        o.order_id,
        o.zone,
        o.agent_id,
        o.booked_date,
        o.promised_date,
        o.cod_amount,
        ISNULL(le.status, 'no_event')                        AS final_status,
        CASE WHEN le.status = 'delivered'
             THEN CAST(le.event_at AS DATE) END              AS delivered_date,
        CASE WHEN le.status = 'delivered'
             THEN o.cod_amount ELSE 0 END                    AS cod_due,
        CASE WHEN le.status = 'delivered'
                  AND CAST(le.event_at AS DATE) <= o.promised_date
             THEN 1 ELSE 0 END                               AS on_time,
        CASE WHEN le.status = 'delivered'
                  AND CAST(le.event_at AS DATE) > o.promised_date
             THEN DATEDIFF(DAY, o.promised_date, CAST(le.event_at AS DATE))
             ELSE 0 END                                      AS days_late
    INTO clean.order_final
    FROM clean.orders o
    LEFT JOIN last_event le
           ON le.order_id = o.order_id AND le.rn = 1;
""")
run_sql("ALTER TABLE clean.order_final ALTER COLUMN order_id NVARCHAR(20) NOT NULL;")
run_sql("ALTER TABLE clean.order_final ADD CONSTRAINT pk_order_final PRIMARY KEY (order_id);")

print(f"\n  clean.order_final: {table_count('clean.order_final'):,} rows "
      f"(one per order in clean.orders - {table_count('clean.orders'):,})")

step(2, "What did we just build?")
print()
print(fetch_df("""
    SELECT final_status,
           COUNT(*)         AS orders,
           SUM(cod_due)     AS cod_due,
           SUM(cod_amount)  AS cod_on_the_orders
    FROM clean.order_final
    GROUP BY final_status
    ORDER BY orders DESC;
""").to_string(index=False))

step(3, "The sanity check that catches a broken date parse")
bad = fetch_df("""
    SELECT COUNT(*) AS n FROM clean.order_final
    WHERE delivered_date < booked_date
""").n[0]
print(f"\n  orders 'delivered' before they were booked: {bad}  (must be 0)")
if bad:
    raise SystemExit("  Time is running backwards. Fix step 3 before continuing.")

done("One trustworthy row per order. Every question now reads from here.\n"
     "     Next:  python 05_answer_the_questions.py")
