# PostgreSQL Tuning

> Reference for: Database Optimizer
> Load when: PostgreSQL-specific optimizations, configuration tuning

## Memory Configuration

### Shared Buffers

```sql
-- Recommended: 25% of system RAM (up to 40% for dedicated DB server)
-- For 16GB RAM server:
ALTER SYSTEM SET shared_buffers = '4GB';

-- Check current setting
SHOW shared_buffers;

-- Monitor buffer hit ratio (target: >99%)
SELECT
    sum(heap_blks_read) as heap_read,
    sum(heap_blks_hit) as heap_hit,
    round(sum(heap_blks_hit) / nullif(sum(heap_blks_hit) + sum(heap_blks_read), 0) * 100, 2) as cache_hit_ratio
FROM pg_statio_user_tables;
```

### Work Memory

```sql
-- Per-operation memory for sorting/hashing
-- Recommended: (Total RAM * 0.25) / max_connections
-- For 16GB RAM, 100 connections: ~40MB
ALTER SYSTEM SET work_mem = '40MB';

-- Monitor sorts
SELECT
    query,
    calls,
    total_exec_time,
    mean_exec_time,
    min_exec_time,
    max_exec_time
FROM pg_stat_statements
WHERE query LIKE '%ORDER BY%' OR query LIKE '%GROUP BY%'
ORDER BY total_exec_time DESC
LIMIT 10;

-- Set per-session for large operations
SET work_mem = '256MB';
SELECT ... ORDER BY ... LIMIT 1000;
RESET work_mem;
```

### Maintenance Work Memory

```sql
-- For VACUUM, CREATE INDEX, ALTER TABLE
-- Recommended: 1-2GB for production systems
ALTER SYSTEM SET maintenance_work_mem = '2GB';

-- Autovacuum workers use proportional amount
ALTER SYSTEM SET autovacuum_work_mem = '512MB';
```

### Effective Cache Size

```sql
-- Planner hint for available OS cache
-- Recommended: 50-75% of total RAM
-- For 16GB RAM:
ALTER SYSTEM SET effective_cache_size = '12GB';
```

## Query Planner Settings

### Statistics Target

```sql
-- Default is 100, increase for better estimates on complex queries
ALTER SYSTEM SET default_statistics_target = 200;

-- Per-column statistics for specific columns
ALTER TABLE users ALTER COLUMN email SET STATISTICS 500;

-- Force statistics update
ANALYZE users;

-- Check statistics quality
SELECT
    schemaname, tablename, attname,
    n_distinct, correlation
FROM pg_stats
WHERE tablename = 'users';
```

### Parallel Query Configuration

```sql
-- Enable parallel queries
ALTER SYSTEM SET max_parallel_workers_per_gather = 4;
ALTER SYSTEM SET max_parallel_workers = 8;
ALTER SYSTEM SET parallel_setup_cost = 100;
ALTER SYSTEM SET parallel_tuple_cost = 0.01;

-- Minimum rows to consider parallel execution
ALTER SYSTEM SET min_parallel_table_scan_size = '8MB';
ALTER SYSTEM SET min_parallel_index_scan_size = '512kB';

-- Check if query uses parallel execution
EXPLAIN (ANALYZE, BUFFERS)
SELECT COUNT(*) FROM large_table WHERE condition = 'value';
-- Look for "Parallel Seq Scan" or "Gather" nodes
```

### Join and Scan Methods

```sql
-- Enable all join methods (usually all enabled by default)
ALTER SYSTEM SET enable_hashjoin = on;
ALTER SYSTEM SET enable_mergejoin = on;
ALTER SYSTEM SET enable_nestloop = on;

-- Cost parameters (adjust based on hardware)
ALTER SYSTEM SET random_page_cost = 1.1;  -- For SSD (default 4.0 is for HDD)
ALTER SYSTEM SET seq_page_cost = 1.0;

-- Disable methods for testing (don't do in production)
SET enable_seqscan = off;  -- Force index usage for testing
```

## Write Performance Optimization

### WAL Configuration

