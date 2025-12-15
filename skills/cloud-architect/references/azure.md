# Azure Architecture Reference

Comprehensive guide for Azure services, patterns, and Cloud Adoption Framework implementation.

## Cloud Adoption Framework

### Framework Phases

1. **Strategy**
   - Define business justification
   - Expected business outcomes
   - Business case development
   - First project prioritization

2. **Plan**
   - Digital estate assessment
   - Initial organization alignment
   - Skills readiness plan
   - Cloud adoption plan

3. **Ready**
   - Azure landing zone setup
   - Azure setup guide
   - Migration readiness
   - Best practices validation

4. **Adopt (Migrate + Innovate)**
   - Migration: Assess, migrate, optimize
   - Innovate: Build cloud-native solutions
   - Best practices and patterns

5. **Govern**
   - Methodology for governance
   - Governance benchmark
   - Initial governance foundation
   - Mature governance evolution

6. **Manage**
   - Business commitments
   - Operations baseline
   - Platform and workload specialization

## Azure Well-Architected Framework

### Five Pillars

1. **Cost Optimization**
   - Azure Cost Management and Billing
   - Reserved instances and Savings Plans
   - Azure Hybrid Benefit
   - Auto-scaling and right-sizing

2. **Operational Excellence**
   - Infrastructure as Code (ARM, Bicep, Terraform)
   - Azure DevOps and GitHub Actions
   - Azure Monitor and Application Insights
   - Deployment slots and blue-green deployments

3. **Performance Efficiency**
   - Azure CDN and Front Door
   - Auto-scaling (VMSS, App Service)
   - Caching (Redis, CDN)
   - Performance diagnostics

4. **Reliability**
   - Availability Zones and regions
   - Azure Site Recovery
   - Load Balancer and Traffic Manager
   - Backup and disaster recovery

5. **Security**
   - Azure AD (Entra ID)
   - Network Security Groups and Firewalls
   - Azure Key Vault
   - Microsoft Defender for Cloud

## Core Services Architecture

### Compute

**Virtual Machines**
- VM sizes: General (D-series), Compute (F-series), Memory (E-series), GPU (N-series)
- Availability Sets (99.95% SLA)
- Availability Zones (99.99% SLA)
- VM Scale Sets for auto-scaling
- Best practices: Use managed disks, enable accelerated networking, use proximity placement groups

**App Service**
- Web Apps, API Apps, Mobile Apps
- Deployment slots for staging
- Auto-scaling based on metrics or schedule
- Supports .NET, Java, Node.js, Python, PHP, Ruby
- Best practices: Use deployment slots, enable auto-scaling, use App Service Plan efficiently

**Azure Functions**
- Consumption Plan (serverless)
- Premium Plan (VNet integration, no cold start)
- Dedicated Plan (App Service Plan)
- Durable Functions for orchestration
- Best practices: Keep functions small, use Premium for production, implement retry policies

**Azure Kubernetes Service (AKS)**
- Managed Kubernetes control plane
- Azure CNI or kubenet networking
- Azure AD integration
- Virtual nodes (Azure Container Instances)
- Best practices: Use system node pools, enable autoscaling, implement network policies

**Container Instances**
- Serverless containers
- Fast startup without infrastructure management
- Best for batch jobs and burstable workloads

**Azure Batch**
- Large-scale parallel and HPC workloads
- Auto-scaling compute nodes
- Task scheduling and dependencies

### Storage

**Blob Storage**
- Storage tiers: Hot, Cool, Archive
- Access tiers: Premium, Standard
- Lifecycle management policies
- Immutable storage for compliance
- Best practices: Use lifecycle policies, enable soft delete, implement versioning

**Azure Files**
- SMB and NFS file shares
- Integration with Azure File Sync
- Premium tier for high performance
- Best practices: Use Premium for databases, implement snapshots

**Disk Storage**
- Managed Disks: Premium SSD, Standard SSD, Standard HDD, Ultra Disk
- Disk encryption with Azure Disk Encryption
- Snapshots and incremental backups
- Best practices: Use Premium SSD for production, enable encryption

**Data Lake Storage Gen2**
- Hierarchical namespace for big data
- Built on Blob Storage
- Integration with Azure Synapse and Databricks
- Best practices: Enable hierarchical namespace, use lifecycle policies

**Azure NetApp Files**
- Enterprise-grade NFS and SMB shares
- High performance and low latency
- Snapshots and data protection

### Database

**Azure SQL Database**
- Serverless and provisioned compute
- Hyperscale for up to 100TB
- Elastic pools for multiple databases
- Auto-tuning and intelligent insights
- Best practices: Use serverless for dev/test, enable geo-replication

**Azure SQL Managed Instance**
- Near 100% compatibility with SQL Server
- VNet integration for isolation
- Native virtual network implementation
- Best practices: Use for lift-and-shift migrations

