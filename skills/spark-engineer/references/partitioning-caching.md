# Partitioning and Caching

---

## Partitioning Fundamentals

### Why Partitioning Matters

- **Parallelism**: Each partition runs on a separate task
- **Data locality**: Minimize data movement across network
- **Memory efficiency**: Right-sized partitions prevent OOM
- **Join performance**: Co-partitioned data avoids shuffle

### Partition Count Guidelines

```python
# Rule of thumb: 2-4 partitions per CPU core
# For 100 executor cores: 200-400 partitions

# Check current partitions
print(f"Number of partitions: {df.rdd.getNumPartitions()}")

# Recommended formula
total_cores = num_executors * cores_per_executor
recommended_partitions = total_cores * 2 to 4

# Target partition size: 128MB - 256MB per partition
# For 100GB data with 128MB target: ~800 partitions
```

### Optimal Partition Sizes

| Data Volume | Target Partition Size | Partition Count |
|-------------|----------------------|-----------------|
| < 1GB | 64MB | 8-16 |
| 1-10GB | 128MB | 8-80 |
| 10-100GB | 128-256MB | 40-800 |
| 100GB-1TB | 256MB | 400-4000 |
| > 1TB | 256MB | 4000+ |

---

## DataFrame Partitioning

### Repartition (Full Shuffle)

```python
from pyspark.sql import functions as F

# Repartition to specific number
df_repart = df.repartition(200)

# Repartition by column(s) - same keys go to same partition
df_repart = df.repartition("user_id")
df_repart = df.repartition("user_id", "date")

# Repartition with count and columns
df_repart = df.repartition(100, "user_id")

# Range partitioning (for sorted access patterns)
df_range = df.repartitionByRange(100, "date")
```

```scala
// Scala repartition
val dfRepart = df.repartition(200)
val dfByCol = df.repartition($"user_id")
val dfRange = df.repartitionByRange(100, $"date")
```

### Coalesce (No Shuffle)

```python
# Reduce partitions without shuffle - efficient!
# Use after filtering reduces data significantly
df_coalesced = df.coalesce(50)

# Common pattern: filter then coalesce
df_filtered = df.filter(F.col("active") == True)
# If filter reduced data by 80%, reduce partitions too
df_optimized = df_filtered.coalesce(40)  # From 200 to 40
```

**When to use:**
- `repartition(n)`: Increase partitions, need even distribution, partition by column
- `coalesce(n)`: Decrease partitions only (no shuffle benefit)
- `repartitionByRange()`: Need sorted partitions for range queries

### Checking Partition Distribution

```python
from pyspark.sql import functions as F

# Check partition count
print(f"Partitions: {df.rdd.getNumPartitions()}")

# Check partition sizes (row counts)
partition_counts = df.withColumn("partition_id", F.spark_partition_id()) \
    .groupBy("partition_id") \
    .count() \
    .orderBy("partition_id")

partition_counts.show()

# Get partition statistics
stats = partition_counts.agg(
    F.min("count").alias("min_rows"),
    F.max("count").alias("max_rows"),
    F.avg("count").alias("avg_rows"),
    F.stddev("count").alias("stddev")
)
stats.show()

# Identify skew: max/avg ratio > 3 indicates skew
```

---

## Shuffle Partitions

### Configuration

```python
# Default shuffle partitions (200) - often suboptimal
spark.conf.set("spark.sql.shuffle.partitions", 200)

# For small data (<10GB), reduce
spark.conf.set("spark.sql.shuffle.partitions", 50)

# For large data (>100GB), increase
spark.conf.set("spark.sql.shuffle.partitions", 2000)

# Adaptive Query Execution (Spark 3.0+) - dynamic partition sizing
spark.conf.set("spark.sql.adaptive.enabled", "true")
spark.conf.set("spark.sql.adaptive.coalescePartitions.enabled", "true")
spark.conf.set("spark.sql.adaptive.coalescePartitions.minPartitionSize", "64MB")
spark.conf.set("spark.sql.adaptive.advisoryPartitionSizeInBytes", "128MB")
```

