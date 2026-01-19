# Deployment and DevOps

> Reference for: Salesforce Developer
> Load when: Salesforce DX, CI/CD, scratch orgs, metadata API

---

## Salesforce DX Project Setup

### Project Structure

```
my-salesforce-project/
├── .forceignore              # Files to ignore in deployments
├── .gitignore                # Git ignore patterns
├── sfdx-project.json         # Project configuration
├── config/
│   └── project-scratch-def.json  # Scratch org definition
├── force-app/
│   └── main/
│       └── default/
│           ├── classes/      # Apex classes
│           ├── triggers/     # Apex triggers
│           ├── lwc/          # Lightning Web Components
│           ├── aura/         # Aura components
│           ├── objects/      # Custom objects
│           ├── layouts/      # Page layouts
│           ├── flows/        # Flows
│           ├── profiles/     # Profiles
│           ├── permissionsets/  # Permission sets
│           └── staticresources/ # Static resources
├── scripts/
│   └── apex/                 # Anonymous Apex scripts
├── data/                     # Sample data files
└── manifest/
    └── package.xml           # Deployment manifest
```

### sfdx-project.json

```json
{
  "packageDirectories": [
    {
      "path": "force-app",
      "default": true,
      "package": "MyPackage",
      "versionName": "ver 1.0",
      "versionNumber": "1.0.0.NEXT",
      "definitionFile": "config/project-scratch-def.json"
    },
    {
      "path": "unpackaged",
      "default": false
    }
  ],
  "name": "my-salesforce-project",
  "namespace": "",
  "sfdcLoginUrl": "https://login.salesforce.com",
  "sourceApiVersion": "59.0",
  "plugins": {
    "salesforcedx-templates": {
      "minApiVersion": "55.0"
    }
  }
}
```

### Scratch Org Definition

```json
{
  "orgName": "My Company Dev Org",
  "edition": "Developer",
  "features": [
    "EnableSetPasswordInApi",
    "Communities",
    "ServiceCloud",
    "SalesCloud",
    "MultiCurrency"
  ],
  "settings": {
    "lightningExperienceSettings": {
      "enableS1DesktopEnabled": true
    },
    "mobileSettings": {
      "enableS1EncryptedStoragePref2": false
    },
    "securitySettings": {
      "passwordPolicies": {
        "enableSetPasswordInApi": true
      }
    },
    "communitiesSettings": {
      "enableNetworksEnabled": true
    },
    "languageSettings": {
      "enableTranslationWorkbench": true
    }
  },
  "objectSettings": {
    "opportunity": {
      "sharingModel": "private"
    },
    "account": {
      "sharingModel": "readWrite"
    }
  }
}
```

### .forceignore

```
# Profiles (use Permission Sets instead)
**/profiles/**

# User-specific settings
**/settings/**

# Package installation
**/*-meta.xml.bak

# IDE files
.sfdx/
.sf/
.idea/
*.log

# OS files
.DS_Store
Thumbs.db

# Test data
**/test-data/**

# Ignore standard objects
**/objects/Account/fields/IsDeleted.field-meta.xml
**/objects/Account/fields/IsPersonAccount.field-meta.xml
```

---

## SF CLI Commands

### Authentication

```bash
# Login to Dev Hub (web browser)
sf org login web --set-default-dev-hub --alias mydevhub

# Login to production/sandbox
sf org login web --alias myprod --instance-url https://login.salesforce.com
sf org login web --alias mysandbox --instance-url https://test.salesforce.com

# Login with JWT (CI/CD)
sf org login jwt \
  --client-id YOUR_CONNECTED_APP_CLIENT_ID \
  --jwt-key-file server.key \
  --username admin@mycompany.com \
  --set-default-dev-hub \
  --alias mydevhub

# List authenticated orgs
sf org list

# Logout
sf org logout --target-org myalias
```

### Scratch Org Management

```bash
# Create scratch org (30-day expiration)
sf org create scratch \
  --definition-file config/project-scratch-def.json \
  --alias myscratch \
  --set-default \
  --duration-days 30

# Open scratch org in browser
sf org open --target-org myscratch

# Push source to scratch org
sf project deploy start --target-org myscratch

# Pull changes from scratch org
sf project retrieve start --target-org myscratch

# Delete scratch org
sf org delete scratch --target-org myscratch --no-prompt

# List scratch orgs
sf org list --all
```