**Cosmos DB**
- Multi-model NoSQL database
- Global distribution with multi-master
- Consistency levels: Strong, Bounded staleness, Session, Consistent prefix, Eventual
- APIs: SQL, MongoDB, Cassandra, Gremlin, Table
- Best practices: Choose appropriate consistency, partition key design critical

**Azure Database for PostgreSQL/MySQL/MariaDB**
- Flexible Server (newer) vs Single Server (legacy)
- High availability with zone redundancy
- Read replicas for scaling
- Best practices: Use Flexible Server, enable HA, implement connection pooling

**Azure Cache for Redis**
- In-memory caching
- Clustering for scalability
- Geo-replication for disaster recovery
- Best practices: Use Premium tier for production, enable persistence

### Networking

**Virtual Network (VNet)**
- CIDR planning (avoid overlaps)
- Subnets with Network Security Groups
- Service endpoints and Private Link
- VNet peering for connectivity
- Best practices: Plan IP address space, use NSGs, implement Private Link

**Azure Load Balancer**
- Layer 4 load balancing
- Standard SKU (zone-redundant, SLA)
- Health probes and distribution algorithms
- Best practices: Use Standard SKU, configure health probes

**Application Gateway**
- Layer 7 load balancing
- WAF (Web Application Firewall)
- URL-based routing and SSL termination
- Best practices: Enable WAF, use autoscaling

**Azure Front Door**
- Global load balancing and CDN
- WAF at edge
- Anycast for low latency
- Best practices: Use for global applications, enable caching

**VPN Gateway and ExpressRoute**
- Site-to-Site VPN for encrypted connectivity
- ExpressRoute for private, dedicated connection
- Virtual WAN for global transit network
- Best practices: Use ExpressRoute for production, implement redundancy

**Azure Firewall**
- Managed firewall service
- Application and network rules
- Threat intelligence
- Best practices: Use in hub-spoke topology, enable DNS proxy

**Azure Private Link**
- Private connectivity to Azure services
- No public internet exposure
- Available for PaaS services
- Best practices: Use for all PaaS services in production

### Security and Identity

**Azure Active Directory (Microsoft Entra ID)**
- Identity and access management
- Conditional Access policies
- Multi-factor authentication
- B2B and B2C scenarios
- Best practices: Enable MFA, use Conditional Access, implement PIM

**Azure Key Vault**
- Secrets, keys, and certificates management
- Hardware Security Module (HSM) backed
- Soft delete and purge protection
- Best practices: Enable soft delete, use RBAC, implement Private Link

**Microsoft Defender for Cloud**
- Security posture management
- Threat protection for hybrid workloads
- Regulatory compliance dashboard
- Just-in-time VM access
- Best practices: Enable enhanced security, implement recommendations

**Azure Policy**
- Governance and compliance at scale
- Built-in and custom policies
- Deny, audit, append effects
- Best practices: Assign at management group level, test before enforce

**Azure Sentinel**
- Cloud-native SIEM and SOAR
- AI-powered threat detection
- Integration with Microsoft 365, third-party tools
- Best practices: Enable data connectors, create custom analytics rules

## Architecture Patterns

### High Availability

**Zone-Redundant Pattern**
```
Azure Front Door (global)
    |
    v
Application Gateway (zone-redundant)
    |
    v
VM Scale Set (across availability zones)
    |
    v
Azure SQL Database (zone-redundant)
```

**Multi-Region Pattern**
```
Azure Traffic Manager (DNS-based routing)
    |
    ├── Region 1: App Service + SQL Database (primary)
    └── Region 2: App Service + SQL Database (geo-replica)
```

### Hub-Spoke Topology

```
Hub VNet
├── Azure Firewall
├── VPN Gateway
└── Shared Services
    |
    ├── Spoke VNet 1 (Production)
    ├── Spoke VNet 2 (Development)
    └── Spoke VNet 3 (DMZ)
```

### Serverless Architecture

**Event-Driven Pattern**
```
Event Grid -> Azure Functions -> Cosmos DB
                    |
                    v
              Service Bus -> Functions (processing)
```

**API-First Pattern**
```
API Management
    |
    ├── Function App 1 (auth)
    ├── Function App 2 (business logic)
    └── Function App 3 (data access)
```

### Microservices on Azure

**AKS-Based**
```
Azure Front Door
    |
    v
Application Gateway + WAF
    |
    v
AKS (multiple microservices)
    |
    ├── Cosmos DB (microservice A)
    ├── SQL Database (microservice B)
    └── Service Bus (async communication)
```

**Container Apps Pattern**
```
Azure Container Apps
├── Dapr for state management
├── KEDA for event-driven scaling
└── Azure Monitor for observability
```

### Data Platform

```
Data Sources
    |
    v
Event Hubs / IoT Hub
    |
    v
Stream Analytics (real-time processing)
    |
    v
Data Lake Storage Gen2
    |
    v
Azure Synapse Analytics
    |
    v
Power BI (visualization)
```

