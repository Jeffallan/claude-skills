# Terraform Best Practices

## DRY Principles

**Use Modules for Reusability**
```hcl
# Bad - Repeated code
resource "aws_vpc" "app1" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  tags                 = { Name = "app1-vpc", Environment = "prod" }
}

resource "aws_vpc" "app2" {
  cidr_block           = "10.1.0.0/16"
  enable_dns_hostnames = true
  tags                 = { Name = "app2-vpc", Environment = "prod" }
}

# Good - Use module
module "vpc_app1" {
  source = "./modules/vpc"

  name        = "app1"
  cidr_block  = "10.0.0.0/16"
  environment = "prod"
}

module "vpc_app2" {
  source = "./modules/vpc"

  name        = "app2"
  cidr_block  = "10.1.0.0/16"
  environment = "prod"
}
```

**Use Locals for Repeated Values**
```hcl
locals {
  common_tags = {
    Environment = var.environment
    ManagedBy   = "Terraform"
    Project     = var.project_name
    CostCenter  = var.cost_center
  }

  name_prefix = "${var.project_name}-${var.environment}"

  # Computed locals
  vpc_cidr = var.environment == "production" ? "10.0.0.0/16" : "10.1.0.0/16"

  # Complex data structures
  availability_zones = slice(data.aws_availability_zones.available.names, 0, var.az_count)
}

resource "aws_vpc" "main" {
  cidr_block = local.vpc_cidr
  tags       = merge(local.common_tags, { Name = "${local.name_prefix}-vpc" })
}
```

**Use Data Sources Instead of Hardcoding**
```hcl
# Bad - Hardcoded AMI
resource "aws_instance" "web" {
  ami           = "ami-0c55b159cbfafe1f0"
  instance_type = "t3.micro"
}

# Good - Dynamic AMI lookup
data "aws_ami" "amazon_linux" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["al2023-ami-2023.*-x86_64"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

resource "aws_instance" "web" {
  ami           = data.aws_ami.amazon_linux.id
  instance_type = "t3.micro"
}
```

**Use for_each for Multiple Similar Resources**
```hcl
# Bad - Duplicated resources
resource "aws_subnet" "private_1" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.1.0/24"
  availability_zone = "us-east-1a"
}

resource "aws_subnet" "private_2" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.2.0/24"
  availability_zone = "us-east-1b"
}

# Good - Use for_each
variable "private_subnets" {
  type = map(object({
    cidr_block = string
    az         = string
  }))
  default = {
    subnet1 = { cidr_block = "10.0.1.0/24", az = "us-east-1a" }
    subnet2 = { cidr_block = "10.0.2.0/24", az = "us-east-1b" }
  }
}

resource "aws_subnet" "private" {
  for_each = var.private_subnets

  vpc_id            = aws_vpc.main.id
  cidr_block        = each.value.cidr_block
  availability_zone = each.value.az

  tags = {
    Name = "${var.name}-private-${each.key}"
  }
}
```

## Naming Conventions

**Resource Naming**
```hcl
# Pattern: {resource_type}_{descriptive_name}

# Good examples
resource "aws_vpc" "main" {}
resource "aws_subnet" "private" {}
resource "aws_security_group" "web" {}
resource "aws_instance" "app" {}

# Avoid generic names
resource "aws_vpc" "vpc" {}       # Bad
resource "aws_subnet" "subnet" {} # Bad
resource "aws_vpc" "this" {}      # Use in modules only
# Resource names are singular nouns without the resource type; use "main" when
# only one instance exists
```

**AWS Resource Name Tags**
```hcl
locals {
  # Pattern: {project}-{environment}-{resource}-{identifier}
  name_prefix = "${var.project_name}-${var.environment}"
}

resource "aws_vpc" "main" {
  cidr_block = var.cidr_block

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-vpc"
  })
}

resource "aws_subnet" "private" {
  for_each = var.private_subnets

  vpc_id     = aws_vpc.main.id
  cidr_block = each.value.cidr_block

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-private-${each.key}"
    Type = "private"
  })
}

resource "aws_security_group" "web" {
  name   = "${local.name_prefix}-web-sg"
  vpc_id = aws_vpc.main.id

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-web-sg"
  })
}
```

**Variable Naming**
```hcl
# Use snake_case for all names
variable "instance_type" {} # Good
variable "instanceType" {}  # Bad
variable "InstanceType" {}  # Bad

# Be descriptive
variable "vpc_cidr_block" {} # Good
variable "cidr" {}           # Too vague

# Boolean variables should be questions
variable "enable_nat_gateway" {} # Good
variable "nat_gateway" {}        # Ambiguous

# Plural for lists/maps
variable "availability_zones" {} # Good
variable "private_subnets" {}    # Good
```

