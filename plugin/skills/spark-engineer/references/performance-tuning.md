# Performance Tuning

---

## Cluster Sizing

### Executor Configuration

```python
# Key executor configurations
spark.conf.set("spark.executor.instances", 10)      # Number of executors
spark.conf.set("spark.executor.cores", 4)           # Cores per executor
spark.conf.set("spark.executor.memory", "16g")      # Memory per executor

# Dynamic allocation (recommended for varying workloads)
spark.conf.set("spark.dynamicAllocation.enabled", "true")
spark.conf.set("spark.dynamicAllocation.minExecutors", 2)
spark.conf.set("spark.dynamicAllocation.maxExecutors", 100)
spark.conf.set("spark.dynamicAllocation.executorIdleTimeout", "60s")
```

### Sizing Guidelines

| Cluster Size | Executor Memory | Executor Cores | Instances |
|--------------|-----------------|----------------|-----------|
| Small (dev) | 4-8GB | 2-4 | 2-5 |
| Medium | 8-16GB | 4-5 | 10-50 |
| Large | 16-32GB | 5-8 | 50-200 |
| Very Large | 32-64GB | 8-16 | 200+ |

**Rules of thumb:**
- 5 cores per executor is optimal (avoids HDFS I/O bottleneck)
- Leave 1 core per node for OS/YARN
- Leave 1GB per node for overhead
- executor.memoryOverhead = max(384MB, 10% of executor.memory)

### Memory Configuration

```python
# Executor memory breakdown
spark.conf.set("spark.executor.memory", "16g")
spark.conf.set("spark.executor.memoryOverhead", "2g")  # For off-heap, network buffers

# Memory fractions (default values usually good)
spark.conf.set("spark.memory.fraction", 0.6)           # Unified memory pool
spark.conf.set("spark.memory.storageFraction", 0.5)    # Cache vs execution split

# Off-heap memory (for large data)
spark.conf.set("spark.memory.offHeap.enabled", "true")
spark.conf.set("spark.memory.offHeap.size", "8g")
```

---

## Shuffle Optimization

### Shuffle Configuration

```python
# Number of shuffle partitions
spark.conf.set("spark.sql.shuffle.partitions", 200)  # Adjust based on data size

# Shuffle behavior
spark.conf.set("spark.shuffle.compress", "true")              # Compress shuffle data
spark.conf.set("spark.shuffle.spill.compress", "true")        # Compress spill data
spark.conf.set("spark.io.compression.codec", "lz4")           # Fast compression

# Shuffle file management
spark.conf.set("spark.shuffle.file.buffer", "64k")            # Buffer for shuffle writes
spark.conf.set("spark.shuffle.io.maxRetries", 3)              # Retry failed fetches
spark.conf.set("spark.shuffle.io.retryWait", "5s")            # Wait between retries

# Sort-based shuffle (default in Spark 2.0+)
spark.conf.set("spark.shuffle.sort.bypassMergeThreshold", 200)
```

### Reducing Shuffle Size

```python
from pyspark.sql import functions as F

# 1. Filter before join/aggregation
df_filtered = df.filter(F.col("date") >= "2024-01-01")
result = df_filtered.groupBy("category").count()

# 2. Use broadcast for small tables
from pyspark.sql.functions import broadcast
result = large_df.join(broadcast(small_df), "key")  # No shuffle for small_df

# 3. Select only needed columns before shuffle
df_slim = df.select("key", "value")  # Not all 50 columns
result = df_slim.groupBy("key").sum("value")

# 4. Use reduceByKey over groupByKey (RDD)
# BAD: groupByKey shuffles all values
counts = rdd.groupByKey().mapValues(len)
# GOOD: reduceByKey combines locally first
counts = rdd.map(lambda x: (x, 1)).reduceByKey(lambda a, b: a + b)

# 5. Coalesce after filter reduces data
df_filtered = df.filter(condition).coalesce(50)  # Reduce partitions without shuffle
```

### Spark UI Shuffle Metrics

In Stages tab, check:
- **Shuffle Write Size**: Total data written for shuffle
- **Shuffle Read Size**: Total data read from shuffle
- **Shuffle Read Blocked Time**: Time waiting for shuffle data
- **Shuffle Spill (Memory)**: Data spilled to memory
- **Shuffle Spill (Disk)**: Data spilled to disk (bad, increase memory)

---

## Data Skew Handling

### Identifying Skew

