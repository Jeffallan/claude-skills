# Monitoring and Analysis

> Reference for: Database Optimizer
> Load when: Performance metrics, diagnostics, troubleshooting

## PostgreSQL Monitoring

### Essential Extensions

```sql
-- Install performance monitoring extensions
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;
CREATE EXTENSION IF NOT EXISTS pg_buffercache;
CREATE EXTENSION IF NOT EXISTS pg_trgm;  -- For similarity searches

-- Reset statistics
SELECT pg_stat_statements_reset();
SELECT pg_stat_reset();
```

### Query Performance Tracking

```sql
-- Top queries by total time
SELECT
    substring(query, 1, 100) as short_query,
    round(total_exec_time::numeric, 2) as total_time_ms,
    calls,
    round(mean_exec_time::numeric, 2) as mean_time_ms,
    round(stddev_exec_time::numeric, 2) as stddev_ms,
    round((100 * total_exec_time / sum(total_exec_time) OVER ())::numeric, 2) as pct_total
FROM pg_stat_statements
WHERE query NOT LIKE '%pg_stat_statements%'
ORDER BY total_exec_time DESC
LIMIT 20;

-- Queries with high variance
SELECT
    substring(query, 1, 100) as short_query,
    calls,
    round(mean_exec_time::numeric, 2) as mean_ms,
    round(stddev_exec_time::numeric, 2) as stddev_ms,
    round(max_exec_time::numeric, 2) as max_ms,
    round((stddev_exec_time / NULLIF(mean_exec_time, 0))::numeric, 2) as coeff_var
FROM pg_stat_statements
WHERE calls > 100
  AND stddev_exec_time > mean_exec_time * 0.5
ORDER BY stddev_exec_time DESC
LIMIT 20;

-- I/O intensive queries
SELECT
    substring(query, 1, 100) as short_query,
    calls,
    shared_blks_hit,
    shared_blks_read,
    shared_blks_written,
    round((shared_blks_read::numeric / NULLIF(calls, 0)), 2) as reads_per_call,
    round((shared_blks_hit / NULLIF(shared_blks_hit + shared_blks_read, 0)::numeric * 100), 2) as cache_hit_pct
FROM pg_stat_statements
WHERE shared_blks_read > 0
ORDER BY shared_blks_read DESC
LIMIT 20;
```

### Connection and Lock Monitoring

```sql
-- Current activity
SELECT
    pid,
    usename,
    application_name,
    client_addr,
    state,
    state_change,
    query_start,
    now() - query_start as duration,
    wait_event_type,
    wait_event,
    substring(query, 1, 100) as query
FROM pg_stat_activity
WHERE state != 'idle'
ORDER BY query_start;

-- Blocking queries
SELECT
    blocked_locks.pid AS blocked_pid,
    blocked_activity.usename AS blocked_user,
    blocking_locks.pid AS blocking_pid,
    blocking_activity.usename AS blocking_user,
    blocked_activity.query AS blocked_query,
    blocking_activity.query AS blocking_query,
    blocked_activity.application_name AS blocked_app
FROM pg_catalog.pg_locks blocked_locks
JOIN pg_catalog.pg_stat_activity blocked_activity ON blocked_activity.pid = blocked_locks.pid
JOIN pg_catalog.pg_locks blocking_locks
    ON blocking_locks.locktype = blocked_locks.locktype
    AND blocking_locks.database IS NOT DISTINCT FROM blocked_locks.database
    AND blocking_locks.relation IS NOT DISTINCT FROM blocked_locks.relation
    AND blocking_locks.page IS NOT DISTINCT FROM blocked_locks.page
    AND blocking_locks.tuple IS NOT DISTINCT FROM blocked_locks.tuple
    AND blocking_locks.virtualxid IS NOT DISTINCT FROM blocked_locks.virtualxid
    AND blocking_locks.transactionid IS NOT DISTINCT FROM blocked_locks.transactionid
    AND blocking_locks.classid IS NOT DISTINCT FROM blocked_locks.classid
    AND blocking_locks.objid IS NOT DISTINCT FROM blocked_locks.objid
    AND blocking_locks.objsubid IS NOT DISTINCT FROM blocked_locks.objsubid
    AND blocking_locks.pid != blocked_locks.pid
JOIN pg_catalog.pg_stat_activity blocking_activity ON blocking_activity.pid = blocking_locks.pid
WHERE NOT blocked_locks.granted;

-- Wait events summary
SELECT
    wait_event_type,
    wait_event,
    count(*) as waiting_connections
FROM pg_stat_activity
WHERE wait_event IS NOT NULL
GROUP BY wait_event_type, wait_event
ORDER BY waiting_connections DESC;
```

