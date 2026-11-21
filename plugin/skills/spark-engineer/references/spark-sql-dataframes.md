# Spark SQL and DataFrame API

---

## When to Use DataFrames vs RDDs

**Use DataFrames when:**
- Processing structured or semi-structured data (JSON, Parquet, CSV, Avro)
- Performing SQL-like operations (joins, aggregations, filters)
- Need Catalyst optimizer benefits (predicate pushdown, column pruning)
- Working with columnar formats for better compression

**Use RDDs when:**
- Need fine-grained control over physical data distribution
- Working with unstructured data (text processing, custom binary formats)
- Implementing custom partitioning logic
- Legacy code migration (prefer DataFrame migration when possible)

---

## Schema Definition

### Explicit Schema (Production Required)

```python
# PySpark - Explicit schema definition
from pyspark.sql.types import (
    StructType, StructField, StringType, IntegerType,
    DoubleType, TimestampType, ArrayType, MapType
)

# Define schema explicitly - ALWAYS do this in production
user_schema = StructType([
    StructField("user_id", StringType(), nullable=False),
    StructField("name", StringType(), nullable=True),
    StructField("age", IntegerType(), nullable=True),
    StructField("email", StringType(), nullable=True),
    StructField("created_at", TimestampType(), nullable=False),
    StructField("tags", ArrayType(StringType()), nullable=True),
    StructField("metadata", MapType(StringType(), StringType()), nullable=True)
])

# Read with explicit schema - no inference overhead
df = spark.read.schema(user_schema).json("s3://bucket/users/")
```

```scala
// Scala - Explicit schema definition
import org.apache.spark.sql.types._

val userSchema = StructType(Seq(
  StructField("user_id", StringType, nullable = false),
  StructField("name", StringType, nullable = true),
  StructField("age", IntegerType, nullable = true),
  StructField("email", StringType, nullable = true),
  StructField("created_at", TimestampType, nullable = false),
  StructField("tags", ArrayType(StringType), nullable = true),
  StructField("metadata", MapType(StringType, StringType), nullable = true)
))

val df = spark.read.schema(userSchema).json("s3://bucket/users/")
```

### Schema Inference Pitfalls

```python
# AVOID in production - causes full data scan
df = spark.read.json("s3://bucket/users/")  # Infers schema - slow!

# If you must infer, sample a small portion
df = spark.read.option("samplingRatio", 0.01).json("s3://bucket/users/")
```

---

## Column Operations and Expressions

### Built-in Functions (Always Prefer Over UDFs)

```python
from pyspark.sql import functions as F
from pyspark.sql.window import Window

# Column transformations - use built-in functions
df = df.withColumn("name_upper", F.upper(F.col("name")))
df = df.withColumn("email_domain", F.split(F.col("email"), "@")[1])
df = df.withColumn("age_group",
    F.when(F.col("age") < 18, "minor")
     .when(F.col("age") < 65, "adult")
     .otherwise("senior")
)

# Date/time operations
df = df.withColumn("year", F.year("created_at"))
df = df.withColumn("date_str", F.date_format("created_at", "yyyy-MM-dd"))
df = df.withColumn("days_since", F.datediff(F.current_date(), "created_at"))

# Array operations
df = df.withColumn("first_tag", F.col("tags")[0])
df = df.withColumn("tag_count", F.size("tags"))
df = df.withColumn("has_premium", F.array_contains("tags", "premium"))

# Null handling
df = df.withColumn("name_clean", F.coalesce("name", F.lit("Unknown")))
df = df.filter(F.col("email").isNotNull())
```

### Window Functions

```python
from pyspark.sql.window import Window
from pyspark.sql import functions as F

# Define window specifications
user_window = Window.partitionBy("user_id").orderBy("created_at")
category_window = Window.partitionBy("category")

# Ranking functions
df = df.withColumn("row_num", F.row_number().over(user_window))
df = df.withColumn("rank", F.rank().over(user_window))
df = df.withColumn("dense_rank", F.dense_rank().over(user_window))

# Analytic functions
df = df.withColumn("prev_value", F.lag("amount", 1).over(user_window))
df = df.withColumn("next_value", F.lead("amount", 1).over(user_window))
df = df.withColumn("running_total", F.sum("amount").over(user_window))

# Aggregations over windows
df = df.withColumn("category_avg", F.avg("amount").over(category_window))
df = df.withColumn("category_max", F.max("amount").over(category_window))

# Rolling windows
rolling_7day = Window.partitionBy("user_id") \
    .orderBy(F.col("created_at").cast("long")) \
    .rangeBetween(-7*86400, 0)  # 7 days in seconds

df = df.withColumn("rolling_7d_sum", F.sum("amount").over(rolling_7day))
```

