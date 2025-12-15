# Terraform State Management

> Reference for: Terraform Engineer
> Load when: Configuring backends, state locking, workspaces, migrations

## Remote Backend - S3 (AWS)

**Backend Configuration**
```hcl
# backend.tf
terraform {
  backend "s3" {
    bucket         = "my-terraform-state"
    key            = "production/vpc/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "terraform-state-lock"

    # Optional: Enable versioning for state file history
    versioning = true
  }
}
```

**S3 Bucket Setup**
```hcl
# State bucket with versioning and encryption
resource "aws_s3_bucket" "terraform_state" {
  bucket = "my-terraform-state"

  lifecycle {
    prevent_destroy = true
  }

  tags = {
    Name        = "Terraform State"
    Environment = "global"
  }
}

resource "aws_s3_bucket_versioning" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# DynamoDB table for state locking
resource "aws_dynamodb_table" "terraform_lock" {
  name           = "terraform-state-lock"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "LockID"

  attribute {
    name = "LockID"
    type = "S"
  }

  tags = {
    Name        = "Terraform State Lock"
    Environment = "global"
  }
}
```

## Remote Backend - Azure Blob

```hcl
terraform {
  backend "azurerm" {
    resource_group_name  = "terraform-state-rg"
    storage_account_name = "tfstatestorage"
    container_name       = "tfstate"
    key                  = "production.terraform.tfstate"

    # State locking is automatic with Azure Blob
    use_azuread_auth = true
  }
}
```

**Azure Storage Setup**
```hcl
resource "azurerm_resource_group" "terraform_state" {
  name     = "terraform-state-rg"
  location = "East US"
}

resource "azurerm_storage_account" "terraform_state" {
  name                     = "tfstatestorage"
  resource_group_name      = azurerm_resource_group.terraform_state.name
  location                 = azurerm_resource_group.terraform_state.location
  account_tier             = "Standard"
  account_replication_type = "GRS"

  enable_https_traffic_only = true
  min_tls_version          = "TLS1_2"

  blob_properties {
    versioning_enabled = true
  }

  tags = {
    environment = "global"
    purpose     = "terraform-state"
  }
}

resource "azurerm_storage_container" "terraform_state" {
  name                  = "tfstate"
  storage_account_name  = azurerm_storage_account.terraform_state.name
  container_access_type = "private"
}
```

## Remote Backend - GCS (GCP)

```hcl
terraform {
  backend "gcs" {
    bucket = "my-terraform-state"
    prefix = "production/vpc"

    # State locking is automatic with GCS
  }
}
```

## Workspaces

**Using Workspaces**
```bash
# List workspaces
terraform workspace list

# Create new workspace
terraform workspace new staging

# Switch workspace
terraform workspace select production

# Show current workspace
terraform workspace show

# Delete workspace
terraform workspace delete dev
```

**Workspace-Aware Configuration**
```hcl
locals {
  environment = terraform.workspace

  # Environment-specific configuration
  vpc_cidr = {
    production = "10.0.0.0/16"
    staging    = "10.1.0.0/16"
    dev        = "10.2.0.0/16"
  }

  instance_count = {
    production = 5
    staging    = 2
    dev        = 1
  }
}

resource "aws_vpc" "main" {
  cidr_block = local.vpc_cidr[local.environment]

  tags = {
    Name        = "${local.environment}-vpc"
    Environment = local.environment
  }
}

resource "aws_instance" "app" {
  count = local.instance_count[local.environment]

  ami           = var.ami_id
  instance_type = "t3.micro"

  tags = {
    Name        = "${local.environment}-app-${count.index + 1}"
    Environment = local.environment
  }
}
```

## Partial Backend Configuration

**Backend template**
```hcl
# backend.tf
terraform {
  backend "s3" {
    # Configuration provided via backend config file or CLI
  }
}
```

**Environment-specific backend configs**
```hcl
# config/backend-prod.hcl
bucket         = "terraform-state-prod"
key            = "vpc/terraform.tfstate"
region         = "us-east-1"
encrypt        = true
dynamodb_table = "terraform-lock-prod"
```

```bash
# Initialize with backend config
terraform init -backend-config=config/backend-prod.hcl
```

## State Operations

**Import Existing Resources**
```bash
# Import AWS VPC
terraform import aws_vpc.main vpc-12345678

# Import with module
terraform import module.network.aws_vpc.main vpc-12345678
```

**State Manipulation**
```bash
# List resources in state
terraform state list

# Show resource details
terraform state show aws_vpc.main

# Move resource in state
terraform state mv aws_instance.old aws_instance.new

# Remove resource from state (doesn't destroy)
terraform state rm aws_instance.example

# Pull remote state to local file
terraform state pull > terraform.tfstate.backup

# Push local state to remote
terraform state push terraform.tfstate
```

**State Migration**
```bash
# Migrate from local to remote backend
terraform init -migrate-state

# Change backend configuration
terraform init -reconfigure

# Copy state to new backend
terraform init -backend-config=new-backend.hcl -migrate-state
```

## State Locking

**Manual Lock Management**
```bash
# Force unlock if lock is stuck (use carefully!)
terraform force-unlock LOCK_ID

# Example: terraform force-unlock a1b2c3d4-e5f6-7890-abcd-ef1234567890
```

**Prevent Concurrent Modifications**
```hcl
# State locking happens automatically with supported backends
# DynamoDB for S3, automatic for Azure Blob and GCS

# Disable locking for specific operations (not recommended)
terraform apply -lock=false  # DON'T DO THIS IN PRODUCTION
```

## State File Security

**Encryption at Rest**
```hcl
# S3 bucket encryption
resource "aws_s3_bucket_server_side_encryption_configuration" "state" {
  bucket = aws_s3_bucket.terraform_state.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = aws_kms_key.terraform.arn
    }
    bucket_key_enabled = true
  }
}
```

**Access Control**
```hcl
# S3 bucket policy - restrict access
resource "aws_s3_bucket_policy" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "RequireEncryptedTransport"
        Effect = "Deny"
        Principal = "*"
        Action = "s3:*"
        Resource = [
          aws_s3_bucket.terraform_state.arn,
          "${aws_s3_bucket.terraform_state.arn}/*"
        ]
        Condition = {
          Bool = {
            "aws:SecureTransport" = "false"
          }
        }
      }
    ]
  })
}
```

## State File Organization

```
# Recommended structure for multiple environments
terraform-state-bucket/
├── production/
│   ├── vpc/terraform.tfstate
│   ├── eks/terraform.tfstate
│   └── rds/terraform.tfstate
├── staging/
│   ├── vpc/terraform.tfstate
│   └── eks/terraform.tfstate
└── dev/
    └── vpc/terraform.tfstate
```

## Best Practices

- Always use remote state for teams
- Enable state locking to prevent conflicts
- Encrypt state files at rest and in transit
- Enable versioning for state file history
- Use separate state files per environment
- Restrict access to state buckets
- Back up state files regularly
- Never commit state files to git
- Use workspaces for similar environments only
- Document state migration procedures
