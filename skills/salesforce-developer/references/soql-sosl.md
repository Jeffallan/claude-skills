# SOQL and SOSL

> Reference for: Salesforce Developer
> Load when: Query optimization, relationships, governor limits

---

## SOQL Fundamentals

### Basic Query Structure

```sql
SELECT Id, Name, Industry, AnnualRevenue
FROM Account
WHERE Industry = 'Technology'
AND AnnualRevenue > 1000000
ORDER BY AnnualRevenue DESC NULLS LAST
LIMIT 100
OFFSET 0
```

### Governor Limits

| Limit | Synchronous | Asynchronous |
|-------|-------------|--------------|
| Total SOQL queries | 100 | 200 |
| Total records retrieved | 50,000 | 50,000 |
| Query rows in aggregate | 50,000 | 50,000 |
| SOSL queries | 20 | 20 |

---

## Query Optimization

### Selective Queries

Queries must be selective to avoid full table scans. A query is selective when it uses indexed fields that filter to less than 10% of records (or 333,333 records for large objects).

**Standard Indexed Fields:**
- Id
- Name
- OwnerId
- CreatedDate
- SystemModstamp
- RecordTypeId
- External ID fields
- Lookup/Master-Detail fields

```apex
// GOOD - Uses indexed field (Id)
List<Account> accounts = [
    SELECT Id, Name
    FROM Account
    WHERE Id IN :accountIds
];

// GOOD - Uses indexed field (OwnerId)
List<Account> accounts = [
    SELECT Id, Name
    FROM Account
    WHERE OwnerId = :UserInfo.getUserId()
];

// BAD - Non-indexed field with leading wildcard
List<Account> accounts = [
    SELECT Id, Name
    FROM Account
    WHERE Name LIKE '%Corp'
];

// BETTER - Trailing wildcard is acceptable
List<Account> accounts = [
    SELECT Id, Name
    FROM Account
    WHERE Name LIKE 'Acme%'
];
```

### Bulkification Patterns

```apex
// BAD - SOQL inside loop (will hit governor limits)
for (Contact c : contacts) {
    Account acc = [SELECT Id, Name FROM Account WHERE Id = :c.AccountId];
    // Process account
}

// GOOD - Bulkified query
Set<Id> accountIds = new Set<Id>();
for (Contact c : contacts) {
    accountIds.add(c.AccountId);
}

Map<Id, Account> accountMap = new Map<Id, Account>([
    SELECT Id, Name
    FROM Account
    WHERE Id IN :accountIds
]);

for (Contact c : contacts) {
    Account acc = accountMap.get(c.AccountId);
    // Process account
}
```

### Query Plan Analysis

Use the Query Plan tool in Developer Console to analyze query performance.

```apex
// Check if query is selective
String query = 'SELECT Id FROM Account WHERE Industry = \'Technology\'';

// In Developer Console: Query Editor > Query Plan
// Look for:
// - Cost < 1 (selective)
// - Leading operation type (Index vs TableScan)
// - Cardinality (estimated rows)
```

---

## Relationship Queries

### Parent-to-Child (Subquery)

Query child records from parent object.

```apex
// Query Accounts with their Contacts
List<Account> accounts = [
    SELECT Id, Name,
           (SELECT Id, FirstName, LastName, Email
            FROM Contacts
            WHERE IsActive__c = true
            ORDER BY LastName
            LIMIT 100)
    FROM Account
    WHERE Industry = 'Technology'
];

// Access child records
for (Account acc : accounts) {
    System.debug('Account: ' + acc.Name);
    for (Contact c : acc.Contacts) {
        System.debug('  Contact: ' + c.FirstName + ' ' + c.LastName);
    }
}
```

### Child-to-Parent (Dot Notation)

Query parent fields from child object.

```apex
// Query Contacts with Account information
List<Contact> contacts = [
    SELECT Id, FirstName, LastName,
           Account.Name,
           Account.Industry,
           Account.Owner.Name,
           Account.Parent.Name
    FROM Contact
    WHERE Account.Industry = 'Technology'
];

// Access parent fields
for (Contact c : contacts) {
    System.debug('Contact: ' + c.FirstName + ' ' + c.LastName);
    System.debug('  Account: ' + c.Account.Name);
    System.debug('  Owner: ' + c.Account.Owner.Name);
}
```

### Multi-Level Relationships

```apex
// Up to 5 levels of parent relationships
// Up to 1 level of child relationship per query

// Complex relationship query
List<Contact> contacts = [
    SELECT Id, Name,
           Account.Name,
           Account.Parent.Name,
           Account.Parent.Parent.Name,
           Account.Owner.Profile.Name,
           (SELECT Id, Subject FROM Tasks WHERE IsClosed = false LIMIT 5)
    FROM Contact
    WHERE Account.Industry = 'Technology'
    AND Account.Parent.AnnualRevenue > 1000000
];
```