```scala
// Scala window functions
import org.apache.spark.sql.expressions.Window
import org.apache.spark.sql.functions._

val userWindow = Window.partitionBy("user_id").orderBy("created_at")
val categoryWindow = Window.partitionBy("category")

val result = df
  .withColumn("row_num", row_number().over(userWindow))
  .withColumn("running_total", sum("amount").over(userWindow))
  .withColumn("category_avg", avg("amount").over(categoryWindow))
```

---

## Spark SQL Queries

### Registering DataFrames as Views

```python
# Temporary view - session scoped
df.createOrReplaceTempView("users")

# Global temporary view - application scoped
df.createOrReplaceGlobalTempView("users")
# Access via: global_temp.users

# Execute SQL
result = spark.sql("""
    SELECT
        user_id,
        name,
        COUNT(*) as order_count,
        SUM(amount) as total_spent
    FROM users u
    JOIN orders o ON u.user_id = o.user_id
    WHERE u.created_at >= '2024-01-01'
    GROUP BY user_id, name
    HAVING total_spent > 1000
    ORDER BY total_spent DESC
""")
```

### CTEs and Subqueries

```python
result = spark.sql("""
    WITH user_stats AS (
        SELECT
            user_id,
            COUNT(*) as order_count,
            SUM(amount) as total_spent,
            AVG(amount) as avg_order
        FROM orders
        WHERE order_date >= '2024-01-01'
        GROUP BY user_id
    ),
    ranked_users AS (
        SELECT
            *,
            PERCENT_RANK() OVER (ORDER BY total_spent) as spend_percentile
        FROM user_stats
    )
    SELECT *
    FROM ranked_users
    WHERE spend_percentile >= 0.9
""")
```

---

## Join Strategies

### Join Types and When to Use

```python
# Inner join - matching records only
result = orders.join(users, orders.user_id == users.user_id, "inner")

# Left outer - all from left, matching from right
result = orders.join(users, "user_id", "left")

# Right outer - all from right, matching from left
result = orders.join(users, "user_id", "right")

# Full outer - all records from both
result = orders.join(users, "user_id", "full")

# Left anti - records in left NOT in right
new_users = all_users.join(existing_users, "user_id", "left_anti")

# Left semi - records in left that have match in right (no columns from right)
active_users = users.join(orders, "user_id", "left_semi")

# Cross join - cartesian product (use carefully!)
result = df1.crossJoin(df2)
```

### Broadcast Join (Small Table Optimization)

```python
from pyspark.sql.functions import broadcast

# Explicit broadcast hint - join small table to large table
# Broadcasts entire small_df to all executors (must fit in memory)
result = large_df.join(broadcast(small_df), "join_key")

# Auto broadcast threshold (default 10MB)
spark.conf.set("spark.sql.autoBroadcastJoinThreshold", 200 * 1024 * 1024)  # 200MB

# Disable auto broadcast for specific query
spark.conf.set("spark.sql.autoBroadcastJoinThreshold", -1)
```

**Spark UI Check:** In SQL tab, look for "BroadcastHashJoin" vs "SortMergeJoin". Broadcast should show quick exchange, while sort-merge shows shuffle.

### Handling Skewed Joins (Spark 3.x AQE)

```python
# Enable Adaptive Query Execution (Spark 3.0+)
spark.conf.set("spark.sql.adaptive.enabled", "true")
spark.conf.set("spark.sql.adaptive.skewJoin.enabled", "true")
spark.conf.set("spark.sql.adaptive.skewJoin.skewedPartitionFactor", 5)
spark.conf.set("spark.sql.adaptive.skewJoin.skewedPartitionThresholdInBytes", "256MB")

# Manual skew handling with salting
from pyspark.sql.functions import monotonically_increasing_id, explode, array, lit

# Add salt to skewed key in large table
salt_count = 10
large_df_salted = large_df.withColumn(
    "join_key_salted",
    F.concat(F.col("join_key"), F.lit("_"), (F.monotonically_increasing_id() % salt_count).cast("string"))
)

# Explode small table to match salted keys
small_df_exploded = small_df.withColumn(
    "salt", F.explode(F.array([F.lit(i) for i in range(salt_count)]))
).withColumn(
    "join_key_salted",
    F.concat(F.col("join_key"), F.lit("_"), F.col("salt").cast("string"))
)

# Join on salted key
result = large_df_salted.join(small_df_exploded, "join_key_salted")
```

---

## Aggregations

### GroupBy Operations

