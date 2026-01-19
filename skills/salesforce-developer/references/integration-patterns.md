# Integration Patterns

> Reference for: Salesforce Developer
> Load when: REST/SOAP APIs, platform events, external services

---

## REST API Integration

### Outbound REST Callouts

Calling external APIs from Salesforce.

```apex
/**
 * HTTP Callout Service
 * Handles outbound REST API calls with retry logic
 */
public class HttpCalloutService {

    private static final Integer MAX_RETRIES = 3;
    private static final Integer TIMEOUT_MS = 30000;

    /**
     * Performs GET request with retry logic
     */
    public static HttpResponse doGet(String endpoint, Map<String, String> headers) {
        return doCallout('GET', endpoint, headers, null);
    }

    /**
     * Performs POST request with JSON body
     */
    public static HttpResponse doPost(String endpoint, Map<String, String> headers, Object body) {
        return doCallout('POST', endpoint, headers, JSON.serialize(body));
    }

    /**
     * Generic callout method with retry logic
     */
    private static HttpResponse doCallout(
        String method,
        String endpoint,
        Map<String, String> headers,
        String body
    ) {
        HttpRequest request = new HttpRequest();
        request.setEndpoint(endpoint);
        request.setMethod(method);
        request.setTimeout(TIMEOUT_MS);

        // Set default headers
        request.setHeader('Content-Type', 'application/json');
        request.setHeader('Accept', 'application/json');

        // Set custom headers
        if (headers != null) {
            for (String key : headers.keySet()) {
                request.setHeader(key, headers.get(key));
            }
        }

        // Set body for POST/PUT/PATCH
        if (String.isNotBlank(body)) {
            request.setBody(body);
        }

        Http http = new Http();
        HttpResponse response;
        Integer retryCount = 0;

        while (retryCount < MAX_RETRIES) {
            try {
                response = http.send(request);

                // Success or client error - don't retry
                if (response.getStatusCode() < 500) {
                    break;
                }

                // Server error - retry
                retryCount++;
                if (retryCount < MAX_RETRIES) {
                    // Exponential backoff simulation via logging
                    System.debug('Retry ' + retryCount + ' after server error');
                }

            } catch (CalloutException e) {
                retryCount++;
                if (retryCount >= MAX_RETRIES) {
                    throw e;
                }
            }
        }

        return response;
    }
}
```

### Named Credentials

Always use Named Credentials for secure credential management.

```apex
/**
 * External API integration using Named Credentials
 */
public class ExternalApiService {

    // Named Credential endpoint (configured in Setup > Named Credentials)
    private static final String NAMED_CREDENTIAL = 'callout:External_API';

    /**
     * Get customer data from external system
     */
    public static CustomerResponse getCustomer(String customerId) {
        String endpoint = NAMED_CREDENTIAL + '/customers/' + customerId;

        HttpResponse response = HttpCalloutService.doGet(endpoint, null);

        if (response.getStatusCode() == 200) {
            return (CustomerResponse)JSON.deserialize(
                response.getBody(),
                CustomerResponse.class
            );
        } else {
            throw new IntegrationException(
                'Failed to get customer: ' + response.getStatusCode() +
                ' - ' + response.getBody()
            );
        }
    }

    /**
     * Create customer in external system
     */
    public static CustomerResponse createCustomer(CustomerRequest request) {
        String endpoint = NAMED_CREDENTIAL + '/customers';

        HttpResponse response = HttpCalloutService.doPost(endpoint, null, request);

        if (response.getStatusCode() == 201) {
            return (CustomerResponse)JSON.deserialize(
                response.getBody(),
                CustomerResponse.class
            );
        } else {
            throw new IntegrationException(
                'Failed to create customer: ' + response.getBody()
            );
        }
    }

    // Request/Response wrapper classes
    public class CustomerRequest {
        public String name;
        public String email;
        public String phone;
        public Address address;
    }

    public class CustomerResponse {
        public String id;
        public String name;
        public String email;
        public String status;
        public DateTime createdAt;
    }

    public class Address {
        public String street;
        public String city;
        public String state;
        public String country;
        public String postalCode;
    }

    public class IntegrationException extends Exception {}
}
```

