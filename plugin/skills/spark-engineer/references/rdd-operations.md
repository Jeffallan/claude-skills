# RDD Operations

---

## When to Use RDDs

**Use RDDs when:**
- Processing unstructured data (raw text, custom binary formats)
- Need fine-grained control over physical data placement
- Implementing custom partitioning logic for specific access patterns
- Working with legacy Spark code that needs maintenance
- Building custom data structures not expressible as DataFrames

**Prefer DataFrames when:**
- Processing structured/semi-structured data
- Performing SQL-like operations
- Need Catalyst optimizer benefits
- Working with standard file formats (Parquet, JSON, ORC)

---

## RDD Creation

### From Collections

```python
# PySpark - Create RDD from Python collection
data = [1, 2, 3, 4, 5]
rdd = spark.sparkContext.parallelize(data, numSlices=4)  # 4 partitions

# From key-value pairs
pairs = [("a", 1), ("b", 2), ("c", 3)]
pair_rdd = spark.sparkContext.parallelize(pairs)
```

```scala
// Scala - Create RDD from collection
val data = Seq(1, 2, 3, 4, 5)
val rdd = spark.sparkContext.parallelize(data, numSlices = 4)

// From key-value pairs
val pairs = Seq(("a", 1), ("b", 2), ("c", 3))
val pairRdd = spark.sparkContext.parallelize(pairs)
```

### From Files

```python
# Text files - each line becomes an element
text_rdd = spark.sparkContext.textFile("hdfs://path/to/files/*.txt")

# Whole text files - each file as (filename, content) pair
files_rdd = spark.sparkContext.wholeTextFiles("hdfs://path/to/files/")

# Binary files
binary_rdd = spark.sparkContext.binaryFiles("hdfs://path/to/files/")

# Sequence files (Hadoop)
seq_rdd = spark.sparkContext.sequenceFile("hdfs://path/to/seqfile",
    "org.apache.hadoop.io.Text",
    "org.apache.hadoop.io.IntWritable")
```

### From DataFrame

```python
# Convert DataFrame to RDD of Rows
df = spark.read.parquet("s3://bucket/data/")
row_rdd = df.rdd

# Access Row fields
result_rdd = row_rdd.map(lambda row: (row.user_id, row.amount))

# Convert back to DataFrame
from pyspark.sql import Row
df_new = result_rdd.map(lambda x: Row(user_id=x[0], amount=x[1])).toDF()
```

---

## Transformations (Lazy)

Transformations return a new RDD and are not executed until an action is called.

### Basic Transformations

```python
# map - apply function to each element
squares = rdd.map(lambda x: x ** 2)

# flatMap - apply function returning iterator, flatten results
words = text_rdd.flatMap(lambda line: line.split(" "))

# filter - keep elements matching predicate
evens = rdd.filter(lambda x: x % 2 == 0)

# distinct - remove duplicates (causes shuffle)
unique = rdd.distinct()

# sample - random sample
sampled = rdd.sample(withReplacement=False, fraction=0.1, seed=42)

# union - combine two RDDs
combined = rdd1.union(rdd2)

# intersection - elements in both RDDs (causes shuffle)
common = rdd1.intersection(rdd2)

# subtract - elements in rdd1 not in rdd2 (causes shuffle)
diff = rdd1.subtract(rdd2)

# cartesian - all pairs (expensive!)
product = rdd1.cartesian(rdd2)
```

```scala
// Scala transformations
val squares = rdd.map(x => x * x)
val words = textRdd.flatMap(line => line.split(" "))
val evens = rdd.filter(_ % 2 == 0)
val unique = rdd.distinct()
val sampled = rdd.sample(withReplacement = false, fraction = 0.1, seed = 42L)
```

### MapPartitions (Efficient Batch Processing)

```python
# Process entire partition at once - more efficient than map
# Good for: database connections, expensive initialization, batch operations

def process_partition(iterator):
    # Initialize expensive resource once per partition
    connection = create_database_connection()
    try:
        for record in iterator:
            result = connection.process(record)
            yield result
    finally:
        connection.close()

result_rdd = rdd.mapPartitions(process_partition)

# With partition index
def process_with_index(partition_index, iterator):
    for record in iterator:
        yield (partition_index, record)

result_rdd = rdd.mapPartitionsWithIndex(process_with_index)
```

```scala
// Scala mapPartitions
val result = rdd.mapPartitions { iterator =>
  val connection = createDatabaseConnection()
  try {
    iterator.map(record => connection.process(record))
  } finally {
    connection.close()
  }
}
```

