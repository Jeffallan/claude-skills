# GCP Architecture Reference

Comprehensive guide for Google Cloud Platform services, patterns, and architecture framework.

## Google Cloud Architecture Framework

### Five Pillars

1. **Operational Excellence**
   - Infrastructure as Code (Deployment Manager, Terraform)
   - CI/CD with Cloud Build
   - Monitoring with Cloud Monitoring (Stackdriver)
   - SRE principles and SLOs
   - Incident management

2. **Security, Privacy, and Compliance**
   - Identity and Access Management (Cloud IAM)
   - VPC Service Controls for data perimeter
   - Binary Authorization for containers
   - Data encryption (default at rest and in transit)
   - Security Command Center

3. **Reliability**
   - Multi-zone and multi-region deployments
   - Load balancing and autoscaling
   - Disaster recovery planning
   - Chaos engineering practices
   - SLIs, SLOs, and error budgets

4. **Cost Optimization**
   - Committed Use Discounts
   - Sustained Use Discounts (automatic)
   - Preemptible VMs and Spot VMs
   - Recommender for right-sizing
   - Active Assist for optimization

5. **Performance Optimization**
   - Cloud CDN and Media CDN
   - Caching strategies (Memorystore)
   - Database performance tuning
   - Network optimization (Premium vs Standard tier)
   - Regional and zonal resource placement

## Core Services Architecture

### Compute

**Compute Engine**
- Machine types: E2 (cost-optimized), N2 (balanced), C2 (compute-optimized), M2 (memory-optimized)
- Custom machine types for specific needs
- Preemptible VMs (up to 80% discount, max 24 hours)
- Spot VMs (similar to preemptible, better availability)
- Instance groups: Managed (with autoscaling), unmanaged
- Best practices: Use latest generation, committed use discounts, Spot for batch jobs

**Cloud Run**
- Fully managed serverless container platform
- Auto-scaling to zero
- Pay per request
- CPU allocated only during request handling
- Best practices: Stateless containers, optimize cold starts, use Cloud Run jobs for batch

**Cloud Functions**
- Event-driven serverless functions
- 1st gen: HTTP and background functions
- 2nd gen: Built on Cloud Run, better performance
- Event sources: Pub/Sub, Cloud Storage, Firestore, HTTP
- Best practices: Use 2nd gen, minimize cold starts, implement retry logic

**Google Kubernetes Engine (GKE)**
- Managed Kubernetes with GCP integration
- Autopilot mode: Fully managed, per-pod pricing
- Standard mode: More control, node management
- Workload Identity for secure service access
- Binary Authorization for deployment policies
- Best practices: Use Autopilot for simplicity, enable Workload Identity, implement network policies

**App Engine**
- Fully managed platform (PaaS)
- Standard environment (sandboxed, auto-scaling)
- Flexible environment (Docker containers, custom runtimes)
- Traffic splitting for canary deployments
- Best practices: Use Standard for web apps, Flexible for custom dependencies

### Storage

**Cloud Storage**
- Storage classes: Standard, Nearline (30-day), Coldline (90-day), Archive (365-day)
- Object lifecycle management
- Object versioning and retention policies
- Autoclass for automatic tier transitions
- Requester pays for data transfer
- Best practices: Use Autoclass, enable versioning, implement lifecycle policies

**Persistent Disk**
- Types: Standard (HDD), Balanced SSD, SSD, Extreme
- Zonal and regional persistent disks
- Snapshots for backup (incremental)
- Disk resize without downtime
- Best practices: Use Balanced SSD for most workloads, enable snapshots

**Filestore**
- Managed NFS file storage
- Tiers: Basic (1-63.9 TB), Enterprise (1-10 TB, better performance)
- Backup to Cloud Storage
- Best practices: Use Enterprise for production, implement backups

**Cloud Storage for Firebase**
- Object storage for mobile and web apps
- Client SDKs for direct upload/download
- Security rules for access control

### Database

**Cloud SQL**
- Managed MySQL, PostgreSQL, SQL Server
- High availability configuration (regional)
- Read replicas for scaling
- Automated backups and point-in-time recovery
- Best practices: Enable HA, use read replicas, implement connection pooling with Cloud SQL Proxy

**Cloud Spanner**
- Globally distributed relational database
- Horizontal scalability with strong consistency
- Multi-region for 99.999% availability
- TrueTime for global consistency
- Best practices: Design proper schema splits, use commit timestamps, optimize hotspots