### Polymorphic Relationships

Handle fields that can reference multiple object types (e.g., WhoId, WhatId).

```apex
// Query Tasks with polymorphic WhoId
List<Task> tasks = [
    SELECT Id, Subject,
           Who.Type,
           Who.Name,
           TYPEOF Who
               WHEN Contact THEN FirstName, LastName, Account.Name
               WHEN Lead THEN FirstName, LastName, Company
           END
    FROM Task
    WHERE CreatedDate = TODAY
];

for (Task t : tasks) {
    if (t.Who instanceof Contact) {
        Contact c = (Contact)t.Who;
        System.debug('Contact: ' + c.FirstName + ' ' + c.LastName);
    } else if (t.Who instanceof Lead) {
        Lead l = (Lead)t.Who;
        System.debug('Lead: ' + l.FirstName + ' ' + l.LastName);
    }
}
```

---

## Aggregate Queries

### COUNT, SUM, AVG, MIN, MAX

```apex
// Simple count
Integer accountCount = [SELECT COUNT() FROM Account WHERE Industry = 'Technology'];

// Aggregate functions with GROUP BY
List<AggregateResult> results = [
    SELECT Industry,
           COUNT(Id) recordCount,
           SUM(AnnualRevenue) totalRevenue,
           AVG(AnnualRevenue) avgRevenue,
           MIN(AnnualRevenue) minRevenue,
           MAX(AnnualRevenue) maxRevenue
    FROM Account
    WHERE AnnualRevenue != null
    GROUP BY Industry
    HAVING COUNT(Id) > 5
    ORDER BY SUM(AnnualRevenue) DESC
];

for (AggregateResult ar : results) {
    String industry = (String)ar.get('Industry');
    Integer count = (Integer)ar.get('recordCount');
    Decimal totalRevenue = (Decimal)ar.get('totalRevenue');

    System.debug(industry + ': ' + count + ' accounts, $' + totalRevenue);
}
```

### GROUP BY with ROLLUP and CUBE

```apex
// GROUP BY ROLLUP - hierarchical subtotals
List<AggregateResult> results = [
    SELECT Industry, Type,
           COUNT(Id) cnt,
           SUM(AnnualRevenue) revenue
    FROM Account
    GROUP BY ROLLUP(Industry, Type)
];

// GROUP BY CUBE - all combinations
List<AggregateResult> results = [
    SELECT Industry, Rating,
           COUNT(Id) cnt
    FROM Account
    GROUP BY CUBE(Industry, Rating)
];
```

### COUNT_DISTINCT

```apex
// Count unique values
List<AggregateResult> results = [
    SELECT COUNT_DISTINCT(Industry) uniqueIndustries,
           COUNT_DISTINCT(OwnerId) uniqueOwners
    FROM Account
];
```

---

## Dynamic SOQL

### Building Queries Dynamically

```apex
public class DynamicQueryBuilder {

    public static List<SObject> search(
        String objectName,
        List<String> fields,
        Map<String, Object> filters,
        String orderBy,
        Integer limitCount
    ) {
        // Build SELECT clause
        String query = 'SELECT ' + String.join(fields, ', ');
        query += ' FROM ' + String.escapeSingleQuotes(objectName);

        // Build WHERE clause
        List<String> conditions = new List<String>();
        for (String field : filters.keySet()) {
            Object value = filters.get(field);

            if (value instanceof String) {
                conditions.add(field + ' = \'' + String.escapeSingleQuotes((String)value) + '\'');
            } else if (value instanceof Set<Id>) {
                conditions.add(field + ' IN :filterIds');
            } else if (value instanceof Date) {
                conditions.add(field + ' = ' + ((Date)value).format());
            } else if (value != null) {
                conditions.add(field + ' = ' + value);
            }
        }

        if (!conditions.isEmpty()) {
            query += ' WHERE ' + String.join(conditions, ' AND ');
        }

        // Add ORDER BY
        if (String.isNotBlank(orderBy)) {
            query += ' ORDER BY ' + String.escapeSingleQuotes(orderBy);
        }

        // Add LIMIT
        if (limitCount != null && limitCount > 0) {
            query += ' LIMIT ' + limitCount;
        }

        System.debug('Dynamic Query: ' + query);

        // Execute query
        return Database.query(query);
    }
}

// Usage
Map<String, Object> filters = new Map<String, Object>{
    'Industry' => 'Technology',
    'AnnualRevenue' => 1000000
};

List<Account> accounts = (List<Account>)DynamicQueryBuilder.search(
    'Account',
    new List<String>{'Id', 'Name', 'Industry'},
    filters,
    'Name ASC',
    100
);
```

### Security with Dynamic SOQL