### Repartition and Coalesce

```python
# repartition - increase or decrease partitions (full shuffle)
rdd_repart = rdd.repartition(100)

# coalesce - decrease partitions only (avoids full shuffle)
rdd_coalesced = rdd.coalesce(10)  # Efficient reduction

# glom - collect each partition into an array
partitions = rdd.glom()  # RDD[Array[T]]
```

**When to use:**
- `repartition(n)`: When increasing partitions or need even distribution
- `coalesce(n)`: When decreasing partitions (after filter reduced data)

---

## Pair RDD Operations

Pair RDDs (key-value pairs) enable powerful transformations.

### Creating Pair RDDs

```python
# From tuples
pair_rdd = rdd.map(lambda x: (x.key, x.value))

# keyBy - create pairs from existing elements
pair_rdd = rdd.keyBy(lambda x: x.user_id)
```

### Transformations on Pair RDDs

```python
# reduceByKey - aggregate values by key (more efficient than groupByKey)
counts = pair_rdd.reduceByKey(lambda a, b: a + b)

# groupByKey - group all values for each key (shuffles all data!)
grouped = pair_rdd.groupByKey()  # Avoid when possible

# aggregateByKey - combine with different local/global combiners
sum_count = pair_rdd.aggregateByKey(
    zeroValue=(0, 0),  # (sum, count)
    seqFunc=lambda acc, v: (acc[0] + v, acc[1] + 1),  # within partition
    combFunc=lambda a, b: (a[0] + b[0], a[1] + b[1])  # across partitions
)

# combineByKey - most general aggregation
averages = pair_rdd.combineByKey(
    createCombiner=lambda v: (v, 1),
    mergeValue=lambda acc, v: (acc[0] + v, acc[1] + 1),
    mergeCombiners=lambda a, b: (a[0] + b[0], a[1] + b[1])
).mapValues(lambda x: x[0] / x[1])

# mapValues - transform values only (preserves partitioning)
doubled = pair_rdd.mapValues(lambda v: v * 2)

# flatMapValues - flatMap on values only
expanded = pair_rdd.flatMapValues(lambda v: range(v))

# keys and values
keys_rdd = pair_rdd.keys()
values_rdd = pair_rdd.values()

# sortByKey
sorted_rdd = pair_rdd.sortByKey(ascending=True)

# join operations (all cause shuffle)
joined = rdd1.join(rdd2)              # inner join
left = rdd1.leftOuterJoin(rdd2)       # left outer
right = rdd1.rightOuterJoin(rdd2)     # right outer
full = rdd1.fullOuterJoin(rdd2)       # full outer
cogroup = rdd1.cogroup(rdd2)          # group by key from both RDDs

# subtractByKey - remove keys present in other RDD
filtered = rdd1.subtractByKey(rdd2)
```

```scala
// Scala pair RDD operations
val counts = pairRdd.reduceByKey(_ + _)
val grouped = pairRdd.groupByKey()  // Avoid when possible

val averages = pairRdd.combineByKey(
  (v: Int) => (v, 1),
  (acc: (Int, Int), v: Int) => (acc._1 + v, acc._2 + 1),
  (a: (Int, Int), b: (Int, Int)) => (a._1 + b._1, a._2 + b._2)
).mapValues { case (sum, count) => sum.toDouble / count }

val joined = rdd1.join(rdd2)
```

### reduceByKey vs groupByKey

```python
# BAD: groupByKey shuffles all values
# Memory-intensive, can cause OOM
word_counts = words.map(lambda w: (w, 1)).groupByKey().mapValues(sum)

# GOOD: reduceByKey combines locally first
# Much more efficient, less data shuffled
word_counts = words.map(lambda w: (w, 1)).reduceByKey(lambda a, b: a + b)
```

**Spark UI Check:** Compare shuffle write sizes. `reduceByKey` should show much smaller shuffle than `groupByKey` for the same operation.

---

## Actions (Trigger Execution)

Actions return values to the driver or write to storage.

### Collection Actions

