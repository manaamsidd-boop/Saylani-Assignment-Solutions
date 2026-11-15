SELECT TOP 5 o.agent_id,
       COUNT(*)                                                  AS orders_with_deposit,
       SUM(CASE WHEN d.amount < o.cod_due THEN 1 ELSE 0 END)     AS short_orders,
       SUM(CASE WHEN d.amount > o.cod_due THEN 1 ELSE 0 END)     AS over_orders,
       SUM(o.cod_due - d.amount)                                 AS total_shortfall
FROM clean.order_final o
JOIN clean.deposits d ON d.order_id = o.order_id
WHERE o.final_status = 'delivered'
GROUP BY o.agent_id
ORDER BY total_shortfall DESC;
