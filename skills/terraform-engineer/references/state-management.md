# Terraform State Management

## Remote Backend - S3 (AWS)

**Backend Configuration**
```hcl
# backend.tf
terraform {
  backend "s3" {
    bucket       = "my-terraform-state"
    key          = "production/vpc/terraform.tfstate"
    region       = "us-east-1"
    encrypt      = true
    use_lockfile = true # native S3 locking, Terraform 1.11+
  }
}
```

`use_lockfile` writes a `<key>.tflock` object next to the state, so the identity
running Terraform needs `s3:GetObject`, `s3:PutObject` and `s3:DeleteObject` on it.
The `dynamodb_table` argument is deprecated. When migrating an existing backend,
set `use_lockfile = true`, run `terraform init -reconfigure`, then remove
`dynamodb_table` and the DynamoDB table. Enable bucket versioning (below) for state
history; it is configured on the bucket, not in the backend block.

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
```

## Remote Backend - Azure Blob

```hcl
terraform {
  backend "azurerm" {
    resource_group_name  = "terraform-state-rg"
    storage_account_name = "tfstatestorage"
    container_name       = "tfstate"
    key                  = "production.terraform.tfstate"

    # State locking is automatic (blob lease); authenticate with Entra ID
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

  https_traffic_only_enabled = true
  min_tls_version            = "TLS1_2"

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
  storage_account_id    = azurerm_storage_account.terraform_state.id
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
bucket       = "terraform-state-prod"
key          = "vpc/terraform.tfstate"
region       = "us-east-1"
encrypt      = true
use_lockfile = true
```

```bash
# Initialize with backend config
terraform init -backend-config=config/backend-prod.hcl
```

## State Operations

Prefer declarative blocks over state-mutating CLI commands: they are reviewed in
`terraform plan`, live in version control, and work the same in every workspace and
in HCP Terraform runs.

**Import Existing Resources (`import` block, Terraform 1.5+)**
```hcl
import {
  to = aws_vpc.main
  id = "vpc-12345678"
}

# Inside a module, address the resource within the module
import {
  to = module.network.aws_vpc.main
  id = "vpc-12345678"
}
```

```bash
# Draft the matching resource configuration (writes a new file, not state)
terraform plan -generate-config-out=generated.tf   # experimental; review the output
```

Review the generated code and move it into your own files. Remove the `import`
block after the apply that imports the resource. To discover many existing
resources at once, use `terraform query` with `list` blocks (Terraform 1.14+).

**Rename or Move Resources (`moved` block, Terraform 1.1+)**
```hcl
moved {
  from = aws_instance.old
  to   = aws_instance.new
}
```

**Stop Managing a Resource Without Destroying It (`removed` block, Terraform 1.7+)**
```hcl
removed {
  from = aws_instance.example

  lifecycle {
    destroy = false
  }
}
```

**Inspect State (read-only)**
```bash
terraform state list
terraform state show aws_vpc.main
```

**State Surgery (last resort, requires explicit user approval)**

Only when no declarative block can express the change, for example repairing
corrupt state. Back up first and never print the output; state contains secrets
in plaintext.
```bash
terraform state pull > terraform.tfstate.backup   # keep out of version control
terraform state mv aws_instance.old aws_instance.new
terraform state rm aws_instance.example
terraform state push terraform.tfstate            # overwrites remote state
```

**State Migration**
```bash
# Migrate from local to remote backend, or between backends
terraform init -migrate-state

# Accept a changed backend configuration without migrating state
terraform init -reconfigure

# Move state to a new backend described by a config file
terraform init -backend-config=new-backend.hcl -migrate-state
```

## State Locking

**Manual Lock Management (requires explicit user approval)**
```bash
# Only after confirming that no other run holds the lock
terraform force-unlock LOCK_ID

# Example: terraform force-unlock a1b2c3d4-e5f6-7890-abcd-ef1234567890
```

**Prevent Concurrent Modifications**

State locking happens automatically on supported backends: native lock file for S3
(`use_lockfile`), blob leases for Azure and lock objects for GCS. Never bypass it
with `-lock=false` in production; a stuck lock should be investigated, not skipped.

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
        Sid       = "RequireEncryptedTransport"
        Effect    = "Deny"
        Principal = "*"
        Action    = "s3:*"
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