### AQE Automatic Optimization (Spark 3.x)

```python
# Enable full AQE suite
spark.conf.set("spark.sql.adaptive.enabled", "true")

# Auto-coalesce shuffle partitions
spark.conf.set("spark.sql.adaptive.coalescePartitions.enabled", "true")
spark.conf.set("spark.sql.adaptive.coalescePartitions.parallelismFirst", "false")

# Handle skewed partitions automatically
spark.conf.set("spark.sql.adaptive.skewJoin.enabled", "true")
spark.conf.set("spark.sql.adaptive.skewJoin.skewedPartitionFactor", 5)
spark.conf.set("spark.sql.adaptive.skewJoin.skewedPartitionThresholdInBytes", "256MB")

# Local shuffle reader (avoid remote reads when possible)
spark.conf.set("spark.sql.adaptive.localShuffleReader.enabled", "true")
```

**Spark UI Check:** With AQE, check "Adaptive" badge in SQL tab. View coalesced partition counts in stage details.

---

## Caching and Persistence

### When to Cache

**Cache when:**
- DataFrame is reused multiple times in same job
- DataFrame is expensive to compute (complex joins/aggregations)
- Iterative algorithms (ML training loops)
- Interactive exploration in notebooks

**Do NOT cache when:**
- DataFrame used only once
- Data doesn't fit in cluster memory
- Source data is already fast (local SSD, columnar formats)
- Storage level causes excessive GC

### Persistence Levels

```python
from pyspark import StorageLevel

# Memory only (default for cache())
df.cache()  # Equivalent to persist(MEMORY_AND_DISK)
df.persist()  # Same as cache()

# Specific storage levels
df.persist(StorageLevel.MEMORY_ONLY)         # Fast, may lose partitions
df.persist(StorageLevel.MEMORY_AND_DISK)     # Spill to disk if needed
df.persist(StorageLevel.MEMORY_ONLY_SER)     # Serialized, less memory, slower
df.persist(StorageLevel.MEMORY_AND_DISK_SER) # Serialized with disk spill
df.persist(StorageLevel.DISK_ONLY)           # Only disk, slowest
df.persist(StorageLevel.OFF_HEAP)            # Off-heap memory

# With replication (for fault tolerance)
df.persist(StorageLevel.MEMORY_AND_DISK_2)   # 2x replication

# Unpersist when done
df.unpersist()
df.unpersist(blocking=True)  # Wait for completion
```

```scala
// Scala persistence
import org.apache.spark.storage.StorageLevel

df.cache()
df.persist(StorageLevel.MEMORY_AND_DISK_SER)
df.unpersist()
```

### Storage Level Selection Guide

| Storage Level | Use When |
|---------------|----------|
| MEMORY_ONLY | Enough memory, need fastest access |
| MEMORY_AND_DISK | Default, safe for most cases |
| MEMORY_ONLY_SER | Memory constrained, CPU available |
| MEMORY_AND_DISK_SER | Large data, memory constrained |
| DISK_ONLY | Very large data, memory scarce |
| OFF_HEAP | Using Tungsten off-heap memory |

### Caching Best Practices

```python
# Pattern 1: Cache after expensive transformation
expensive_df = source_df \
    .join(lookup_df, "key") \
    .groupBy("category").agg(F.sum("amount"))

expensive_df.cache()

# Trigger caching with action
expensive_df.count()

# Reuse cached data
result1 = expensive_df.filter(F.col("category") == "A")
result2 = expensive_df.filter(F.col("category") == "B")

# Clean up
expensive_df.unpersist()

# Pattern 2: Cache at checkpoint in iterative algorithm
for iteration in range(100):
    df = df.transform(update_function)
    if iteration % 10 == 0:
        df.cache()
        df.count()  # Materialize
        df.unpersist()  # Clean previous

# Pattern 3: Checkpoint to break lineage (long pipelines)
spark.sparkContext.setCheckpointDir("hdfs://path/checkpoints/")
df.checkpoint()  # Truncates lineage, saves to reliable storage
```

### Monitoring Cache Usage

