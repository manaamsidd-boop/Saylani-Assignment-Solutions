SELECT o.order_id, o.agent_id, o.final_status, d.amount AS total_deposited
FROM clean.order_final o
JOIN clean.deposits d ON d.order_id = o.order_id
WHERE o.final_status <> 'delivered'
ORDER BY o.order_id;
