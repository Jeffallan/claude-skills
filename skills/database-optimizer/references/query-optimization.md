# Query Optimization

> Reference for: Database Optimizer
> Load when: Analyzing slow queries, execution plans, query rewrites

## Execution Plan Analysis

### PostgreSQL EXPLAIN ANALYZE

```sql
-- Get actual execution statistics
EXPLAIN (ANALYZE, BUFFERS, VERBOSE, TIMING)
SELECT u.id, u.name, COUNT(o.id) as order_count
FROM users u
LEFT JOIN orders o ON u.id = o.user_id
WHERE u.created_at > NOW() - INTERVAL '30 days'
GROUP BY u.id, u.name
HAVING COUNT(o.id) > 5;

-- Key metrics to examine:
-- 1. Actual time vs Planning time
-- 2. Rows estimate vs Actual rows (cardinality)
-- 3. Buffers (shared hits vs reads)
-- 4. Sequential Scans vs Index Scans
-- 5. Join methods (Nested Loop, Hash Join, Merge Join)
```

### MySQL EXPLAIN

```sql
-- Basic execution plan
EXPLAIN SELECT * FROM orders
WHERE user_id = 123 AND status = 'pending';

-- JSON format for detailed analysis
EXPLAIN FORMAT=JSON
SELECT u.name, o.total
FROM users u
INNER JOIN orders o ON u.id = o.user_id
WHERE o.created_at > '2024-01-01';

-- Analyze actual execution (MySQL 8.0+)
EXPLAIN ANALYZE
SELECT * FROM products
WHERE category_id = 5
ORDER BY price DESC
LIMIT 10;
```

## Query Rewriting Patterns

### Eliminate Subqueries

```sql
-- BEFORE (Slow - executes subquery for each row)
SELECT *
FROM orders o
WHERE total > (
    SELECT AVG(total)
    FROM orders
    WHERE user_id = o.user_id
);

-- AFTER (Fast - single join with window function)
WITH user_averages AS (
    SELECT user_id, AVG(total) as avg_total
    FROM orders
    GROUP BY user_id
)
SELECT o.*
FROM orders o
INNER JOIN user_averages ua ON o.user_id = ua.user_id
WHERE o.total > ua.avg_total;
```

### Optimize JOIN Order

```sql
-- BEFORE (Cartesian product then filter)
SELECT p.name, c.name, s.stock
FROM products p, categories c, stock s
WHERE p.category_id = c.id
  AND p.id = s.product_id
  AND c.active = true;

-- AFTER (Filter first, then join)
SELECT p.name, c.name, s.stock
FROM categories c
INNER JOIN products p ON p.category_id = c.id
INNER JOIN stock s ON s.product_id = p.id
WHERE c.active = true;
```

### Use EXISTS Instead of IN

```sql
-- BEFORE (Slow - materializes entire subquery)
SELECT * FROM users
WHERE id IN (
    SELECT DISTINCT user_id
    FROM orders
    WHERE total > 1000
);

-- AFTER (Fast - short-circuits on first match)
SELECT * FROM users u
WHERE EXISTS (
    SELECT 1 FROM orders o
    WHERE o.user_id = u.id
    AND o.total > 1000
);
```

### Optimize DISTINCT

```sql
-- BEFORE (Sorts entire result set)
SELECT DISTINCT u.email
FROM users u
INNER JOIN orders o ON u.id = o.user_id
WHERE o.status = 'completed';

-- AFTER (Uses index for uniqueness)
SELECT u.email
FROM users u
WHERE EXISTS (
    SELECT 1 FROM orders o
    WHERE o.user_id = u.id
    AND o.status = 'completed'
);
```

## CTE Optimization

### Materialized vs Inline CTEs

```sql
-- PostgreSQL: Force materialization for reuse
WITH expensive_calculation AS MATERIALIZED (
    SELECT user_id,
           SUM(total) as lifetime_value,
           COUNT(*) as order_count
    FROM orders
    WHERE created_at > NOW() - INTERVAL '1 year'
    GROUP BY user_id
)
SELECT *
FROM expensive_calculation
WHERE lifetime_value > 10000
   OR order_count > 50;

-- Force inline for single-use CTEs
WITH recent_users AS NOT MATERIALIZED (
    SELECT id FROM users
    WHERE created_at > NOW() - INTERVAL '7 days'
)
SELECT * FROM recent_users;
```

## Window Function Optimization

```sql
-- BEFORE (Multiple subqueries)
SELECT
    o.id,
    o.total,
    (SELECT MAX(total) FROM orders WHERE user_id = o.user_id) as max_total,
    (SELECT AVG(total) FROM orders WHERE user_id = o.user_id) as avg_total
FROM orders o;

-- AFTER (Single window function scan)
SELECT
    id,
    total,
    MAX(total) OVER (PARTITION BY user_id) as max_total,
    AVG(total) OVER (PARTITION BY user_id) as avg_total
FROM orders;
```

## Aggregation Strategies

### Partial Aggregation

```sql
-- For large cardinality groups, pre-aggregate
WITH daily_stats AS (
    SELECT
        DATE(created_at) as day,
        user_id,
        COUNT(*) as daily_orders,
        SUM(total) as daily_total
    FROM orders
    WHERE created_at > NOW() - INTERVAL '90 days'
    GROUP BY DATE(created_at), user_id
)
SELECT
    user_id,
    SUM(daily_orders) as total_orders,
    AVG(daily_total) as avg_daily_total
FROM daily_stats
GROUP BY user_id;
```

## Pagination Optimization

```sql
-- BEFORE (Slow on large offsets)
SELECT * FROM products
ORDER BY created_at DESC
LIMIT 20 OFFSET 10000;

-- AFTER (Keyset pagination - cursor-based)
SELECT * FROM products
WHERE created_at < '2024-01-01 12:00:00'
   OR (created_at = '2024-01-01 12:00:00' AND id < 12345)
ORDER BY created_at DESC, id DESC
LIMIT 20;

-- Create index for keyset pagination
CREATE INDEX idx_products_pagination
ON products (created_at DESC, id DESC);
```

## Query Pattern Red Flags

| Pattern | Issue | Solution |
|---------|-------|----------|
| `SELECT *` | Fetches unnecessary columns | Select only needed columns |
| `OR` conditions | Prevents index usage | Use UNION or separate queries |
| `LIKE '%term%'` | Full table scan | Use full-text search or trigram indexes |
| `WHERE DATE(column) = ...` | Function prevents index usage | Use range: `column >= '2024-01-01' AND column < '2024-01-02'` |
| Large `IN` lists | Inefficient for >100 items | Use temporary table or JOIN |
| Implicit type conversion | Prevents index usage | Match column data types exactly |

## Performance Validation

```sql
-- PostgreSQL: Compare query performance
EXPLAIN (ANALYZE, BUFFERS)
-- your query here

-- Check buffer cache hits
SELECT
    sum(heap_blks_read) as heap_read,
    sum(heap_blks_hit) as heap_hit,
    sum(heap_blks_hit) / (sum(heap_blks_hit) + sum(heap_blks_read)) as ratio
FROM pg_statio_user_tables;

-- MySQL: Check handler statistics
SHOW STATUS LIKE 'Handler%';
FLUSH STATUS;
-- run your query
SHOW STATUS LIKE 'Handler%';
```
