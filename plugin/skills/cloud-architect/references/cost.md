# Cloud Cost Optimization Reference

Comprehensive guide for cloud cost optimization including reserved instances, spot/preemptible, right-sizing, and FinOps practices.

## FinOps Framework

### FinOps Principles

1. **Teams need to collaborate** - Finance, engineering, and business work together
2. **Everyone takes ownership** - Decentralized cost responsibility
3. **A centralized team drives FinOps** - Center of excellence for best practices
4. **Reports should be accessible and timely** - Real-time visibility
5. **Decisions are driven by business value** - Cost per business outcome
6. **Take advantage of variable cost model** - Scale up and down as needed

### FinOps Lifecycle

```
      Inform
         |
    +---------+
    |         |
    v         v
 Optimize --> Operate
    ^         |
    |         |
    +---------+
```

**Inform Phase**
- Visibility into cloud spend
- Allocation and showback
- Benchmarking and forecasting

**Optimize Phase**
- Rate optimization (RIs, savings plans)
- Usage optimization (right-sizing)
- Architectural optimization

**Operate Phase**
- Continuous improvement
- Automation and governance
- Anomaly detection

## Compute Cost Optimization

### Reserved Instances / Savings Plans

**AWS Savings Plans**

| Type | Flexibility | Savings |
|------|-------------|---------|
| Compute Savings Plans | Any EC2, Fargate, Lambda | Up to 66% |
| EC2 Instance Savings Plans | Specific instance family, region | Up to 72% |
| Reserved Instances | Specific instance type, AZ | Up to 72% |

**Commitment Strategy**
```
Baseline (always-on): 1-year or 3-year Savings Plans
Variable (predictable): Scheduled Reserved Instances
Spiky (unpredictable): On-Demand + Spot
```

**Azure Reservations**
```
# Azure CLI - Purchase reservation
az reservations reservation-order purchase \
  --sku Standard_D2s_v3 \
  --term P1Y \
  --billing-scope /subscriptions/{subscription-id} \
  --quantity 10 \
  --applied-scope-type Shared
```

**GCP Committed Use Discounts**
- Resource-based: Specific vCPUs and memory
- Spend-based: Dollar commitment for flexibility
- 1-year (37% discount) or 3-year (55% discount)

### Spot/Preemptible Instances

**When to Use Spot**
- Batch processing and analytics
- CI/CD build agents
- Stateless web servers (with auto-scaling)
- Machine learning training
- Development and testing environments

**AWS Spot Best Practices**
```yaml
# EC2 Auto Scaling with Spot
MixedInstancesPolicy:
  InstancesDistribution:
    OnDemandBaseCapacity: 2
    OnDemandPercentageAboveBaseCapacity: 20
    SpotAllocationStrategy: capacity-optimized
  LaunchTemplate:
    Overrides:
      - InstanceType: m5.large
      - InstanceType: m5a.large
      - InstanceType: m4.large
      - InstanceType: r5.large
```

**Spot Interruption Handling**
```python
# Check for spot termination notice (AWS)
import requests

def check_spot_termination():
    try:
        response = requests.get(
            "http://169.254.169.254/latest/meta-data/spot/termination-time",
            timeout=2
        )
        if response.status_code == 200:
            # 2-minute warning - gracefully shutdown
            graceful_shutdown()
    except requests.exceptions.RequestException:
        pass  # Not being terminated
```

**GCP Preemptible/Spot VMs**
```hcl
# Terraform - GCP Spot VM
resource "google_compute_instance" "spot" {
  name         = "spot-instance"
  machine_type = "n2-standard-4"

  scheduling {
    preemptible                 = true
    automatic_restart           = false
    provisioning_model          = "SPOT"
    instance_termination_action = "STOP"
  }
}
```

### Right-Sizing

**Analysis Process**
1. Collect metrics (CPU, memory, network, disk I/O)
2. Identify idle or underutilized resources
3. Recommend appropriate instance size
4. Implement changes during maintenance windows
5. Monitor and iterate