```python
from pyspark.sql import functions as F

# Check key distribution
key_counts = df.groupBy("join_key").count()
key_counts.orderBy(F.desc("count")).show(20)

# Summary statistics
stats = key_counts.agg(
    F.min("count").alias("min"),
    F.max("count").alias("max"),
    F.avg("count").alias("avg"),
    F.percentile_approx("count", 0.99).alias("p99")
)
stats.show()

# Skew ratio: max/avg > 10 indicates severe skew
```

**Spark UI indicators:**
- Few tasks taking much longer than others
- Task duration histogram shows long tail
- Some partitions much larger than others

### Skew Solutions

#### 1. Adaptive Query Execution (Spark 3.x)

```python
# Enable AQE skew handling
spark.conf.set("spark.sql.adaptive.enabled", "true")
spark.conf.set("spark.sql.adaptive.skewJoin.enabled", "true")
spark.conf.set("spark.sql.adaptive.skewJoin.skewedPartitionFactor", 5)
spark.conf.set("spark.sql.adaptive.skewJoin.skewedPartitionThresholdInBytes", "256MB")

# AQE will automatically split skewed partitions
result = large_df.join(another_df, "key")
```

#### 2. Salting Technique

```python
from pyspark.sql import functions as F

# Identify skewed keys
skewed_keys = ["NULL", "UNKNOWN", "DEFAULT"]
salt_buckets = 20

# Salt the skewed keys in large table
large_salted = large_df.withColumn(
    "salted_key",
    F.when(
        F.col("join_key").isin(skewed_keys),
        F.concat(F.col("join_key"), F.lit("_"), (F.rand() * salt_buckets).cast("int").cast("string"))
    ).otherwise(F.col("join_key"))
)

# Explode small table for skewed keys only
from pyspark.sql.functions import explode, array, lit, when

small_exploded = small_df.withColumn(
    "salted_key",
    F.when(
        F.col("join_key").isin(skewed_keys),
        F.explode(F.array([F.concat(F.col("join_key"), F.lit("_"), F.lit(i)) for i in range(salt_buckets)]))
    ).otherwise(F.col("join_key"))
)

# Join on salted key
result = large_salted.join(small_exploded, "salted_key")
```

#### 3. Broadcast Join for Skewed Keys

```python
from pyspark.sql.functions import broadcast

# Separate skewed and non-skewed data
skewed_keys = ["NULL", "UNKNOWN"]

large_skewed = large_df.filter(F.col("join_key").isin(skewed_keys))
large_normal = large_df.filter(~F.col("join_key").isin(skewed_keys))

small_skewed = small_df.filter(F.col("join_key").isin(skewed_keys))
small_normal = small_df.filter(~F.col("join_key").isin(skewed_keys))

# Broadcast join for skewed (small result expected)
result_skewed = large_skewed.join(broadcast(small_skewed), "join_key")

# Regular join for non-skewed
result_normal = large_normal.join(small_normal, "join_key")

# Union results
final_result = result_skewed.union(result_normal)
```

#### 4. Iterative Broadcast for Large Skewed Keys

```python
# For extremely skewed single keys
skewed_key_value = "NULL"

# Process skewed key separately with broadcast
skewed_large = large_df.filter(F.col("join_key") == skewed_key_value)
skewed_small = small_df.filter(F.col("join_key") == skewed_key_value)
result_skewed = skewed_large.crossJoin(broadcast(skewed_small))

# Process rest normally
normal_large = large_df.filter(F.col("join_key") != skewed_key_value)
normal_small = small_df.filter(F.col("join_key") != skewed_key_value)
result_normal = normal_large.join(normal_small, "join_key")

# Combine
final = result_skewed.union(result_normal)
```

---

## Memory Tuning

### Memory Pressure Symptoms

| Symptom | Cause | Solution |
|---------|-------|----------|
| Long GC pauses | Too much cached data | Reduce cache, use serialized storage |
| Spill to disk | Partitions too large | Increase partitions, add memory |
| OOM on driver | Large collect/broadcast | Reduce data to driver |
| OOM on executor | Large partitions | Repartition, increase memory |

### Garbage Collection Tuning