### Table and Index Statistics

```sql
-- Table bloat and dead tuples
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as total_size,
    n_live_tup,
    n_dead_tup,
    round(n_dead_tup * 100.0 / NULLIF(n_live_tup + n_dead_tup, 0), 2) as dead_pct,
    last_vacuum,
    last_autovacuum,
    last_analyze,
    last_autoanalyze
FROM pg_stat_user_tables
WHERE n_live_tup > 1000
ORDER BY n_dead_tup DESC;

-- Index usage and efficiency
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch,
    pg_size_pretty(pg_relation_size(indexrelid)) as size,
    CASE
        WHEN idx_scan = 0 THEN 'UNUSED'
        WHEN idx_tup_read = 0 THEN 'NEVER_READ'
        ELSE 'ACTIVE'
    END as status
FROM pg_stat_user_indexes
ORDER BY pg_relation_size(indexrelid) DESC;

-- Sequential scans on large tables
SELECT
    schemaname,
    tablename,
    seq_scan,
    seq_tup_read,
    idx_scan,
    n_live_tup,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_stat_user_tables
WHERE seq_scan > 0
  AND n_live_tup > 10000
  AND seq_tup_read / NULLIF(seq_scan, 0) > 10000
ORDER BY seq_tup_read DESC;
```

### Database Statistics

```sql
-- Database size and activity
SELECT
    datname,
    pg_size_pretty(pg_database_size(datname)) as size,
    numbackends as connections,
    xact_commit,
    xact_rollback,
    round(xact_rollback * 100.0 / NULLIF(xact_commit + xact_rollback, 0), 2) as rollback_pct,
    blks_read,
    blks_hit,
    round(blks_hit * 100.0 / NULLIF(blks_hit + blks_read, 0), 2) as cache_hit_pct
FROM pg_stat_database
WHERE datname NOT IN ('template0', 'template1', 'postgres')
ORDER BY pg_database_size(datname) DESC;

-- Checkpoint and bgwriter statistics
SELECT
    checkpoints_timed,
    checkpoints_req,
    checkpoint_write_time,
    checkpoint_sync_time,
    buffers_checkpoint,
    buffers_clean,
    buffers_backend,
    buffers_alloc,
    round(100.0 * checkpoints_req / NULLIF(checkpoints_timed + checkpoints_req, 0), 2) as req_checkpoint_pct
FROM pg_stat_bgwriter;
```

## MySQL Monitoring

### Performance Schema Queries

```sql
-- Top statements by total latency
SELECT
    DIGEST_TEXT as query,
    COUNT_STAR as exec_count,
    ROUND(AVG_TIMER_WAIT / 1000000000000, 3) as avg_sec,
    ROUND(SUM_TIMER_WAIT / 1000000000000, 3) as total_sec,
    ROUND(MAX_TIMER_WAIT / 1000000000000, 3) as max_sec,
    ROUND((SUM_TIMER_WAIT / SUM(SUM_TIMER_WAIT) OVER ()) * 100, 2) as pct_total
FROM performance_schema.events_statements_summary_by_digest
WHERE SCHEMA_NAME NOT IN ('performance_schema', 'mysql', 'sys')
ORDER BY SUM_TIMER_WAIT DESC
LIMIT 20;

-- Statements with full table scans
SELECT
    OBJECT_SCHEMA as db,
    OBJECT_NAME as tbl,
    COUNT_STAR as exec_count,
    SUM_NO_INDEX_USED as full_scans,
    SUM_NO_GOOD_INDEX_USED as bad_index
FROM performance_schema.table_io_waits_summary_by_index_usage
WHERE INDEX_NAME IS NULL
  AND OBJECT_SCHEMA NOT IN ('performance_schema', 'mysql', 'sys')
  AND COUNT_STAR > 0
ORDER BY SUM_NO_INDEX_USED DESC;

-- Table I/O statistics
SELECT
    OBJECT_SCHEMA,
    OBJECT_NAME,
    COUNT_READ,
    COUNT_WRITE,
    COUNT_FETCH,
    COUNT_INSERT,
    COUNT_UPDATE,
    COUNT_DELETE,
    ROUND(SUM_TIMER_WAIT / 1000000000000, 3) as total_latency_sec
FROM performance_schema.table_io_waits_summary_by_table
WHERE OBJECT_SCHEMA NOT IN ('performance_schema', 'mysql', 'sys')
ORDER BY SUM_TIMER_WAIT DESC
LIMIT 20;
```

### InnoDB Status Monitoring

