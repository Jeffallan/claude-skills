# Streaming Patterns

---

## Structured Streaming Overview

### When to Use Structured Streaming

**Use when:**
- Processing continuous data streams (Kafka, files, sockets)
- Need exactly-once processing guarantees
- Real-time analytics and dashboards
- Event-driven architectures
- Incremental ETL from streaming sources

**Consider alternatives when:**
- Batch processing is sufficient (lower complexity)
- Sub-second latency required (consider Flink)
- Very simple event processing (Kafka Streams may suffice)

---

## Reading from Streaming Sources

### Kafka Source

```python
# Read from Kafka
df = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "broker1:9092,broker2:9092") \
    .option("subscribe", "topic1,topic2") \
    .option("startingOffsets", "latest") \
    .option("maxOffsetsPerTrigger", 100000) \
    .option("kafka.security.protocol", "SASL_SSL") \
    .option("kafka.sasl.mechanism", "PLAIN") \
    .load()

# Kafka provides key, value as bytes
# Parse JSON value
from pyspark.sql import functions as F
from pyspark.sql.types import StructType, StructField, StringType, TimestampType, DoubleType

schema = StructType([
    StructField("event_id", StringType()),
    StructField("user_id", StringType()),
    StructField("event_time", TimestampType()),
    StructField("amount", DoubleType())
])

parsed_df = df.select(
    F.col("key").cast("string").alias("kafka_key"),
    F.from_json(F.col("value").cast("string"), schema).alias("data"),
    F.col("timestamp").alias("kafka_timestamp"),
    F.col("partition"),
    F.col("offset")
).select("kafka_key", "data.*", "kafka_timestamp", "partition", "offset")
```

```scala
// Scala Kafka source
val df = spark.readStream
  .format("kafka")
  .option("kafka.bootstrap.servers", "broker1:9092,broker2:9092")
  .option("subscribe", "topic1")
  .option("startingOffsets", "latest")
  .load()

val parsed = df.select(
  col("key").cast("string"),
  from_json(col("value").cast("string"), schema).as("data")
).select("key", "data.*")
```

### File Source (Auto-Discovery)

```python
# Read new files as they arrive
df = spark.readStream \
    .format("parquet") \
    .schema(my_schema) \
    .option("path", "s3://bucket/incoming/") \
    .option("maxFilesPerTrigger", 100) \
    .load()

# For JSON files
df = spark.readStream \
    .format("json") \
    .schema(my_schema) \
    .option("path", "s3://bucket/incoming/") \
    .load()

# CSV with header
df = spark.readStream \
    .format("csv") \
    .schema(my_schema) \
    .option("path", "s3://bucket/incoming/") \
    .option("header", "true") \
    .load()
```

### Rate Source (Testing)

```python
# Generate test data at specified rate
df = spark.readStream \
    .format("rate") \
    .option("rowsPerSecond", 1000) \
    .option("numPartitions", 10) \
    .load()

# Columns: timestamp, value (incrementing long)
```

---

## Output Modes

### Append Mode (Default)

```python
# Only new rows added since last trigger
# Use when: No aggregations, or windowed aggregations with watermark
query = df.writeStream \
    .outputMode("append") \
    .format("parquet") \
    .option("path", "s3://bucket/output/") \
    .option("checkpointLocation", "s3://bucket/checkpoints/") \
    .start()
```

### Update Mode

```python
# Only rows that changed since last trigger
# Use when: Aggregations, want incremental updates
query = df.groupBy("user_id").count() \
    .writeStream \
    .outputMode("update") \
    .format("console") \
    .start()
```

### Complete Mode

```python
# Entire result table every trigger
# Use when: Need full aggregation result each time
# Warning: Can be expensive for large state
query = df.groupBy("user_id").count() \
    .writeStream \
    .outputMode("complete") \
    .format("console") \
    .start()
```

### Mode Selection Guide

| Use Case | Output Mode | Notes |
|----------|-------------|-------|
| ETL to files | append | Default, efficient |
| Windowed aggregations | append | With watermark |
| Running counts/sums | update | Incremental |
| Dashboards needing full state | complete | Expensive |
| Deduplication | append | With dropDuplicates |

---

## Watermarks and Event Time

