# Terraform Provider Configuration

## AWS Provider

**Basic Configuration**
```hcl
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Environment = var.environment
      ManagedBy   = "Terraform"
      Project     = var.project_name
    }
  }
}
```

**Multiple AWS Accounts/Regions**
```hcl
provider "aws" {
  alias  = "primary"
  region = "us-east-1"

  assume_role {
    role_arn     = "arn:aws:iam::123456789012:role/TerraformRole"
    session_name = "terraform-session"
  }
}

provider "aws" {
  alias  = "secondary"
  region = "us-west-2"

  assume_role {
    role_arn = "arn:aws:iam::987654321098:role/TerraformRole"
  }
}

# Use aliased provider
resource "aws_vpc" "primary" {
  provider   = aws.primary
  cidr_block = "10.0.0.0/16"
}

resource "aws_vpc" "secondary" {
  provider   = aws.secondary
  cidr_block = "10.1.0.0/16"
}
```

**AWS Authentication Methods**
```hcl
# Method 1: Environment variables (recommended for CI/CD)
# AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_SESSION_TOKEN

# Method 2: Shared credentials file
provider "aws" {
  region                   = "us-east-1"
  shared_credentials_files = ["~/.aws/credentials"]
  profile                  = "production"
}

# Method 3: IAM role (recommended for EC2/ECS)
provider "aws" {
  region = "us-east-1"
  # Automatically uses instance profile
}

# Method 4: Assume role
provider "aws" {
  region = "us-east-1"

  assume_role {
    role_arn     = var.terraform_role_arn
    session_name = "terraform-${var.environment}"
    external_id  = var.external_id
  }
}
```

**AWS Provider Features**
```hcl
provider "aws" {
  region = "us-east-1"

  # Default tags applied to all resources
  default_tags {
    tags = {
      Environment = "production"
      ManagedBy   = "Terraform"
      CostCenter  = "engineering"
    }
  }

  # Ignore specific tags (useful for auto-scaling)
  ignore_tags {
    keys = ["aws:autoscaling:groupName"]
  }

  # Custom endpoint for localstack/testing
  endpoints {
    s3  = "http://localhost:4566"
    ec2 = "http://localhost:4566"
  }

  # Rate limiting
  max_retries = 3

  # HTTP proxy
  http_proxy = "http://proxy.example.com:8080"
}
```

## Azure Provider (azurerm)

**Basic Configuration**
```hcl
terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
  }
}

provider "azurerm" {
  features {
    resource_group {
      prevent_deletion_if_contains_resources = true
    }

    key_vault {
      purge_soft_delete_on_destroy    = false
      recover_soft_deleted_key_vaults = true
    }

    virtual_machine {
      delete_os_disk_on_deletion     = true
      graceful_shutdown              = false
      skip_shutdown_and_force_delete = false
    }
  }

  subscription_id = var.subscription_id
  tenant_id       = var.tenant_id
}
```

**Multiple Azure Subscriptions**
```hcl
provider "azurerm" {
  alias           = "production"
  subscription_id = var.prod_subscription_id
  tenant_id       = var.tenant_id

  features {}
}

provider "azurerm" {
  alias           = "development"
  subscription_id = var.dev_subscription_id
  tenant_id       = var.tenant_id

  features {}
}

resource "azurerm_resource_group" "prod" {
  provider = azurerm.production
  name     = "prod-rg"
  location = "East US"
}
```

**Azure Authentication Methods**
```hcl
# Method 1: Service Principal with Client Secret
provider "azurerm" {
  features {}

  subscription_id = var.subscription_id
  tenant_id       = var.tenant_id
  client_id       = var.client_id
  client_secret   = var.client_secret
}

# Method 2: Service Principal with Certificate
provider "azurerm" {
  features {}

  subscription_id             = var.subscription_id
  tenant_id                   = var.tenant_id
  client_id                   = var.client_id
  client_certificate_path     = var.client_certificate_path
  client_certificate_password = var.client_certificate_password
}

# Method 3: Managed Identity (for Azure VMs)
provider "azurerm" {
  features {}

  use_msi         = true
  subscription_id = var.subscription_id
  tenant_id       = var.tenant_id
}

# Method 4: Azure CLI (local development)
provider "azurerm" {
  features {}

  use_cli = true
}
```

