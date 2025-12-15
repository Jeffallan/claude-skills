# MySQL Tuning

> Reference for: Database Optimizer
> Load when: MySQL-specific optimizations, InnoDB tuning

## InnoDB Memory Configuration

### Buffer Pool

```sql
-- Recommended: 70-80% of system RAM for dedicated MySQL server
-- For 16GB RAM server:
SET GLOBAL innodb_buffer_pool_size = 12884901888;  -- 12GB

-- Check buffer pool usage
SHOW GLOBAL STATUS LIKE 'Innodb_buffer_pool_%';

-- Buffer pool hit ratio (target: >99%)
SELECT
    (1 - (Innodb_buffer_pool_reads / Innodb_buffer_pool_read_requests)) * 100 as hit_ratio
FROM (
    SELECT
        VARIABLE_VALUE as Innodb_buffer_pool_reads
    FROM performance_schema.global_status
    WHERE VARIABLE_NAME = 'Innodb_buffer_pool_reads'
) reads,
(
    SELECT
        VARIABLE_VALUE as Innodb_buffer_pool_read_requests
    FROM performance_schema.global_status
    WHERE VARIABLE_NAME = 'Innodb_buffer_pool_read_requests'
) requests;

-- Buffer pool instances (for multi-core systems)
-- Recommended: 1 instance per 1GB, max 64
SET GLOBAL innodb_buffer_pool_instances = 8;
```

### Sort and Join Buffers

```sql
-- Sort buffer per connection
SET GLOBAL sort_buffer_size = 2097152;  -- 2MB

-- Join buffer for full joins
SET GLOBAL join_buffer_size = 2097152;  -- 2MB

-- Temporary table size
SET GLOBAL tmp_table_size = 67108864;  -- 64MB
SET GLOBAL max_heap_table_size = 67108864;  -- 64MB

-- Monitor temp table usage
SHOW GLOBAL STATUS LIKE 'Created_tmp%';
```

## Query Cache (Deprecated in 8.0)

```sql
-- MySQL 5.7 and earlier
-- Note: Removed in MySQL 8.0
SET GLOBAL query_cache_type = 1;
SET GLOBAL query_cache_size = 67108864;  -- 64MB

-- Check query cache effectiveness
SHOW STATUS LIKE 'Qcache%';

-- Query cache hit ratio
SELECT
    Qcache_hits / (Qcache_hits + Com_select) * 100 as cache_hit_ratio
FROM (
    SELECT VARIABLE_VALUE as Qcache_hits
    FROM performance_schema.global_status
    WHERE VARIABLE_NAME = 'Qcache_hits'
) hits,
(
    SELECT VARIABLE_VALUE as Com_select
    FROM performance_schema.global_status
    WHERE VARIABLE_NAME = 'Com_select'
) selects;
```

## InnoDB Performance Settings

### Log Files and Flushing

```sql
-- InnoDB log file size (larger = better write performance)
-- Recommended: 1-2GB for write-heavy workloads
SET GLOBAL innodb_log_file_size = 1073741824;  -- 1GB

-- Log buffer size
SET GLOBAL innodb_log_buffer_size = 16777216;  -- 16MB

-- Flush method (O_DIRECT for dedicated server, avoids double buffering)
-- Set in my.cnf
innodb_flush_method = O_DIRECT

-- Flush log at transaction commit
-- 1 = full ACID (default, safest)
-- 2 = write to OS cache, flush every second
-- 0 = write and flush every second (fastest, risk data loss)
SET GLOBAL innodb_flush_log_at_trx_commit = 1;

-- For replication slaves or analytics (trade safety for speed)
SET GLOBAL innodb_flush_log_at_trx_commit = 2;
```

### I/O Configuration

```sql
-- Read I/O threads
SET GLOBAL innodb_read_io_threads = 8;

-- Write I/O threads
SET GLOBAL innodb_write_io_threads = 8;

-- I/O capacity (IOPS your storage can handle)
-- For SSD: 5000-20000
SET GLOBAL innodb_io_capacity = 10000;
SET GLOBAL innodb_io_capacity_max = 20000;

-- Flush method for optimal I/O
-- my.cnf:
innodb_flush_method = O_DIRECT
innodb_flush_neighbors = 0  -- Disable for SSD
```

### Thread Configuration