### Understanding Watermarks

Watermarks define how late data can arrive before being dropped. They enable Spark to:
- Clean up old state (bounded memory)
- Emit results at appropriate times
- Handle out-of-order events

### Setting Watermarks

```python
from pyspark.sql import functions as F

# Define watermark on event time column
df_with_watermark = df \
    .withWatermark("event_time", "10 minutes")

# Watermark threshold: max_event_time - 10 minutes
# Events older than watermark are dropped
# State older than watermark is cleaned up
```

### Watermark Guidelines

| Scenario | Watermark Duration | Reasoning |
|----------|-------------------|-----------|
| Real-time analytics | 1-5 minutes | Low latency, tolerate minimal late data |
| Standard ETL | 10-30 minutes | Balance latency and late data |
| Late-arriving data common | 1-24 hours | Accommodate delayed events |
| Best-effort real-time | 0 minutes | No late data tolerance |

### Example with Windowed Aggregation

```python
from pyspark.sql import functions as F
from pyspark.sql.window import Window

# Streaming aggregation with watermark
result = df \
    .withWatermark("event_time", "10 minutes") \
    .groupBy(
        F.window("event_time", "5 minutes", "1 minute"),  # 5-min tumbling window, 1-min slide
        "user_id"
    ) \
    .agg(
        F.count("*").alias("event_count"),
        F.sum("amount").alias("total_amount")
    )

# Output schema includes window struct: window.start, window.end
query = result \
    .select(
        F.col("window.start").alias("window_start"),
        F.col("window.end").alias("window_end"),
        "user_id",
        "event_count",
        "total_amount"
    ) \
    .writeStream \
    .outputMode("append") \
    .format("parquet") \
    .option("path", "s3://bucket/windowed_output/") \
    .option("checkpointLocation", "s3://bucket/checkpoints/") \
    .start()
```

---

## Windowed Operations

### Tumbling Windows (Non-Overlapping)

```python
from pyspark.sql import functions as F

# 5-minute tumbling windows
result = df \
    .withWatermark("event_time", "10 minutes") \
    .groupBy(
        F.window("event_time", "5 minutes"),
        "category"
    ) \
    .agg(F.sum("amount").alias("total"))

# Windows: [00:00-00:05), [00:05-00:10), [00:10-00:15), ...
```

### Sliding Windows (Overlapping)

```python
# 10-minute windows, sliding every 2 minutes
result = df \
    .withWatermark("event_time", "10 minutes") \
    .groupBy(
        F.window("event_time", "10 minutes", "2 minutes"),
        "category"
    ) \
    .agg(F.sum("amount").alias("total"))

# Windows: [00:00-00:10), [00:02-00:12), [00:04-00:14), ...
```

### Session Windows (Gap-Based)

```python
# Session windows with 5-minute gap threshold
result = df \
    .withWatermark("event_time", "10 minutes") \
    .groupBy(
        F.session_window("event_time", "5 minutes"),  # Spark 3.2+
        "user_id"
    ) \
    .agg(
        F.count("*").alias("events_in_session"),
        F.first("event_time").alias("session_start"),
        F.last("event_time").alias("session_end")
    )
```

---

## Stateful Operations

### Aggregations (Built-in State)

```python
# Running count by key
running_counts = df \
    .withWatermark("event_time", "1 hour") \
    .groupBy("user_id") \
    .agg(F.count("*").alias("total_events"))

# State stored per user_id
# Cleaned up based on watermark
```

### Deduplication

```python
# Drop duplicates within watermark window
deduped = df \
    .withWatermark("event_time", "10 minutes") \
    .dropDuplicates(["event_id"])  # Keep first occurrence

# Can also dedupe by multiple columns
deduped = df \
    .withWatermark("event_time", "10 minutes") \
    .dropDuplicates(["user_id", "event_type", "event_time"])
```

### Custom Stateful Processing (flatMapGroupsWithState)