```python
# Check if DataFrame is cached
print(df.storageLevel)  # StorageLevel(False, False, False, False, 1) = not cached

# Check storage tab in Spark UI for:
# - Size in Memory
# - Size on Disk
# - Fraction Cached (should be 100%)
```

**Spark UI Check:** Storage tab shows cached RDDs/DataFrames. Monitor "Fraction Cached" - if < 100%, memory is insufficient.

---

## Broadcast Variables

### When to Use Broadcast

- Small lookup tables (< 200MB)
- Dimension tables joined to large fact tables
- Configuration data used across all tasks
- Avoiding shuffle in map-side joins

### DataFrame Broadcast Join

```python
from pyspark.sql.functions import broadcast

# Explicit broadcast hint
large_df = spark.read.parquet("s3://bucket/transactions/")  # 100GB
small_df = spark.read.parquet("s3://bucket/categories/")    # 50MB

# Broadcast small table for efficient join
result = large_df.join(broadcast(small_df), "category_id")

# Auto-broadcast threshold configuration
spark.conf.set("spark.sql.autoBroadcastJoinThreshold", 100 * 1024 * 1024)  # 100MB

# Disable auto-broadcast (force sort-merge join)
spark.conf.set("spark.sql.autoBroadcastJoinThreshold", -1)
```

### RDD Broadcast Variables

```python
# Create broadcast variable
lookup_dict = {"A": 1, "B": 2, "C": 3}
broadcast_lookup = spark.sparkContext.broadcast(lookup_dict)

# Use in transformation
def enrich_with_lookup(row):
    lookup = broadcast_lookup.value
    return Row(
        id=row.id,
        code=row.code,
        value=lookup.get(row.code, 0)
    )

enriched_rdd = df.rdd.map(enrich_with_lookup)

# Clean up
broadcast_lookup.unpersist()
broadcast_lookup.destroy()
```

### Broadcast Size Limits

```python
# Maximum broadcast size (default 8GB, adjustable)
spark.conf.set("spark.sql.autoBroadcastJoinThreshold", 200 * 1024 * 1024)  # 200MB

# For larger broadcasts
spark.conf.set("spark.driver.maxResultSize", "4g")

# Monitor broadcast time in Spark UI
# Long broadcast time indicates table too large
```

**Warning:** Broadcasting tables > 200MB can cause driver OOM and slow broadcast. Use sort-merge join instead.

---

## Partitioning Strategies for Common Patterns

### Time-Series Data

```python
# Partition by date for time-range queries
df_partitioned = df.repartition("date")

# Range partition for ordered access
df_range = df.repartitionByRange(365, "date")  # One year

# Write partitioned by date
df.write.partitionBy("year", "month", "day").parquet("s3://bucket/data/")

# Read with partition pruning
df = spark.read.parquet("s3://bucket/data/") \
    .filter(F.col("year") == 2024)  # Only reads 2024 partitions
```

### User/Entity Data

```python
# Partition by user_id for user-specific queries
df_user_partitioned = df.repartition(1000, "user_id")

# Co-partition for efficient joins
users_partitioned = users.repartition(1000, "user_id")
orders_partitioned = orders.repartition(1000, "user_id")

# Join without shuffle (if partitioners match)
joined = users_partitioned.join(orders_partitioned, "user_id")
```

### Skewed Data

```python
# Salt skewed keys
salt_buckets = 10

# Add salt to skewed table
salted_df = large_df.withColumn(
    "salted_key",
    F.concat(
        F.col("join_key"),
        F.lit("_"),
        (F.monotonically_increasing_id() % salt_buckets).cast("string")
    )
)

# Explode small table to match
from pyspark.sql.functions import explode, array, lit

small_exploded = small_df.withColumn(
    "salt",
    explode(array([lit(i) for i in range(salt_buckets)]))
).withColumn(
    "salted_key",
    F.concat(F.col("join_key"), F.lit("_"), F.col("salt").cast("string"))
)

# Join on salted key
result = salted_df.join(small_exploded, "salted_key")
```

---

