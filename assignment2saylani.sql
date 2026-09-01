-- Muhammad Manaam Siddiqui
-- ============================================================
--  ASSIGNMENT 02 — Joins
--  Database : BikeStores
-- ============================================================


-- ============================================================
--  Question 1
--  Retrieve the product_name, list_price, and category_name
--  for every product.
--  Use production.products and production.categories.
--  Sort the results by product_name ascending.
-- ============================================================

-- Write your query below:
SELECT pr.product_name, pr.list_price, ca.category_name
FROM production.products pr
INNER JOIN production.categories ca
ON pr.category_id = ca.category_id
ORDER BY pr.product_name;



-- ============================================================
--  Question 2
--  Show the customer full name (as full_name), order_id,
--  and order_date for all customers who have placed an order.
--  Use sales.customers and sales.orders.
--  Sort by order_date descending.
-- ============================================================

-- Write your query below:
SELECT cu.first_name || ' ' || cu.last_name AS full_name, ord.order_id, ord.order_date
FROM sales.customers cu
INNER JOIN sales.orders ord
ON cu.customer_id = ord.customer_id
ORDER BY ord.order_date DESC;



-- ============================================================
--  Question 3
--  Retrieve product_name, list_price, category_name, and
--  brand_name for every product.
--  Use production.products, production.categories,
--  and production.brands.
--  Sort by brand_name then product_name (both ascending).
-- ============================================================

-- Write your query below:
SELECT br.brand_name, pr.product_name, pr.list_price, ca.category_name
FROM production.categories ca
INNER JOIN production.products pr
ON ca.category_id = pr.category_id
INNER JOIN production.brands br
ON pr.brand_id = br.brand_id
ORDER BY br.brand_name, pr.product_name;



-- ============================================================
--  Question 4
--  List all products along with their order_id and item_id.
--  Make sure products that have NEVER been ordered also appear
--  in the result (those rows will have NULL for order_id
--  and item_id).
--  Use production.products and sales.order_items.
--  Sort by order_id ascending.
-- ============================================================

-- Write your query below:
SELECT pr.product_name, oi.order_id, oi.item_id
FROM production.products pr
LEFT JOIN sales.order_items oi
ON pr.product_id = oi.product_id
ORDER BY oi.order_id;



-- ============================================================
--  Question 5
--  Using your answer from Question 4 as a base, filter the
--  results to show ONLY the products that have never been
--  ordered.
--  Display only product_id and product_name.
-- ============================================================

-- Write your query below:
SELECT pr.product_id, pr.product_name
FROM production.products pr
LEFT JOIN sales.order_items oi
ON pr.product_id = oi.product_id
WHERE oi.order_id IS NULL;



-- ============================================================
--  Question 6
--  Show all stores along with any orders placed at each store.
--  Display store_name, store_id (from stores), order_id,
--  and order_date.
--  Every store must appear in the result, even if it has
--  no orders yet.
--  Use sales.orders and sales.stores.
-- ============================================================

-- Write your query below:
SELECT st.store_id, st.store_name, ord.order_id, ord.order_date
FROM sales.stores st
LEFT JOIN sales.orders ord
ON st.store_id = ord.store_id;



-- ============================================================
--  Question 7
--  List every staff member alongside their manager's name.
--  Display:
--    • staff full name   (as staff_name)
--    • manager full name (as manager_name)
--  Use only the sales.staffs table.
--  Staff who have no manager should NOT appear in the result.
-- ============================================================

-- Write your query below:
SELECT sf.first_name || ' ' || sf.last_name AS staff_name, mg.first_name || ' ' || mg.last_name AS manager_name
FROM sales.staffs sf
INNER JOIN sales.staffs mg
ON mg.staff_id = sf.manager_id;



-- ============================================================
--  Question 8
--  Generate every possible combination of store name and
--  brand name.
--  Display store_name and brand_name.
--  Use sales.stores and production.brands.
--  How many total rows do you expect?
--  Write the expected count as a comment next to your query.
-- ============================================================

-- Write your query below:
SELECT st.store_name, br.brand_name
FROM sales.stores st
CROSS JOIN production.brands br;

-- 27 Rows Returned



-- ============================================================
--  Question 9
--  Retrieve the customer full name (as full_name), order_id,
--  order_date, product_name, and list_price for every order
--  that has been placed.
--  Use sales.customers, sales.orders, sales.order_items,
--  and production.products.
--  Sort by order_date ascending, then full_name ascending.
-- ============================================================

-- Write your query below:
SELECT ord.order_id, cu.first_name || ' ' || cu.last_name AS full_name, ord.order_date, pr.product_name, pr.list_price
FROM sales.customers cu
INNER JOIN sales.orders ord
	ON cu.customer_id = ord.customer_id
INNER JOIN sales.order_items oi
	ON ord.order_id = oi.order_id
INNER JOIN production.products pr
	ON oi.product_id = pr.product_id
ORDER BY ord.order_date, full_name;