```sql
-- Max connections
SET GLOBAL max_connections = 200;

-- Thread cache (reuse threads)
SET GLOBAL thread_cache_size = 100;

-- Check thread cache effectiveness
SHOW STATUS LIKE 'Threads_%';
SHOW STATUS LIKE 'Connections';

-- Thread cache hit ratio (target: >90%)
SELECT
    (1 - (Threads_created / Connections)) * 100 as thread_cache_hit_ratio
FROM (
    SELECT VARIABLE_VALUE as Threads_created
    FROM performance_schema.global_status
    WHERE VARIABLE_NAME = 'Threads_created'
) created,
(
    SELECT VARIABLE_VALUE as Connections
    FROM performance_schema.global_status
    WHERE VARIABLE_NAME = 'Connections'
) conns;
```

## Query Optimization

### Slow Query Log

```sql
-- Enable slow query logging
SET GLOBAL slow_query_log = 'ON';
SET GLOBAL long_query_time = 1.0;  -- Log queries > 1 second
SET GLOBAL log_queries_not_using_indexes = 'ON';

-- Slow query log file location
SET GLOBAL slow_query_log_file = '/var/log/mysql/slow-query.log';

-- Analyze slow query log with pt-query-digest
-- $ pt-query-digest /var/log/mysql/slow-query.log

-- Check slow query status
SHOW GLOBAL STATUS LIKE 'Slow_queries';
```

### Performance Schema

```sql
-- Enable performance schema (my.cnf)
performance_schema = ON

-- Top queries by total execution time
SELECT
    DIGEST_TEXT,
    COUNT_STAR as exec_count,
    ROUND(AVG_TIMER_WAIT / 1000000000000, 3) as avg_time_sec,
    ROUND(SUM_TIMER_WAIT / 1000000000000, 3) as total_time_sec,
    ROUND((SUM_TIMER_WAIT / SUM(SUM_TIMER_WAIT) OVER ()) * 100, 2) as pct
FROM performance_schema.events_statements_summary_by_digest
ORDER BY SUM_TIMER_WAIT DESC
LIMIT 10;

-- Full table scans
SELECT * FROM sys.statements_with_full_table_scans
ORDER BY exec_count DESC
LIMIT 10;

-- Tables with high I/O
SELECT
    object_schema,
    object_name,
    count_read,
    count_write,
    count_fetch,
    SUM_TIMER_WAIT / 1000000000000 as total_latency_sec
FROM performance_schema.table_io_waits_summary_by_table
WHERE object_schema NOT IN ('mysql', 'performance_schema', 'sys')
ORDER BY SUM_TIMER_WAIT DESC
LIMIT 10;
```

## Index Optimization

### Index Statistics

```sql
-- Update index statistics
ANALYZE TABLE users;

-- Check index cardinality
SHOW INDEX FROM users;

-- Find duplicate/redundant indexes
SELECT
    a.table_schema,
    a.table_name,
    a.index_name as index1,
    a.column_name,
    b.index_name as index2
FROM information_schema.statistics a
JOIN information_schema.statistics b
    ON a.table_schema = b.table_schema
    AND a.table_name = b.table_name
    AND a.seq_in_index = b.seq_in_index
    AND a.column_name = b.column_name
    AND a.index_name != b.index_name
WHERE a.table_schema NOT IN ('mysql', 'information_schema', 'performance_schema', 'sys')
ORDER BY a.table_schema, a.table_name, a.index_name;

-- Find unused indexes
SELECT
    object_schema,
    object_name,
    index_name
FROM performance_schema.table_io_waits_summary_by_index_usage
WHERE index_name IS NOT NULL
  AND count_star = 0
  AND object_schema NOT IN ('mysql', 'performance_schema', 'sys')
ORDER BY object_schema, object_name;
```

### Covering Indexes

```sql
-- Create covering index
CREATE INDEX idx_users_email_name_created
ON users(email, name, created_at);

-- Query can use covering index
EXPLAIN
SELECT name, created_at FROM users WHERE email = 'user@example.com';
-- Look for "Using index" in Extra column

-- Force index usage for testing
SELECT name FROM users FORCE INDEX (idx_users_email_name_created)
WHERE email = 'user@example.com';
```

## Partitioning

### Range Partitioning

```sql
-- Create partitioned table
CREATE TABLE events (
    id BIGINT NOT NULL AUTO_INCREMENT,
    event_type VARCHAR(50),
    created_at DATETIME NOT NULL,
    data JSON,
    PRIMARY KEY (id, created_at)
) PARTITION BY RANGE (YEAR(created_at)) (
    PARTITION p2023 VALUES LESS THAN (2024),
    PARTITION p2024 VALUES LESS THAN (2025),
    PARTITION p2025 VALUES LESS THAN (2026),
    PARTITION pmax VALUES LESS THAN MAXVALUE
);

-- Query with partition pruning
EXPLAIN PARTITIONS
SELECT * FROM events
WHERE created_at >= '2024-01-01' AND created_at < '2024-02-01';
-- Should show "partitions: p2024"

-- Add new partition
ALTER TABLE events
ADD PARTITION (PARTITION p2026 VALUES LESS THAN (2027));

-- Drop old partition (fast delete)
ALTER TABLE events DROP PARTITION p2023;
```