### Inbound REST API

Exposing Salesforce as a REST API.

```apex
/**
 * Custom REST API endpoint
 * Endpoint: /services/apexrest/accounts
 */
@RestResource(urlMapping='/accounts/*')
global with sharing class AccountRestService {

    /**
     * GET /services/apexrest/accounts/{id}
     * Returns account by ID
     */
    @HttpGet
    global static AccountWrapper getAccount() {
        RestRequest req = RestContext.request;
        RestResponse res = RestContext.response;

        // Extract ID from URL
        String accountId = req.requestURI.substringAfterLast('/');

        if (String.isBlank(accountId)) {
            res.statusCode = 400;
            return new AccountWrapper('Account ID is required', null);
        }

        try {
            Account acc = [
                SELECT Id, Name, Industry, AnnualRevenue, BillingCity, BillingCountry
                FROM Account
                WHERE Id = :accountId
                WITH SECURITY_ENFORCED
            ];

            res.statusCode = 200;
            return new AccountWrapper(null, acc);

        } catch (QueryException e) {
            res.statusCode = 404;
            return new AccountWrapper('Account not found', null);
        }
    }

    /**
     * POST /services/apexrest/accounts
     * Creates new account
     */
    @HttpPost
    global static AccountWrapper createAccount(AccountRequest request) {
        RestResponse res = RestContext.response;

        // Validate request
        if (String.isBlank(request.name)) {
            res.statusCode = 400;
            return new AccountWrapper('Name is required', null);
        }

        try {
            Account acc = new Account(
                Name = request.name,
                Industry = request.industry,
                AnnualRevenue = request.annualRevenue,
                BillingStreet = request.billingStreet,
                BillingCity = request.billingCity,
                BillingState = request.billingState,
                BillingCountry = request.billingCountry,
                BillingPostalCode = request.billingPostalCode
            );

            insert acc;

            res.statusCode = 201;
            return new AccountWrapper(null, acc);

        } catch (DmlException e) {
            res.statusCode = 400;
            return new AccountWrapper(e.getMessage(), null);
        }
    }

    /**
     * PATCH /services/apexrest/accounts/{id}
     * Updates existing account
     */
    @HttpPatch
    global static AccountWrapper updateAccount(AccountRequest request) {
        RestRequest req = RestContext.request;
        RestResponse res = RestContext.response;

        String accountId = req.requestURI.substringAfterLast('/');

        try {
            Account acc = [SELECT Id FROM Account WHERE Id = :accountId];

            if (String.isNotBlank(request.name)) acc.Name = request.name;
            if (String.isNotBlank(request.industry)) acc.Industry = request.industry;
            if (request.annualRevenue != null) acc.AnnualRevenue = request.annualRevenue;

            update acc;

            res.statusCode = 200;
            return new AccountWrapper(null, acc);

        } catch (QueryException e) {
            res.statusCode = 404;
            return new AccountWrapper('Account not found', null);
        }
    }

    /**
     * DELETE /services/apexrest/accounts/{id}
     * Deletes account
     */
    @HttpDelete
    global static AccountWrapper deleteAccount() {
        RestRequest req = RestContext.request;
        RestResponse res = RestContext.response;

        String accountId = req.requestURI.substringAfterLast('/');

        try {
            Account acc = [SELECT Id FROM Account WHERE Id = :accountId];
            delete acc;

            res.statusCode = 200;
            return new AccountWrapper('Account deleted', null);

        } catch (QueryException e) {
            res.statusCode = 404;
            return new AccountWrapper('Account not found', null);
        }
    }

    // Wrapper classes
    global class AccountWrapper {
        public String error;
        public Account account;

        public AccountWrapper(String error, Account account) {
            this.error = error;
            this.account = account;
        }
    }

    global class AccountRequest {
        public String name;
        public String industry;
        public Decimal annualRevenue;
        public String billingStreet;
        public String billingCity;
        public String billingState;
        public String billingCountry;
        public String billingPostalCode;
    }
}
```

---

## Platform Events

### Event-Driven Architecture

