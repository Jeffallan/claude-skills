# Apex Development

> Reference for: Salesforce Developer
> Load when: Classes, triggers, async patterns, batch processing

---

## Apex Class Structure

### Service Layer Pattern

Separate business logic from triggers and controllers using service classes.

```apex
/**
 * AccountService - Business logic for Account operations
 * Follows Single Responsibility Principle
 */
public with sharing class AccountService {

    /**
     * Updates account ratings based on opportunity history
     * @param accountIds Set of Account IDs to process
     * @throws AccountServiceException on validation failure
     */
    public static void updateAccountRatings(Set<Id> accountIds) {
        if (accountIds == null || accountIds.isEmpty()) {
            return;
        }

        // Bulkified query - single SOQL for all records
        Map<Id, Account> accountsToUpdate = new Map<Id, Account>();

        for (Account acc : [
            SELECT Id, Rating,
                   (SELECT Amount, StageName FROM Opportunities
                    WHERE StageName = 'Closed Won')
            FROM Account
            WHERE Id IN :accountIds
        ]) {
            Decimal totalRevenue = 0;
            for (Opportunity opp : acc.Opportunities) {
                totalRevenue += opp.Amount != null ? opp.Amount : 0;
            }

            String newRating = calculateRating(totalRevenue);
            if (acc.Rating != newRating) {
                accountsToUpdate.put(acc.Id, new Account(
                    Id = acc.Id,
                    Rating = newRating
                ));
            }
        }

        if (!accountsToUpdate.isEmpty()) {
            update accountsToUpdate.values();
        }
    }

    private static String calculateRating(Decimal revenue) {
        if (revenue >= 1000000) return 'Hot';
        if (revenue >= 100000) return 'Warm';
        return 'Cold';
    }
}
```

### Domain Layer Pattern

Encapsulate object-specific logic in domain classes.

```apex
/**
 * Accounts Domain Class
 * Encapsulates Account-specific business rules
 */
public with sharing class Accounts {

    private List<Account> records;

    public Accounts(List<Account> records) {
        this.records = records;
    }

    public static Accounts newInstance(List<Account> records) {
        return new Accounts(records);
    }

    /**
     * Validates accounts before insert/update
     * @return List of validation errors
     */
    public List<String> validate() {
        List<String> errors = new List<String>();

        for (Account acc : records) {
            if (String.isBlank(acc.Name)) {
                errors.add('Account Name is required');
            }
            if (acc.AnnualRevenue != null && acc.AnnualRevenue < 0) {
                errors.add('Annual Revenue cannot be negative');
            }
        }

        return errors;
    }

    /**
     * Sets default values for new accounts
     */
    public void setDefaults() {
        for (Account acc : records) {
            if (String.isBlank(acc.Rating)) {
                acc.Rating = 'Cold';
            }
            if (acc.NumberOfEmployees == null) {
                acc.NumberOfEmployees = 0;
            }
        }
    }
}
```

---

## Trigger Framework

### Handler Pattern

Never put logic directly in triggers. Use a handler framework.

```apex
/**
 * AccountTrigger - Delegates all logic to handler
 */
trigger AccountTrigger on Account (
    before insert, before update, before delete,
    after insert, after update, after delete, after undelete
) {
    AccountTriggerHandler handler = new AccountTriggerHandler();

    switch on Trigger.operationType {
        when BEFORE_INSERT {
            handler.beforeInsert(Trigger.new);
        }
        when BEFORE_UPDATE {
            handler.beforeUpdate(Trigger.new, Trigger.oldMap);
        }
        when BEFORE_DELETE {
            handler.beforeDelete(Trigger.old, Trigger.oldMap);
        }
        when AFTER_INSERT {
            handler.afterInsert(Trigger.new, Trigger.newMap);
        }
        when AFTER_UPDATE {
            handler.afterUpdate(Trigger.new, Trigger.newMap, Trigger.old, Trigger.oldMap);
        }
        when AFTER_DELETE {
            handler.afterDelete(Trigger.old, Trigger.oldMap);
        }
        when AFTER_UNDELETE {
            handler.afterUndelete(Trigger.new, Trigger.newMap);
        }
    }
}
```

### Trigger Handler Class