```python
# collect - return all elements to driver (OOM risk!)
all_data = rdd.collect()  # Use carefully on large RDDs

# take - return first n elements
first_10 = rdd.take(10)

# takeOrdered - return smallest/largest n elements
smallest_5 = rdd.takeOrdered(5)  # ascending
largest_5 = rdd.takeOrdered(5, key=lambda x: -x)

# takeSample - random sample
sample = rdd.takeSample(withReplacement=False, num=100, seed=42)

# first - return first element
first = rdd.first()

# top - return largest n elements
top_5 = rdd.top(5)

# count - count elements
total = rdd.count()

# countByKey - count elements per key (returns dict to driver)
key_counts = pair_rdd.countByKey()

# countByValue - count occurrences of each value
value_counts = rdd.countByValue()
```

### Aggregation Actions

```python
# reduce - aggregate all elements
total = rdd.reduce(lambda a, b: a + b)

# fold - reduce with zero value
total = rdd.fold(0, lambda a, b: a + b)

# aggregate - combine with different types
stats = rdd.aggregate(
    zeroValue=(0, 0),  # (sum, count)
    seqOp=lambda acc, v: (acc[0] + v, acc[1] + 1),
    combOp=lambda a, b: (a[0] + b[0], a[1] + b[1])
)
average = stats[0] / stats[1]
```

### Output Actions

```python
# saveAsTextFile - save as text files
rdd.saveAsTextFile("hdfs://path/output/")

# saveAsSequenceFile - save as Hadoop sequence file
pair_rdd.saveAsSequenceFile("hdfs://path/output/")

# saveAsPickleFile - Python pickle format
rdd.saveAsPickleFile("hdfs://path/output/")

# foreach - apply function to each element (side effects)
rdd.foreach(lambda x: print(x))  # Runs on executors

# foreachPartition - apply function to each partition
def save_partition(iterator):
    connection = create_connection()
    for record in iterator:
        connection.save(record)
    connection.close()

rdd.foreachPartition(save_partition)
```

---

## Custom Partitioners

### Implementing Custom Partitioner

```python
from pyspark import Partitioner

class RangePartitioner(Partitioner):
    def __init__(self, ranges):
        """
        ranges: list of (min, max) tuples defining partition boundaries
        """
        self.ranges = ranges

    def numPartitions(self):
        return len(self.ranges)

    def getPartition(self, key):
        for i, (min_val, max_val) in enumerate(self.ranges):
            if min_val <= key < max_val:
                return i
        return len(self.ranges) - 1  # Default to last partition

# Use custom partitioner
ranges = [(0, 100), (100, 500), (500, 1000), (1000, float('inf'))]
partitioner = RangePartitioner(ranges)
partitioned_rdd = pair_rdd.partitionBy(partitioner.numPartitions(), partitioner.getPartition)
```

```scala
// Scala custom partitioner
import org.apache.spark.Partitioner

class DomainPartitioner(numParts: Int) extends Partitioner {
  override def numPartitions: Int = numParts

  override def getPartition(key: Any): Int = {
    val domain = key.asInstanceOf[String].split("@")(1)
    math.abs(domain.hashCode % numPartitions)
  }

  override def equals(other: Any): Boolean = other match {
    case p: DomainPartitioner => p.numPartitions == numPartitions
    case _ => false
  }
}

val partitioned = pairRdd.partitionBy(new DomainPartitioner(10))
```

### Hash Partitioner (Default)

```python
from pyspark import HashPartitioner

# Repartition with hash partitioner
partitioned_rdd = pair_rdd.partitionBy(100)  # Uses HashPartitioner

# Preserve partitioning across transformations
# mapValues and flatMapValues preserve partitioner
preserved = partitioned_rdd.mapValues(lambda v: v * 2)
assert preserved.partitioner == partitioned_rdd.partitioner

# map does NOT preserve partitioner
not_preserved = partitioned_rdd.map(lambda x: (x[0], x[1] * 2))
assert not_preserved.partitioner is None
```

---

## Broadcast Variables and Accumulators

### Broadcast Variables

```python
# Broadcast large read-only data to all executors
lookup_table = {"a": 1, "b": 2, "c": 3}  # Small example
lookup_broadcast = spark.sparkContext.broadcast(lookup_table)

def enrich_record(record):
    table = lookup_broadcast.value  # Access broadcast value
    return (record, table.get(record, 0))

enriched_rdd = rdd.map(enrich_record)

# Clean up when done
lookup_broadcast.unpersist()
lookup_broadcast.destroy()
```

```scala
// Scala broadcast
val lookupTable = Map("a" -> 1, "b" -> 2, "c" -> 3)
val lookupBroadcast = spark.sparkContext.broadcast(lookupTable)

val enriched = rdd.map { record =>
  val table = lookupBroadcast.value
  (record, table.getOrElse(record, 0))
}
```