```apex
public with sharing class SecureDynamicQuery {

    public static List<SObject> queryWithFLS(
        String objectName,
        List<String> fields,
        String whereClause
    ) {
        // Check object accessibility
        Schema.DescribeSObjectResult objDescribe =
            Schema.getGlobalDescribe().get(objectName).getDescribe();

        if (!objDescribe.isAccessible()) {
            throw new SecurityException('No access to object: ' + objectName);
        }

        // Filter to accessible fields only
        Map<String, Schema.SObjectField> fieldMap = objDescribe.fields.getMap();
        List<String> accessibleFields = new List<String>();

        for (String field : fields) {
            Schema.SObjectField fieldToken = fieldMap.get(field);
            if (fieldToken != null && fieldToken.getDescribe().isAccessible()) {
                accessibleFields.add(field);
            }
        }

        if (accessibleFields.isEmpty()) {
            throw new SecurityException('No accessible fields');
        }

        String query = 'SELECT ' + String.join(accessibleFields, ', ');
        query += ' FROM ' + String.escapeSingleQuotes(objectName);

        if (String.isNotBlank(whereClause)) {
            query += ' WHERE ' + whereClause;
        }

        // WITH SECURITY_ENFORCED ensures FLS/CRUD
        query += ' WITH SECURITY_ENFORCED';

        return Database.query(query);
    }
}
```

---

## SOSL (Salesforce Object Search Language)

### Basic SOSL Syntax

```apex
// Search across multiple objects
List<List<SObject>> searchResults = [
    FIND 'Acme*' IN ALL FIELDS
    RETURNING
        Account(Id, Name, Industry WHERE Industry = 'Technology'),
        Contact(Id, FirstName, LastName, Email),
        Opportunity(Id, Name, Amount)
    LIMIT 100
];

List<Account> accounts = (List<Account>)searchResults[0];
List<Contact> contacts = (List<Contact>)searchResults[1];
List<Opportunity> opportunities = (List<Opportunity>)searchResults[2];
```

### Search Scope Options

```apex
// ALL FIELDS - Search all searchable text fields
FIND 'Acme' IN ALL FIELDS

// NAME FIELDS - Search only name fields
FIND 'Acme' IN NAME FIELDS

// EMAIL FIELDS - Search only email fields
FIND 'john@acme.com' IN EMAIL FIELDS

// PHONE FIELDS - Search only phone fields
FIND '555-1234' IN PHONE FIELDS

// SIDEBAR FIELDS - Search fields displayed in sidebar
FIND 'Acme' IN SIDEBAR FIELDS
```

### Search Term Syntax

```apex
// Wildcard search (trailing only for SOSL)
FIND 'Acme*'

// Phrase search (exact match)
FIND '"Acme Corporation"'

// Boolean operators
FIND 'Acme AND Technology'
FIND 'Acme OR Technology'
FIND 'Acme AND NOT Closed'

// Grouping
FIND '(Acme OR Globex) AND Technology'
```

### Dynamic SOSL

```apex
public class GlobalSearch {

    public static Map<String, List<SObject>> search(
        String searchTerm,
        List<String> objectNames
    ) {
        if (String.isBlank(searchTerm) || searchTerm.length() < 2) {
            return new Map<String, List<SObject>>();
        }

        // Sanitize search term
        String sanitized = String.escapeSingleQuotes(searchTerm);

        // Build RETURNING clause
        List<String> returningClauses = new List<String>();
        for (String objName : objectNames) {
            returningClauses.add(objName + '(Id, Name LIMIT 20)');
        }

        String sosl = 'FIND \'' + sanitized + '*\' IN ALL FIELDS RETURNING ' +
                      String.join(returningClauses, ', ') +
                      ' LIMIT 100';

        List<List<SObject>> results = Search.query(sosl);

        // Map results to object names
        Map<String, List<SObject>> resultMap = new Map<String, List<SObject>>();
        for (Integer i = 0; i < objectNames.size(); i++) {
            resultMap.put(objectNames[i], results[i]);
        }

        return resultMap;
    }
}

// Usage
Map<String, List<SObject>> results = GlobalSearch.search(
    'Acme',
    new List<String>{'Account', 'Contact', 'Opportunity'}
);
```

---

## Performance Patterns

### Avoiding Common Anti-Patterns

```apex
// ANTI-PATTERN 1: SOQL in loops
// BAD
for (Contact c : contacts) {
    Account acc = [SELECT Id FROM Account WHERE Id = :c.AccountId];
}

// GOOD
Map<Id, Account> accounts = new Map<Id, Account>([
    SELECT Id FROM Account WHERE Id IN :contactAccountIds
]);

// ANTI-PATTERN 2: Querying all fields
// BAD
List<Account> accounts = [SELECT FIELDS(ALL) FROM Account LIMIT 100];

// GOOD - Query only needed fields
List<Account> accounts = [SELECT Id, Name, Industry FROM Account LIMIT 100];

// ANTI-PATTERN 3: Not using bind variables
// BAD - Risk of SOQL injection
String query = 'SELECT Id FROM Account WHERE Name = \'' + userInput + '\'';

// GOOD - Use bind variables
String accountName = userInput;
List<Account> accounts = [SELECT Id FROM Account WHERE Name = :accountName];

// ANTI-PATTERN 4: Querying without limits on unbounded queries
// BAD
List<Account> allAccounts = [SELECT Id FROM Account];

// GOOD
List<Account> accounts = [SELECT Id FROM Account LIMIT 10000];
```

