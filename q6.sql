SELECT SUM(o.cod_due)                          AS cash_due,
       SUM(ISNULL(d.amount, 0))                AS cash_collected,
       SUM(o.cod_due) - SUM(ISNULL(d.amount, 0)) AS cash_gap
FROM clean.order_final o
LEFT JOIN clean.deposits d ON d.order_id = o.order_id
WHERE o.final_status = 'delivered';