```python
# GC options (set via spark-submit --conf)
# For executor JVM
spark.conf.set("spark.executor.extraJavaOptions",
    "-XX:+UseG1GC -XX:InitiatingHeapOccupancyPercent=35 -XX:ConcGCThreads=4")

# For driver JVM
spark.conf.set("spark.driver.extraJavaOptions",
    "-XX:+UseG1GC -XX:InitiatingHeapOccupancyPercent=35")

# Monitor GC in Spark UI
# Executors tab shows GC Time for each executor
# Target: GC Time < 10% of total task time
```

### Reducing Memory Pressure

```python
# 1. Use serialized caching
from pyspark import StorageLevel
df.persist(StorageLevel.MEMORY_AND_DISK_SER)

# 2. Kryo serialization (faster, more compact)
spark.conf.set("spark.serializer", "org.apache.spark.serializer.KryoSerializer")

# 3. Avoid UDFs that create objects
# BAD: Creates Python objects
@udf("string")
def process(x):
    return x.upper()  # String allocation

# GOOD: Use built-in
df.withColumn("upper", F.upper("column"))

# 4. Use mapPartitions with generators
def efficient_process(iterator):
    for row in iterator:
        yield transform(row)  # No list allocation

result = df.rdd.mapPartitions(efficient_process)

# 5. Release cached data promptly
df.unpersist()
```

### Driver Memory Issues

```python
# Increase driver memory
spark.conf.set("spark.driver.memory", "8g")
spark.conf.set("spark.driver.maxResultSize", "4g")

# Avoid large collects
# BAD
all_data = df.collect()  # Pulls everything to driver

# GOOD
sample = df.take(1000)  # Small sample
df.write.parquet("s3://output/")  # Write distributed
```

---

## Join Optimization

### Join Strategy Selection

```python
# Broadcast Hash Join - small table (< 200MB)
from pyspark.sql.functions import broadcast
result = large.join(broadcast(small), "key")

# Sort Merge Join - large tables, equi-join
# Default for non-broadcast joins
result = large1.join(large2, "key")

# Shuffle Hash Join - medium tables, memory-constrained
spark.conf.set("spark.sql.join.preferSortMergeJoin", "false")

# Cartesian Product - cross join (avoid if possible)
result = df1.crossJoin(df2)

# Bucket Join - pre-bucketed tables (no shuffle)
# Requires saveAsTable with bucketBy
```

### Join Hints (Spark 3.0+)

```python
# Broadcast hint
result = df1.join(df2.hint("broadcast"), "key")

# Shuffle merge hint
result = df1.hint("merge").join(df2, "key")

# Shuffle hash hint
result = df1.hint("shuffle_hash").join(df2, "key")

# Shuffle replicate NL hint (for small-large joins)
result = df1.hint("shuffle_replicate_nl").join(df2, "key")
```

### Checking Join Plan

```python
# View physical plan
df1.join(df2, "key").explain(True)

# Look for:
# - BroadcastHashJoin (best for small tables)
# - SortMergeJoin (good for large-large joins)
# - BroadcastNestedLoopJoin (avoid, expensive)
# - CartesianProduct (avoid unless intentional)
```

---

## I/O Optimization

### Reading Data

```python
# Parquet (best for Spark)
df = spark.read.parquet("s3://bucket/data/")

# Optimize Parquet reading
spark.conf.set("spark.sql.parquet.filterPushdown", "true")
spark.conf.set("spark.sql.parquet.mergeSchema", "false")  # Faster if schema consistent

# Partition pruning - filter on partition columns
df = spark.read.parquet("s3://bucket/data/") \
    .filter(F.col("date") >= "2024-01-01")  # Only reads matching partitions

# Column pruning - select only needed columns
df = spark.read.parquet("s3://bucket/data/").select("id", "name", "amount")

# Explicit schema (avoid inference)
df = spark.read.schema(my_schema).json("s3://bucket/data/")
```

### Writing Data

```python
# Optimal file sizes (128MB-256MB)
spark.conf.set("spark.sql.files.maxRecordsPerFile", 1000000)

# Compaction for small files
df.coalesce(100).write.parquet("s3://bucket/output/")

# Partitioned writes
df.write.partitionBy("date").parquet("s3://bucket/output/")

# Bucketed writes (requires Hive metastore)
df.write.bucketBy(100, "user_id").sortBy("timestamp").saveAsTable("table")

# Compression
df.write.option("compression", "snappy").parquet("s3://bucket/output/")
```

### Small File Problem