**File Naming**
```
# Standard structure
terraform.tf      # Terraform and provider version requirements
providers.tf      # Provider configurations
main.tf           # Primary resources and data sources
variables.tf      # Input variables (alphabetical)
outputs.tf        # Output values (alphabetical)
locals.tf         # Local values
backend.tf        # Backend configuration (optional)

# Resource-specific files for complex modules
vpc.tf
subnets.tf
security_groups.tf
route_tables.tf
```

## Security Best Practices

**Secret Management**
```hcl
# Bad - Secrets in plain text
variable "db_password" {
  default = "<db-password>" # NEVER DO THIS
}

# Good - Use sensitive variables
variable "db_password" {
  description = "Database password"
  type        = string
  sensitive   = true
  # No default - must be provided
}

# Best - let the service manage the secret so it never enters your state
resource "aws_db_instance" "main" {
  identifier                  = "main"
  engine                      = "postgres"
  instance_class              = "db.t4g.micro"
  allocated_storage           = 20
  username                    = "app"
  manage_master_user_password = true # stored in AWS Secrets Manager
}
```

Reading a secret through a regular data source
(`data.aws_secretsmanager_secret_version`) writes the value to state in plaintext.
Follow this priority order for sensitive attributes (Terraform 1.11+):

1. Native secrets-manager integration such as `manage_master_user_password`.
2. An `ephemeral` resource passed to a write-only attribute (`*_wo`, with its
   `*_wo_version`); neither value is stored in state or plan files.
3. A regular resource or data source only when neither option exists.

```hcl
ephemeral "random_password" "db" {
  length = 24
}

resource "aws_secretsmanager_secret_version" "db" {
  secret_id                = aws_secretsmanager_secret.db.id
  secret_string_wo         = ephemeral.random_password.db.result
  secret_string_wo_version = 1 # bump to rotate
}
```

**Encryption at Rest**
```hcl
# S3 bucket with encryption
resource "aws_s3_bucket" "data" {
  bucket = "my-data-bucket"
}

resource "aws_s3_bucket_server_side_encryption_configuration" "data" {
  bucket = aws_s3_bucket.data.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = aws_kms_key.s3.arn
    }
    bucket_key_enabled = true
  }
}

# EBS volume encryption
resource "aws_ebs_volume" "data" {
  availability_zone = "us-east-1a"
  size              = 100
  encrypted         = true
  kms_key_id        = aws_kms_key.ebs.arn
}

# RDS encryption
resource "aws_db_instance" "main" {
  storage_encrypted = true
  kms_key_id        = aws_kms_key.rds.arn
}
```

**Least Privilege IAM**
```hcl
# Bad - Overly permissive
data "aws_iam_policy_document" "bad" {
  statement {
    effect    = "Allow"
    actions   = ["*"]
    resources = ["*"]
  }
}

# Good - Specific permissions
data "aws_iam_policy_document" "good" {
  statement {
    effect = "Allow"
    actions = [
      "s3:GetObject",
      "s3:PutObject"
    ]
    resources = [
      "${aws_s3_bucket.data.arn}/*"
    ]
  }

  statement {
    effect = "Allow"
    actions = [
      "s3:ListBucket"
    ]
    resources = [
      aws_s3_bucket.data.arn
    ]
  }
}
```

**Network Security**
```hcl
# Manage rules as standalone resources: inline ingress/egress blocks conflict with
# them and make rule-level changes recreate or clobber each other
resource "aws_security_group" "web" {
  name        = "${var.name}-web-sg"
  description = "Security group for web servers"
  vpc_id      = aws_vpc.main.id
}

resource "aws_vpc_security_group_ingress_rule" "web_https" {
  security_group_id = aws_security_group.web.id
  description       = "HTTPS from internet"
  from_port         = 443
  to_port           = 443
  ip_protocol       = "tcp"
  cidr_ipv4         = "0.0.0.0/0"
}

resource "aws_vpc_security_group_ingress_rule" "web_http_from_alb" {
  security_group_id            = aws_security_group.web.id
  description                  = "HTTP from ALB"
  from_port                    = 80
  to_port                      = 80
  ip_protocol                  = "tcp"
  referenced_security_group_id = aws_security_group.alb.id
}

# Avoid opening every port to the internet (from_port 0 - 65535, 0.0.0.0/0)

resource "aws_vpc_security_group_egress_rule" "web_all" {
  security_group_id = aws_security_group.web.id
  description       = "All outbound"
  ip_protocol       = "-1"
  cidr_ipv4         = "0.0.0.0/0"
}
```

