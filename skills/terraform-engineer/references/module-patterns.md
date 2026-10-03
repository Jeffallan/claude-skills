# Terraform Module Patterns

## Module Structure

```
terraform-aws-vpc/
├── main.tf           # Primary resource definitions
├── variables.tf      # Input variable declarations
├── outputs.tf        # Output value definitions
├── versions.tf       # Provider version constraints
├── README.md         # Module documentation
├── examples/
│   └── complete/
│       ├── main.tf
│       └── variables.tf
└── tests/
    └── vpc_test.go
```

## Basic Module Pattern

**main.tf**
```hcl
resource "aws_vpc" "this" {
  cidr_block           = var.cidr_block
  enable_dns_hostnames = var.enable_dns_hostnames
  enable_dns_support   = var.enable_dns_support

  tags = merge(
    var.tags,
    {
      Name = var.name
    }
  )
}

resource "aws_subnet" "private" {
  for_each = var.private_subnets

  vpc_id            = aws_vpc.this.id
  cidr_block        = each.value.cidr_block
  availability_zone = each.value.az

  tags = merge(
    var.tags,
    {
      Name = "${var.name}-private-${each.key}"
      Type = "private"
    }
  )
}
```

**variables.tf**
```hcl
variable "name" {
  description = "Name prefix for all resources"
  type        = string

  validation {
    condition     = length(var.name) > 0 && length(var.name) <= 32
    error_message = "Name must be 1-32 characters"
  }
}

variable "cidr_block" {
  description = "CIDR block for VPC"
  type        = string

  validation {
    condition     = can(cidrhost(var.cidr_block, 0))
    error_message = "Must be valid IPv4 CIDR block"
  }
}

variable "private_subnets" {
  description = "Map of private subnet configurations"
  type = map(object({
    cidr_block = string
    az         = string
  }))
  default = {}
}

variable "tags" {
  description = "Common tags for all resources"
  type        = map(string)
  default     = {}
}

variable "enable_dns_hostnames" {
  description = "Enable DNS hostnames in VPC"
  type        = bool
  default     = true
}

variable "enable_dns_support" {
  description = "Enable DNS support in VPC"
  type        = bool
  default     = true
}
```

**outputs.tf**
```hcl
output "vpc_id" {
  description = "ID of the VPC"
  value       = aws_vpc.this.id
}

output "vpc_cidr_block" {
  description = "CIDR block of the VPC"
  value       = aws_vpc.this.cidr_block
}

output "private_subnet_ids" {
  description = "IDs of private subnets"
  value       = { for k, v in aws_subnet.private : k => v.id }
}

output "private_subnet_cidrs" {
  description = "CIDR blocks of private subnets"
  value       = { for k, v in aws_subnet.private : k => v.cidr_block }
}
```

**versions.tf**
```hcl
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

## Module Composition

```hcl
# Composite module using child modules
module "networking" {
  source = "./modules/vpc"

  name       = "production"
  cidr_block = "10.0.0.0/16"

  private_subnets = {
    app1 = { cidr_block = "10.0.1.0/24", az = "us-east-1a" }
    app2 = { cidr_block = "10.0.2.0/24", az = "us-east-1b" }
  }

  tags = local.common_tags
}

module "security" {
  source = "./modules/security-groups"

  vpc_id = module.networking.vpc_id

  security_groups = {
    web = {
      ingress = [
        { from_port = 443, to_port = 443, protocol = "tcp", cidr_blocks = ["0.0.0.0/0"] }
      ]
    }
  }
}
```

## Dynamic Blocks

```hcl
resource "aws_security_group" "this" {
  name   = var.name
  vpc_id = var.vpc_id

  dynamic "ingress" {
    for_each = var.ingress_rules
    content {
      from_port   = ingress.value.from_port
      to_port     = ingress.value.to_port
      protocol    = ingress.value.protocol
      cidr_blocks = ingress.value.cidr_blocks
      description = ingress.value.description
    }
  }

  dynamic "egress" {
    for_each = var.egress_rules
    content {
      from_port   = egress.value.from_port
      to_port     = egress.value.to_port
      protocol    = egress.value.protocol
      cidr_blocks = egress.value.cidr_blocks
      description = egress.value.description
    }
  }
}
```

## Conditional Resources

```hcl
# Create NAT gateway only if enabled
resource "aws_nat_gateway" "this" {
  count = var.enable_nat_gateway ? 1 : 0

  allocation_id = aws_eip.nat[0].id
  subnet_id     = aws_subnet.public[0].id

  tags = {
    Name = "${var.name}-nat"
  }

  depends_on = [aws_internet_gateway.this]
}

# Use for_each for multiple optional resources
resource "aws_route53_zone" "private" {
  for_each = var.create_private_zone ? { main = var.domain_name } : {}

  name = each.value

  vpc {
    vpc_id = aws_vpc.this.id
  }
}
```

## Module Versioning

```hcl
# Pin to specific version
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "5.1.2"

  # ... configuration
}

# Use version constraints
module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 19.0"  # >= 19.0, < 20.0

  # ... configuration
}

# Reference Git tags
module "custom" {
  source = "git::https://github.com/org/terraform-modules.git//vpc?ref=v1.2.3"

  # ... configuration
}
```

## Module Testing Example

```hcl
# examples/complete/main.tf
module "vpc_test" {
  source = "../.."

  name       = "test-vpc"
  cidr_block = "10.100.0.0/16"

  private_subnets = {
    app = { cidr_block = "10.100.1.0/24", az = "us-east-1a" }
  }

  tags = {
    Environment = "test"
    ManagedBy   = "terraform"
  }
}

output "vpc_id" {
  value = module.vpc_test.vpc_id
}
```

## Best Practices

- Keep modules focused and single-purpose
- Use `for_each` over `count` for resources
- Validate all inputs with validation blocks
- Document all variables and outputs
- Use semantic versioning (MAJOR.MINOR.PATCH)
- Provide complete examples
- Test modules before publishing
- Use consistent naming conventions
- Tag all taggable resources
- Avoid hardcoded values