### List Partitioning

```sql
-- Partition by discrete values
CREATE TABLE orders (
    id BIGINT NOT NULL AUTO_INCREMENT,
    user_id BIGINT,
    status VARCHAR(20),
    PRIMARY KEY (id, status)
) PARTITION BY LIST COLUMNS(status) (
    PARTITION p_pending VALUES IN ('pending', 'processing'),
    PARTITION p_completed VALUES IN ('completed', 'shipped'),
    PARTITION p_cancelled VALUES IN ('cancelled', 'refunded')
);
```

## Replication Optimization

### Binary Log Settings

```sql
-- Binary log format
SET GLOBAL binlog_format = 'ROW';  -- ROW, STATEMENT, or MIXED

-- Binary log cache size
SET GLOBAL binlog_cache_size = 1048576;  -- 1MB per transaction

-- Sync binary log (durability vs performance)
SET GLOBAL sync_binlog = 1;  -- Safest, sync after each commit
-- sync_binlog = 0  -- Fastest, let OS handle flushing

-- Expire binary logs after N days
SET GLOBAL binlog_expire_logs_seconds = 604800;  -- 7 days
```

### Replication Lag Monitoring

```sql
-- On replica: Check replication lag
SHOW SLAVE STATUS\G

-- Parse seconds behind master
SELECT
    IF(Slave_IO_Running = 'Yes' AND Slave_SQL_Running = 'Yes',
       Seconds_Behind_Master,
       NULL) as replication_lag_seconds
FROM (SHOW SLAVE STATUS) s;

-- Parallel replication (MySQL 8.0+)
SET GLOBAL slave_parallel_workers = 4;
SET GLOBAL slave_parallel_type = 'LOGICAL_CLOCK';
```

## Table Optimization

### Table Maintenance

```sql
-- Optimize table (rebuilds, reclaims space)
OPTIMIZE TABLE users;

-- Check table for errors
CHECK TABLE users;

-- Repair table if corrupted
REPAIR TABLE users;

-- Analyze table statistics
ANALYZE TABLE users;

-- Check fragmentation
SELECT
    table_schema,
    table_name,
    ROUND(data_length / 1024 / 1024, 2) as data_mb,
    ROUND(data_free / 1024 / 1024, 2) as free_mb,
    ROUND(data_free / data_length * 100, 2) as fragmentation_pct
FROM information_schema.tables
WHERE table_schema NOT IN ('mysql', 'information_schema', 'performance_schema', 'sys')
  AND data_free > 0
ORDER BY fragmentation_pct DESC;
```

### Table Compression

```sql
-- InnoDB compression (requires ROW_FORMAT=COMPRESSED)
CREATE TABLE compressed_logs (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    message TEXT,
    created_at DATETIME
) ROW_FORMAT=COMPRESSED KEY_BLOCK_SIZE=8;

-- Check compression ratio
SELECT
    table_schema,
    table_name,
    ROUND(data_length / 1024 / 1024, 2) as data_mb,
    ROUND(index_length / 1024 / 1024, 2) as index_mb,
    create_options
FROM information_schema.tables
WHERE row_format = 'Compressed';
```

## Configuration File Example

```ini
# my.cnf - Production optimized for 16GB RAM server

[mysqld]
# InnoDB Settings
innodb_buffer_pool_size = 12G
innodb_buffer_pool_instances = 8
innodb_log_file_size = 1G
innodb_log_buffer_size = 16M
innodb_flush_log_at_trx_commit = 1
innodb_flush_method = O_DIRECT
innodb_flush_neighbors = 0

# I/O Settings
innodb_read_io_threads = 8
innodb_write_io_threads = 8
innodb_io_capacity = 10000
innodb_io_capacity_max = 20000

# Connection Settings
max_connections = 200
thread_cache_size = 100

# Query Cache (MySQL 5.7)
# query_cache_type = 1
# query_cache_size = 64M

# Temporary Tables
tmp_table_size = 64M
max_heap_table_size = 64M

# Slow Query Log
slow_query_log = ON
long_query_time = 1
log_queries_not_using_indexes = ON

# Binary Log
binlog_format = ROW
sync_binlog = 1
binlog_expire_logs_seconds = 604800

# Performance Schema
performance_schema = ON

# Character Set
character_set_server = utf8mb4
collation_server = utf8mb4_unicode_ci