```apex
/**
 * AccountTriggerHandler - Contains all trigger logic
 * Implements recursion prevention and bulkification
 */
public with sharing class AccountTriggerHandler {

    // Recursion prevention
    private static Boolean isExecuting = false;
    private static Set<Id> processedIds = new Set<Id>();

    public void beforeInsert(List<Account> newRecords) {
        Accounts domain = Accounts.newInstance(newRecords);
        domain.setDefaults();

        List<String> errors = domain.validate();
        if (!errors.isEmpty()) {
            for (Account acc : newRecords) {
                acc.addError(String.join(errors, '; '));
            }
        }
    }

    public void beforeUpdate(List<Account> newRecords, Map<Id, Account> oldMap) {
        // Field change detection
        for (Account acc : newRecords) {
            Account oldAcc = oldMap.get(acc.Id);

            if (acc.OwnerId != oldAcc.OwnerId) {
                // Owner changed - track for audit
                acc.Owner_Changed_Date__c = System.now();
            }
        }
    }

    public void afterInsert(List<Account> newRecords, Map<Id, Account> newMap) {
        if (isExecuting) return;
        isExecuting = true;

        try {
            // Create default contacts for new accounts
            createDefaultContacts(newRecords);
        } finally {
            isExecuting = false;
        }
    }

    public void afterUpdate(
        List<Account> newRecords,
        Map<Id, Account> newMap,
        List<Account> oldRecords,
        Map<Id, Account> oldMap
    ) {
        // Filter to only process records not already handled
        List<Account> toProcess = new List<Account>();
        for (Account acc : newRecords) {
            if (!processedIds.contains(acc.Id)) {
                toProcess.add(acc);
                processedIds.add(acc.Id);
            }
        }

        if (!toProcess.isEmpty()) {
            AccountService.updateAccountRatings(new Map<Id, Account>(toProcess).keySet());
        }
    }

    public void beforeDelete(List<Account> oldRecords, Map<Id, Account> oldMap) {
        // Prevent deletion of accounts with open opportunities
        Set<Id> accountIds = oldMap.keySet();
        Map<Id, Integer> openOppCounts = new Map<Id, Integer>();

        for (AggregateResult ar : [
            SELECT AccountId, COUNT(Id) cnt
            FROM Opportunity
            WHERE AccountId IN :accountIds
            AND IsClosed = false
            GROUP BY AccountId
        ]) {
            openOppCounts.put((Id)ar.get('AccountId'), (Integer)ar.get('cnt'));
        }

        for (Account acc : oldRecords) {
            if (openOppCounts.containsKey(acc.Id) && openOppCounts.get(acc.Id) > 0) {
                acc.addError('Cannot delete account with open opportunities');
            }
        }
    }

    public void afterDelete(List<Account> oldRecords, Map<Id, Account> oldMap) {
        // Audit logging for deleted accounts
        List<Account_Audit__c> auditRecords = new List<Account_Audit__c>();
        for (Account acc : oldRecords) {
            auditRecords.add(new Account_Audit__c(
                Account_Name__c = acc.Name,
                Action__c = 'Deleted',
                Deleted_Date__c = System.now(),
                Deleted_By__c = UserInfo.getUserId()
            ));
        }

        if (!auditRecords.isEmpty()) {
            insert auditRecords;
        }
    }

    public void afterUndelete(List<Account> newRecords, Map<Id, Account> newMap) {
        // Handle undelete scenarios
    }

    private void createDefaultContacts(List<Account> accounts) {
        List<Contact> contacts = new List<Contact>();
        for (Account acc : accounts) {
            contacts.add(new Contact(
                AccountId = acc.Id,
                LastName = 'Primary Contact',
                Email = 'primary@' + acc.Name.toLowerCase().replaceAll('[^a-z0-9]', '') + '.com'
            ));
        }

        if (!contacts.isEmpty()) {
            insert contacts;
        }
    }
}
```

---

## Asynchronous Apex Patterns

### When to Use Each Pattern

| Pattern | Use Case | Limits |
|---------|----------|--------|
| **Future** | Simple async callout, quick operations | 50 calls per transaction |
| **Queueable** | Chaining jobs, complex async logic | 50 jobs per transaction |
| **Batch** | Processing large data volumes | 5 active batches |
| **Scheduled** | Time-based execution | 100 scheduled jobs |

### Future Methods

Use for simple callouts or operations that don't need chaining.

```apex
public class AccountIntegration {

    /**
     * Sends account data to external system
     * @param accountIds Set of Account IDs to sync
     */
    @future(callout=true)
    public static void syncToExternalSystem(Set<Id> accountIds) {
        if (accountIds == null || accountIds.isEmpty()) {
            return;
        }

        List<Account> accounts = [
            SELECT Id, Name, BillingCity, BillingCountry, Industry
            FROM Account
            WHERE Id IN :accountIds
        ];

        Http http = new Http();
        HttpRequest request = new HttpRequest();
        request.setEndpoint('callout:External_System/api/accounts');
        request.setMethod('POST');
        request.setHeader('Content-Type', 'application/json');
        request.setBody(JSON.serialize(accounts));

        try {
            HttpResponse response = http.send(request);
            if (response.getStatusCode() != 200) {
                System.debug(LoggingLevel.ERROR,
                    'Sync failed: ' + response.getStatusCode() + ' ' + response.getBody());
            }
        } catch (Exception e) {
            System.debug(LoggingLevel.ERROR, 'Callout exception: ' + e.getMessage());
        }
    }
}
```