Platform Events enable loosely-coupled, event-driven integrations.

### Publishing Events

```apex
/**
 * Platform Event: Order_Event__e
 * Fields: Order_Id__c, Customer_Id__c, Status__c, Amount__c, Payload__c
 */
public class OrderEventPublisher {

    /**
     * Publishes order events
     * @param orders List of orders to publish
     * @return List of publish results
     */
    public static List<Database.SaveResult> publishOrderEvents(List<Order> orders) {
        List<Order_Event__e> events = new List<Order_Event__e>();

        for (Order ord : orders) {
            events.add(new Order_Event__e(
                Order_Id__c = ord.Id,
                Customer_Id__c = ord.AccountId,
                Status__c = ord.Status,
                Amount__c = ord.TotalAmount,
                Payload__c = JSON.serialize(new OrderPayload(ord))
            ));
        }

        // Publish events
        List<Database.SaveResult> results = EventBus.publish(events);

        // Check results
        for (Integer i = 0; i < results.size(); i++) {
            if (!results[i].isSuccess()) {
                for (Database.Error err : results[i].getErrors()) {
                    System.debug(LoggingLevel.ERROR,
                        'Error publishing event: ' + err.getMessage());
                }
            }
        }

        return results;
    }

    /**
     * Publishes single event immediately
     */
    public static void publishOrderStatusChange(Id orderId, String newStatus) {
        Order_Event__e event = new Order_Event__e(
            Order_Id__c = orderId,
            Status__c = newStatus
        );

        Database.SaveResult result = EventBus.publish(event);

        if (!result.isSuccess()) {
            throw new EventPublishException('Failed to publish order event');
        }
    }

    private class OrderPayload {
        public String orderId;
        public String orderNumber;
        public String status;
        public Decimal amount;
        public List<OrderItemPayload> items;

        public OrderPayload(Order ord) {
            this.orderId = ord.Id;
            this.orderNumber = ord.OrderNumber;
            this.status = ord.Status;
            this.amount = ord.TotalAmount;
        }
    }

    private class OrderItemPayload {
        public String productId;
        public Integer quantity;
        public Decimal unitPrice;
    }

    public class EventPublishException extends Exception {}
}
```

### Subscribing to Events (Apex Trigger)

```apex
/**
 * Platform Event Trigger
 * Subscribes to Order_Event__e
 */
trigger OrderEventTrigger on Order_Event__e (after insert) {
    OrderEventHandler handler = new OrderEventHandler();
    handler.handleEvents(Trigger.new);
}
```

```apex
/**
 * Platform Event Handler
 */
public class OrderEventHandler {

    public void handleEvents(List<Order_Event__e> events) {
        List<Order_Sync__c> syncs = new List<Order_Sync__c>();
        List<Id> orderIds = new List<Id>();

        for (Order_Event__e event : events) {
            // Track replay ID for debugging
            System.debug('Processing event with replay ID: ' + event.ReplayId);

            orderIds.add(event.Order_Id__c);

            // Create sync record
            syncs.add(new Order_Sync__c(
                Order_Id__c = event.Order_Id__c,
                Status__c = event.Status__c,
                Event_Replay_Id__c = String.valueOf(event.ReplayId),
                Processed_Date__c = DateTime.now()
            ));
        }

        // Process in bulk
        if (!syncs.isEmpty()) {
            insert syncs;
        }

        // Call external system asynchronously
        if (!orderIds.isEmpty() && !System.isBatch() && !System.isFuture()) {
            syncOrdersToExternalSystem(orderIds);
        }
    }

    @future(callout=true)
    private static void syncOrdersToExternalSystem(List<Id> orderIds) {
        // Callout to external system
    }
}
```

### Subscribing via CometD (External Systems)