```python
# Detect small files
file_list = spark.sparkContext._jvm.org.apache.hadoop.fs.FileSystem \
    .get(spark.sparkContext._jsc.hadoopConfiguration()) \
    .listStatus(spark.sparkContext._jvm.org.apache.hadoop.fs.Path("s3://bucket/data/"))

# Compact small files
df = spark.read.parquet("s3://bucket/small_files/")
df.coalesce(optimal_partition_count).write.parquet("s3://bucket/compacted/")

# Or use repartition for even distribution
df.repartition(100).write.parquet("s3://bucket/compacted/")
```

---

## Spark UI Deep Dive

### Jobs Tab

- **Job Duration**: Identify slow jobs
- **Stages**: Number of stages (more stages = more shuffles)
- **DAG Visualization**: Understand data flow

### Stages Tab

| Metric | Healthy | Action if Abnormal |
|--------|---------|-------------------|
| Duration | < 5 min per stage | Break up large stages |
| Tasks | Even distribution | Address skew |
| Shuffle Write | Minimize | Filter earlier, select fewer columns |
| Shuffle Read Blocked Time | Near 0 | Check network, increase parallelism |
| Spill (Disk) | 0 | Increase memory or partitions |
| GC Time | < 10% of task time | Tune GC, reduce cached data |

### Executors Tab

- **Storage Memory**: Cache usage
- **Shuffle Read/Write**: I/O patterns
- **GC Time**: Garbage collection overhead
- **Failed Tasks**: Executor failures

### SQL Tab

- **Duration**: Query execution time
- **Details**: Physical plan details
- **Metrics**: Input/output rows at each stage

### Storage Tab

- **Cached RDDs/DataFrames**: Size and partition distribution
- **Fraction Cached**: Should be 100%

---

## Common Configuration Template

```python
# Production configuration template
spark_configs = {
    # Executor configuration
    "spark.executor.instances": 50,
    "spark.executor.cores": 5,
    "spark.executor.memory": "16g",
    "spark.executor.memoryOverhead": "2g",

    # Driver configuration
    "spark.driver.memory": "8g",
    "spark.driver.maxResultSize": "4g",

    # Shuffle configuration
    "spark.sql.shuffle.partitions": 500,
    "spark.shuffle.compress": "true",
    "spark.io.compression.codec": "lz4",

    # SQL optimization
    "spark.sql.adaptive.enabled": "true",
    "spark.sql.adaptive.coalescePartitions.enabled": "true",
    "spark.sql.adaptive.skewJoin.enabled": "true",
    "spark.sql.autoBroadcastJoinThreshold": str(200 * 1024 * 1024),  # 200MB

    # Serialization
    "spark.serializer": "org.apache.spark.serializer.KryoSerializer",

    # Dynamic allocation
    "spark.dynamicAllocation.enabled": "true",
    "spark.dynamicAllocation.minExecutors": 5,
    "spark.dynamicAllocation.maxExecutors": 100,
}

for key, value in spark_configs.items():
    spark.conf.set(key, value)
```

---

## Troubleshooting Decision Tree

```
Slow Spark Job
├── Long GC Time (> 10%)?
│   ├── Yes → Increase executor memory or reduce cache
│   └── No → Continue
├── Shuffle Spill to Disk?
│   ├── Yes → Increase partitions or memory
│   └── No → Continue
├── Uneven Task Duration?
│   ├── Yes → Data skew, use salting or AQE
│   └── No → Continue
├── Long Shuffle Read Time?
│   ├── Yes → Network bottleneck, increase locality
│   └── No → Continue
├── Large Shuffle Size?
│   ├── Yes → Filter earlier, broadcast small tables
│   └── No → Continue
└── Too Many Small Tasks?
    ├── Yes → Reduce partitions with coalesce
    └── No → Check for code-level optimizations
```

---

## Best Practices Summary

1. **Size executors appropriately** - 5 cores, 16GB memory typical
2. **Enable AQE (Spark 3.x)** - Automatic optimization for partitions and skew
3. **Tune shuffle partitions** - Based on data size, not default 200
4. **Address data skew** - Salt keys or use AQE automatic handling
5. **Monitor Spark UI** - Check shuffle, spill, GC metrics
6. **Use broadcast joins** - For tables under 200MB
7. **Filter and select early** - Reduce data before shuffle
8. **Avoid UDFs** - Use built-in functions (10-100x faster)
9. **Cache strategically** - Only reused data, unpersist when done
10. **Test at scale** - Performance varies significantly with data volume