```python
# PySpark - Custom state using applyInPandasWithState (Spark 3.4+)
from pyspark.sql.streaming.state import GroupState, GroupStateTimeout

def update_session_state(
    key: tuple,
    pdf_iter: Iterator[pd.DataFrame],
    state: GroupState
) -> Iterator[pd.DataFrame]:
    # Get or initialize state
    if state.exists:
        session_data = state.get
    else:
        session_data = {"count": 0, "total": 0.0}

    # Process input data
    for pdf in pdf_iter:
        session_data["count"] += len(pdf)
        session_data["total"] += pdf["amount"].sum()

    # Update state
    state.update(session_data)

    # Optionally set timeout
    state.setTimeoutDuration(10 * 60 * 1000)  # 10 minutes

    # Yield output
    yield pd.DataFrame([{
        "user_id": key[0],
        "event_count": session_data["count"],
        "total_amount": session_data["total"]
    }])

# Apply stateful function
result = df \
    .withWatermark("event_time", "10 minutes") \
    .groupBy("user_id") \
    .applyInPandasWithState(
        update_session_state,
        outputStructType=output_schema,
        stateStructType=state_schema,
        outputMode="update",
        timeoutConf=GroupStateTimeout.ProcessingTimeTimeout
    )
```

```scala
// Scala flatMapGroupsWithState
import org.apache.spark.sql.streaming.{GroupState, GroupStateTimeout}

case class UserState(count: Long, totalAmount: Double)
case class UserOutput(userId: String, count: Long, totalAmount: Double)

def updateState(
    userId: String,
    events: Iterator[Event],
    state: GroupState[UserState]
): Iterator[UserOutput] = {

  val currentState = state.getOption.getOrElse(UserState(0, 0.0))

  var newCount = currentState.count
  var newTotal = currentState.totalAmount

  events.foreach { event =>
    newCount += 1
    newTotal += event.amount
  }

  val newState = UserState(newCount, newTotal)
  state.update(newState)
  state.setTimeoutDuration("10 minutes")

  Iterator(UserOutput(userId, newCount, newTotal))
}

val result = df
  .withWatermark("event_time", "10 minutes")
  .as[Event]
  .groupByKey(_.userId)
  .flatMapGroupsWithState(
    OutputMode.Update,
    GroupStateTimeout.ProcessingTimeTimeout
  )(updateState)
```

---

## Streaming Joins

### Stream-Static Join

```python
# Join streaming data with static lookup table
static_df = spark.read.parquet("s3://bucket/lookup/")

# Streaming df joined with static - no watermark needed
result = streaming_df.join(static_df, "join_key", "left")

# Static table can be periodically refreshed
# Use broadcast for small static tables
from pyspark.sql.functions import broadcast
result = streaming_df.join(broadcast(static_df), "join_key")
```

### Stream-Stream Join

```python
# Join two streams - requires watermarks on both
from pyspark.sql import functions as F

stream1 = spark.readStream.format("kafka")...
stream2 = spark.readStream.format("kafka")...

# Both streams need watermarks
stream1_wm = stream1.withWatermark("event_time", "10 minutes")
stream2_wm = stream2.withWatermark("event_time", "10 minutes")

# Inner join with time constraint
result = stream1_wm.join(
    stream2_wm,
    F.expr("""
        stream1.user_id = stream2.user_id AND
        stream1.event_time >= stream2.event_time AND
        stream1.event_time <= stream2.event_time + INTERVAL 5 MINUTES
    """),
    "inner"
)

# Left outer join (Spark 2.3+)
result = stream1_wm.join(
    stream2_wm,
    F.expr("""
        stream1.user_id = stream2.user_id AND
        stream1.event_time >= stream2.event_time - INTERVAL 5 MINUTES AND
        stream1.event_time <= stream2.event_time + INTERVAL 5 MINUTES
    """),
    "leftOuter"
)
```

### Join Type Support

| Join Type | Stream-Static | Stream-Stream |
|-----------|---------------|---------------|
| Inner | Yes | Yes |
| Left Outer | Yes | Yes (Spark 2.3+) |
| Right Outer | Yes | Yes (Spark 2.3+) |
| Full Outer | Yes | Yes (Spark 2.4+) |
| Left Semi | Yes | Not supported |
| Left Anti | Yes | Not supported |

---

## Sinks

### Kafka Sink

```python
# Write to Kafka
query = df \
    .select(
        F.col("user_id").alias("key"),
        F.to_json(F.struct("*")).alias("value")
    ) \
    .writeStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "broker1:9092") \
    .option("topic", "output_topic") \
    .option("checkpointLocation", "s3://bucket/checkpoints/") \
    .start()
```