**Firestore (Native mode)**
- NoSQL document database
- Real-time synchronization
- Offline support for mobile
- ACID transactions
- Best practices: Design document structure carefully, use collection group queries wisely

**Bigtable**
- NoSQL wide-column database
- Petabyte-scale with single-digit millisecond latency
- HBase API compatible
- Linear scalability by adding nodes
- Best practices: Design row keys to avoid hotspots, use replication for HA

**Memorystore**
- Managed Redis and Memcached
- Standard tier (HA with replica) and Basic tier
- Best practices: Use Standard tier for production, implement connection pooling

**BigQuery**
- Serverless data warehouse
- SQL analytics on petabyte-scale data
- Column-oriented storage
- Automatic caching and optimization
- Best practices: Partition and cluster tables, use approximate functions, control costs with quotas

### Networking

**VPC (Virtual Private Cloud)**
- Global resource (subnets are regional)
- Custom or auto mode networks
- Firewall rules (stateful)
- VPC peering and Shared VPC
- Private Google Access for GCP services
- Best practices: Use custom mode VPC, plan IP ranges, implement firewall rules

**Cloud Load Balancing**
- Global load balancing (HTTP(S), TCP/SSL Proxy, external TCP/UDP)
- Regional load balancing (internal HTTP(S), internal TCP/UDP)
- Anycast IP for global distribution
- Backend services with health checks
- Best practices: Use global for multi-region, enable CDN, configure health checks

**Cloud CDN**
- Global content delivery network
- Cache invalidation and signed URLs
- Integration with Cloud Storage and compute
- Best practices: Enable compression, use cache-control headers

**Cloud Interconnect and VPN**
- Dedicated Interconnect (10 Gbps or 100 Gbps)
- Partner Interconnect (50 Mbps to 50 Gbps)
- Cloud VPN (HA VPN for 99.99% SLA)
- Best practices: Use HA VPN for redundancy, Dedicated Interconnect for high bandwidth

**Cloud Armor**
- DDoS protection and WAF
- Preconfigured and custom rules
- Adaptive protection (ML-based)
- Best practices: Enable for internet-facing services, use preconfigured rules

**Private Service Connect**
- Private connectivity to Google APIs and services
- Service Directory for service discovery
- Best practices: Use for all managed services in production

### Serverless and Event-Driven

**Pub/Sub**
- Global message queue
- At-least-once delivery
- Push and pull subscriptions
- Message ordering and filtering
- Dead-letter topics
- Best practices: Use message attributes for filtering, implement idempotent processing

**Eventarc**
- Event-driven architecture
- Triggers for Cloud Run, Workflows, GKE
- Sources: Audit Logs, Pub/Sub, custom events
- Best practices: Use for decoupled architectures, implement event filtering

**Cloud Scheduler**
- Fully managed cron service
- HTTP, Pub/Sub, and App Engine targets
- Best practices: Use for periodic tasks, implement retry logic

**Workflows**
- Orchestrate and automate GCP and HTTP services
- YAML-based workflow definition
- Built-in error handling and retry
- Best practices: Use for complex multi-step processes, implement compensating transactions

### Security and Identity

**Cloud IAM**
- Resource hierarchy: Organization -> Folders -> Projects -> Resources
- Roles: Primitive (Owner, Editor, Viewer), Predefined, Custom
- Service accounts for applications
- Workload Identity for GKE
- Best practices: Use predefined roles, least privilege, service accounts for apps

**Cloud Key Management (KMS)**
- Encryption key management
- Customer-managed encryption keys (CMEK)
- Hardware Security Module (HSM) backed
- Automatic key rotation
- Best practices: Enable automatic rotation, use separate keys per environment

**Secret Manager**
- Store API keys, passwords, certificates
- Versioning and access control
- Automatic rotation integration
- Best practices: Rotate secrets regularly, use IAM for access control

**Security Command Center**
- Centralized security and risk management
- Asset discovery and vulnerability scanning
- Threat detection and compliance monitoring
- Best practices: Enable all detectors, review findings regularly

**VPC Service Controls**
- Create security perimeters around GCP resources
- Prevent data exfiltration
- Best practices: Use for sensitive data, implement access levels

### AI and Machine Learning

