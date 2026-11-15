SELECT zone, final_status, COUNT(*) AS total_orders
FROM clean.order_final
GROUP BY zone, final_status
ORDER BY zone, final_status;