**AWS Compute Optimizer**
```bash
# Enable Compute Optimizer
aws compute-optimizer update-enrollment-status \
  --status Active \
  --include-member-accounts

# Get recommendations
aws compute-optimizer get-ec2-instance-recommendations \
  --filters name=Finding,values=OVER_PROVISIONED
```

**Right-Sizing Thresholds**
| Metric | Underutilized | Optimal | Overutilized |
|--------|---------------|---------|--------------|
| CPU | <20% avg | 40-60% avg | >80% avg |
| Memory | <30% avg | 50-70% avg | >85% avg |
| Network | <10% capacity | Variable | >80% capacity |

**Azure Advisor Recommendations**
```bash
# Get cost recommendations
az advisor recommendation list \
  --category Cost \
  --query "[?impact=='High']"
```

## Storage Cost Optimization

### Object Storage Tiering

**AWS S3 Storage Classes**
```
S3 Standard
    |
    | (30 days)
    v
S3 Standard-IA
    |
    | (90 days)
    v
S3 Glacier Instant Retrieval
    |
    | (180 days)
    v
S3 Glacier Deep Archive
```

**Lifecycle Policy Example**
```json
{
  "Rules": [
    {
      "ID": "OptimizeCosts",
      "Status": "Enabled",
      "Filter": { "Prefix": "logs/" },
      "Transitions": [
        { "Days": 30, "StorageClass": "STANDARD_IA" },
        { "Days": 90, "StorageClass": "GLACIER" },
        { "Days": 365, "StorageClass": "DEEP_ARCHIVE" }
      ],
      "Expiration": { "Days": 730 }
    }
  ]
}
```

**S3 Intelligent-Tiering**
- Automatic tiering based on access patterns
- No retrieval fees
- Small monitoring fee per object
- Best for unpredictable access patterns

### Block Storage Optimization

**EBS Volume Selection**
| Type | Use Case | $/GB/month |
|------|----------|------------|
| gp3 | General purpose | $0.08 |
| gp2 | Legacy (migrate to gp3) | $0.10 |
| io2 | High IOPS databases | $0.125+ |
| st1 | Throughput (big data) | $0.045 |
| sc1 | Cold archives | $0.015 |

**gp3 Migration (20% savings)**
```bash
# Modify EBS volume from gp2 to gp3
aws ec2 modify-volume \
  --volume-id vol-12345678 \
  --volume-type gp3 \
  --iops 3000 \
  --throughput 125
```

### Database Storage

**Aurora Storage Optimization**
- Pay only for storage used (auto-scaling)
- No pre-provisioning required
- 10GB increments up to 128TB

**DynamoDB Capacity Modes**
| Mode | Best For | Pricing |
|------|----------|---------|
| On-Demand | Unpredictable traffic | Pay per request |
| Provisioned | Steady traffic | Pay per capacity unit |
| Provisioned + Auto Scaling | Variable but predictable | Lower cost than on-demand |

## Network Cost Optimization

### Data Transfer Costs

**AWS Data Transfer Pricing**
```
Inbound: Free
Same AZ: Free
Cross-AZ: $0.01/GB each direction
Same Region (via public IP): $0.01/GB
Cross-Region: $0.02/GB
Internet Egress: $0.09/GB (first 10TB)
```

**Optimization Strategies**
1. Keep traffic within same AZ when possible
2. Use VPC endpoints for AWS services
3. Use CloudFront for cacheable content
4. Compress data before transfer
5. Use regional rather than global services

**VPC Endpoints (Avoid NAT Gateway)**
```hcl
# Gateway endpoint (free for S3, DynamoDB)
resource "aws_vpc_endpoint" "s3" {
  vpc_id       = aws_vpc.main.id
  service_name = "com.amazonaws.us-east-1.s3"
}

# Interface endpoint (cheaper than NAT for specific services)
resource "aws_vpc_endpoint" "ecr" {
  vpc_id            = aws_vpc.main.id
  service_name      = "com.amazonaws.us-east-1.ecr.api"
  vpc_endpoint_type = "Interface"
}
```

### CDN Optimization