### File Sink (Parquet, JSON, CSV)

```python
# Parquet sink with partitioning
query = df.writeStream \
    .format("parquet") \
    .option("path", "s3://bucket/output/") \
    .option("checkpointLocation", "s3://bucket/checkpoints/") \
    .partitionBy("date", "hour") \
    .trigger(processingTime="1 minute") \
    .start()

# JSON sink
query = df.writeStream \
    .format("json") \
    .option("path", "s3://bucket/output/") \
    .option("checkpointLocation", "s3://bucket/checkpoints/") \
    .start()
```

### Delta Lake Sink

```python
# Delta Lake (ACID transactions, schema evolution)
query = df.writeStream \
    .format("delta") \
    .outputMode("append") \
    .option("path", "s3://bucket/delta_table/") \
    .option("checkpointLocation", "s3://bucket/checkpoints/") \
    .option("mergeSchema", "true") \
    .start()

# Upsert with foreachBatch
def upsert_to_delta(batch_df, batch_id):
    delta_table = DeltaTable.forPath(spark, "s3://bucket/delta_table/")
    delta_table.alias("target").merge(
        batch_df.alias("source"),
        "target.id = source.id"
    ).whenMatchedUpdateAll() \
     .whenNotMatchedInsertAll() \
     .execute()

query = df.writeStream \
    .foreachBatch(upsert_to_delta) \
    .option("checkpointLocation", "s3://bucket/checkpoints/") \
    .start()
```

### Custom Sink (foreachBatch)

```python
def write_to_database(batch_df, batch_id):
    """Write each micro-batch to external database."""
    batch_df.write \
        .format("jdbc") \
        .option("url", "jdbc:postgresql://host:5432/db") \
        .option("dbtable", "output_table") \
        .option("user", "user") \
        .option("password", "password") \
        .mode("append") \
        .save()

query = df.writeStream \
    .foreachBatch(write_to_database) \
    .option("checkpointLocation", "s3://bucket/checkpoints/") \
    .trigger(processingTime="30 seconds") \
    .start()
```

### foreach (Row-by-Row)

```python
# For custom processing of each row
class ForeachWriter:
    def open(self, partition_id, epoch_id):
        # Initialize connection
        self.connection = create_connection()
        return True

    def process(self, row):
        # Process each row
        self.connection.insert(row.asDict())

    def close(self, error):
        # Clean up
        self.connection.close()

query = df.writeStream \
    .foreach(ForeachWriter()) \
    .start()
```

---

## Triggers

### Available Trigger Types

```python
# Process as fast as possible (default)
query = df.writeStream.trigger(processingTime="0 seconds").start()

# Fixed interval
query = df.writeStream.trigger(processingTime="1 minute").start()

# Once - process all available data, then stop
query = df.writeStream.trigger(once=True).start()

# Available now - process all available data (Spark 3.3+)
query = df.writeStream.trigger(availableNow=True).start()

# Continuous processing (experimental, low latency)
query = df.writeStream.trigger(continuous="1 second").start()
```

### Trigger Selection Guide

| Trigger | Use Case |
|---------|----------|
| processingTime="0 seconds" | Maximum throughput |
| processingTime="N seconds" | Controlled resource usage |
| once=True | Batch-style processing |
| availableNow=True | Catch-up processing |
| continuous="N ms" | Ultra-low latency (experimental) |

---

## Monitoring and Management

### Query Management

```python
# Start query and get handle
query = df.writeStream.format("console").start()

# Query properties
print(f"Query ID: {query.id}")
print(f"Run ID: {query.runId}")
print(f"Name: {query.name}")
print(f"Is Active: {query.isActive}")
print(f"Status: {query.status}")
print(f"Last Progress: {query.lastProgress}")
print(f"Recent Progress: {query.recentProgress}")

# Wait for termination
query.awaitTermination()
query.awaitTermination(timeout=60)  # With timeout

# Stop query
query.stop()

# Get exception if failed
exception = query.exception()
```

### Progress Monitoring