## File Partitioning (Write Optimization)

### Hive-Style Partitioning

```python
# Write with partitioning
df.write \
    .mode("overwrite") \
    .partitionBy("year", "month") \
    .parquet("s3://bucket/data/")

# Result directory structure:
# s3://bucket/data/year=2024/month=01/part-*.parquet
# s3://bucket/data/year=2024/month=02/part-*.parquet

# Read with partition discovery
df = spark.read.parquet("s3://bucket/data/")
# Columns year, month automatically added from path
```

### Bucketing (Hash-Based File Partitioning)

```python
# Write bucketed table for optimized joins
df.write \
    .mode("overwrite") \
    .bucketBy(100, "user_id") \
    .sortBy("timestamp") \
    .saveAsTable("bucketed_orders")

# Read bucketed table
orders = spark.table("bucketed_orders")
users = spark.table("bucketed_users")  # Same bucket count

# Bucket join - no shuffle if buckets match
result = orders.join(users, "user_id")
```

**Note:** Bucketing requires Hive metastore and saveAsTable. Doesn't work with direct file writes.

### Controlling Output Files

```python
# Control number of output files
# One file per partition
df.coalesce(1).write.parquet("s3://bucket/output/")

# Multiple files per partition (for large partitions)
df.repartition(100).write.parquet("s3://bucket/output/")

# Max records per file
df.write \
    .option("maxRecordsPerFile", 1000000) \
    .parquet("s3://bucket/output/")
```

---

## Spark UI Analysis for Partitioning/Caching

### Jobs Tab

- Check if cached data shows "(cached)" in DAG
- Look for skipped stages (using cached data)

### Stages Tab

- **Shuffle Write Size**: Large values indicate repartition opportunities
- **Shuffle Read Size**: Should be similar across tasks (no skew)
- **Task Duration Distribution**: Wide variance indicates partition imbalance

### Storage Tab

- **Size in Memory**: Actual cached size
- **Size on Disk**: Spilled size
- **Fraction Cached**: Should be 100% if memory sufficient

### SQL Tab

- Look for "BroadcastExchange" - indicates broadcast join
- Look for "ShuffleExchange" - indicates data movement
- Check "Rows Output" at each stage for data flow

---

## Common Anti-Patterns

```python
# BAD: Caching without measuring benefit
for table in all_tables:
    spark.read.parquet(table).cache()  # Wastes memory

# GOOD: Cache only if reused
expensive_df.cache()
result1 = expensive_df.groupBy("a").count()
result2 = expensive_df.groupBy("b").count()
expensive_df.unpersist()

# BAD: Too many small partitions
df.repartition(10000)  # Creates scheduling overhead

# GOOD: Right-size partitions (128MB-256MB each)
df.repartition(100)

# BAD: Too few partitions for large data
df.coalesce(1)  # Single partition can't parallelize

# GOOD: Maintain parallelism
df.coalesce(max(1, target_size))

# BAD: Repartition before filter
df.repartition(1000).filter(F.col("active") == True)  # Shuffles then filters

# GOOD: Filter then coalesce
df.filter(F.col("active") == True).coalesce(100)  # Filter first, then resize

# BAD: Broadcasting large table
result = large.join(broadcast(also_large), "key")  # OOM risk

# GOOD: Let Spark decide or use sort-merge
result = large.join(also_large, "key")  # Sort-merge join
```

---

## Best Practices Summary

1. **Target 128-256MB partitions** - Not too small (overhead) or large (OOM)
2. **Use 2-4 partitions per core** - Maximize parallelism
3. **Enable AQE in Spark 3.x** - Automatic partition optimization
4. **Cache only reused DataFrames** - Measure before caching everything
5. **Use MEMORY_AND_DISK** - Safe default storage level
6. **Broadcast tables < 200MB** - Avoid shuffle for small dimension tables
7. **Coalesce after filters** - Reduce partitions when data shrinks
8. **Repartition for joins** - Co-partition related tables
9. **Partition writes by filter columns** - Enable partition pruning
10. **Monitor Storage tab** - Ensure cache fits in memory
