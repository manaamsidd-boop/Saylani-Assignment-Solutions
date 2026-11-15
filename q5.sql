SELECT COUNT(*)      AS orders_without_deposit,
       SUM(cod_due)  AS total_rupees_at_risk
FROM clean.order_final o
WHERE o.final_status = 'delivered' AND o.cod_due > 0
  AND NOT EXISTS (SELECT 1 FROM clean.deposits d WHERE d.order_id = o.order_id);