**CloudFront Cost Savings**
- Lower data transfer rates than direct from origin
- Cache hit ratio optimization (target >90%)
- Use Origin Shield to reduce origin load
- Compress objects (Gzip/Brotli)

```yaml
# CloudFront cache optimization
CacheBehaviors:
  - PathPattern: "/static/*"
    CachePolicyId: 658327ea-f89d-4fab-a63d-7e88639e58f6  # CachingOptimized
    Compress: true
    TTL:
      DefaultTTL: 86400
      MaxTTL: 31536000
```

## Serverless Cost Optimization

### Lambda Optimization

**Memory/CPU Tuning**
```python
# Use AWS Lambda Power Tuning
# Finds optimal memory for cost vs performance

# Results example:
# 128MB:  $0.000021 per invocation, 3200ms duration
# 256MB:  $0.000025 per invocation, 1600ms duration
# 512MB:  $0.000031 per invocation, 800ms duration
# 1024MB: $0.000042 per invocation, 450ms duration
# Optimal: 512MB (best cost-performance balance)
```

**Cost Reduction Strategies**
1. Right-size memory allocation
2. Minimize cold starts (provisioned concurrency for critical paths)
3. Use ARM64 (Graviton2) - 20% cheaper
4. Optimize package size for faster cold starts
5. Use Lambda Layers for shared dependencies

**Graviton2 Migration**
```yaml
# SAM template with ARM64
Resources:
  MyFunction:
    Type: AWS::Serverless::Function
    Properties:
      Runtime: python3.11
      Architectures:
        - arm64  # 20% cost savings
```

### Container Optimization

**Fargate Pricing Optimization**
```
# Fargate Spot: Up to 70% discount
# Use for fault-tolerant workloads

ECS Service:
  CapacityProviderStrategy:
    - CapacityProvider: FARGATE_SPOT
      Weight: 4
    - CapacityProvider: FARGATE
      Weight: 1
      Base: 2  # Minimum on-demand tasks
```

**Right-Size Container Resources**
```yaml
# Analyze actual usage with Container Insights
resources:
  requests:
    memory: "256Mi"  # Based on p95 usage + 20% buffer
    cpu: "100m"      # Based on p95 usage + 20% buffer
  limits:
    memory: "512Mi"  # 2x requests for burst
    cpu: "500m"
```

## Cost Allocation and Tagging

### Tagging Strategy

**Required Tags**
```yaml
# Terraform - enforce tags
variable "required_tags" {
  default = {
    environment  = "prod"
    cost-center  = "engineering"
    owner        = "platform-team"
    project      = "api-gateway"
    managed-by   = "terraform"
  }
}

resource "aws_instance" "example" {
  ami           = data.aws_ami.latest.id
  instance_type = "t3.medium"
  tags          = var.required_tags
}
```

**Tag Enforcement**
```json
// AWS SCP - Deny untagged resources
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "DenyUntaggedEC2",
      "Effect": "Deny",
      "Action": "ec2:RunInstances",
      "Resource": "arn:aws:ec2:*:*:instance/*",
      "Condition": {
        "Null": {
          "aws:RequestTag/cost-center": "true"
        }
      }
    }
  ]
}
```

### Cost Allocation Reports

**AWS Cost and Usage Report**
```bash
# Enable detailed billing reports
aws cur put-report-definition \
  --report-definition '{
    "ReportName": "detailed-cost-report",
    "TimeUnit": "HOURLY",
    "Format": "Parquet",
    "Compression": "Parquet",
    "S3Bucket": "my-billing-bucket",
    "S3Region": "us-east-1",
    "AdditionalArtifacts": ["ATHENA"]
  }'
```

**Athena Queries for Analysis**
```sql
-- Cost by service and tag
SELECT
  line_item_product_code as service,
  resource_tags_user_cost_center as cost_center,
  SUM(line_item_unblended_cost) as cost
FROM cost_report
WHERE month = '2024-01'
GROUP BY 1, 2
ORDER BY 3 DESC;

-- Unused Reserved Instances
SELECT
  reservation_reservation_a_r_n,
  reservation_unused_quantity,
  reservation_unused_normalized_unit_quantity
FROM cost_report
WHERE reservation_unused_quantity > 0;
```

