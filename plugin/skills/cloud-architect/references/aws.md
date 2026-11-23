# AWS Architecture Reference

Comprehensive guide for AWS services, patterns, and Well-Architected Framework implementation.

## Well-Architected Framework

### Six Pillars

1. **Operational Excellence**
   - Infrastructure as Code (CloudFormation, CDK, Terraform)
   - Continuous integration/deployment
   - Observability (CloudWatch, X-Ray)
   - Runbooks and playbooks
   - Game days and failure injection

2. **Security**
   - Identity and Access Management (IAM)
   - Detective controls (GuardDuty, Security Hub)
   - Infrastructure protection (VPC, security groups, NACLs)
   - Data protection (KMS, encryption at rest/transit)
   - Incident response automation

3. **Reliability**
   - Multi-AZ deployments
   - Auto Scaling groups
   - Route 53 health checks and failover
   - Backup and restore (AWS Backup)
   - Chaos engineering (AWS FIS)

4. **Performance Efficiency**
   - Right-sizing with Compute Optimizer
   - Caching strategies (CloudFront, ElastiCache)
   - Database optimization (RDS Performance Insights)
   - Serverless architectures
   - Global content delivery

5. **Cost Optimization**
   - Reserved Instances and Savings Plans
   - Spot Instances for fault-tolerant workloads
   - S3 Intelligent-Tiering and lifecycle policies
   - Right-sizing recommendations
   - Cost allocation tags and budgets

6. **Sustainability**
   - Region selection for renewable energy
   - Serverless to minimize idle resources
   - Efficient data storage patterns
   - Resource utilization optimization

## Core Services Architecture

### Compute

**EC2 (Elastic Compute Cloud)**
- Instance families: General (t3, m5), Compute (c5), Memory (r5), GPU (p3, g4)
- Auto Scaling: Target tracking, step scaling, scheduled scaling
- Placement groups: Cluster, partition, spread
- Best practices: Use latest generation, right-size, enable detailed monitoring

**Lambda**
- Invocation models: Synchronous, asynchronous, event source mapping
- Concurrency: Reserved, provisioned, burst limits
- Layers for shared dependencies
- Best practices: Keep functions small, use environment variables, set timeouts

**ECS/EKS (Container Services)**
- ECS: Fargate for serverless, EC2 for control
- EKS: Managed Kubernetes with AWS integration
- Service mesh: App Mesh for observability
- Best practices: Use Fargate for simplicity, EKS for portability

**Elastic Beanstalk**
- Managed platform for web apps
- Auto-scaling and load balancing included
- Support for multiple languages and Docker

### Storage

**S3 (Simple Storage Service)**
- Storage classes: Standard, IA, One Zone-IA, Glacier, Deep Archive
- Lifecycle policies for automatic tiering
- Versioning and MFA delete for protection
- Cross-region replication for DR
- Best practices: Enable versioning, use lifecycle policies, block public access

**EBS (Elastic Block Store)**
- Volume types: gp3 (general), io2 (IOPS), st1 (throughput), sc1 (cold)
- Snapshots to S3 for backup
- Encryption by default
- Best practices: Use gp3 for most workloads, enable encryption

**EFS (Elastic File System)**
- NFSv4 file system for shared access
- Performance modes: General purpose, Max I/O
- Throughput modes: Bursting, provisioned
- Best practices: Use lifecycle management, enable encryption

**FSx**
- FSx for Windows File Server (SMB)
- FSx for Lustre (HPC workloads)
- FSx for NetApp ONTAP
- FSx for OpenZFS

### Database

**RDS (Relational Database Service)**
- Engines: MySQL, PostgreSQL, MariaDB, Oracle, SQL Server, Aurora
- Multi-AZ for high availability
- Read replicas for scalability
- Automated backups and point-in-time recovery
- Best practices: Use Aurora for performance, enable Multi-AZ, use read replicas

**Aurora**
- MySQL and PostgreSQL compatible
- 5x MySQL, 3x PostgreSQL performance
- Global databases for cross-region DR
- Serverless v2 for variable workloads
- Best practices: Use Aurora Serverless for unpredictable workloads

**DynamoDB**
- NoSQL key-value and document database
- On-demand or provisioned capacity
- Global tables for multi-region replication
- DynamoDB Streams for change data capture
- Best practices: Use on-demand for unpredictable traffic, implement GSI carefully

**ElastiCache**
- Redis or Memcached in-memory caching
- Cluster mode for Redis scalability
- Best practices: Use for session storage, API caching

### Networking

**VPC (Virtual Private Cloud)**
- CIDR planning: Avoid overlaps, plan for growth
- Subnets: Public (IGW), private (NAT), isolated (no internet)
- Route tables and routing decisions
- Security groups (stateful) and NACLs (stateless)
- Best practices: Use /16 for VPC, /24 for subnets, plan IP space

**Route 53**
- DNS service with health checks
- Routing policies: Simple, weighted, latency, failover, geolocation
- Best practices: Use alias records, enable DNSSEC

**CloudFront**
- Global CDN with edge locations
- Origin types: S3, ALB, custom origins
- Lambda@Edge for request/response manipulation
- Best practices: Enable compression, use field-level encryption

**VPN and Direct Connect**
- Site-to-Site VPN for encrypted tunnels
- Direct Connect for dedicated bandwidth
- Transit Gateway for hub-and-spoke topology
- Best practices: Use Direct Connect for high bandwidth, Transit Gateway for complex routing

**API Gateway**
- REST APIs, HTTP APIs, WebSocket APIs
- Throttling and quotas
- Integration with Lambda, HTTP endpoints, AWS services
- Best practices: Use HTTP APIs for lower cost, implement caching

### Security