```python
from pyspark.sql import functions as F

# Basic aggregations
stats = df.groupBy("category").agg(
    F.count("*").alias("count"),
    F.sum("amount").alias("total"),
    F.avg("amount").alias("average"),
    F.min("amount").alias("minimum"),
    F.max("amount").alias("maximum"),
    F.stddev("amount").alias("std_dev"),
    F.countDistinct("user_id").alias("unique_users"),
    F.collect_list("product_id").alias("products"),  # Caution: can OOM
    F.collect_set("product_id").alias("unique_products")
)

# Multiple grouping sets (Spark SQL)
result = spark.sql("""
    SELECT
        category,
        region,
        SUM(amount) as total
    FROM sales
    GROUP BY GROUPING SETS (
        (category, region),
        (category),
        (region),
        ()
    )
""")

# Equivalent with rollup/cube
rollup_df = df.rollup("category", "region").agg(F.sum("amount"))
cube_df = df.cube("category", "region").agg(F.sum("amount"))
```

### Pivot Tables

```python
# Pivot - turn row values into columns
pivot_df = df.groupBy("user_id").pivot("category", ["electronics", "clothing", "food"]) \
    .agg(F.sum("amount"))

# Result columns: user_id, electronics, clothing, food

# Unpivot (melt) - turn columns into rows
from pyspark.sql.functions import expr

unpivot_df = pivot_df.select(
    "user_id",
    expr("stack(3, 'electronics', electronics, 'clothing', clothing, 'food', food) as (category, amount)")
).filter("amount is not null")
```

---

## Catalyst Optimizer Tips

### Predicate Pushdown

```python
# Good - filter pushed down to data source
df = spark.read.parquet("s3://bucket/data/").filter(F.col("date") == "2024-01-01")

# Check physical plan for PushedFilters
df.explain(True)
```

### Column Pruning

```python
# Good - only read required columns
df = spark.read.parquet("s3://bucket/data/").select("id", "name", "amount")

# Bad - reads all columns then filters
df = spark.read.parquet("s3://bucket/data/")
result = df.select("id", "name", "amount")
```

### Partition Pruning

```python
# Data partitioned by date
# Good - only reads matching partitions
df = spark.read.parquet("s3://bucket/data/") \
    .filter(F.col("date").between("2024-01-01", "2024-01-31"))

# Verify partition pruning in Spark UI - Files Read should be reduced
```

---

## Common Anti-Patterns

### Avoid These Patterns

```python
# BAD: Using Python UDF when built-in exists
from pyspark.sql.functions import udf
@udf("string")
def upper_udf(s):
    return s.upper() if s else None
df.withColumn("name", upper_udf("name"))  # 10-100x slower!

# GOOD: Use built-in function
df.withColumn("name", F.upper("name"))

# BAD: Collect large data to driver
all_data = df.collect()  # OOM risk!
for row in all_data:
    process(row)

# GOOD: Process distributed or use take/limit
sample = df.take(100)  # Small sample
df.foreach(process_partition)  # Distributed processing

# BAD: Multiple actions triggering recomputation
count = df.count()
total = df.agg(F.sum("amount")).collect()
# Two full scans of data!

# GOOD: Cache if multiple actions needed
df.cache()
count = df.count()
total = df.agg(F.sum("amount")).collect()
df.unpersist()

# BAD: String column used in filter (case sensitivity issues)
df.filter(df.status == "ACTIVE")  # May miss "active", "Active"

# GOOD: Normalize or use case-insensitive comparison
df.filter(F.upper("status") == "ACTIVE")
```

---

## Spark UI Analysis for DataFrames

### SQL Tab Metrics to Monitor

1. **Duration** - Long stages indicate optimization opportunities
2. **Input Size** - Verify partition pruning reduced data read
3. **Shuffle Write/Read** - Large shuffles suggest join/aggregation issues
4. **Spill (Memory/Disk)** - Indicates memory pressure, increase executor memory

### Physical Plan Analysis

```python
# View physical plan
df.explain(True)

# Look for:
# - FileScan with PushedFilters (predicate pushdown working)
# - BroadcastHashJoin vs SortMergeJoin (broadcast optimization)
# - Exchange (shuffle operations)
# - WholeStageCodegen (Tungsten optimization active)
```

### Key Metrics in Stages Tab

| Metric | Healthy Range | Action if High |
|--------|---------------|----------------|
| Shuffle Read Size | < 1GB per task | Increase partitions, add filter |
| Spill (Disk) | 0 | Increase executor memory |
| GC Time | < 10% of task time | Tune memory fractions |
| Task Duration Variance | < 2x median | Address data skew |

---

## Best Practices Summary

1. **Always define explicit schemas** - No inference in production
2. **Use built-in functions** - Avoid UDFs when possible
3. **Broadcast small tables** - Tables under 200MB
4. **Filter early** - Push filters before joins and aggregations
5. **Select only needed columns** - Enable column pruning
6. **Partition by common filter columns** - Enable partition pruning
7. **Cache strategically** - Only reused DataFrames
8. **Monitor Spark UI** - Check shuffle, spill, and GC metrics
9. **Enable AQE in Spark 3.x** - Automatic optimization for skew and partitions
10. **Test with production data volume** - Performance varies with scale