## Automation and Governance

### Automated Cost Controls

**AWS Budgets with Actions**
```yaml
# CloudFormation - Budget with auto-stop
Resources:
  MonthlyCostBudget:
    Type: AWS::Budgets::Budget
    Properties:
      Budget:
        BudgetName: monthly-cost-limit
        BudgetLimit:
          Amount: 10000
          Unit: USD
        TimeUnit: MONTHLY
        BudgetType: COST
      NotificationsWithSubscribers:
        - Notification:
            NotificationType: ACTUAL
            ComparisonOperator: GREATER_THAN
            Threshold: 80
          Subscribers:
            - SubscriptionType: EMAIL
              Address: finance@company.com
```

**Scheduled Scaling (Dev/Test)**
```yaml
# Stop non-prod resources nights/weekends
Resources:
  ScaleDownSchedule:
    Type: AWS::AutoScaling::ScheduledAction
    Properties:
      AutoScalingGroupName: !Ref DevASG
      DesiredCapacity: 0
      Recurrence: "0 20 * * MON-FRI"  # 8 PM weekdays

  ScaleUpSchedule:
    Type: AWS::AutoScaling::ScheduledAction
    Properties:
      AutoScalingGroupName: !Ref DevASG
      DesiredCapacity: 3
      Recurrence: "0 8 * * MON-FRI"   # 8 AM weekdays
```

### Cost Anomaly Detection

**AWS Cost Anomaly Detection**
```bash
# Create anomaly monitor
aws ce create-anomaly-monitor \
  --anomaly-monitor '{
    "MonitorName": "ServiceMonitor",
    "MonitorType": "DIMENSIONAL",
    "MonitorDimension": "SERVICE"
  }'

# Create anomaly subscription
aws ce create-anomaly-subscription \
  --anomaly-subscription '{
    "SubscriptionName": "CostAlerts",
    "MonitorArnList": ["arn:aws:ce::123456789:anomalymonitor/abc123"],
    "Subscribers": [{"Type": "EMAIL", "Address": "alerts@company.com"}],
    "Threshold": 100
  }'
```

## Cost Metrics and KPIs

### Key Metrics

| Metric | Formula | Target |
|--------|---------|--------|
| Unit Cost | Total Cost / Business Metric | Decreasing |
| Coverage | Reserved Hours / Total Hours | >70% |
| Utilization | Used Reserved Hours / Purchased | >80% |
| Waste | Idle Resource Cost / Total Cost | <10% |
| Forecast Accuracy | Actual / Forecasted | 90-110% |

### Dashboard Example

```sql
-- Cost efficiency dashboard metrics
WITH metrics AS (
  SELECT
    date_trunc('month', usage_date) as month,
    SUM(cost) as total_cost,
    SUM(CASE WHEN reservation_arn IS NOT NULL THEN cost END) as reserved_cost,
    COUNT(DISTINCT user_id) as active_users
  FROM cloud_costs
  GROUP BY 1
)
SELECT
  month,
  total_cost,
  reserved_cost / total_cost as reservation_coverage,
  total_cost / active_users as cost_per_user
FROM metrics;
```

## Quick Wins Checklist

**Immediate Savings (This Week)**
- [ ] Delete unused EBS volumes and snapshots
- [ ] Terminate stopped EC2 instances not needed
- [ ] Remove unused Elastic IPs
- [ ] Delete unused load balancers
- [ ] Review and delete old AMIs

**Short-Term (This Month)**
- [ ] Right-size underutilized instances
- [ ] Migrate gp2 volumes to gp3
- [ ] Implement S3 lifecycle policies
- [ ] Enable S3 Intelligent-Tiering
- [ ] Schedule dev/test environments

**Medium-Term (This Quarter)**
- [ ] Purchase Savings Plans for baseline
- [ ] Implement Spot for fault-tolerant workloads
- [ ] Set up cost allocation tags
- [ ] Enable Cost Anomaly Detection
- [ ] Establish FinOps practices