**Vertex AI**
- Unified ML platform
- AutoML for custom models
- Pre-trained models (Vision, Natural Language, etc.)
- MLOps with pipelines
- Best practices: Use AutoML for quick start, implement feature store

**BigQuery ML**
- Create and execute ML models using SQL
- Model types: Linear regression, logistic regression, clustering, etc.
- Integration with Vertex AI
- Best practices: Use for simple models, leverage BigQuery's scale

## Architecture Patterns

### High Availability

**Multi-Zone Pattern**
```
Global HTTP(S) Load Balancer
    |
    v
Managed Instance Group (multi-zone)
    |
    v
Cloud SQL (regional, HA configuration)
    |
    v
Cloud Storage (multi-region)
```

**Multi-Region Pattern**
```
Global HTTP(S) Load Balancer
    |
    ├── Backend Service Region 1 (Cloud Run)
    └── Backend Service Region 2 (Cloud Run)
         |
         v
    Cloud Spanner (multi-region)
```

### Serverless Architecture

**Event-Driven Pattern**
```
Cloud Storage upload event
    |
    v
Pub/Sub topic
    |
    v
Cloud Functions (image processing)
    |
    v
Firestore (metadata storage)
```

**API-First Pattern**
```
Cloud Endpoints or API Gateway
    |
    v
Cloud Run (multiple services)
    |
    ├── Cloud SQL (transactional data)
    └── Firestore (user data)
```

### Microservices on GKE

**GKE with Service Mesh**
```
Global Load Balancer
    |
    v
GKE Ingress
    |
    v
Anthos Service Mesh (Istio)
    |
    v
Microservices (Cloud Spanner, Firestore, Memorystore)
```

### Data Analytics Platform

```
Data Sources
    |
    v
Pub/Sub (streaming)
    |
    v
Dataflow (Apache Beam)
    |
    v
BigQuery (data warehouse)
    |
    v
Looker or Data Studio (visualization)
```

**Batch Processing**
```
Cloud Storage (raw data)
    |
    v
Dataproc (Apache Spark)
    |
    v
BigQuery (analytics)
```

## Landing Zone Design

### Resource Hierarchy

```
Organization
├── Folders (by environment or team)
│   ├── Production Folder
│   │   ├── Project A
│   │   └── Project B
│   ├── Staging Folder
│   └── Development Folder
└── Shared Services Folder
    ├── Networking Project (Shared VPC host)
    ├── Security Project (KMS, Secret Manager)
    └── Logging Project (centralized logs)
```

### Network Design

**Shared VPC Pattern**
```
Host Project (networking team)
├── Shared VPC
│   ├── Subnet Production (region A)
│   ├── Subnet Staging (region A)
│   └── Subnet Development (region B)

Service Projects (application teams)
├── Production Project (uses Production subnet)
├── Staging Project (uses Staging subnet)
└── Development Project (uses Development subnet)
```

**Hub-and-Spoke with VPN**
```
On-premises Network
    |
    v
Cloud VPN / Interconnect
    |
    v
Hub VPC (shared services)
    |
    ├── Spoke VPC 1 (production workloads)
    ├── Spoke VPC 2 (development workloads)
    └── Spoke VPC 3 (analytics workloads)
```

### Governance

**Organization Policies**
- Restrict public IP assignment
- Enforce uniform bucket-level access
- Restrict VM external IP
- Define allowed resource locations

**IAM Strategy**
- Use Google Groups for role assignments
- Separate duties (network admin, security admin, etc.)
- Service accounts per application
- Workload Identity for GKE workloads

**Logging and Monitoring**
```
All Projects
    |
    v
Log Router
    |
    ├── Cloud Logging (default sink)
    ├── BigQuery (long-term analysis)
    ├── Cloud Storage (archive)
    └── Pub/Sub (real-time processing)
```

## Migration Strategies

### Migrate to Virtual Machines

**Tools**
- Migrate to Virtual Machines (formerly Migrate for Compute Engine)
- Supports VMware, AWS, Azure, physical servers
- Agentless or agent-based migration
- Waves and test clones

**Process**
1. Assess: Fit assessment and TCO analysis
2. Plan: Group VMs, define migration waves
3. Deploy: Set up infrastructure (VPC, firewall rules)
4. Migrate: Test migration, cutover, validation
5. Optimize: Right-sizing, committed use discounts

### Database Migration

**Database Migration Service**
- Minimal downtime migrations
- Supports MySQL, PostgreSQL, SQL Server, Oracle
- Continuous replication for cutover flexibility