## Resource Tagging

**Consistent Tagging Strategy**
```hcl
locals {
  # Required tags for all resources
  required_tags = {
    Environment = var.environment
    ManagedBy   = "Terraform"
    Project     = var.project_name
    CostCenter  = var.cost_center
    Owner       = var.owner_email
  }

  # Optional tags
  optional_tags = {
    Repository = "github.com/org/repo"
    Terraform  = "true"
  }

  # Merge all tags
  common_tags = merge(local.required_tags, local.optional_tags, var.additional_tags)
}

# Use provider default tags
provider "aws" {
  region = var.aws_region

  default_tags {
    tags = local.common_tags
  }
}

# Resource-specific tags
resource "aws_instance" "app" {
  ami           = data.aws_ami.amazon_linux.id
  instance_type = var.instance_type

  tags = merge(local.common_tags, {
    Name   = "${var.name}-app"
    Role   = "application"
    Backup = "daily"
  })
}
```

## Cost Optimization

**Cost-Aware Resource Sizing**
```hcl
variable "environment" {
  type = string
}

locals {
  # Environment-based sizing
  instance_type = {
    production  = "t3.large"
    staging     = "t3.medium"
    development = "t3.micro"
  }

  rds_instance_class = {
    production  = "db.r5.xlarge"
    staging     = "db.t3.medium"
    development = "db.t3.micro"
  }

  enable_multi_az = var.environment == "production" ? true : false
}

resource "aws_instance" "app" {
  instance_type = local.instance_type[var.environment]
}

resource "aws_db_instance" "main" {
  instance_class = local.rds_instance_class[var.environment]
  multi_az       = local.enable_multi_az
}
```

**Lifecycle Management**
```hcl
resource "aws_instance" "app" {
  ami           = data.aws_ami.amazon_linux.id
  instance_type = var.instance_type

  lifecycle {
    create_before_destroy = true
    prevent_destroy       = true # must be a literal; lifecycle arguments cannot use variables
    ignore_changes        = [ami, user_data]
  }
}

# S3 lifecycle rules for cost savings
resource "aws_s3_bucket_lifecycle_configuration" "data" {
  bucket = aws_s3_bucket.data.id

  rule {
    id     = "transition-to-ia"
    status = "Enabled"

    transition {
      days          = 30
      storage_class = "STANDARD_IA"
    }

    transition {
      days          = 90
      storage_class = "GLACIER"
    }

    expiration {
      days = 365
    }
  }
}
```

## Code Organization

**Directory Structure**
```
terraform/
├── environments/
│   ├── production/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   ├── terraform.tfvars
│   │   └── backend.tf
│   ├── staging/
│   └── development/
├── modules/
│   ├── vpc/
│   ├── eks/
│   └── rds/
├── global/
│   ├── iam/
│   └── route53/
└── README.md
```

**Module Best Practices**
```hcl
# Keep modules small and focused
# modules/vpc/main.tf - Does ONE thing well

# Clear input/output contracts
# modules/vpc/variables.tf
variable "cidr_block" {
  description = "CIDR block for VPC"
  type        = string

  validation {
    condition     = can(cidrhost(var.cidr_block, 0))
    error_message = "Must be a valid IPv4 CIDR block."
  }
}

# modules/vpc/outputs.tf
output "vpc_id" {
  description = "ID of the VPC"
  value       = aws_vpc.this.id
}

# Version all modules
# modules/vpc/terraform.tf
terraform {
  required_version = ">= 1.14"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
}
```

## Best Practices Checklist

- [ ] Use remote state with locking
- [ ] Pin Terraform and provider versions
- [ ] Validate all input variables
- [ ] Use consistent naming conventions
- [ ] Tag all resources for cost tracking
- [ ] Encrypt sensitive data at rest and in transit
- [ ] Implement least privilege IAM policies
- [ ] Use modules for reusable components
- [ ] Document module interfaces
- [ ] Run terraform fmt before commit
- [ ] Run terraform validate in CI/CD
- [ ] Review plan output before apply
- [ ] Use data sources instead of hardcoding
- [ ] Implement automated testing
- [ ] Use for_each instead of count (count only for conditional creation)
- [ ] Commit .terraform.lock.hcl
- [ ] Keep secrets out of state (managed secrets, ephemeral resources, write-only attributes)
- [ ] Avoid hardcoded secrets
- [ ] Enable logging and monitoring
- [ ] Implement cost optimization strategies
- [ ] Use lifecycle rules appropriately
- [ ] Keep modules focused and single-purpose