```python
# Get latest progress
progress = query.lastProgress
if progress:
    print(f"Input rows/sec: {progress['inputRowsPerSecond']}")
    print(f"Processed rows/sec: {progress['processedRowsPerSecond']}")
    print(f"Batch ID: {progress['batchId']}")
    print(f"Duration: {progress['batchDuration']} ms")
    print(f"State rows: {progress['stateOperators']}")

# Custom progress listener
class ProgressListener:
    def onQueryProgress(self, event):
        print(f"Progress: {event.progress}")

    def onQueryTerminated(self, event):
        print(f"Terminated: {event.exception}")

spark.streams.addListener(ProgressListener())
```

### Checkpointing

```python
# Checkpoint location is required for fault tolerance
query = df.writeStream \
    .format("parquet") \
    .option("path", "s3://bucket/output/") \
    .option("checkpointLocation", "s3://bucket/checkpoints/query_name/") \
    .start()

# Checkpoint contains:
# - Offsets (what data has been processed)
# - State (for stateful operations)
# - Commits (what batches completed)

# Recovery: Query restarts from last checkpoint automatically
# Clean start: Delete checkpoint directory (loses state!)
```

---

## Performance Patterns

### Optimizing Throughput

```python
# 1. Increase Kafka partitions for parallelism
# Consumer parallelism = Kafka partitions

# 2. Tune maxOffsetsPerTrigger
query = df.readStream \
    .format("kafka") \
    .option("maxOffsetsPerTrigger", 500000) \  # More data per batch
    .load()

# 3. Optimize shuffle partitions
spark.conf.set("spark.sql.shuffle.partitions", 100)

# 4. Use appropriate trigger interval
query = df.writeStream \
    .trigger(processingTime="30 seconds") \
    .start()

# 5. Enable AQE for dynamic optimization
spark.conf.set("spark.sql.adaptive.enabled", "true")
```

### Managing State Size

```python
# 1. Always use watermarks for stateful operations
df.withWatermark("event_time", "1 hour")

# 2. Monitor state size in progress
progress = query.lastProgress
for operator in progress["stateOperators"]:
    print(f"State rows: {operator['numRowsTotal']}")
    print(f"Memory used: {operator['memoryUsedBytes']}")

# 3. Configure state store
spark.conf.set("spark.sql.streaming.stateStore.providerClass",
    "org.apache.spark.sql.execution.streaming.state.RocksDBStateStoreProvider")
# RocksDB handles larger state better than in-memory default

# 4. Set state cleanup mode
spark.conf.set("spark.sql.streaming.stateStore.stateSchemaCheck", "false")
```

---

## Common Anti-Patterns

```python
# BAD: No watermark with aggregation
df.groupBy("user_id").count()  # Unbounded state growth!

# GOOD: Always use watermark
df.withWatermark("event_time", "1 hour").groupBy("user_id").count()

# BAD: Complete mode with large state
df.groupBy("user_id").count().writeStream.outputMode("complete")  # Outputs entire state

# GOOD: Update mode for incremental
df.groupBy("user_id").count().writeStream.outputMode("update")

# BAD: No checkpoint location
query = df.writeStream.format("console").start()  # No fault tolerance!

# GOOD: Always specify checkpoint
query = df.writeStream.format("console") \
    .option("checkpointLocation", "/checkpoints/query") \
    .start()

# BAD: foreach for high-throughput
df.writeStream.foreach(process_row).start()  # Row-by-row overhead

# GOOD: foreachBatch for batched processing
df.writeStream.foreachBatch(process_batch).start()  # Batch-level efficiency
```

---

## Best Practices Summary

1. **Always use watermarks** - Prevents unbounded state growth
2. **Choose appropriate output mode** - Append for ETL, Update for aggregations
3. **Set checkpoint locations** - Required for fault tolerance
4. **Use foreachBatch over foreach** - Better performance for custom sinks
5. **Monitor state size** - Watch for memory growth in progress metrics
6. **Tune trigger intervals** - Balance latency vs throughput
7. **Match Kafka partitions to parallelism** - Consumer tasks = Kafka partitions
8. **Use stream-static joins when possible** - Simpler than stream-stream
9. **Test with production data rates** - Performance varies with volume
10. **Enable structured streaming UI** - Detailed metrics in Spark UI
