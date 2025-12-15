# Application Profiling

> Reference for: Monitoring Expert
> Load when: Profiling, performance optimization, bottlenecks

## Node.js Profiling

### CPU Profiling with clinic.js

```bash
# Install
npm install -g clinic

# CPU profiling
clinic doctor -- node app.js

# Flame graph
clinic flame -- node app.js

# Bubble profiling
clinic bubbleprof -- node app.js

# Generate report
clinic doctor --collect-only -- node app.js
clinic doctor --visualize-only PID.clinic-doctor
```

### Built-in Node.js Profiler

```javascript
// Start profiling
node --prof app.js

# Process the output
node --prof-process isolate-0x*.log > processed.txt

# Chrome DevTools
node --inspect app.js
# Open chrome://inspect
```

### Memory Profiling

```javascript
import v8 from 'v8';
import fs from 'fs';

// Heap snapshot
const snapshot = v8.writeHeapSnapshot();
console.log('Snapshot written to:', snapshot);

// Memory usage
const usage = process.memoryUsage();
console.log({
  rss: `${Math.round(usage.rss / 1024 / 1024)}MB`,
  heapTotal: `${Math.round(usage.heapTotal / 1024 / 1024)}MB`,
  heapUsed: `${Math.round(usage.heapUsed / 1024 / 1024)}MB`,
  external: `${Math.round(usage.external / 1024 / 1024)}MB`,
});
```

### Custom Performance Marks

```javascript
import { performance, PerformanceObserver } from 'perf_hooks';

// Mark start
performance.mark('operation-start');

// ... do work ...
await processOrder(orderId);

// Mark end
performance.mark('operation-end');

// Measure
performance.measure('operation', 'operation-start', 'operation-end');

// Observer
const obs = new PerformanceObserver((items) => {
  items.getEntries().forEach((entry) => {
    console.log(`${entry.name}: ${entry.duration}ms`);
  });
});
obs.observe({ entryTypes: ['measure'] });
```

## Python Profiling

### cProfile

```python
import cProfile
import pstats

# Profile a function
def main():
    # Your code here
    process_data()

if __name__ == '__main__':
    profiler = cProfile.Profile()
    profiler.enable()

    main()

    profiler.disable()
    stats = pstats.Stats(profiler)
    stats.sort_stats('cumulative')
    stats.print_stats(20)  # Top 20 functions
```

### Line Profiler

```python
from line_profiler import LineProfiler

@profile
def expensive_function():
    # Code to profile
    result = []
    for i in range(10000):
        result.append(i ** 2)
    return result

# Run with: kernprof -l -v script.py
```

### Memory Profiler

```python
from memory_profiler import profile

@profile
def process_large_data():
    data = [i for i in range(1000000)]
    result = [x * 2 for x in data]
    return result

# Run with: python -m memory_profiler script.py
```

### py-spy

```bash
# CPU sampling (live process)
py-spy top --pid 12345

# Generate flame graph
py-spy record -o profile.svg --pid 12345

# Record for duration
py-spy record -o profile.svg --duration 60 -- python app.py
```

## Go Profiling

### pprof

```go
import (
    "net/http"
    _ "net/http/pprof"
    "runtime"
)

func main() {
    // Enable profiling endpoint
    go func() {
        http.ListenAndServe("localhost:6060", nil)
    }()

    // Your application code
}
```

```bash
# CPU profile
curl http://localhost:6060/debug/pprof/profile?seconds=30 > cpu.prof
go tool pprof cpu.prof

# Memory profile
curl http://localhost:6060/debug/pprof/heap > heap.prof
go tool pprof heap.prof

# Goroutine profile
curl http://localhost:6060/debug/pprof/goroutine > goroutine.prof
go tool pprof goroutine.prof

# Web interface
go tool pprof -http=:8080 cpu.prof
```

## Java Profiling

### VisualVM

```bash
# Start application with JMX
java -Dcom.sun.management.jmxremote \
     -Dcom.sun.management.jmxremote.port=9010 \
     -Dcom.sun.management.jmxremote.authenticate=false \
     -Dcom.sun.management.jmxremote.ssl=false \
     -jar app.jar

# Connect with VisualVM
jvisualvm
```

### async-profiler

```bash
# CPU profiling
./profiler.sh -d 30 -f cpu.html <pid>

# Allocation profiling
./profiler.sh -d 30 -e alloc -f alloc.html <pid>

# Flame graph
./profiler.sh -d 30 -f flamegraph.svg <pid>
```

## Database Query Profiling

### PostgreSQL

```sql
-- Enable query logging
ALTER SYSTEM SET log_min_duration_statement = 100;  -- Log queries > 100ms
SELECT pg_reload_conf();

-- Explain analyze
EXPLAIN ANALYZE
SELECT * FROM orders
WHERE user_id = 123
AND created_at > NOW() - INTERVAL '30 days';

-- Track slow queries
SELECT query, calls, total_time, mean_time
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 10;
```

### MySQL

```sql
-- Enable slow query log
SET GLOBAL slow_query_log = 'ON';
SET GLOBAL long_query_time = 0.1;  -- 100ms

-- Explain query
EXPLAIN ANALYZE
SELECT * FROM orders
WHERE user_id = 123;

-- Performance schema
SELECT * FROM performance_schema.events_statements_summary_by_digest
ORDER BY SUM_TIMER_WAIT DESC
LIMIT 10;
```

## APM Integration

### New Relic

```javascript
import newrelic from 'newrelic';

// Custom transaction
newrelic.startBackgroundTransaction('process-orders', async () => {
  const orders = await getOrders();

  // Custom segment
  await newrelic.startSegment('validate-orders', true, async () => {
    return validateOrders(orders);
  });
});

// Custom metrics
newrelic.recordMetric('Custom/OrderValue', orderTotal);
```

### DataDog APM

```javascript
import tracer from 'dd-trace';
tracer.init();

// Custom span
const span = tracer.startSpan('process.order', {
  resource: orderId,
  tags: {
    'order.total': orderTotal,
    'user.id': userId,
  },
});

try {
  await processOrder(orderId);
  span.setTag('status', 'success');
} catch (err) {
  span.setTag('error', err);
} finally {
  span.finish();
}
```

## Quick Reference

| Tool | Language | Type |
|------|----------|------|
| clinic.js | Node.js | CPU, Event loop |
| Chrome DevTools | Node.js | CPU, Memory |
| cProfile | Python | CPU |
| py-spy | Python | CPU (sampling) |
| pprof | Go | CPU, Memory, Goroutines |
| VisualVM | Java | CPU, Memory, Threads |
| async-profiler | Java | CPU, Allocation |

| Metric | What to Look For |
|--------|------------------|
| CPU time | Hot functions, tight loops |
| Memory | Large allocations, leaks |
| I/O wait | Blocking operations |
| GC time | Excessive collections |
| Thread count | Thread pool saturation |

| Problem | Symptom |
|---------|---------|
| CPU bound | High CPU usage, slow processing |
| Memory leak | Growing memory, eventual crash |
| I/O bound | Low CPU, high wait time |
| Lock contention | Idle threads, poor scaling |