```javascript
// Node.js CometD client for Platform Events
const cometd = require('cometd');
const jsforce = require('jsforce');

async function subscribeToEvents() {
    const conn = new jsforce.Connection({
        loginUrl: process.env.SF_LOGIN_URL
    });

    await conn.login(process.env.SF_USERNAME, process.env.SF_PASSWORD);

    const client = new cometd.CometD();

    client.configure({
        url: conn.instanceUrl + '/cometd/58.0',
        requestHeaders: {
            Authorization: 'Bearer ' + conn.accessToken
        }
    });

    client.handshake((status) => {
        if (status.successful) {
            // Subscribe to platform event channel
            client.subscribe('/event/Order_Event__e', (message) => {
                console.log('Received event:', message.data.payload);

                const orderId = message.data.payload.Order_Id__c;
                const status = message.data.payload.Status__c;

                // Process event
                processOrderEvent(orderId, status);
            });
        }
    });
}
```

---

## Change Data Capture

### Subscribing to Change Events

```apex
/**
 * Change Data Capture Trigger for Account changes
 * Object must have CDC enabled in Setup
 */
trigger AccountChangeEventTrigger on AccountChangeEvent (after insert) {
    AccountChangeEventHandler handler = new AccountChangeEventHandler();
    handler.handleChanges(Trigger.new);
}
```

```apex
/**
 * Change Data Capture Handler
 */
public class AccountChangeEventHandler {

    public void handleChanges(List<AccountChangeEvent> changes) {
        List<Account_Audit__c> auditRecords = new List<Account_Audit__c>();

        for (AccountChangeEvent event : changes) {
            EventBus.ChangeEventHeader header = event.ChangeEventHeader;

            String changeType = header.getChangeType();
            List<String> changedFields = header.getChangedFields();
            String recordIds = String.join(header.getRecordIds(), ',');

            System.debug('Change Type: ' + changeType);
            System.debug('Changed Fields: ' + changedFields);
            System.debug('Record IDs: ' + recordIds);

            // Create audit record
            auditRecords.add(new Account_Audit__c(
                Account_Ids__c = recordIds,
                Change_Type__c = changeType,
                Changed_Fields__c = String.join(changedFields, ', '),
                Change_User__c = header.getCommitUser(),
                Change_Timestamp__c = header.getCommitTimestamp()
            ));

            // Handle specific change types
            if (changeType == 'CREATE') {
                handleCreate(event, header.getRecordIds());
            } else if (changeType == 'UPDATE') {
                handleUpdate(event, changedFields);
            } else if (changeType == 'DELETE') {
                handleDelete(header.getRecordIds());
            }
        }

        if (!auditRecords.isEmpty()) {
            insert auditRecords;
        }
    }

    private void handleCreate(AccountChangeEvent event, List<String> recordIds) {
        // New account created - trigger onboarding workflow
        System.debug('New accounts created: ' + recordIds);
    }

    private void handleUpdate(AccountChangeEvent event, List<String> changedFields) {
        // Check for specific field changes
        if (changedFields.contains('OwnerId')) {
            System.debug('Account ownership changed');
            // Notify new owner
        }

        if (changedFields.contains('Rating')) {
            System.debug('Account rating changed to: ' + event.Rating);
            // Update related records
        }
    }

    private void handleDelete(List<String> recordIds) {
        System.debug('Accounts deleted: ' + recordIds);
        // Clean up related external systems
    }
}
```

---

## External Services

### Using External Services

External Services auto-generate Apex classes from OpenAPI specifications.

```apex
/**
 * Using auto-generated External Service class
 * External Service name: PaymentGateway
 */
public class PaymentService {

    public static PaymentResult processPayment(
        String orderId,
        Decimal amount,
        String currency_x
    ) {
        // Get External Service instance
        ExternalService.PaymentGateway service = new ExternalService.PaymentGateway();

        // Build request using generated request class
        ExternalService.PaymentGateway_PaymentRequest request =
            new ExternalService.PaymentGateway_PaymentRequest();
        request.orderId = orderId;
        request.amount = amount;
        request.currency_x = currency_x;

        try {
            // Call external service
            ExternalService.PaymentGateway_PaymentResponse response =
                service.processPayment(request);

            return new PaymentResult(
                response.transactionId,
                response.status,
                null
            );

        } catch (ExternalService.PaymentGateway_Exception e) {
            return new PaymentResult(null, 'FAILED', e.getMessage());
        }
    }

    public class PaymentResult {
        public String transactionId;
        public String status;
        public String errorMessage;

        public PaymentResult(String txnId, String status, String error) {
            this.transactionId = txnId;
            this.status = status;
            this.errorMessage = error;
        }
    }
}
```