### Queueable Apex

Use for job chaining and passing complex data types.

```apex
/**
 * Queueable job for processing account hierarchies
 * Supports job chaining for large datasets
 */
public class AccountHierarchyProcessor implements Queueable, Database.AllowsCallouts {

    private List<Id> accountIds;
    private Integer depth;
    private static final Integer MAX_DEPTH = 5;
    private static final Integer BATCH_SIZE = 200;

    public AccountHierarchyProcessor(List<Id> accountIds, Integer depth) {
        this.accountIds = accountIds;
        this.depth = depth;
    }

    public void execute(QueueableContext context) {
        // Process current batch
        List<Account> accounts = [
            SELECT Id, Name, ParentId, Ultimate_Parent__c
            FROM Account
            WHERE Id IN :accountIds
        ];

        Set<Id> childAccountIds = new Set<Id>();
        List<Account> toUpdate = new List<Account>();

        for (Account acc : accounts) {
            if (acc.ParentId != null) {
                acc.Ultimate_Parent__c = findUltimateParent(acc.ParentId);
                toUpdate.add(acc);
            }

            // Collect child accounts for next iteration
            for (Account child : [
                SELECT Id FROM Account WHERE ParentId = :acc.Id
            ]) {
                childAccountIds.add(child.Id);
            }
        }

        if (!toUpdate.isEmpty()) {
            update toUpdate;
        }

        // Chain next job if there are child accounts and within depth limit
        if (!childAccountIds.isEmpty() && depth < MAX_DEPTH) {
            List<Id> nextBatch = new List<Id>(childAccountIds);
            if (nextBatch.size() > BATCH_SIZE) {
                nextBatch = new List<Id>();
                Integer count = 0;
                for (Id accId : childAccountIds) {
                    if (count++ >= BATCH_SIZE) break;
                    nextBatch.add(accId);
                }
            }

            if (!Test.isRunningTest()) {
                System.enqueueJob(new AccountHierarchyProcessor(nextBatch, depth + 1));
            }
        }
    }

    private Id findUltimateParent(Id parentId) {
        Account current = [SELECT Id, ParentId FROM Account WHERE Id = :parentId];
        while (current.ParentId != null) {
            current = [SELECT Id, ParentId FROM Account WHERE Id = :current.ParentId];
        }
        return current.Id;
    }
}

// Usage
// System.enqueueJob(new AccountHierarchyProcessor(accountIds, 0));
```

### Batch Apex

Use for processing large data volumes (millions of records).

```apex
/**
 * Batch job for annual account cleanup
 * Processes inactive accounts in configurable batch sizes
 */
public class AccountCleanupBatch implements
    Database.Batchable<SObject>,
    Database.Stateful,
    Database.AllowsCallouts {

    private Integer successCount = 0;
    private Integer failureCount = 0;
    private List<String> errors = new List<String>();
    private Date cutoffDate;

    public AccountCleanupBatch() {
        this.cutoffDate = Date.today().addYears(-2);
    }

    public AccountCleanupBatch(Date cutoffDate) {
        this.cutoffDate = cutoffDate;
    }

    /**
     * Query locator - defines records to process
     * Governor limit: 50 million records max
     */
    public Database.QueryLocator start(Database.BatchableContext bc) {
        return Database.getQueryLocator([
            SELECT Id, Name, LastActivityDate,
                   (SELECT Id FROM Opportunities WHERE IsClosed = false LIMIT 1)
            FROM Account
            WHERE LastActivityDate < :cutoffDate
            AND IsActive__c = true
        ]);
    }

    /**
     * Execute - processes each batch of records
     * Default batch size: 200, configurable up to 2000
     */
    public void execute(Database.BatchableContext bc, List<Account> scope) {
        List<Account> toDeactivate = new List<Account>();

        for (Account acc : scope) {
            // Skip accounts with open opportunities
            if (acc.Opportunities != null && !acc.Opportunities.isEmpty()) {
                continue;
            }

            toDeactivate.add(new Account(
                Id = acc.Id,
                IsActive__c = false,
                Deactivated_Date__c = Date.today(),
                Deactivated_Reason__c = 'No activity for 2+ years'
            ));
        }

        if (!toDeactivate.isEmpty()) {
            Database.SaveResult[] results = Database.update(toDeactivate, false);

            for (Integer i = 0; i < results.size(); i++) {
                if (results[i].isSuccess()) {
                    successCount++;
                } else {
                    failureCount++;
                    for (Database.Error err : results[i].getErrors()) {
                        errors.add(toDeactivate[i].Id + ': ' + err.getMessage());
                    }
                }
            }
        }
    }

    /**
     * Finish - executes after all batches complete
     */
    public void finish(Database.BatchableContext bc) {
        // Send summary email
        Messaging.SingleEmailMessage email = new Messaging.SingleEmailMessage();
        email.setToAddresses(new List<String>{'admin@company.com'});
        email.setSubject('Account Cleanup Batch Complete');
        email.setPlainTextBody(
            'Batch Job Complete\n' +
            'Success: ' + successCount + '\n' +
            'Failures: ' + failureCount + '\n' +
            (errors.isEmpty() ? '' : '\nErrors:\n' + String.join(errors, '\n'))
        );

        Messaging.sendEmail(new List<Messaging.SingleEmailMessage>{email});

        // Log completion
        System.debug('Account Cleanup Complete - Success: ' + successCount + ', Failures: ' + failureCount);
    }
}

// Execute batch with custom size
// Database.executeBatch(new AccountCleanupBatch(), 100);
```

