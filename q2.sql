SELECT zone,
       COUNT(*)                                              AS total_delivered,
       SUM(on_time)                                          AS on_time_deliveries,
       CAST(100.0 * SUM(on_time) / COUNT(*) AS DECIMAL(5,2)) AS on_time_rate,
       CAST(AVG(CAST(days_late AS FLOAT)) AS DECIMAL(5,2))   AS avg_days_late
FROM clean.order_final
WHERE final_status = 'delivered'
GROUP BY zone
ORDER BY on_time_rate DESC;