### Source Deployment

```bash
# Deploy to target org
sf project deploy start --target-org myprod

# Deploy specific metadata
sf project deploy start \
  --target-org myprod \
  --source-dir force-app/main/default/classes

# Deploy with tests
sf project deploy start \
  --target-org myprod \
  --test-level RunLocalTests

# Deploy using manifest
sf project deploy start \
  --target-org myprod \
  --manifest manifest/package.xml

# Quick deploy (after validation)
sf project deploy quick --job-id 0Af...

# Check deploy status
sf project deploy report --job-id 0Af...

# Cancel deployment
sf project deploy cancel --job-id 0Af...
```

### Retrieve Metadata

```bash
# Retrieve all metadata
sf project retrieve start --target-org myprod

# Retrieve specific components
sf project retrieve start \
  --target-org myprod \
  --metadata ApexClass:AccountService

# Retrieve using package.xml
sf project retrieve start \
  --target-org myprod \
  --manifest manifest/package.xml

# Generate package.xml from org
sf project generate manifest \
  --from-org myprod \
  --output-dir manifest
```

### Running Tests

```bash
# Run all tests
sf apex run test --target-org myscratch --code-coverage --result-format human

# Run specific test classes
sf apex run test \
  --target-org myscratch \
  --class-names AccountServiceTest,ContactServiceTest \
  --code-coverage

# Run tests with output to file
sf apex run test \
  --target-org myscratch \
  --test-level RunLocalTests \
  --output-dir test-results \
  --wait 10

# Run async tests and check later
sf apex run test --target-org myscratch --synchronous false
sf apex get test --target-org myscratch --test-run-id 707...
```

### Data Operations

```bash
# Export data using SOQL
sf data query \
  --target-org myprod \
  --query "SELECT Id, Name FROM Account LIMIT 10" \
  --result-format csv \
  > accounts.csv

# Import data
sf data import tree \
  --target-org myscratch \
  --plan data/sample-data-plan.json

# Export data for reimport
sf data export tree \
  --target-org myprod \
  --query "SELECT Id, Name, (SELECT Id, Name FROM Contacts) FROM Account LIMIT 10" \
  --output-dir data

# Bulk upsert
sf data upsert bulk \
  --target-org myprod \
  --sobject Account \
  --file accounts.csv \
  --external-id External_Id__c
```

---

## Package.xml Manifest

### Complete Example

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>AccountService</members>
        <members>AccountTriggerHandler</members>
        <members>HttpCalloutService</members>
        <name>ApexClass</name>
    </types>
    <types>
        <members>AccountServiceTest</members>
        <name>ApexClass</name>
    </types>
    <types>
        <members>AccountTrigger</members>
        <name>ApexTrigger</name>
    </types>
    <types>
        <members>accountCard</members>
        <members>accountList</members>
        <name>LightningComponentBundle</name>
    </types>
    <types>
        <members>Account.External_System_Id__c</members>
        <members>Account.IsActive__c</members>
        <name>CustomField</name>
    </types>
    <types>
        <members>Integration_Log__c</members>
        <members>Account_Audit__c</members>
        <name>CustomObject</name>
    </types>
    <types>
        <members>Account_Manager</members>
        <members>Sales_Rep</members>
        <name>PermissionSet</name>
    </types>
    <types>
        <members>Order_Event__e</members>
        <name>PlatformEventChannel</name>
    </types>
    <types>
        <members>Account_Update_Flow</members>
        <name>Flow</name>
    </types>
    <types>
        <members>External_System</members>
        <name>NamedCredential</name>
    </types>
    <types>
        <members>CustomLabels</members>
        <name>CustomLabels</name>
    </types>
    <version>59.0</version>
</Package>
```

### Wildcard Retrieval

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>*</members>
        <name>ApexClass</name>
    </types>
    <types>
        <members>*</members>
        <name>ApexTrigger</name>
    </types>
    <types>
        <members>*</members>
        <name>LightningComponentBundle</name>
    </types>
    <types>
        <members>*</members>
        <name>CustomObject</name>
    </types>
    <types>
        <members>*</members>
        <name>Flow</name>
    </types>
    <version>59.0</version>
</Package>
```

---

## CI/CD Pipeline

### GitHub Actions Workflow