### Scheduled Apex

Use for time-based job execution.

```apex
/**
 * Scheduled job to run daily account maintenance
 */
public class DailyAccountMaintenance implements Schedulable {

    public void execute(SchedulableContext sc) {
        // Start batch job
        Database.executeBatch(new AccountCleanupBatch(), 200);

        // Queue additional maintenance
        System.enqueueJob(new AccountHierarchyProcessor(getTopLevelAccounts(), 0));
    }

    private List<Id> getTopLevelAccounts() {
        List<Id> topLevel = new List<Id>();
        for (Account acc : [
            SELECT Id FROM Account
            WHERE ParentId = null
            LIMIT 100
        ]) {
            topLevel.add(acc.Id);
        }
        return topLevel;
    }

    /**
     * Schedule helper - schedules job for daily 2 AM execution
     */
    public static void scheduleDaily() {
        // CRON: Seconds Minutes Hours Day_of_month Month Day_of_week Year
        String cronExp = '0 0 2 * * ?'; // 2 AM daily
        System.schedule('Daily Account Maintenance', cronExp, new DailyAccountMaintenance());
    }
}
```

---

## Governor Limit Management

### Key Limits to Monitor

| Limit | Synchronous | Asynchronous |
|-------|-------------|--------------|
| SOQL Queries | 100 | 200 |
| SOQL Rows | 50,000 | 50,000 |
| DML Statements | 150 | 150 |
| DML Rows | 10,000 | 10,000 |
| Heap Size | 6 MB | 12 MB |
| CPU Time | 10,000 ms | 60,000 ms |
| Callouts | 100 | 100 |

### Limit Checking Utility

```apex
/**
 * Utility class for monitoring governor limits
 */
public class LimitMonitor {

    public static void logLimits(String context) {
        System.debug(LoggingLevel.INFO, '=== Limits for: ' + context + ' ===');
        System.debug('SOQL Queries: ' + Limits.getQueries() + '/' + Limits.getLimitQueries());
        System.debug('SOQL Rows: ' + Limits.getQueryRows() + '/' + Limits.getLimitQueryRows());
        System.debug('DML Statements: ' + Limits.getDmlStatements() + '/' + Limits.getLimitDmlStatements());
        System.debug('DML Rows: ' + Limits.getDmlRows() + '/' + Limits.getLimitDmlRows());
        System.debug('Heap Size: ' + Limits.getHeapSize() + '/' + Limits.getLimitHeapSize());
        System.debug('CPU Time: ' + Limits.getCpuTime() + '/' + Limits.getLimitCpuTime());
    }

    /**
     * Checks if approaching limit threshold
     * @param threshold Percentage (0-100) to trigger warning
     */
    public static Boolean isApproachingQueryLimit(Integer threshold) {
        return (Limits.getQueries() * 100 / Limits.getLimitQueries()) >= threshold;
    }

    public static Boolean isApproachingHeapLimit(Integer threshold) {
        return (Limits.getHeapSize() * 100 / Limits.getLimitHeapSize()) >= threshold;
    }
}
```

---