**Transfer Appliance**
- Physical device for large data transfers
- Up to 1 PB capacity
- Offline data transfer

## Cost Optimization

### Compute Savings

**Committed Use Discounts**
- 1-year or 3-year commitments
- Up to 57% savings for VMs
- Resource-based or spend-based

**Sustained Use Discounts**
- Automatic discounts for running VMs >25% of month
- Up to 30% savings
- No commitment required

**Preemptible and Spot VMs**
- Up to 80% discount
- Can be terminated by GCP
- Best for batch processing, fault-tolerant workloads

**Recommender**
- VM rightsizing recommendations
- Idle resource identification
- Committed use discount recommendations

### Storage Savings

**Cloud Storage**
- Autoclass for automatic tier transitions
- Lifecycle policies (delete or transition)
- Nearline (30+ days), Coldline (90+ days), Archive (365+ days)
- Requester pays for data transfer

**Persistent Disk**
- Delete orphaned disks
- Use balanced SSD instead of SSD when possible
- Resize disks to match actual usage

### BigQuery Savings

**On-Demand Pricing**
- $5 per TB processed
- Use partitioning and clustering
- Query cache for free repeated queries

**Flat-Rate Pricing**
- Predictable costs for heavy users
- Autoscaling slots available
- Flex slots for short-term commitments

**Best Practices**
- Use approximate aggregation functions (APPROX_COUNT_DISTINCT)
- Avoid SELECT *, specify columns
- Use materialized views for common queries
- Set up cost controls with custom quotas

### Monitoring Costs

**Cloud Billing**
- Budgets and alerts
- Cost breakdown by project, service, SKU
- Export to BigQuery for analysis
- Recommendations from Active Assist

## Disaster Recovery

### Backup Strategies

**VM Backups**
- Persistent disk snapshots (incremental)
- Machine images (include metadata and config)
- Cross-region snapshot copy
- Snapshot schedules for automation

**Database Backups**
- Cloud SQL: Automated backups (7-365 days retention)
- Cloud Spanner: Backups on demand or scheduled
- Firestore: Automated daily exports
- Bigtable: Backups to Cloud Storage

### High Availability

**RTO/RPO Matrix**

| Pattern | RPO | RTO | Cost |
|---------|-----|-----|------|
| Active-Active Multi-Region | Seconds | Seconds | High |
| Active-Passive with Replication | Minutes | Minutes | Medium |
| Warm Standby | Minutes | 10-30 min | Medium |
| Backup and Restore | Hours | Hours | Low |

**Cloud SQL HA**
- Regional configuration with synchronous replication
- Automatic failover
- 99.95% SLA (vs 99.5% for single zone)

**Cloud Spanner**
- Multi-region configuration
- 99.999% availability SLA
- Synchronous replication across regions

### Disaster Recovery Testing

- Regular DR drills (quarterly recommended)
- Document runbooks
- Test restoration procedures
- Measure actual RTO/RPO vs targets

## Monitoring and Observability

### Cloud Monitoring (formerly Stackdriver)

**Metrics**
- System metrics (CPU, memory, disk, network)
- Custom metrics via Cloud Monitoring API
- Metric scopes for multi-project monitoring
- Uptime checks for availability

**Dashboards and Charts**
- Predefined dashboards for GCP services
- Custom dashboards with filters and grouping
- SLO monitoring with error budgets

### Cloud Logging

**Log Types**
- Admin Activity logs (always enabled, no charge)
- Data Access logs (must be enabled)
- System Event logs
- Access Transparency logs (for Google access)

**Log Sinks**
- Route logs to BigQuery, Cloud Storage, Pub/Sub
- Aggregated sinks at organization/folder level
- Exclusion filters to reduce costs

### Cloud Trace

**Distributed Tracing**
- Automatic instrumentation for App Engine, Cloud Run, GKE
- Manual instrumentation with client libraries
- Latency analysis and performance insights
- Integration with Zipkin

### Cloud Profiler

**Continuous Profiling**
- CPU and memory profiling
- Low overhead (< 0.5% CPU)
- Flame graphs for visualization
- Supported languages: Java, Go, Python, Node.js

### Error Reporting

**Aggregated Error Tracking**
- Automatic error grouping
- Stack trace analysis
- Integration with Cloud Logging
- Notifications for new errors