```sql
-- InnoDB buffer pool status
SELECT
    POOL_ID,
    POOL_SIZE,
    FREE_BUFFERS,
    DATABASE_PAGES,
    OLD_DATABASE_PAGES,
    MODIFIED_DATABASE_PAGES,
    PENDING_DECOMPRESS,
    PENDING_READS,
    PENDING_FLUSH_LRU,
    PENDING_FLUSH_LIST
FROM information_schema.INNODB_BUFFER_POOL_STATS;

-- InnoDB lock waits
SELECT
    r.trx_id as waiting_trx,
    r.trx_mysql_thread_id as waiting_thread,
    r.trx_query as waiting_query,
    b.trx_id as blocking_trx,
    b.trx_mysql_thread_id as blocking_thread,
    b.trx_query as blocking_query
FROM information_schema.innodb_lock_waits w
INNER JOIN information_schema.innodb_trx b ON b.trx_id = w.blocking_trx_id
INNER JOIN information_schema.innodb_trx r ON r.trx_id = w.requesting_trx_id;

-- Long-running transactions
SELECT
    trx_id,
    trx_state,
    trx_started,
    TIMESTAMPDIFF(SECOND, trx_started, NOW()) as duration_sec,
    trx_requested_lock_id,
    trx_mysql_thread_id,
    trx_query
FROM information_schema.innodb_trx
WHERE TIMESTAMPDIFF(SECOND, trx_started, NOW()) > 60
ORDER BY trx_started;
```

### Connection and Process Monitoring

```sql
-- Current connections by state
SELECT
    command,
    state,
    COUNT(*) as connections,
    MAX(time) as max_time_sec
FROM information_schema.processlist
GROUP BY command, state
ORDER BY connections DESC;

-- Long-running queries
SELECT
    id,
    user,
    host,
    db,
    command,
    time,
    state,
    LEFT(info, 100) as query
FROM information_schema.processlist
WHERE command != 'Sleep'
  AND time > 10
ORDER BY time DESC;

-- Connection usage
SHOW STATUS LIKE 'Threads_%';
SHOW STATUS LIKE 'Max_used_connections';
SHOW VARIABLES LIKE 'max_connections';
```

### System Status Variables

```sql
-- Key buffer efficiency (MyISAM)
SHOW STATUS LIKE 'Key_%';

-- InnoDB metrics
SHOW STATUS LIKE 'Innodb_buffer_pool_%';
SHOW STATUS LIKE 'Innodb_rows_%';
SHOW STATUS LIKE 'Innodb_data_%';

-- Table locks
SHOW STATUS LIKE 'Table_locks_%';

-- Temporary tables
SHOW STATUS LIKE 'Created_tmp_%';

-- Thread cache
SHOW STATUS LIKE 'Threads_%';
SHOW STATUS LIKE 'Connections';

-- Query cache (MySQL 5.7)
SHOW STATUS LIKE 'Qcache_%';
```

## Cross-Platform Monitoring

### Resource Utilization

```sql
-- PostgreSQL: Database size growth
SELECT
    current_database() as database,
    pg_size_pretty(pg_database_size(current_database())) as size,
    (SELECT pg_size_pretty(sum(pg_total_relation_size(schemaname||'.'||tablename)))
     FROM pg_tables
     WHERE schemaname = 'public') as public_schema_size;

-- MySQL: Database size
SELECT
    table_schema as database,
    ROUND(SUM(data_length + index_length) / 1024 / 1024, 2) as size_mb
FROM information_schema.tables
WHERE table_schema NOT IN ('information_schema', 'performance_schema', 'mysql', 'sys')
GROUP BY table_schema
ORDER BY size_mb DESC;
```

### Health Check Queries

```sql
-- PostgreSQL: Overall health
SELECT
    'connections' as metric,
    count(*) as current,
    current_setting('max_connections')::int as max
FROM pg_stat_activity
UNION ALL
SELECT
    'cache_hit_ratio',
    round((sum(heap_blks_hit) / NULLIF(sum(heap_blks_hit) + sum(heap_blks_read), 0) * 100)::numeric, 2),
    95
FROM pg_statio_user_tables
UNION ALL
SELECT
    'database_size_gb',
    round((pg_database_size(current_database()) / 1024.0 / 1024.0 / 1024.0)::numeric, 2),
    NULL;

-- MySQL: Overall health
SELECT 'connections' as metric,
       (SELECT COUNT(*) FROM information_schema.processlist) as current,
       @@max_connections as max
UNION ALL
SELECT 'buffer_pool_hit_ratio',
       ROUND((1 - (
           (SELECT VARIABLE_VALUE FROM performance_schema.global_status WHERE VARIABLE_NAME = 'Innodb_buffer_pool_reads') /
           (SELECT VARIABLE_VALUE FROM performance_schema.global_status WHERE VARIABLE_NAME = 'Innodb_buffer_pool_read_requests')
       )) * 100, 2),
       95
UNION ALL
SELECT 'slow_queries',
       (SELECT VARIABLE_VALUE FROM performance_schema.global_status WHERE VARIABLE_NAME = 'Slow_queries'),
       NULL;
```