### Large Data Volume Strategies

```apex
public class LargeDataVolumeQuery {

    // Strategy 1: Query with date ranges
    public static List<Account> getRecentAccounts() {
        return [
            SELECT Id, Name
            FROM Account
            WHERE CreatedDate = LAST_N_DAYS:30
            ORDER BY CreatedDate DESC
            LIMIT 1000
        ];
    }

    // Strategy 2: Use QueryLocator for batch processing
    public Database.QueryLocator getQueryLocator() {
        return Database.getQueryLocator([
            SELECT Id, Name, Industry
            FROM Account
            WHERE Industry = 'Technology'
        ]);
    }

    // Strategy 3: Skinny tables for specific fields
    // (Must be enabled by Salesforce Support for the object)

    // Strategy 4: Custom indexes on frequently queried fields
    // (Request via Salesforce Support)

    // Strategy 5: Archive old records
    // Use Big Objects for historical data
}
```

### Query Locator vs List

```apex
// Use QueryLocator for Batch Apex (up to 50 million records)
public Database.QueryLocator start(Database.BatchableContext bc) {
    return Database.getQueryLocator([
        SELECT Id, Name FROM Account
    ]);
}

// Use List for smaller datasets (up to 50,000 records)
public List<Account> start(Database.BatchableContext bc) {
    return [SELECT Id, Name FROM Account LIMIT 50000];
}
```

---

## Date Functions and Literals

### Date Literals

```apex
// Relative date literals
WHERE CreatedDate = TODAY
WHERE CreatedDate = YESTERDAY
WHERE CreatedDate = TOMORROW
WHERE CreatedDate = LAST_WEEK
WHERE CreatedDate = THIS_WEEK
WHERE CreatedDate = NEXT_WEEK
WHERE CreatedDate = LAST_MONTH
WHERE CreatedDate = THIS_MONTH
WHERE CreatedDate = NEXT_MONTH
WHERE CreatedDate = LAST_90_DAYS
WHERE CreatedDate = NEXT_90_DAYS
WHERE CreatedDate = LAST_N_DAYS:30
WHERE CreatedDate = NEXT_N_DAYS:30
WHERE CreatedDate = THIS_QUARTER
WHERE CreatedDate = LAST_QUARTER
WHERE CreatedDate = NEXT_QUARTER
WHERE CreatedDate = THIS_YEAR
WHERE CreatedDate = LAST_YEAR
WHERE CreatedDate = NEXT_YEAR
WHERE CreatedDate = THIS_FISCAL_QUARTER
WHERE CreatedDate = THIS_FISCAL_YEAR
```

### Date Functions

```apex
// Calendar functions in GROUP BY
SELECT CALENDAR_MONTH(CreatedDate) month, COUNT(Id) cnt
FROM Account
GROUP BY CALENDAR_MONTH(CreatedDate)

SELECT CALENDAR_YEAR(CloseDate) year, SUM(Amount) total
FROM Opportunity
WHERE IsWon = true
GROUP BY CALENDAR_YEAR(CloseDate)

// Fiscal functions
SELECT FISCAL_QUARTER(CloseDate) quarter, SUM(Amount)
FROM Opportunity
GROUP BY FISCAL_QUARTER(CloseDate)

// Week functions
SELECT WEEK_IN_MONTH(CreatedDate) week, COUNT(Id)
FROM Lead
GROUP BY WEEK_IN_MONTH(CreatedDate)

// Hour functions (for DateTime fields)
SELECT HOUR_IN_DAY(CreatedDate) hour, COUNT(Id)
FROM Case
GROUP BY HOUR_IN_DAY(CreatedDate)
```

---

## When to Use

- **SOQL**: Retrieving specific records with known criteria
- **SOSL**: Full-text search across multiple objects
- **Aggregate queries**: Reports, dashboards, summary calculations
- **Dynamic SOQL**: User-configurable queries, generic utilities
- **Relationship queries**: Parent-child data in single query

## When NOT to Use

- **SOQL in loops**: Always bulkify outside loops
- **SELECT ***: Query only needed fields
- **Non-selective queries**: Add indexed field filters
- **SOSL for exact matches**: Use SOQL for precise criteria
- **Aggregate for single records**: Use standard queries for individual records
