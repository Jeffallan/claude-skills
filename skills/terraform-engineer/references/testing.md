# Terraform Testing Strategies

## Terraform Plan Validation

**Basic Plan Workflow**
```bash
# Initialize and validate syntax
terraform init
terraform fmt -check
terraform validate

# Plan with output
terraform plan -out=tfplan

# Show plan in JSON for automated review
terraform show -json tfplan | jq .

# Apply specific plan
terraform apply tfplan
```

**Plan with Variable Files**
```bash
# Plan with specific tfvars
terraform plan -var-file="production.tfvars"

# Plan with inline variables
terraform plan -var="instance_count=5"

# Plan with multiple var files
terraform plan \
  -var-file="common.tfvars" \
  -var-file="production.tfvars"
```

**Plan Analysis**
```bash
# Resource targeting is for exceptional recovery only; it skips dependency
# checks and leaves the rest of the configuration unreviewed
terraform plan -target=aws_vpc.main

# Refresh only (check drift)
terraform plan -refresh-only

# Destroy plan
terraform plan -destroy

# Save plan output
terraform plan -out=tfplan 2>&1 | tee plan-output.txt
```

## Terraform Test (native)

`terraform test` is the default choice for module tests. Reach for Terratest only
when you must call cloud APIs to verify real infrastructure.

**Test File Structure**

Terraform discovers `.tftest.hcl` files only directly inside `tests/` (or the
directory passed to `-test-directory`); it does **not** recurse into subdirectories.
Encode the test type in the file name instead:

```
tests/
├── defaults_unit_test.tftest.hcl          # command = plan, fast, no resources
├── validation_unit_test.tftest.hcl        # command = plan
└── complete_integration_test.tftest.hcl   # command = apply, creates real resources
```

**Unit Test (plan mode)**
```hcl
# tests/defaults_unit_test.tftest.hcl
mock_provider "aws" {} # unit tests need no credentials

variables {
  name       = "test-vpc"
  cidr_block = "10.0.0.0/16"
}

run "creates_vpc_with_expected_cidr" {
  command = plan

  assert {
    condition     = aws_vpc.this.cidr_block == "10.0.0.0/16"
    error_message = "VPC CIDR block did not match expected value"
  }

  assert {
    condition     = aws_vpc.this.enable_dns_hostnames
    error_message = "DNS hostnames should be enabled by default"
  }
}

run "rejects_invalid_cidr" {
  command = plan

  variables {
    cidr_block = "not-a-cidr"
  }

  expect_failures = [var.cidr_block]
}
```

**Mock Provider (no credentials, no resources)**

`mock_provider` (Terraform 1.7+) lets plan- and apply-mode tests run without cloud
access; without it, even a `plan` run needs valid provider credentials. Override
computed values the module depends on, such as ARNs and IDs:

```hcl
# tests/mocked_unit_test.tftest.hcl
mock_provider "aws" {
  mock_resource "aws_vpc" {
    defaults = {
      id  = "vpc-12345678"
      arn = "arn:aws:ec2:us-east-1:123456789012:vpc/vpc-12345678"
    }
  }
}

run "exposes_vpc_id" {
  command = apply

  variables {
    name       = "mocked-vpc"
    cidr_block = "10.0.0.0/16"
  }

  assert {
    condition     = output.vpc_id == "vpc-12345678"
    error_message = "vpc_id output should come from the VPC resource"
  }
}
```

**Integration Test (apply mode)**
```hcl
# tests/complete_integration_test.tftest.hcl
run "create_full_stack" {
  command = apply

  variables {
    name       = "integration-test"
    cidr_block = "10.0.0.0/16"

    private_subnets = {
      app = { cidr_block = "10.0.1.0/24", az = "us-east-1a" }
    }
  }

  assert {
    condition     = length(aws_subnet.private) == 1
    error_message = "Should create exactly one private subnet"
  }

  assert {
    condition     = output.vpc_id != ""
    error_message = "VPC ID should not be empty"
  }
}
```