---

## Async Integration Patterns

### Queueable for Callouts

```apex
/**
 * Queueable class for async callouts
 * Supports chaining for multi-step integrations
 */
public class OrderSyncQueueable implements Queueable, Database.AllowsCallouts {

    private List<Id> orderIds;
    private Integer batchNumber;
    private static final Integer BATCH_SIZE = 50;

    public OrderSyncQueueable(List<Id> orderIds) {
        this(orderIds, 0);
    }

    public OrderSyncQueueable(List<Id> orderIds, Integer batchNumber) {
        this.orderIds = orderIds;
        this.batchNumber = batchNumber;
    }

    public void execute(QueueableContext context) {
        // Get batch to process
        Integer startIndex = batchNumber * BATCH_SIZE;
        Integer endIndex = Math.min(startIndex + BATCH_SIZE, orderIds.size());

        List<Id> batchIds = new List<Id>();
        for (Integer i = startIndex; i < endIndex; i++) {
            batchIds.add(orderIds[i]);
        }

        // Process batch
        List<Order> orders = [
            SELECT Id, OrderNumber, Status, TotalAmount, Account.Name
            FROM Order
            WHERE Id IN :batchIds
        ];

        // Sync to external system
        HttpResponse response = syncOrders(orders);

        if (response.getStatusCode() == 200) {
            // Update sync status
            List<Order> toUpdate = new List<Order>();
            for (Order ord : orders) {
                toUpdate.add(new Order(
                    Id = ord.Id,
                    External_Sync_Status__c = 'Synced',
                    External_Sync_Date__c = DateTime.now()
                ));
            }
            update toUpdate;
        }

        // Chain next batch if more records
        if (endIndex < orderIds.size() && !Test.isRunningTest()) {
            System.enqueueJob(new OrderSyncQueueable(orderIds, batchNumber + 1));
        }
    }

    private HttpResponse syncOrders(List<Order> orders) {
        HttpRequest request = new HttpRequest();
        request.setEndpoint('callout:Order_System/api/orders/batch');
        request.setMethod('POST');
        request.setHeader('Content-Type', 'application/json');
        request.setBody(JSON.serialize(orders));

        Http http = new Http();
        return http.send(request);
    }
}
```

### Continuation for Long-Running Callouts

```apex
/**
 * Continuation for async callouts in Visualforce/LWC
 * Avoids timeout issues with long-running external calls
 */
public class LongRunningCalloutController {

    @AuraEnabled
    public static Object startCallout(String accountId) {
        Continuation cont = new Continuation(120); // 120 second timeout
        cont.continuationMethod = 'processResponse';

        HttpRequest request = new HttpRequest();
        request.setEndpoint('callout:Slow_External_API/analyze/' + accountId);
        request.setMethod('GET');

        cont.addHttpRequest(request);

        return cont;
    }

    @AuraEnabled
    public static Object processResponse(List<String> labels, Object state) {
        HttpResponse response = Continuation.getResponse(labels[0]);

        if (response.getStatusCode() == 200) {
            return JSON.deserializeUntyped(response.getBody());
        } else {
            throw new AuraHandledException(
                'Callout failed: ' + response.getStatusCode()
            );
        }
    }
}
```

---

## Error Handling Patterns

### Robust Integration Error Handling