```yaml
# .github/workflows/salesforce-ci.yml
name: Salesforce CI/CD

on:
  push:
    branches: [main, develop]
    paths:
      - 'force-app/**'
      - 'manifest/**'
  pull_request:
    branches: [main, develop]

env:
  SFDX_CLI_URL: https://developer.salesforce.com/media/salesforce-cli/sf/channels/stable/sf-linux-x64.tar.xz

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Install Salesforce CLI
        run: |
          wget $SFDX_CLI_URL
          mkdir sfdx
          tar xJf sf-linux-x64.tar.xz -C sfdx --strip-components 1
          ./sfdx/bin/sf version

      - name: Authenticate to Dev Hub
        run: |
          echo "${{ secrets.SFDX_AUTH_URL }}" > auth.txt
          ./sfdx/bin/sf org login sfdx-url --sfdx-url-file auth.txt --alias devhub --set-default-dev-hub

      - name: Create Scratch Org
        run: |
          ./sfdx/bin/sf org create scratch \
            --definition-file config/project-scratch-def.json \
            --alias ci-scratch \
            --set-default \
            --duration-days 1

      - name: Push Source
        run: ./sfdx/bin/sf project deploy start --target-org ci-scratch

      - name: Run Apex Tests
        run: |
          ./sfdx/bin/sf apex run test \
            --target-org ci-scratch \
            --code-coverage \
            --result-format human \
            --wait 20 \
            --test-level RunLocalTests

      - name: Check Code Coverage
        run: |
          COVERAGE=$(./sfdx/bin/sf apex get test --target-org ci-scratch --code-coverage --json | jq '.result.summary.orgWideCoverage' | tr -d '"' | tr -d '%')
          echo "Code coverage: $COVERAGE%"
          if [ "$COVERAGE" -lt "75" ]; then
            echo "Code coverage is below 75%"
            exit 1
          fi

      - name: Delete Scratch Org
        if: always()
        run: ./sfdx/bin/sf org delete scratch --target-org ci-scratch --no-prompt

  deploy-staging:
    needs: validate
    if: github.ref == 'refs/heads/develop'
    runs-on: ubuntu-latest
    environment: staging
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Install Salesforce CLI
        run: |
          wget $SFDX_CLI_URL
          mkdir sfdx
          tar xJf sf-linux-x64.tar.xz -C sfdx --strip-components 1

      - name: Authenticate to Staging
        run: |
          echo "${{ secrets.STAGING_AUTH_URL }}" > auth.txt
          ./sfdx/bin/sf org login sfdx-url --sfdx-url-file auth.txt --alias staging

      - name: Deploy to Staging
        run: |
          ./sfdx/bin/sf project deploy start \
            --target-org staging \
            --test-level RunLocalTests \
            --wait 30

  deploy-production:
    needs: validate
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    environment: production
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Install Salesforce CLI
        run: |
          wget $SFDX_CLI_URL
          mkdir sfdx
          tar xJf sf-linux-x64.tar.xz -C sfdx --strip-components 1

      - name: Authenticate to Production
        run: |
          echo "${{ secrets.PROD_AUTH_URL }}" > auth.txt
          ./sfdx/bin/sf org login sfdx-url --sfdx-url-file auth.txt --alias prod

      - name: Validate Deployment
        run: |
          ./sfdx/bin/sf project deploy validate \
            --target-org prod \
            --test-level RunLocalTests \
            --wait 30

      - name: Quick Deploy
        run: |
          JOB_ID=$(./sfdx/bin/sf project deploy report --json | jq -r '.result.id')
          ./sfdx/bin/sf project deploy quick --job-id $JOB_ID --target-org prod
```

### GitLab CI Pipeline