Resources created by `apply` runs are destroyed automatically in reverse run order
when the file finishes. Integration tests create real, billable resources, so run
them only with the user's approval and in a sandbox account.

**Run Tests**
```bash
terraform test                                       # every file in tests/
terraform test -filter=tests/defaults_unit_test.tftest.hcl  # one file (repeatable)
terraform test -test-directory=integration-tests     # custom test directory
terraform test -verbose                              # print plan/state per run block
terraform test -junit-xml=results.xml                # CI report
```

## Terratest (Go-based Testing)

**Test Structure**
```
tests/
├── go.mod
├── go.sum
└── vpc_test.go
```

**go.mod**
```go
module github.com/example/terraform-modules/tests

go 1.26.0

require (
    github.com/gruntwork-io/terratest v1.0.1
    github.com/stretchr/testify v1.11.1
)
```

**Basic Terratest**
```go
// tests/vpc_test.go
package test

import (
    "testing"

    "github.com/gruntwork-io/terratest/modules/terraform"
    "github.com/stretchr/testify/assert"
)

func TestVPCCreation(t *testing.T) {
    t.Parallel()

    terraformOptions := terraform.WithDefaultRetryableErrors(t, &terraform.Options{
        TerraformDir: "../examples/complete",

        Vars: map[string]interface{}{
            "name":       "test-vpc",
            "cidr_block": "10.0.0.0/16",
        },

        EnvVars: map[string]string{
            "AWS_DEFAULT_REGION": "us-east-1",
        },
    })

    defer terraform.Destroy(t, terraformOptions)

    terraform.InitAndApply(t, terraformOptions)

    vpcID := terraform.Output(t, terraformOptions, "vpc_id")
    assert.NotEmpty(t, vpcID)

    vpcCIDR := terraform.Output(t, terraformOptions, "vpc_cidr_block")
    assert.Equal(t, "10.0.0.0/16", vpcCIDR)
}
```

**Verifying Real Cloud State**

To assert against the live resource (for example, that a VPC really has flow logs),
call the cloud API from the test with AWS SDK for Go **v2**
(`github.com/aws/aws-sdk-go-v2`); v1 is end-of-support. Prefer a `terraform test`
`apply` run first and add Terratest only for checks that Terraform assertions
cannot express.

**Run Terratest**
```bash
cd tests
go mod download
go test -v -timeout 30m ./...
```

## Policy as Code - OPA/Conftest

Evaluate policies against the JSON plan so that they see the final configuration.
Rego v1 syntax (`contains`/`if`) is the default in OPA 1.0+.

**policy.rego**
```rego
package terraform.analysis

import rego.v1

# Deny created resources that support tags but have no Environment tag
deny contains msg if {
    some r in input.resource_changes
    "create" in r.change.actions
    is_object(r.change.after.tags_all)
    not r.change.after.tags_all.Environment
    msg := sprintf("Resource %s is missing the Environment tag", [r.address])
}

# Require a public access block for every created S3 bucket
deny contains msg if {
    some bucket in input.resource_changes
    bucket.type == "aws_s3_bucket"
    "create" in bucket.change.actions
    not has_public_access_block(bucket.change.after.bucket)
    msg := sprintf("S3 bucket %s needs an aws_s3_bucket_public_access_block", [bucket.address])
}

has_public_access_block(bucket_name) if {
    some r in input.resource_changes
    r.type == "aws_s3_bucket_public_access_block"
    r.change.after.bucket == bucket_name
}
```

Plan JSON does not contain values that are unknown until apply (generated IDs),
so match resources by configured attributes such as names. Matching on `id` or
other computed fields silently never fires.

**Run OPA Policy**
```bash
terraform plan -out=tfplan
terraform show -json tfplan > tfplan.json   # contains sensitive values; delete after use

opa check policy.rego                        # syntax check
opa eval -i tfplan.json -d policy.rego "data.terraform.analysis.deny"
```

**Conftest (OPA wrapper for CI)**
```bash
# Install: https://www.conftest.dev/install/
conftest test tfplan.json --policy policy.rego --namespace terraform.analysis
```