```apex
/**
 * Integration service with comprehensive error handling
 */
public class RobustIntegrationService {

    public static IntegrationResult syncAccount(Id accountId) {
        IntegrationResult result = new IntegrationResult();

        try {
            Account acc = [
                SELECT Id, Name, Industry, AnnualRevenue
                FROM Account
                WHERE Id = :accountId
            ];

            HttpResponse response = callExternalApi(acc);
            result = processResponse(response, acc);

        } catch (QueryException e) {
            result.success = false;
            result.errorCode = 'RECORD_NOT_FOUND';
            result.errorMessage = 'Account not found: ' + accountId;
            logError('QueryException', e.getMessage(), accountId);

        } catch (CalloutException e) {
            result.success = false;
            result.errorCode = 'CALLOUT_FAILED';
            result.errorMessage = 'Unable to reach external system';
            logError('CalloutException', e.getMessage(), accountId);

            // Queue for retry
            queueForRetry(accountId);

        } catch (JSONException e) {
            result.success = false;
            result.errorCode = 'PARSE_ERROR';
            result.errorMessage = 'Invalid response from external system';
            logError('JSONException', e.getMessage(), accountId);

        } catch (Exception e) {
            result.success = false;
            result.errorCode = 'UNKNOWN_ERROR';
            result.errorMessage = e.getMessage();
            logError('Exception', e.getMessage() + '\n' + e.getStackTraceString(), accountId);
        }

        return result;
    }

    private static HttpResponse callExternalApi(Account acc) {
        HttpRequest request = new HttpRequest();
        request.setEndpoint('callout:External_System/accounts');
        request.setMethod('POST');
        request.setHeader('Content-Type', 'application/json');
        request.setBody(JSON.serialize(acc));
        request.setTimeout(30000);

        Http http = new Http();
        return http.send(request);
    }

    private static IntegrationResult processResponse(HttpResponse response, Account acc) {
        IntegrationResult result = new IntegrationResult();

        Integer statusCode = response.getStatusCode();

        if (statusCode >= 200 && statusCode < 300) {
            result.success = true;
            result.externalId = parseExternalId(response.getBody());

            // Update account with external ID
            acc.External_System_Id__c = result.externalId;
            update acc;

        } else if (statusCode == 400) {
            result.success = false;
            result.errorCode = 'VALIDATION_ERROR';
            result.errorMessage = response.getBody();

        } else if (statusCode == 401 || statusCode == 403) {
            result.success = false;
            result.errorCode = 'AUTH_ERROR';
            result.errorMessage = 'Authentication failed';

        } else if (statusCode == 404) {
            result.success = false;
            result.errorCode = 'NOT_FOUND';
            result.errorMessage = 'Endpoint not found';

        } else if (statusCode >= 500) {
            result.success = false;
            result.errorCode = 'SERVER_ERROR';
            result.errorMessage = 'External system error';
            queueForRetry(acc.Id);
        }

        return result;
    }

    private static String parseExternalId(String responseBody) {
        Map<String, Object> body = (Map<String, Object>)JSON.deserializeUntyped(responseBody);
        return (String)body.get('id');
    }

    private static void logError(String errorType, String message, Id recordId) {
        Integration_Log__c log = new Integration_Log__c(
            Error_Type__c = errorType,
            Error_Message__c = message.left(32000),
            Record_Id__c = recordId,
            Timestamp__c = DateTime.now()
        );
        insert log;
    }

    private static void queueForRetry(Id accountId) {
        // Queue for retry with exponential backoff
        Integration_Retry__c retry = new Integration_Retry__c(
            Record_Id__c = accountId,
            Object_Type__c = 'Account',
            Retry_Count__c = 0,
            Next_Retry__c = DateTime.now().addMinutes(5)
        );
        insert retry;
    }

    public class IntegrationResult {
        @AuraEnabled public Boolean success = false;
        @AuraEnabled public String errorCode;
        @AuraEnabled public String errorMessage;
        @AuraEnabled public String externalId;
    }
}
```

---

## When to Use

- **REST callouts**: Real-time sync with external APIs
- **Platform Events**: Event-driven architecture, decoupled integrations
- **Change Data Capture**: Audit trails, external sync on data changes
- **External Services**: OpenAPI-defined integrations with auto-generated code
- **Queueable**: Async callouts needing chaining or complex logic
- **Continuation**: Long-running callouts in UI context

## When NOT to Use

- **Synchronous callouts in triggers**: Use future/queueable instead
- **Callouts during DML operations**: Salesforce prevents mixed DML/callout
- **Platform Events for guaranteed delivery**: Use external queues for critical data
- **Raw HTTP for well-defined APIs**: Use External Services for OpenAPI specs
- **Continuation for batch processing**: Use Batch Apex with Database.AllowsCallouts