```yaml
# .gitlab-ci.yml
stages:
  - validate
  - deploy

variables:
  SF_CLI_VERSION: "2.20.7"

.sf_base:
  image: salesforce/cli:${SF_CLI_VERSION}-full
  before_script:
    - sf --version

validate:
  extends: .sf_base
  stage: validate
  script:
    - echo $SFDX_AUTH_URL > auth.txt
    - sf org login sfdx-url --sfdx-url-file auth.txt --alias devhub --set-default-dev-hub
    - sf org create scratch --definition-file config/project-scratch-def.json --alias ci-scratch --set-default --duration-days 1
    - sf project deploy start --target-org ci-scratch
    - sf apex run test --target-org ci-scratch --code-coverage --result-format junit --output-dir test-results --wait 20
  after_script:
    - sf org delete scratch --target-org ci-scratch --no-prompt || true
  artifacts:
    reports:
      junit: test-results/*.xml
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"

deploy_staging:
  extends: .sf_base
  stage: deploy
  environment:
    name: staging
  script:
    - echo $STAGING_AUTH_URL > auth.txt
    - sf org login sfdx-url --sfdx-url-file auth.txt --alias staging
    - sf project deploy start --target-org staging --test-level RunLocalTests --wait 30
  rules:
    - if: $CI_COMMIT_BRANCH == "develop"

deploy_production:
  extends: .sf_base
  stage: deploy
  environment:
    name: production
  script:
    - echo $PROD_AUTH_URL > auth.txt
    - sf org login sfdx-url --sfdx-url-file auth.txt --alias prod
    - sf project deploy start --target-org prod --test-level RunLocalTests --wait 30
  rules:
    - if: $CI_COMMIT_BRANCH == "main"
  when: manual
```

---

## Deployment Scripts

### Pre-Deployment Validation

```bash
#!/bin/bash
# scripts/validate-deployment.sh

set -e

TARGET_ORG=${1:-"myscratch"}
TEST_LEVEL=${2:-"RunLocalTests"}

echo "=== Validating deployment to $TARGET_ORG ==="

# Check for uncommitted changes
if [[ $(git status --porcelain) ]]; then
    echo "Warning: Uncommitted changes detected"
fi

# Validate package.xml
if [ ! -f "manifest/package.xml" ]; then
    echo "Error: manifest/package.xml not found"
    exit 1
fi

# Run validation
echo "Starting validation deploy..."
sf project deploy validate \
    --target-org "$TARGET_ORG" \
    --manifest manifest/package.xml \
    --test-level "$TEST_LEVEL" \
    --wait 60

echo "=== Validation complete ==="
```

### Post-Deployment Script

```bash
#!/bin/bash
# scripts/post-deployment.sh

set -e

TARGET_ORG=${1:-"myprod"}

echo "=== Running post-deployment tasks ==="

# Run data migration scripts
echo "Running data migration..."
sf apex run \
    --target-org "$TARGET_ORG" \
    --file scripts/apex/data-migration.apex

# Assign permission sets
echo "Assigning permission sets..."
sf org assign permset \
    --target-org "$TARGET_ORG" \
    --name Sales_Manager \
    --on-behalf-of admin@company.com

# Clear cache
echo "Clearing org cache..."
sf apex run \
    --target-org "$TARGET_ORG" \
    --file scripts/apex/clear-cache.apex

echo "=== Post-deployment complete ==="
```

### Anonymous Apex for Deployment

```apex
// scripts/apex/data-migration.apex
// Run data migration after deployment

System.debug('Starting data migration...');

// Update existing records with new field values
List<Account> accounts = [
    SELECT Id, Legacy_Status__c
    FROM Account
    WHERE New_Status__c = null
    AND Legacy_Status__c != null
    LIMIT 10000
];

Map<String, String> statusMapping = new Map<String, String>{
    'A' => 'Active',
    'I' => 'Inactive',
    'P' => 'Pending'
};

for (Account acc : accounts) {
    acc.New_Status__c = statusMapping.get(acc.Legacy_Status__c);
}

if (!accounts.isEmpty()) {
    Database.update(accounts, false);
    System.debug('Updated ' + accounts.size() + ' accounts');
}

System.debug('Data migration complete');
```

---

## Metadata API Operations

### Programmatic Metadata Deployment