Use Sentinel instead when policies must run inside HCP Terraform / Terraform
Enterprise policy sets.

## Security Scanning

`tfsec` is deprecated and now maintained as part of Trivy. Use Trivy or Checkov:

```bash
trivy config .                  # misconfiguration scan of Terraform files
trivy config --severity HIGH,CRITICAL --exit-code 1 .
checkov -d . --framework terraform --quiet
```

## TFLint

**Installation and Configuration**
```bash
# Install: https://github.com/terraform-linters/tflint#installation
tflint --init     # downloads the plugins declared in .tflint.hcl
```

**.tflint.hcl**
```hcl
plugin "terraform" {
  enabled = true
  preset  = "recommended"
}

plugin "aws" {
  enabled = true
  version = "0.50.0"
  source  = "github.com/terraform-linters/tflint-ruleset-aws"
}

rule "terraform_naming_convention" {
  enabled = true
  format  = "snake_case"
}

rule "terraform_required_version" {
  enabled = true
}

rule "terraform_required_providers" {
  enabled = true
}
```

The `terraform` preset already enables the common rules; keep explicit `rule` blocks
only for the ones you configure. Provider rulesets (such as `aws`) detect invalid
instance types, deprecated instance generations and similar errors; see
`tflint --init` output and the ruleset docs for rule names, which change between
releases.

**Run TFLint**
```bash
# Run linter
tflint

# With specific config
tflint --config=.tflint.hcl

# Recursive (all subdirectories)
tflint --recursive

# Output format
tflint --format=json
```

## Pre-commit Hooks

**.pre-commit-config.yaml**
```yaml
repos:
  - repo: https://github.com/antonbabenko/pre-commit-terraform
    rev: v1.109.4
    hooks:
      - id: terraform_fmt
      - id: terraform_validate
      - id: terraform_tflint
        args:
          - --args=--config=__GIT_WORKING_DIR__/.tflint.hcl
      - id: terraform_docs
        args:
          - --hook-config=--path-to-file=README.md
          - --hook-config=--add-to-existing-file=true
      - id: terraform_trivy
        args:
          - --args=--severity=HIGH,CRITICAL
```

**Setup**
```bash
pip install pre-commit
pre-commit install
pre-commit run -a
```

## CI/CD Pipeline Testing

**GitHub Actions Example**

Pin third-party actions to a full commit SHA in production workflows; version tags
are shown here for readability.

```yaml
name: Terraform Test

on: [pull_request]

permissions:
  contents: read

jobs:
  terraform-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v7

      - uses: hashicorp/setup-terraform@v4
        with:
          terraform_version: "~> 1.14"

      - name: Terraform Format
        run: terraform fmt -check -recursive

      - name: Terraform Init
        run: terraform init -backend=false

      - name: Terraform Validate
        run: terraform validate

      - uses: terraform-linters/setup-tflint@v6

      - name: TFLint
        run: |
          tflint --init
          tflint --recursive
        env:
          GITHUB_TOKEN: ${{ github.token }}   # avoids plugin download rate limits

      - name: Terraform Test (plan-mode unit tests)
        run: |
          terraform test \
            -filter=tests/defaults_unit_test.tftest.hcl \
            -filter=tests/validation_unit_test.tftest.hcl

      - name: Trivy
        uses: aquasecurity/trivy-action@v0.36.0
        with:
          scan-type: config
          scan-ref: .
          severity: HIGH,CRITICAL
          exit-code: "1"
```

Run `*_unit_test` files on every pull request and `*_integration_test` files on
merge, since the latter create real resources.

## Best Practices

- Run `terraform validate` before every commit
- Use `terraform test` for unit (plan, mocked) and integration (apply) tests
- Implement policy as code for security compliance
- Run TFLint in CI/CD pipelines
- Use pre-commit hooks for automated checks
- Add Terratest only for checks `terraform test` cannot express
- Always review plan output before apply
- Test provider upgrades in isolated environments
- Document test scenarios and expected outcomes
- Automate testing in pull request workflows