## Alert Thresholds

### PostgreSQL Alerts

```sql
-- Connection pool nearing capacity
SELECT
    count(*) as current_connections,
    current_setting('max_connections')::int as max_connections,
    CASE
        WHEN count(*) > current_setting('max_connections')::int * 0.9 THEN 'CRITICAL'
        WHEN count(*) > current_setting('max_connections')::int * 0.8 THEN 'WARNING'
        ELSE 'OK'
    END as status
FROM pg_stat_activity;

-- Cache hit ratio degradation
WITH cache_stats AS (
    SELECT
        round((sum(heap_blks_hit) / NULLIF(sum(heap_blks_hit) + sum(heap_blks_read), 0) * 100)::numeric, 2) as hit_ratio
    FROM pg_statio_user_tables
)
SELECT
    hit_ratio,
    CASE
        WHEN hit_ratio < 90 THEN 'CRITICAL'
        WHEN hit_ratio < 95 THEN 'WARNING'
        ELSE 'OK'
    END as status
FROM cache_stats;

-- Replication lag (on standby)
SELECT
    CASE
        WHEN pg_last_wal_receive_lsn() = pg_last_wal_replay_lsn() THEN 0
        ELSE EXTRACT(EPOCH FROM (now() - pg_last_xact_replay_timestamp()))
    END as lag_seconds,
    CASE
        WHEN EXTRACT(EPOCH FROM (now() - pg_last_xact_replay_timestamp())) > 60 THEN 'CRITICAL'
        WHEN EXTRACT(EPOCH FROM (now() - pg_last_xact_replay_timestamp())) > 10 THEN 'WARNING'
        ELSE 'OK'
    END as status;
```

### MySQL Alerts

```sql
-- InnoDB buffer pool efficiency
SELECT
    ROUND((1 - (
        (SELECT VARIABLE_VALUE FROM performance_schema.global_status WHERE VARIABLE_NAME = 'Innodb_buffer_pool_reads') /
        (SELECT VARIABLE_VALUE FROM performance_schema.global_status WHERE VARIABLE_NAME = 'Innodb_buffer_pool_read_requests')
    )) * 100, 2) as buffer_pool_hit_ratio,
    CASE
        WHEN (1 - (
            (SELECT VARIABLE_VALUE FROM performance_schema.global_status WHERE VARIABLE_NAME = 'Innodb_buffer_pool_reads') /
            (SELECT VARIABLE_VALUE FROM performance_schema.global_status WHERE VARIABLE_NAME = 'Innodb_buffer_pool_read_requests')
        )) * 100 < 90 THEN 'CRITICAL'
        WHEN (1 - (
            (SELECT VARIABLE_VALUE FROM performance_schema.global_status WHERE VARIABLE_NAME = 'Innodb_buffer_pool_reads') /
            (SELECT VARIABLE_VALUE FROM performance_schema.global_status WHERE VARIABLE_NAME = 'Innodb_buffer_pool_read_requests')
        )) * 100 < 95 THEN 'WARNING'
        ELSE 'OK'
    END as status;

-- Replication lag (on replica)
SELECT
    Seconds_Behind_Master as lag_seconds,
    CASE
        WHEN Slave_IO_Running = 'No' OR Slave_SQL_Running = 'No' THEN 'CRITICAL - Replication stopped'
        WHEN Seconds_Behind_Master > 300 THEN 'CRITICAL'
        WHEN Seconds_Behind_Master > 60 THEN 'WARNING'
        ELSE 'OK'
    END as status
FROM (SHOW SLAVE STATUS) s;
```

## Monitoring Best Practices

1. **Establish baselines** - Record normal performance metrics
2. **Track trends** - Monitor daily/weekly patterns
3. **Set thresholds** - Define warning and critical levels
4. **Automate alerts** - Use monitoring tools (Prometheus, Grafana, Datadog)
5. **Regular reviews** - Weekly performance analysis meetings
6. **Document changes** - Track configuration and schema modifications
7. **Capacity planning** - Monitor growth and forecast needs
8. **Test queries** - Validate optimizations in staging first