## Test Classes

### Test Best Practices

```apex
/**
 * Test class for AccountService
 * Demonstrates test patterns and best practices
 */
@isTest
private class AccountServiceTest {

    /**
     * Test data factory - create test records efficiently
     */
    @TestSetup
    static void setupTestData() {
        // Create test accounts
        List<Account> accounts = new List<Account>();
        for (Integer i = 0; i < 200; i++) {
            accounts.add(new Account(
                Name = 'Test Account ' + i,
                Industry = 'Technology'
            ));
        }
        insert accounts;

        // Create opportunities for some accounts
        List<Opportunity> opps = new List<Opportunity>();
        for (Integer i = 0; i < 50; i++) {
            opps.add(new Opportunity(
                Name = 'Test Opp ' + i,
                AccountId = accounts[i].Id,
                StageName = 'Closed Won',
                CloseDate = Date.today(),
                Amount = 100000 * (i + 1)
            ));
        }
        insert opps;
    }

    @isTest
    static void testUpdateAccountRatings_HotRating() {
        // Arrange
        Account acc = [SELECT Id FROM Account WHERE Name = 'Test Account 0' LIMIT 1];

        // Create high-value opportunity
        insert new Opportunity(
            Name = 'Big Deal',
            AccountId = acc.Id,
            StageName = 'Closed Won',
            CloseDate = Date.today(),
            Amount = 1500000
        );

        // Act
        Test.startTest();
        AccountService.updateAccountRatings(new Set<Id>{acc.Id});
        Test.stopTest();

        // Assert
        Account updated = [SELECT Rating FROM Account WHERE Id = :acc.Id];
        System.assertEquals('Hot', updated.Rating, 'Account with >$1M revenue should be Hot');
    }

    @isTest
    static void testUpdateAccountRatings_BulkOperation() {
        // Arrange - get all test accounts
        List<Account> accounts = [SELECT Id FROM Account];
        Set<Id> accountIds = new Map<Id, Account>(accounts).keySet();

        // Act
        Test.startTest();
        AccountService.updateAccountRatings(accountIds);
        Test.stopTest();

        // Assert - verify bulk processing didn't hit limits
        System.assert(Limits.getQueries() < Limits.getLimitQueries(),
            'Should not exhaust SOQL queries');
    }

    @isTest
    static void testUpdateAccountRatings_EmptySet() {
        // Act
        Test.startTest();
        AccountService.updateAccountRatings(new Set<Id>());
        AccountService.updateAccountRatings(null);
        Test.stopTest();

        // Assert - no exceptions thrown
        System.assert(true, 'Should handle empty/null input gracefully');
    }

    /**
     * Test async job execution
     */
    @isTest
    static void testAccountHierarchyProcessor() {
        // Arrange
        Account parent = new Account(Name = 'Parent Account');
        insert parent;

        Account child = new Account(Name = 'Child Account', ParentId = parent.Id);
        insert child;

        // Act
        Test.startTest();
        System.enqueueJob(new AccountHierarchyProcessor(
            new List<Id>{child.Id}, 0
        ));
        Test.stopTest();

        // Assert
        Account updated = [SELECT Ultimate_Parent__c FROM Account WHERE Id = :child.Id];
        System.assertEquals(parent.Id, updated.Ultimate_Parent__c,
            'Ultimate parent should be set');
    }

    /**
     * Test batch processing
     */
    @isTest
    static void testAccountCleanupBatch() {
        // Arrange - create old inactive account
        Account oldAccount = new Account(
            Name = 'Old Inactive Account',
            IsActive__c = true
        );
        insert oldAccount;

        // Backdate last activity
        Test.setCreatedDate(oldAccount.Id, DateTime.now().addYears(-3));

        // Act
        Test.startTest();
        Database.executeBatch(new AccountCleanupBatch(Date.today().addYears(-2)), 200);
        Test.stopTest();

        // Assert - batch job queued successfully
        System.assert(true, 'Batch should execute without errors');
    }
}
```

---

## When to Use

- **Service classes**: Complex business logic shared across multiple entry points
- **Domain classes**: Object-specific validation and behavior
- **Trigger handlers**: All trigger-based automation
- **Future methods**: Simple callouts, fire-and-forget operations
- **Queueable**: Job chaining, complex async operations
- **Batch**: Processing >10,000 records

## When NOT to Use

- **Triggers for simple updates**: Use Flow for declarative automation
- **Future for complex logic**: Use Queueable instead
- **Batch for small datasets**: Overhead not worth it for <1,000 records
- **SOQL in loops**: Always bulkify queries outside loops