**IAM (Identity and Access Management)**
- Principle of least privilege
- Roles for applications, not access keys
- MFA for privileged users
- Service Control Policies (SCPs) for organization-wide controls
- Best practices: Use roles, enable MFA, rotate credentials

**KMS (Key Management Service)**
- Customer managed keys (CMKs)
- Automatic key rotation
- Envelope encryption pattern
- Best practices: Enable automatic rotation, use grants for temporary access

**Secrets Manager**
- Automatic rotation for RDS credentials
- Versioning and rollback
- Best practices: Rotate secrets regularly, use VPC endpoints

**Security Hub**
- Centralized security findings
- CIS AWS Foundations Benchmark
- Integration with GuardDuty, Inspector, Macie

**GuardDuty**
- Threat detection using ML
- Monitors CloudTrail, VPC Flow Logs, DNS logs

## Architecture Patterns

### High Availability

**Multi-AZ Pattern**
```
- Application Load Balancer across 3 AZs
- Auto Scaling group with instances in each AZ
- RDS Multi-AZ for database
- S3 for static assets (11 9's durability)
```

**Multi-Region Pattern**
```
- Route 53 with health checks and failover
- CloudFront for global distribution
- Aurora Global Database for <1s RPO
- S3 Cross-Region Replication
```

### Serverless Architecture

**API-Driven Pattern**
```
API Gateway -> Lambda -> DynamoDB
              |
              v
          EventBridge -> Lambda (async processing)
```

**Event-Driven Pattern**
```
S3 Event -> Lambda -> Process -> SNS
                                  |
                                  v
                              Multiple subscribers
```

### Microservices on AWS

**Container-Based**
```
ALB -> ECS Fargate (multiple services)
    |
    v
Service Discovery (Cloud Map)
    |
    v
RDS/DynamoDB per service
```

**Service Mesh**
```
App Mesh for traffic management
X-Ray for distributed tracing
CloudWatch Container Insights
```

### Data Lake Architecture

```
Data Sources -> Kinesis Data Streams
                      |
                      v
              Kinesis Firehose
                      |
                      v
                S3 (raw bucket)
                      |
                      v
        Glue ETL or Lambda processing
                      |
                      v
            S3 (processed bucket)
                      |
                      v
          Athena/Redshift Spectrum
                      |
                      v
              QuickSight dashboards
```

## Migration Strategies (6Rs)

1. **Rehost (Lift-and-Shift)**
   - AWS Application Migration Service (MGN)
   - Minimal changes, quick migration
   - Use for legacy apps with compliance constraints

2. **Replatform (Lift-Tinker-and-Shift)**
   - Migrate to RDS instead of self-managed databases
   - Use Elastic Beanstalk instead of custom app servers
   - Small optimizations during migration

3. **Repurchase (Drop-and-Shop)**
   - Move to SaaS (e.g., Salesforce, Workday)
   - Reduce maintenance burden

4. **Refactor/Re-architect**
   - Modernize to serverless or containers
   - Highest effort, highest benefit
   - Use for competitive advantage applications

5. **Retire**
   - Decommission unused applications
   - Reduce attack surface and costs

6. **Retain**
   - Keep on-premises temporarily
   - Migrate later or keep for regulatory reasons

## Landing Zone Design

**AWS Control Tower**
- Multi-account strategy (AWS Organizations)
- Account factory for standardization
- Guardrails for governance (SCPs)
- Centralized logging (CloudTrail, Config)

**Account Structure**
```
Root
├── Security OU
│   ├── Log Archive Account
│   └── Security Tooling Account
├── Infrastructure OU
│   ├── Network Account (Transit Gateway, VPN)
│   └── Shared Services Account
└── Workloads OU
    ├── Production Account
    ├── Staging Account
    └── Development Account
```

**Network Design**
```
Transit Gateway (hub)
    |
    ├── Production VPC
    ├── Staging VPC
    ├── Development VPC
    └── On-premises (Direct Connect/VPN)
```

## Cost Optimization Strategies

**Compute Savings**
- Compute Savings Plans (up to 66% savings)
- EC2 Reserved Instances (1-year or 3-year)
- Spot Instances for batch/fault-tolerant workloads
- Lambda: Reduce memory if possible, use reserved concurrency

**Storage Savings**
- S3 Intelligent-Tiering for unpredictable access
- Lifecycle policies to Glacier/Deep Archive
- EBS gp3 instead of gp2 (20% cheaper, better performance)
- Delete unused snapshots and volumes

**Database Savings**
- Aurora Serverless v2 for variable workloads
- RDS Reserved Instances
- DynamoDB on-demand for unpredictable workloads
- Read replicas in same region to reduce cross-AZ data transfer

**Monitoring and Alerting**
- AWS Cost Explorer for analysis
- AWS Budgets for alerts
- Cost Anomaly Detection
- Trusted Advisor for recommendations

## Disaster Recovery

**RPO and RTO Targets**
- Backup and Restore: Hours RPO/RTO (lowest cost)
- Pilot Light: Minutes RPO, hours RTO
- Warm Standby: Seconds RPO, minutes RTO
- Multi-Site Active/Active: Near-zero RPO/RTO (highest cost)

**Implementation**
- AWS Backup for centralized backup management
- Aurora Global Database for cross-region replication
- S3 Cross-Region Replication
- Route 53 health checks and failover routing
- Regular DR testing with CloudFormation/Terraform

## Monitoring and Observability

**CloudWatch**
- Metrics: Standard (5 min) and detailed (1 min)
- Alarms with SNS notifications
- Logs Insights for log analysis
- Dashboards for visualization

**X-Ray**
- Distributed tracing for microservices
- Service map visualization
- Trace annotations and metadata

**AWS Config**
- Resource inventory and change tracking
- Compliance rules evaluation
- Relationship tracking between resources
