---
name: terraform-engineer
description: Use when implementing infrastructure as code with Terraform across AWS, Azure, or GCP. Invoke for module development (create reusable modules, manage module versioning), state management (migrate backends, import existing resources, resolve state conflicts), provider configuration, multi-environment workflows, and infrastructure testing.
license: MIT
metadata:
  author: https://github.com/Jeffallan
  company: https://synergetic.solutions
  version: "1.2.0"
  domain: infrastructure
  triggers: Terraform, infrastructure as code, IaC, terraform module, terraform state, AWS provider, Azure provider, GCP provider, terraform plan, terraform apply, terraform test
  role: specialist
  scope: implementation
  output-format: code
  related-skills: cloud-architect, devops-engineer, kubernetes-specialist
---

# Terraform Engineer

Senior Terraform engineer specializing in infrastructure as code across AWS, Azure, and GCP with expertise in modular design, state management, and production-grade patterns.

## Core Workflow

1. **Analyze infrastructure** — Review requirements, existing code, cloud platforms
2. **Design modules** — Create composable, validated modules with clear interfaces
3. **Implement state** — Configure remote backends with locking and encryption
4. **Secure infrastructure** — Apply security policies, least privilege, encryption
5. **Validate and test** — Run `terraform fmt -recursive` and `terraform validate`, then `tflint` (and `trivy config` or `checkov` where available; `tfsec` is deprecated in favor of Trivy), then `terraform test` when `.tftest.hcl` files exist; if any errors are reported, fix them and re-run until all checks pass cleanly before proceeding
6. **Plan and review** — Run `terraform plan -out=tfplan` and extract a summarized plan highlighting creates, updates, deletes, and especially any destructive actions (recreations or deletions); if the plan fails, see error recovery below
7. **Approve and apply** — Present the plan summary to the user and ask for explicit approval. Only execute `terraform apply tfplan` after receiving confirmation. Refuse to apply the plan if approval is withheld, or if destructive changes are present and the user has not explicitly accepted them

### Error Recovery

**Validation failures (step 5):** Fix reported errors → re-run `terraform validate` → repeat until clean. For `tflint` warnings, address rule violations before proceeding.

**Plan failures (step 6):**
- *State drift* — Run `terraform apply -refresh-only` to review and reconcile state with real resources (`terraform refresh` is deprecated). Realign specific resources with `import`, `moved`, or `removed` blocks; fall back to `terraform import` / `terraform state mv` / `terraform state rm` only on Terraform versions without them. Then re-plan.
- *Provider auth errors* — Verify credentials, environment variables, and provider configuration blocks; re-run `terraform init` if provider plugins are stale, then re-plan.
- *Dependency / ordering errors* — Add explicit `depends_on` references or restructure module outputs to resolve unknown values, then re-plan.

Any command that writes state (`apply -refresh-only`, `import`, `state mv`, `state rm`) needs explicit user approval first. State holds sensitive values in plaintext, so never print it to logs or chat.

After any fix, return to step 5 to re-validate before re-running the plan.

## Reference Guide

Load detailed guidance based on context:

| Topic | Reference | Load When |
|-------|-----------|-----------|
| Modules | `references/module-patterns.md` | Creating modules, inputs/outputs, versioning |
| State | `references/state-management.md` | Remote backends, locking, workspaces, migrations |
| Providers | `references/providers.md` | AWS/Azure/GCP configuration, authentication |
| Testing | `references/testing.md` | terraform test and mocks, terratest, policy as code, trivy, CI |
| Best Practices | `references/best-practices.md` | DRY patterns, naming, security, cost tracking |

## Constraints

### MUST DO
- Use semantic versioning, pin provider versions to the latest major, and commit `.terraform.lock.hcl`
- Enable remote state with locking and encryption
- Validate inputs with validation blocks; give every variable a `type` and `description` and every output a `description`
- Mark sensitive variables and outputs `sensitive = true`; keep secrets out of state with native secrets-manager integration first, then `ephemeral` resources with write-only (`*_wo`) attributes (Terraform 1.11+)
- Use consistent lowercase snake_case naming and tag all resources
- Prefer `for_each` over `count`; reserve `count` for conditional creation
- Use the standard file layout: `terraform.tf`, `providers.tf`, `main.tf`, `variables.tf`, `locals.tf`, `outputs.tf`
- Document module interfaces
- Run `terraform fmt -recursive` and `terraform validate`

### MUST NOT DO
- Store secrets in plain text or hardcode environment-specific values
- Use local state for production or skip state locking
- Mix provider versions without constraints
- Create circular module dependencies or skip input validation
- Commit `.terraform` directories, state files, plan files, or `.tfvars` files containing secrets
- Use deprecated constructs (`terraform refresh`, `dynamodb_table` state locking, `tfsec`, inline security-group rules, Helm 2.x `set {}` blocks) in new code

## Code Examples

### Minimal Module Structure

**`main.tf`**
```hcl
resource "aws_s3_bucket" "this" {
  bucket = var.bucket_name
  tags   = var.tags
}
```

**`variables.tf`**
```hcl
variable "bucket_name" {
  description = "Name of the S3 bucket"
  type        = string

  validation {
    condition     = length(var.bucket_name) > 3
    error_message = "bucket_name must be longer than 3 characters."
  }
}

variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default     = {}
}
```

**`outputs.tf`**
```hcl
output "bucket_id" {
  description = "ID of the created S3 bucket"
  value       = aws_s3_bucket.this.id
}
```

### Remote Backend Configuration (S3 native locking)

Requires Terraform 1.11+. `dynamodb_table` locking is deprecated. The lock file (`<key>.tflock`) needs `s3:GetObject`, `s3:PutObject`, and `s3:DeleteObject`.

```hcl
terraform {
  backend "s3" {
    bucket       = "my-tf-state"
    key          = "env/prod/terraform.tfstate"
    region       = "us-east-1"
    encrypt      = true
    use_lockfile = true
  }
}
```

### Provider Version Pinning

```hcl
terraform {
  required_version = ">= 1.14"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 5.0"
    }
  }
}
```

### Declarative State Refactoring

```hcl
moved {
  from = aws_s3_bucket.logs
  to   = module.logging.aws_s3_bucket.this
}

import {
  to = aws_s3_bucket.existing
  id = "my-existing-bucket"
}
```

### Native Test (`bucket_unit_test.tftest.hcl`)

```hcl
run "rejects_short_bucket_name" {
  command = plan

  variables {
    bucket_name = "abc"
  }

  expect_failures = [var.bucket_name]
}
```

## Output Format

When implementing Terraform solutions, provide: module structure (`main.tf`, `variables.tf`, `outputs.tf`), backend and provider configuration, example usage with tfvars, `terraform test` files, and a brief explanation of design decisions.

Maintained by [@jeffallan](https://github.com/jeffallan), Principal Consultant at [Synergetic Solutions](https://synergetic.solutions)

[Documentation](https://jeffallan.github.io/claude-skills/skills/infrastructure/terraform-engineer/)