```sql
-- WAL write strategy
ALTER SYSTEM SET wal_buffers = '16MB';
ALTER SYSTEM SET wal_writer_delay = '200ms';

-- Checkpoint configuration
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
ALTER SYSTEM SET max_wal_size = '2GB';
ALTER SYSTEM SET min_wal_size = '1GB';

-- Monitor checkpoints
SELECT
    checkpoints_timed,
    checkpoints_req,
    checkpoint_write_time,
    checkpoint_sync_time,
    buffers_checkpoint,
    buffers_clean,
    buffers_backend
FROM pg_stat_bgwriter;

-- Too many requested checkpoints = increase max_wal_size
```

### Commit Delays

```sql
-- Group commits (trade latency for throughput)
ALTER SYSTEM SET commit_delay = 10000;  -- 10ms
ALTER SYSTEM SET commit_siblings = 5;

-- Asynchronous commit (trade durability for speed)
-- Use cautiously - risk losing recent commits on crash
ALTER SYSTEM SET synchronous_commit = 'off';

-- Or per-transaction
BEGIN;
SET LOCAL synchronous_commit = 'off';
INSERT INTO logs (...) VALUES (...);
COMMIT;
```

## VACUUM and Autovacuum

### Autovacuum Configuration

```sql
-- Enable autovacuum (should always be on)
ALTER SYSTEM SET autovacuum = on;

-- Autovacuum worker settings
ALTER SYSTEM SET autovacuum_max_workers = 4;
ALTER SYSTEM SET autovacuum_naptime = '30s';

-- Thresholds for triggering autovacuum
ALTER SYSTEM SET autovacuum_vacuum_scale_factor = 0.1;  -- 10% dead tuples
ALTER SYSTEM SET autovacuum_vacuum_threshold = 50;

-- Analyze thresholds
ALTER SYSTEM SET autovacuum_analyze_scale_factor = 0.05;  -- 5% changed
ALTER SYSTEM SET autovacuum_analyze_threshold = 50;

-- Per-table autovacuum settings for high-churn tables
ALTER TABLE busy_table SET (
    autovacuum_vacuum_scale_factor = 0.01,  -- More aggressive
    autovacuum_vacuum_cost_delay = 2,       -- Faster vacuum
    autovacuum_vacuum_cost_limit = 1000
);
```

### Manual Vacuum Operations

```sql
-- Full vacuum (locks table, reclaims space)
VACUUM FULL users;  -- Use sparingly, requires exclusive lock

-- Regular vacuum (non-locking)
VACUUM (ANALYZE, VERBOSE) users;

-- Check table bloat
SELECT
    schemaname, tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as total_size,
    pg_size_pretty(pg_relation_size(schemaname||'.'||tablename)) as table_size,
    n_dead_tup,
    n_live_tup,
    round(n_dead_tup * 100.0 / NULLIF(n_live_tup + n_dead_tup, 0), 2) as dead_pct
FROM pg_stat_user_tables
WHERE n_live_tup > 0
ORDER BY n_dead_tup DESC;

-- Monitor autovacuum activity
SELECT
    schemaname, relname,
    last_vacuum, last_autovacuum,
    last_analyze, last_autoanalyze,
    vacuum_count, autovacuum_count,
    analyze_count, autoanalyze_count
FROM pg_stat_user_tables
ORDER BY last_autovacuum DESC NULLS LAST;
```

## Connection Pooling

### Configuration

```sql
-- Max connections (keep reasonable to manage memory)
ALTER SYSTEM SET max_connections = 200;

-- Reserved connections for superuser
ALTER SYSTEM SET superuser_reserved_connections = 3;

-- Connection lifecycle
ALTER SYSTEM SET idle_in_transaction_session_timeout = '5min';
ALTER SYSTEM SET statement_timeout = '30s';  -- Per-query timeout

-- Monitor connections
SELECT
    state,
    count(*),
    max(now() - state_change) as max_idle_time
FROM pg_stat_activity
WHERE state IS NOT NULL
GROUP BY state;

-- Find long-running queries
SELECT
    pid,
    now() - pg_stat_activity.query_start AS duration,
    query,
    state
FROM pg_stat_activity
WHERE (now() - pg_stat_activity.query_start) > interval '5 minutes'
  AND state != 'idle';
```

## Lock Management

### Lock Monitoring