## GCP Provider

**Basic Configuration**
```hcl
terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
  zone    = var.zone

  default_labels = {
    environment = var.environment
    managed_by  = "terraform"
  }
}
```

**Multiple GCP Projects**
```hcl
provider "google" {
  alias   = "production"
  project = var.prod_project_id
  region  = "us-central1"
}

provider "google" {
  alias   = "development"
  project = var.dev_project_id
  region  = "us-central1"
}

resource "google_compute_network" "prod" {
  provider = google.production
  name     = "prod-vpc"
}
```

**GCP Authentication Methods**
```hcl
# Method 1: Service Account Key (not recommended for production)
provider "google" {
  credentials = file("service-account-key.json")
  project     = var.project_id
  region      = var.region
}

# Method 2: Application Default Credentials (recommended)
provider "google" {
  # Uses GOOGLE_APPLICATION_CREDENTIALS env var
  project = var.project_id
  region  = var.region
}

# Method 3: Impersonate Service Account
provider "google" {
  project = var.project_id
  region  = var.region

  impersonate_service_account = "terraform@project-id.iam.gserviceaccount.com"
  scopes = [
    "https://www.googleapis.com/auth/cloud-platform",
    "https://www.googleapis.com/auth/userinfo.email"
  ]
}

# Method 4: Workload Identity (for GKE)
provider "google" {
  project = var.project_id
  region  = var.region
  # Automatically uses workload identity
}
```

**GCP Beta Resources**
```hcl
terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
    google-beta = {
      source  = "hashicorp/google-beta"
      version = "~> 5.0"
    }
  }
}

provider "google-beta" {
  project = var.project_id
  region  = var.region
}

# Use beta provider for features not in stable
resource "google_compute_security_policy" "policy" {
  provider = google-beta
  name     = "my-policy"

  # Beta-only features here
}
```

## Kubernetes Provider

**With AWS EKS**
```hcl
data "aws_eks_cluster" "cluster" {
  name = module.eks.cluster_name
}

data "aws_eks_cluster_auth" "cluster" {
  name = module.eks.cluster_name
}

provider "kubernetes" {
  host                   = data.aws_eks_cluster.cluster.endpoint
  cluster_ca_certificate = base64decode(data.aws_eks_cluster.cluster.certificate_authority[0].data)
  token                  = data.aws_eks_cluster_auth.cluster.token
}
```

**With GKE**
```hcl
data "google_client_config" "default" {}

data "google_container_cluster" "cluster" {
  name     = var.cluster_name
  location = var.region
}

provider "kubernetes" {
  host  = "https://${data.google_container_cluster.cluster.endpoint}"
  token = data.google_client_config.default.access_token
  cluster_ca_certificate = base64decode(
    data.google_container_cluster.cluster.master_auth[0].cluster_ca_certificate
  )
}
```

## Helm Provider

```hcl
provider "helm" {
  kubernetes {
    host                   = data.aws_eks_cluster.cluster.endpoint
    cluster_ca_certificate = base64decode(data.aws_eks_cluster.cluster.certificate_authority[0].data)
    token                  = data.aws_eks_cluster_auth.cluster.token
  }
}

resource "helm_release" "nginx" {
  name       = "nginx-ingress"
  repository = "https://kubernetes.github.io/ingress-nginx"
  chart      = "ingress-nginx"
  version    = "4.8.0"

  values = [
    file("${path.module}/values.yaml")
  ]

  set {
    name  = "controller.service.type"
    value = "LoadBalancer"
  }
}
```

## Provider Version Constraints

```hcl
terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"  # >= 5.0.0, < 6.0.0
    }

    azurerm = {
      source  = "hashicorp/azurerm"
      version = ">= 3.0.0, < 4.0.0"
    }

    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }

    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.23"
    }

    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.11"
    }

    random = {
      source  = "hashicorp/random"
      version = "~> 3.5"
    }
  }
}
```

## Best Practices

- Always pin provider versions with constraints
- Use provider aliases for multi-region/account setups
- Leverage default tags for consistent resource tagging
- Use environment variables for credentials (CI/CD)
- Use IAM roles/managed identities when possible
- Never hardcode credentials in code
- Use separate providers for different environments
- Document provider requirements in README
- Test provider upgrades in non-production first
- Use official providers from HashiCorp registry