```apex
/**
 * Deploy metadata using Metadata API
 */
public class MetadataDeployer {

    public static Id deployZip(Blob zipFile, Boolean checkOnly) {
        Metadata.DeployContainer container = new Metadata.DeployContainer();

        // For zip deployment, use REST API instead
        HttpRequest req = new HttpRequest();
        req.setEndpoint(URL.getOrgDomainUrl().toExternalForm() +
            '/services/data/v59.0/metadata/deployRequest');
        req.setMethod('POST');
        req.setHeader('Authorization', 'Bearer ' + UserInfo.getSessionId());
        req.setHeader('Content-Type', 'application/zip');
        req.setBodyAsBlob(zipFile);

        Http http = new Http();
        HttpResponse res = http.send(req);

        if (res.getStatusCode() == 200) {
            Map<String, Object> result = (Map<String, Object>)JSON.deserializeUntyped(res.getBody());
            return (Id)result.get('id');
        }

        throw new MetadataException('Deployment failed: ' + res.getBody());
    }

    /**
     * Check deployment status
     */
    public static Metadata.DeployResult checkDeployStatus(Id deployId) {
        HttpRequest req = new HttpRequest();
        req.setEndpoint(URL.getOrgDomainUrl().toExternalForm() +
            '/services/data/v59.0/metadata/deployRequest/' + deployId + '?includeDetails=true');
        req.setMethod('GET');
        req.setHeader('Authorization', 'Bearer ' + UserInfo.getSessionId());

        Http http = new Http();
        HttpResponse res = http.send(req);

        // Parse response...
        return null;
    }

    public class MetadataException extends Exception {}
}
```

### Creating Metadata Programmatically

```apex
/**
 * Create custom field using Metadata API
 */
public class MetadataFieldCreator implements Metadata.DeployCallback {

    public void createCustomField(
        String objectName,
        String fieldName,
        String fieldLabel,
        String fieldType
    ) {
        Metadata.CustomField customField = new Metadata.CustomField();
        customField.fullName = objectName + '.' + fieldName;
        customField.label = fieldLabel;
        customField.type_x = Metadata.FieldType.valueOf(fieldType);

        if (fieldType == 'Text') {
            customField.length = 255;
        }

        Metadata.DeployContainer container = new Metadata.DeployContainer();
        container.addMetadata(customField);

        Id jobId = Metadata.Operations.enqueueDeployment(container, this);
        System.debug('Deployment job ID: ' + jobId);
    }

    public void handleResult(
        Metadata.DeployResult result,
        Metadata.DeployCallbackContext context
    ) {
        if (result.status == Metadata.DeployStatus.Succeeded) {
            System.debug('Deployment succeeded');
        } else {
            System.debug('Deployment failed: ' + result.errorMessage);
        }
    }
}
```

---

## Environment Management

### Sandbox Refresh Scripts

```bash
#!/bin/bash
# scripts/post-sandbox-refresh.sh

# Run after sandbox refresh to configure environment

TARGET_ORG=${1:-"sandbox"}

echo "=== Post-Sandbox Refresh Configuration ==="

# 1. Update custom settings
sf apex run --target-org "$TARGET_ORG" << 'EOF'
// Update environment-specific settings
Integration_Settings__c settings = Integration_Settings__c.getOrgDefaults();
settings.Endpoint_URL__c = 'https://sandbox-api.external-system.com';
settings.Environment__c = 'Sandbox';
upsert settings;
System.debug('Settings updated');
EOF

# 2. Deactivate production workflows
sf apex run --target-org "$TARGET_ORG" << 'EOF'
// Deactivate production-only processes
List<ProcessDefinition> processes = [
    SELECT Id, Name
    FROM ProcessDefinition
    WHERE Name LIKE 'PROD_%'
];
System.debug('Found ' + processes.size() + ' production processes to review');
// Note: ProcessDefinition activation must be done via Setup or Metadata API
EOF

# 3. Mask sensitive data
sf apex run --target-org "$TARGET_ORG" << 'EOF'
// Mask email addresses
List<Contact> contacts = [SELECT Id, Email FROM Contact WHERE Email != null LIMIT 10000];
for (Contact c : contacts) {
    c.Email = c.Id + '@sandbox.invalid';
}
update contacts;
System.debug('Masked ' + contacts.size() + ' contact emails');
EOF

echo "=== Post-refresh configuration complete ==="
```

---

## When to Use

- **Scratch orgs**: Development and testing of new features
- **Sandboxes**: Integration testing, UAT, training
- **Package.xml**: Selective metadata deployment
- **CI/CD pipelines**: Automated testing and deployment
- **Metadata API**: Programmatic org configuration

## When NOT to Use

- **Scratch orgs for production data**: Use sandboxes for data-dependent testing
- **Manual deployments in production**: Always use CI/CD for audit trail
- **Wildcard package.xml in production**: Explicitly list components
- **Deployment without tests**: Always run tests in production deployments
- **Direct changes in production**: Always deploy through version control