```sql
-- Check current locks
SELECT
    locktype,
    relation::regclass,
    mode,
    granted,
    pid,
    pg_blocking_pids(pid) as blocked_by
FROM pg_locks
WHERE NOT granted
ORDER BY relation;

-- Find blocking queries
SELECT
    blocked_locks.pid AS blocked_pid,
    blocked_activity.usename AS blocked_user,
    blocking_locks.pid AS blocking_pid,
    blocking_activity.usename AS blocking_user,
    blocked_activity.query AS blocked_statement,
    blocking_activity.query AS blocking_statement
FROM pg_catalog.pg_locks blocked_locks
JOIN pg_catalog.pg_stat_activity blocked_activity ON blocked_activity.pid = blocked_locks.pid
JOIN pg_catalog.pg_locks blocking_locks ON blocking_locks.locktype = blocked_locks.locktype
    AND blocking_locks.relation = blocked_locks.relation
    AND blocking_locks.pid != blocked_locks.pid
JOIN pg_catalog.pg_stat_activity blocking_activity ON blocking_activity.pid = blocking_locks.pid
WHERE NOT blocked_locks.granted;

-- Deadlock configuration
ALTER SYSTEM SET deadlock_timeout = '1s';
ALTER SYSTEM SET log_lock_waits = on;
```

## Partitioning

### Range Partitioning

```sql
-- Create partitioned table
CREATE TABLE events (
    id BIGSERIAL,
    event_type VARCHAR(50),
    created_at TIMESTAMP NOT NULL,
    data JSONB
) PARTITION BY RANGE (created_at);

-- Create partitions
CREATE TABLE events_2024_01 PARTITION OF events
    FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');

CREATE TABLE events_2024_02 PARTITION OF events
    FOR VALUES FROM ('2024-02-01') TO ('2024-03-01');

-- Create indexes on partitions
CREATE INDEX idx_events_2024_01_type ON events_2024_01(event_type);
CREATE INDEX idx_events_2024_02_type ON events_2024_02(event_type);

-- Query uses partition pruning
EXPLAIN (ANALYZE)
SELECT * FROM events
WHERE created_at >= '2024-01-15' AND created_at < '2024-01-20';
-- Should show "Partitions pruned: X"
```

## Performance Monitoring

### Key Metrics Queries

```sql
-- pg_stat_statements (install extension first)
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

-- Top slow queries
SELECT
    round(total_exec_time::numeric, 2) as total_time,
    calls,
    round(mean_exec_time::numeric, 2) as mean_time,
    round((100 * total_exec_time / sum(total_exec_time) OVER ())::numeric, 2) as pct,
    query
FROM pg_stat_statements
ORDER BY total_exec_time DESC
LIMIT 10;

-- Cache hit ratio by table
SELECT
    schemaname,
    tablename,
    heap_blks_hit,
    heap_blks_read,
    round(100.0 * heap_blks_hit / NULLIF(heap_blks_hit + heap_blks_read, 0), 2) as cache_hit_pct
FROM pg_statio_user_tables
WHERE heap_blks_hit + heap_blks_read > 0
ORDER BY heap_blks_read DESC;

-- Index usage statistics
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch,
    pg_size_pretty(pg_relation_size(indexrelid)) as size
FROM pg_stat_user_indexes
ORDER BY idx_scan DESC;
```

## Configuration File Example

```ini
# postgresql.conf - Production optimized for 16GB RAM server

# Memory
shared_buffers = 4GB
effective_cache_size = 12GB
work_mem = 40MB
maintenance_work_mem = 2GB

# WAL
wal_buffers = 16MB
checkpoint_completion_target = 0.9
max_wal_size = 2GB

# Query Planner
default_statistics_target = 200
random_page_cost = 1.1  # SSD
effective_io_concurrency = 200  # SSD

# Parallel Queries
max_parallel_workers_per_gather = 4
max_parallel_workers = 8

# Connections
max_connections = 200

# Logging
log_min_duration_statement = 1000  # Log queries > 1s
log_line_prefix = '%t [%p]: [%l-1] user=%u,db=%d,app=%a,client=%h '
log_checkpoints = on
log_lock_waits = on