### Accumulators

```python
# Long accumulator
error_count = spark.sparkContext.longAccumulator("Error Count")

def process_record(record):
    try:
        return transform(record)
    except Exception:
        error_count.add(1)
        return None

result_rdd = rdd.map(process_record).filter(lambda x: x is not None)
result_rdd.count()  # Trigger execution

print(f"Errors encountered: {error_count.value}")

# Collection accumulator
from pyspark import AccumulatorParam

class SetAccumulatorParam(AccumulatorParam):
    def zero(self, initial_value):
        return set()

    def addInPlace(self, v1, v2):
        return v1.union(v2)

error_types = spark.sparkContext.accumulator(set(), SetAccumulatorParam())

def track_errors(record):
    try:
        return process(record)
    except ValueError:
        error_types.add({"ValueError"})
        return None
    except TypeError:
        error_types.add({"TypeError"})
        return None
```

**Caution:** Accumulators may be updated more than once if tasks are retried. Use only for debugging/monitoring, not business logic.

---

## Performance Patterns

### Avoiding Shuffle

```python
# BAD: Multiple shuffles
result = rdd.groupByKey().mapValues(sum).reduceByKey(max)

# GOOD: Single shuffle with combineByKey
result = rdd.combineByKey(
    createCombiner=lambda v: v,
    mergeValue=lambda acc, v: acc + v,
    mergeCombiners=lambda a, b: max(a, b)
)

# Co-partition related RDDs to avoid join shuffles
partitioned_users = users.partitionBy(100)
partitioned_orders = orders.partitionBy(100)  # Same partitioner
joined = partitioned_users.join(partitioned_orders)  # No shuffle if same partitioner
```

### Efficient Serialization

```python
# Use Kryo serialization for better performance
spark.conf.set("spark.serializer", "org.apache.spark.serializer.KryoSerializer")
spark.conf.set("spark.kryo.registrationRequired", "false")

# Register custom classes for Kryo (Scala)
# spark.conf.set("spark.kryo.classesToRegister", "com.example.MyClass")
```

### Memory-Efficient Operations

```python
# Prefer iterator-based operations
def efficient_processing(iterator):
    for record in iterator:
        # Process one at a time, don't collect
        yield transform(record)

result = rdd.mapPartitions(efficient_processing)

# Avoid collecting large data to driver
# BAD
all_keys = rdd.keys().collect()  # Could be millions!

# GOOD
key_sample = rdd.keys().take(1000)  # Sample only
```

---

## Spark UI Analysis for RDDs

### Stages Tab Metrics

| Metric | What to Check |
|--------|---------------|
| Shuffle Write | Minimize with reduceByKey over groupByKey |
| Shuffle Read | Large reads indicate join/aggregation overhead |
| Spill (Memory) | Indicates partition too large for memory |
| Spill (Disk) | Data being written to disk - increase memory |
| GC Time | Should be < 10% of task time |

### Common Issues

1. **Uneven partition sizes**: Look for tasks taking much longer than others
2. **Data skew**: One partition has much more data than others
3. **Straggler tasks**: A few tasks taking 10x longer than median

### Debugging Tips

```python
# Check partition sizes
partition_sizes = rdd.glom().map(len).collect()
print(f"Partition sizes: min={min(partition_sizes)}, max={max(partition_sizes)}, avg={sum(partition_sizes)/len(partition_sizes)}")

# Check partitioner
print(f"Partitioner: {rdd.partitioner}")
print(f"Num partitions: {rdd.getNumPartitions()}")

# Debug lineage
print(rdd.toDebugString())
```

---

## Best Practices Summary

1. **Prefer DataFrames** - Use RDDs only when DataFrame API insufficient
2. **Use reduceByKey over groupByKey** - Combines locally first, reduces shuffle
3. **Preserve partitioning** - Use mapValues/flatMapValues to keep partitioner
4. **Minimize shuffles** - Co-partition related RDDs, use broadcast for small data
5. **Use mapPartitions** - For expensive initialization (DB connections, etc.)
6. **Avoid collect on large data** - Use take, takeSample, or foreachPartition
7. **Broadcast lookup tables** - Avoid shuffle for small reference data
8. **Monitor accumulators** - Use for debugging, not business logic
9. **Check partition distribution** - Avoid skew with custom partitioners
10. **Profile with Spark UI** - Identify shuffle, spill, and GC issues