## Landing Zone Design

### Enterprise-Scale Landing Zone

**Management Group Hierarchy**
```
Tenant Root Group
├── Platform
│   ├── Management (monitoring, automation)
│   ├── Connectivity (hub networks, VPN)
│   └── Identity (domain controllers)
└── Landing Zones
    ├── Corp (internal workloads)
    └── Online (internet-facing workloads)
```

**Network Topology**
```
Hub VNet (Connectivity subscription)
├── Azure Firewall
├── VPN Gateway
├── ExpressRoute Gateway
└── Bastion

Spoke VNets (Workload subscriptions)
├── Production VNet
├── Staging VNet
└── Development VNet
```

**Governance**
- Azure Policy for compliance
- Management groups for hierarchy
- RBAC assignments at appropriate scope
- Resource tags for cost allocation
- Azure Blueprints for repeatable deployments

## Migration Strategies

### Azure Migrate

1. **Assess**
   - Discovery with Azure Migrate appliance
   - Dependency analysis
   - Performance-based sizing
   - Cost estimation

2. **Migrate**
   - Azure Migrate: Server Migration (agentless)
   - Database Migration Service
   - App Service Migration Assistant
   - Data Box for large data transfers

3. **Optimize**
   - Right-sizing recommendations
   - Reserved instances
   - Azure Hybrid Benefit

### Migration Patterns

**Rehost**: Azure Migrate for VMs
**Replatform**: App Service, Azure SQL Database
**Refactor**: Container Apps, AKS, Functions
**Rebuild**: Azure-native services (Cosmos DB, Cognitive Services)

## Cost Optimization

### Compute Savings
- Azure Reserved Instances (1-year or 3-year, up to 72% savings)
- Azure Savings Plans for Compute (up to 65% savings)
- Spot VMs for fault-tolerant workloads (up to 90% savings)
- Azure Hybrid Benefit (use existing Windows Server/SQL licenses)
- Auto-shutdown for dev/test VMs

### Storage Savings
- Blob Storage lifecycle policies (Hot -> Cool -> Archive)
- Azure Files: Standard tier for general use
- Managed Disks: Standard SSD instead of Premium if possible
- Delete unused snapshots and disks

### Database Savings
- Serverless tier for Azure SQL Database
- Reserved capacity for Cosmos DB
- DTU model vs vCore (choose based on workload)
- Pause Azure Synapse when not in use

### Monitoring
- Azure Cost Management + Billing
- Cost alerts and budgets
- Azure Advisor recommendations
- Resource tagging for cost allocation

## Disaster Recovery

### Azure Site Recovery

**VM Replication**
- Azure to Azure replication
- On-premises to Azure (VMware, Hyper-V, physical)
- RPO: 30 seconds to a few minutes
- Automated failover and failback

**Recovery Plans**
- Multi-tier application recovery
- Customizable scripts and manual actions
- Integration with Azure Automation

### Backup Strategies

**Azure Backup**
- VM backups (application-consistent)
- SQL Server and SAP HANA in Azure VMs
- Azure Files backup
- Cross-region restore

**Database Backup**
- SQL Database: Automated backups (7-35 days)
- Cosmos DB: Continuous backup (30 days)
- Long-term retention policies

### High Availability

**RTO/RPO Targets**
- Active-Active: Multi-region with Traffic Manager (near-zero)
- Active-Passive: Geo-replication with failover (minutes)
- Backup and Restore: Azure Backup (hours)

## Monitoring and Observability

### Azure Monitor

**Components**
- Metrics: Time-series data (1-minute resolution)
- Logs: Log Analytics workspace for queries (KQL)
- Alerts: Metric, log, and activity log alerts
- Dashboards: Custom visualizations

**Application Insights**
- APM for web applications
- Distributed tracing
- Live Metrics Stream
- Smart detection and anomaly detection
- Best practices: Instrument all applications, set up availability tests

### Log Analytics

**KQL Queries**
```kusto
// Performance analysis
Perf
| where CounterName == "% Processor Time"
| summarize avg(CounterValue) by bin(TimeGenerated, 5m), Computer
| render timechart

// Failed requests
requests
| where success == false
| summarize count() by resultCode, bin(timestamp, 1h)
```

**Workbooks**
- Interactive reports
- Parameterized queries
- Combining metrics and logs

## Identity and Access

### Azure AD Best Practices

- Enable MFA for all users
- Use Conditional Access policies
- Implement Privileged Identity Management (PIM)
- Regular access reviews
- Break-glass accounts

### RBAC Design

**Built-in Roles**
- Owner: Full access including RBAC
- Contributor: Full access except RBAC
- Reader: Read-only access
- Custom roles for specific needs

**Scope Hierarchy**
```
Management Group (highest)
    |
Subscription
    |
Resource Group
    |
Resource (lowest)
```

Best practices: Assign at highest appropriate scope, use groups not individual users, apply least privilege
