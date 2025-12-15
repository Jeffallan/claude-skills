# Terraform Best Practices

> Reference for: Terraform Engineer
> Load when: DRY patterns, naming conventions, security, cost optimization

## DRY Principles

**Use Modules for Reusability**
```hcl
# Bad - Repeated code
resource "aws_vpc" "app1" {
  cidr_block = "10.0.0.0/16"
  enable_dns_hostnames = true
  tags = { Name = "app1-vpc", Environment = "prod" }
}

resource "aws_vpc" "app2" {
  cidr_block = "10.1.0.0/16"
  enable_dns_hostnames = true
  tags = { Name = "app2-vpc", Environment = "prod" }
}

# Good - Use module
module "vpc_app1" {
  source = "./modules/vpc"

  name       = "app1"
  cidr_block = "10.0.0.0/16"
  environment = "prod"
}

module "vpc_app2" {
  source = "./modules/vpc"

  name       = "app2"
  cidr_block = "10.1.0.0/16"
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
data "aws_ami" "amazon_linux_2" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["amzn2-ami-hvm-*-x86_64-gp2"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

resource "aws_instance" "web" {
  ami           = data.aws_ami.amazon_linux_2.id
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
resource "aws_vpc" "vpc" {}          # Bad
resource "aws_subnet" "subnet" {}    # Bad
resource "aws_vpc" "this" {}         # Use in modules only
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
variable "instance_type" {}      # Good
variable "instanceType" {}       # Bad
variable "InstanceType" {}       # Bad

# Be descriptive
variable "vpc_cidr_block" {}     # Good
variable "cidr" {}               # Too vague

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
main.tf           # Primary resource definitions
variables.tf      # Input variables
outputs.tf        # Output values
versions.tf       # Terraform and provider versions
backend.tf        # Backend configuration (optional)
locals.tf         # Local values (optional)
data.tf           # Data sources (optional)

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
  default = "SuperSecret123!"  # NEVER DO THIS
}

# Good - Use sensitive variables
variable "db_password" {
  description = "Database password"
  type        = string
  sensitive   = true
  # No default - must be provided
}

# Better - Use secrets manager
data "aws_secretsmanager_secret_version" "db_password" {
  secret_id = "prod/db/password"
}

resource "aws_db_instance" "main" {
  password = data.aws_secretsmanager_secret_version.db_password.secret_string
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
  storage_encrypted   = true
  kms_key_id          = aws_kms_key.rds.arn
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
# Security group with restricted access
resource "aws_security_group" "web" {
  name        = "${var.name}-web-sg"
  description = "Security group for web servers"
  vpc_id      = aws_vpc.main.id

  # Bad - Too permissive
  # ingress {
  #   from_port   = 0
  #   to_port     = 65535
  #   protocol    = "tcp"
  #   cidr_blocks = ["0.0.0.0/0"]
  # }

  # Good - Specific rules
  ingress {
    description = "HTTPS from internet"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description     = "HTTP from ALB"
    from_port       = 80
    to_port         = 80
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }

  egress {
    description = "All outbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
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
  ami           = data.aws_ami.amazon_linux_2.id
  instance_type = var.instance_type

  tags = merge(local.common_tags, {
    Name = "${var.name}-app"
    Role = "application"
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
  ami           = data.aws_ami.amazon_linux_2.id
  instance_type = var.instance_type

  lifecycle {
    create_before_destroy = true
    prevent_destroy       = var.environment == "production"
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

**Resource Scheduling**
```hcl
# Auto-scaling schedule for cost savings
resource "aws_autoscaling_schedule" "scale_down_evening" {
  scheduled_action_name  = "scale-down-evening"
  min_size               = 1
  max_size               = 1
  desired_capacity       = 1
  recurrence             = "0 20 * * MON-FRI"
  autoscaling_group_name = aws_autoscaling_group.app.name
}

resource "aws_autoscaling_schedule" "scale_up_morning" {
  scheduled_action_name  = "scale-up-morning"
  min_size               = 3
  max_size               = 10
  desired_capacity       = 3
  recurrence             = "0 7 * * MON-FRI"
  autoscaling_group_name = aws_autoscaling_group.app.name
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
  validation { ... }
}

# modules/vpc/outputs.tf
output "vpc_id" {
  description = "ID of the VPC"
  value       = aws_vpc.this.id
}

# Version all modules
# modules/vpc/versions.tf
terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
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
- [ ] Use for_each instead of count
- [ ] Avoid hardcoded secrets
- [ ] Enable logging and monitoring
- [ ] Implement cost optimization strategies
- [ ] Use lifecycle rules appropriately
- [ ] Keep modules focused and single-purpose
