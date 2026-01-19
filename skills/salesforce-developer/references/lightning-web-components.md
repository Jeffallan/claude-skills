# Lightning Web Components

> Reference for: Salesforce Developer
> Load when: LWC framework, component design, events, wire service

---

## Component Structure

### Basic LWC Anatomy

Every Lightning Web Component consists of three files:

```
myComponent/
├── myComponent.html     # Template
├── myComponent.js       # JavaScript controller
└── myComponent.js-meta.xml  # Configuration
```

### HTML Template

```html
<!-- accountCard.html -->
<template>
    <lightning-card title={cardTitle} icon-name="standard:account">
        <div class="slds-p-around_medium">
            <!-- Conditional rendering -->
            <template lwc:if={isLoading}>
                <lightning-spinner alternative-text="Loading"></lightning-spinner>
            </template>

            <template lwc:else>
                <!-- Iteration -->
                <template for:each={accounts} for:item="account">
                    <div key={account.Id} class="slds-m-bottom_small">
                        <lightning-tile
                            label={account.Name}
                            href={account.recordUrl}>
                            <p class="slds-truncate">{account.Industry}</p>
                            <p class="slds-text-body_small">
                                Revenue: <lightning-formatted-number
                                    value={account.AnnualRevenue}
                                    format-style="currency"
                                    currency-code="USD">
                                </lightning-formatted-number>
                            </p>
                        </lightning-tile>
                    </div>
                </template>

                <!-- Empty state -->
                <template lwc:if={isEmpty}>
                    <div class="slds-align_absolute-center slds-p-around_large">
                        <p>No accounts found</p>
                    </div>
                </template>
            </template>
        </div>

        <!-- Footer slot -->
        <div slot="footer">
            <lightning-button
                label="Refresh"
                onclick={handleRefresh}
                disabled={isLoading}>
            </lightning-button>
        </div>
    </lightning-card>
</template>
```

### JavaScript Controller

```javascript
// accountCard.js
import { LightningElement, api, wire, track } from 'lwc';
import { NavigationMixin } from 'lightning/navigation';
import { ShowToastEvent } from 'lightning/platformShowToastEvent';
import { refreshApex } from '@salesforce/apex';
import getAccounts from '@salesforce/apex/AccountController.getAccounts';

export default class AccountCard extends NavigationMixin(LightningElement) {

    // Public properties - exposed to parent components
    @api recordId;
    @api maxRecords = 10;

    // Private reactive properties
    accounts = [];
    error;
    isLoading = true;

    // Cached wire result for refresh
    wiredAccountsResult;

    // Computed properties
    get cardTitle() {
        return `Accounts (${this.accounts.length})`;
    }

    get isEmpty() {
        return this.accounts.length === 0;
    }

    // Wire service - reactive data binding
    @wire(getAccounts, { recordId: '$recordId', maxRecords: '$maxRecords' })
    wiredAccounts(result) {
        this.wiredAccountsResult = result;
        const { data, error } = result;

        if (data) {
            this.accounts = data.map(account => ({
                ...account,
                recordUrl: `/lightning/r/Account/${account.Id}/view`
            }));
            this.error = undefined;
        } else if (error) {
            this.error = error;
            this.accounts = [];
            this.showError('Error loading accounts', this.reduceErrors(error));
        }

        this.isLoading = false;
    }

    // Lifecycle hooks
    connectedCallback() {
        console.log('Component connected, recordId:', this.recordId);
    }

    disconnectedCallback() {
        console.log('Component disconnected');
    }

    renderedCallback() {
        // Called after every render
    }

    errorCallback(error, stack) {
        console.error('Component error:', error, stack);
    }

    // Event handlers
    handleRefresh() {
        this.isLoading = true;
        refreshApex(this.wiredAccountsResult)
            .finally(() => {
                this.isLoading = false;
            });
    }

    // Helper methods
    showError(title, message) {
        this.dispatchEvent(new ShowToastEvent({
            title,
            message,
            variant: 'error'
        }));
    }

    reduceErrors(errors) {
        if (!Array.isArray(errors)) {
            errors = [errors];
        }

        return errors
            .filter(error => !!error)
            .map(error => {
                if (typeof error === 'string') {
                    return error;
                }
                if (error.body?.message) {
                    return error.body.message;
                }
                if (error.message) {
                    return error.message;
                }
                return JSON.stringify(error);
            })
            .join(', ');
    }
}
```

### Meta Configuration

```xml
<!-- accountCard.js-meta.xml -->
<?xml version="1.0" encoding="UTF-8"?>
<LightningComponentBundle xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>59.0</apiVersion>
    <isExposed>true</isExposed>
    <masterLabel>Account Card</masterLabel>
    <description>Displays account information in a card format</description>

    <targets>
        <target>lightning__RecordPage</target>
        <target>lightning__AppPage</target>
        <target>lightning__HomePage</target>
        <target>lightningCommunity__Page</target>
    </targets>

    <targetConfigs>
        <targetConfig targets="lightning__RecordPage">
            <objects>
                <object>Account</object>
                <object>Contact</object>
            </objects>
            <property name="maxRecords" type="Integer" default="10"
                      label="Maximum Records" description="Max accounts to display" />
        </targetConfig>
        <targetConfig targets="lightning__AppPage,lightning__HomePage">
            <property name="maxRecords" type="Integer" default="10"
                      label="Maximum Records" />
        </targetConfig>
    </targetConfigs>
</LightningComponentBundle>
```

---

## Wire Service Patterns

### Wire with Apex Methods

```javascript
// Apex Controller
public with sharing class AccountController {

    @AuraEnabled(cacheable=true)
    public static List<Account> getAccounts(Id recordId, Integer maxRecords) {
        return [
            SELECT Id, Name, Industry, AnnualRevenue
            FROM Account
            WHERE Id != :recordId
            ORDER BY AnnualRevenue DESC NULLS LAST
            LIMIT :maxRecords
        ];
    }

    @AuraEnabled
    public static Account updateAccount(Id accountId, Map<String, Object> fields) {
        Account acc = new Account(Id = accountId);
        for (String fieldName : fields.keySet()) {
            acc.put(fieldName, fields.get(fieldName));
        }
        update acc;
        return acc;
    }
}
```

```javascript
// LWC using wire service
import { LightningElement, wire } from 'lwc';
import { getRecord, getFieldValue, updateRecord } from 'lightning/uiRecordApi';
import ACCOUNT_NAME from '@salesforce/schema/Account.Name';
import ACCOUNT_INDUSTRY from '@salesforce/schema/Account.Industry';
import ACCOUNT_REVENUE from '@salesforce/schema/Account.AnnualRevenue';

const FIELDS = [ACCOUNT_NAME, ACCOUNT_INDUSTRY, ACCOUNT_REVENUE];

export default class AccountDetail extends LightningElement {
    @api recordId;

    @wire(getRecord, { recordId: '$recordId', fields: FIELDS })
    account;

    get accountName() {
        return getFieldValue(this.account.data, ACCOUNT_NAME);
    }

    get industry() {
        return getFieldValue(this.account.data, ACCOUNT_INDUSTRY);
    }

    async handleUpdate() {
        const fields = {};
        fields.Id = this.recordId;
        fields[ACCOUNT_INDUSTRY.fieldApiName] = 'Technology';

        try {
            await updateRecord({ fields });
            this.dispatchEvent(new ShowToastEvent({
                title: 'Success',
                message: 'Account updated',
                variant: 'success'
            }));
        } catch (error) {
            this.dispatchEvent(new ShowToastEvent({
                title: 'Error',
                message: error.body.message,
                variant: 'error'
            }));
        }
    }
}
```

### Imperative Apex Calls

Use when you need control over when data is fetched.

```javascript
import { LightningElement, api } from 'lwc';
import searchAccounts from '@salesforce/apex/AccountController.searchAccounts';

export default class AccountSearch extends LightningElement {
    searchTerm = '';
    accounts = [];
    isSearching = false;

    handleSearchChange(event) {
        this.searchTerm = event.target.value;
    }

    async handleSearch() {
        if (this.searchTerm.length < 2) {
            return;
        }

        this.isSearching = true;

        try {
            this.accounts = await searchAccounts({ searchTerm: this.searchTerm });
        } catch (error) {
            console.error('Search error:', error);
            this.accounts = [];
        } finally {
            this.isSearching = false;
        }
    }

    // Debounced search for better UX
    debounceTimeout;
    handleSearchInput(event) {
        clearTimeout(this.debounceTimeout);
        this.searchTerm = event.target.value;

        this.debounceTimeout = setTimeout(() => {
            this.handleSearch();
        }, 300);
    }
}
```

---

## Component Communication

### Parent to Child (Public Properties)

```javascript
// Parent component
// parent.html
<template>
    <c-child-component
        account-id={selectedAccountId}
        display-mode="compact"
        onselect={handleChildSelect}>
    </c-child-component>
</template>
```

```javascript
// Child component
// childComponent.js
import { LightningElement, api } from 'lwc';

export default class ChildComponent extends LightningElement {
    @api accountId;
    @api displayMode = 'full'; // Default value

    // Public method callable by parent
    @api
    refresh() {
        // Refresh logic
    }

    @api
    validate() {
        const input = this.template.querySelector('lightning-input');
        return input.reportValidity();
    }
}
```

### Child to Parent (Custom Events)

```javascript
// Child component dispatching event
export default class ChildComponent extends LightningElement {

    handleAccountSelect(event) {
        const accountId = event.target.dataset.id;

        // Simple event
        this.dispatchEvent(new CustomEvent('select', {
            detail: { accountId }
        }));

        // Bubbling event (crosses shadow DOM)
        this.dispatchEvent(new CustomEvent('accountselected', {
            detail: { accountId, accountName: this.accountName },
            bubbles: true,
            composed: true
        }));
    }
}
```

```javascript
// Parent component handling event
// parent.html
<template>
    <c-child-component onselect={handleSelect}></c-child-component>
</template>

// parent.js
handleSelect(event) {
    const { accountId } = event.detail;
    console.log('Selected account:', accountId);
}
```

### Sibling Communication (Lightning Message Service)

```javascript
// messageChannel/AccountSelected.messageChannel-meta.xml
<?xml version="1.0" encoding="UTF-8"?>
<LightningMessageChannel xmlns="http://soap.sforce.com/2006/04/metadata">
    <masterLabel>Account Selected</masterLabel>
    <isExposed>true</isExposed>
    <description>Channel for account selection events</description>
    <lightningMessageFields>
        <fieldName>accountId</fieldName>
        <description>Selected Account ID</description>
    </lightningMessageFields>
    <lightningMessageFields>
        <fieldName>source</fieldName>
        <description>Component that sent message</description>
    </lightningMessageFields>
</LightningMessageChannel>
```

```javascript
// Publisher component
import { LightningElement, wire } from 'lwc';
import { publish, MessageContext } from 'lightning/messageService';
import ACCOUNT_SELECTED from '@salesforce/messageChannel/AccountSelected__c';

export default class AccountPublisher extends LightningElement {
    @wire(MessageContext)
    messageContext;

    handleAccountClick(event) {
        const accountId = event.target.dataset.id;

        const payload = {
            accountId: accountId,
            source: 'AccountPublisher'
        };

        publish(this.messageContext, ACCOUNT_SELECTED, payload);
    }
}
```

```javascript
// Subscriber component
import { LightningElement, wire } from 'lwc';
import { subscribe, unsubscribe, MessageContext } from 'lightning/messageService';
import ACCOUNT_SELECTED from '@salesforce/messageChannel/AccountSelected__c';

export default class AccountSubscriber extends LightningElement {
    subscription = null;
    selectedAccountId;

    @wire(MessageContext)
    messageContext;

    connectedCallback() {
        this.subscribeToMessageChannel();
    }

    disconnectedCallback() {
        this.unsubscribeFromMessageChannel();
    }

    subscribeToMessageChannel() {
        if (!this.subscription) {
            this.subscription = subscribe(
                this.messageContext,
                ACCOUNT_SELECTED,
                (message) => this.handleMessage(message)
            );
        }
    }

    unsubscribeFromMessageChannel() {
        unsubscribe(this.subscription);
        this.subscription = null;
    }

    handleMessage(message) {
        this.selectedAccountId = message.accountId;
        console.log('Received from:', message.source);
    }
}
```

---

## Form Handling

### Lightning Record Edit Form

```html
<template>
    <lightning-record-edit-form
        record-id={recordId}
        object-api-name="Account"
        onsuccess={handleSuccess}
        onerror={handleError}
        onsubmit={handleSubmit}>

        <lightning-messages></lightning-messages>

        <lightning-input-field field-name="Name"></lightning-input-field>
        <lightning-input-field field-name="Industry"></lightning-input-field>
        <lightning-input-field field-name="AnnualRevenue"></lightning-input-field>

        <div class="slds-m-top_medium">
            <lightning-button
                type="submit"
                variant="brand"
                label="Save">
            </lightning-button>
        </div>
    </lightning-record-edit-form>
</template>
```

```javascript
import { LightningElement, api } from 'lwc';
import { ShowToastEvent } from 'lightning/platformShowToastEvent';

export default class AccountForm extends LightningElement {
    @api recordId;

    handleSubmit(event) {
        event.preventDefault();
        const fields = event.detail.fields;

        // Modify fields before submission
        fields.Description = `Updated on ${new Date().toISOString()}`;

        this.template.querySelector('lightning-record-edit-form').submit(fields);
    }

    handleSuccess(event) {
        const updatedRecord = event.detail.id;
        this.dispatchEvent(new ShowToastEvent({
            title: 'Success',
            message: 'Account saved successfully',
            variant: 'success'
        }));
    }

    handleError(event) {
        console.error('Form error:', event.detail);
    }
}
```

### Custom Form Validation

```html
<template>
    <lightning-card title="Custom Form">
        <div class="slds-p-around_medium">
            <lightning-input
                label="Account Name"
                value={accountName}
                onchange={handleNameChange}
                required
                class="validate">
            </lightning-input>

            <lightning-combobox
                label="Industry"
                value={industry}
                options={industryOptions}
                onchange={handleIndustryChange}
                required
                class="validate">
            </lightning-combobox>

            <lightning-input
                type="number"
                label="Annual Revenue"
                value={revenue}
                onchange={handleRevenueChange}
                min="0"
                formatter="currency"
                class="validate">
            </lightning-input>

            <div class="slds-m-top_medium">
                <lightning-button
                    label="Save"
                    variant="brand"
                    onclick={handleSave}>
                </lightning-button>
            </div>
        </div>
    </lightning-card>
</template>
```

```javascript
import { LightningElement } from 'lwc';
import createAccount from '@salesforce/apex/AccountController.createAccount';

export default class CustomAccountForm extends LightningElement {
    accountName = '';
    industry = '';
    revenue = 0;

    industryOptions = [
        { label: 'Technology', value: 'Technology' },
        { label: 'Healthcare', value: 'Healthcare' },
        { label: 'Finance', value: 'Finance' },
        { label: 'Manufacturing', value: 'Manufacturing' }
    ];

    handleNameChange(event) {
        this.accountName = event.target.value;
    }

    handleIndustryChange(event) {
        this.industry = event.detail.value;
    }

    handleRevenueChange(event) {
        this.revenue = event.target.value;
    }

    validateForm() {
        const inputs = [...this.template.querySelectorAll('.validate')];
        const isValid = inputs.reduce((valid, input) => {
            input.reportValidity();
            return valid && input.checkValidity();
        }, true);

        return isValid;
    }

    async handleSave() {
        if (!this.validateForm()) {
            return;
        }

        try {
            const account = await createAccount({
                name: this.accountName,
                industry: this.industry,
                revenue: this.revenue
            });

            this.dispatchEvent(new ShowToastEvent({
                title: 'Success',
                message: `Account ${account.Name} created`,
                variant: 'success'
            }));

            this.resetForm();
        } catch (error) {
            this.dispatchEvent(new ShowToastEvent({
                title: 'Error',
                message: error.body.message,
                variant: 'error'
            }));
        }
    }

    resetForm() {
        this.accountName = '';
        this.industry = '';
        this.revenue = 0;
    }
}
```

---

## Data Tables

### Lightning Datatable

```html
<template>
    <lightning-card title="Accounts">
        <lightning-datatable
            key-field="Id"
            data={accounts}
            columns={columns}
            sorted-by={sortedBy}
            sorted-direction={sortedDirection}
            onsort={handleSort}
            onrowaction={handleRowAction}
            show-row-number-column
            hide-checkbox-column={hideCheckbox}
            selected-rows={selectedRows}
            onrowselection={handleRowSelection}
            default-sort-direction="asc"
            enable-infinite-loading
            onloadmore={loadMoreData}>
        </lightning-datatable>
    </lightning-card>
</template>
```

```javascript
import { LightningElement, wire } from 'lwc';
import getAccounts from '@salesforce/apex/AccountController.getAccounts';

const COLUMNS = [
    {
        label: 'Account Name',
        fieldName: 'accountUrl',
        type: 'url',
        typeAttributes: {
            label: { fieldName: 'Name' },
            target: '_blank'
        },
        sortable: true
    },
    { label: 'Industry', fieldName: 'Industry', sortable: true },
    {
        label: 'Annual Revenue',
        fieldName: 'AnnualRevenue',
        type: 'currency',
        sortable: true,
        cellAttributes: { alignment: 'right' }
    },
    {
        label: 'Created Date',
        fieldName: 'CreatedDate',
        type: 'date',
        typeAttributes: {
            year: 'numeric',
            month: 'short',
            day: '2-digit'
        }
    },
    {
        type: 'action',
        typeAttributes: {
            rowActions: [
                { label: 'View', name: 'view' },
                { label: 'Edit', name: 'edit' },
                { label: 'Delete', name: 'delete' }
            ]
        }
    }
];

export default class AccountTable extends LightningElement {
    columns = COLUMNS;
    accounts = [];
    selectedRows = [];
    sortedBy = 'Name';
    sortedDirection = 'asc';
    hideCheckbox = false;

    @wire(getAccounts)
    wiredAccounts({ data, error }) {
        if (data) {
            this.accounts = data.map(account => ({
                ...account,
                accountUrl: `/lightning/r/Account/${account.Id}/view`
            }));
        }
    }

    handleSort(event) {
        const { fieldName, sortDirection } = event.detail;
        this.sortedBy = fieldName;
        this.sortedDirection = sortDirection;

        this.sortData(fieldName, sortDirection);
    }

    sortData(fieldName, direction) {
        const parseValue = (value) => {
            if (typeof value === 'string') return value.toLowerCase();
            return value || '';
        };

        const data = [...this.accounts];
        const reverse = direction === 'asc' ? 1 : -1;

        data.sort((a, b) => {
            const aValue = parseValue(a[fieldName]);
            const bValue = parseValue(b[fieldName]);
            return reverse * ((aValue > bValue) - (bValue > aValue));
        });

        this.accounts = data;
    }

    handleRowAction(event) {
        const action = event.detail.action;
        const row = event.detail.row;

        switch (action.name) {
            case 'view':
                this.navigateToRecord(row.Id);
                break;
            case 'edit':
                this.editRecord(row.Id);
                break;
            case 'delete':
                this.deleteRecord(row.Id);
                break;
        }
    }

    handleRowSelection(event) {
        this.selectedRows = event.detail.selectedRows;
    }

    loadMoreData(event) {
        // Implement infinite scrolling
    }
}
```

---

## Performance Optimization

### Best Practices

```javascript
// 1. Use wire service for cacheable data
@wire(getAccounts, { recordId: '$recordId' })
accounts;

// 2. Avoid unnecessary re-renders
// Bad - creates new array every render
get processedAccounts() {
    return this.accounts.map(a => ({ ...a, processed: true }));
}

// Good - cache computed values
_processedAccounts;
@api
get accounts() {
    return this._accounts;
}
set accounts(value) {
    this._accounts = value;
    this._processedAccounts = value.map(a => ({ ...a, processed: true }));
}
get processedAccounts() {
    return this._processedAccounts;
}

// 3. Debounce frequent operations
handleInput(event) {
    window.clearTimeout(this.delayTimeout);
    const searchKey = event.target.value;
    this.delayTimeout = setTimeout(() => {
        this.searchKey = searchKey;
    }, 300);
}

// 4. Use loading states
isLoading = true;
async loadData() {
    this.isLoading = true;
    try {
        this.data = await getData();
    } finally {
        this.isLoading = false;
    }
}
```

---

## When to Use

- **Wire service**: Read-only data that should be cached
- **Imperative calls**: User-triggered actions, data mutations
- **Custom events**: Parent-child communication
- **Lightning Message Service**: Cross-component communication, sibling components
- **Lightning Data Service**: Single record CRUD operations

## When NOT to Use

- **LWC for simple displays**: Use formula fields or Flow screen components
- **Complex forms**: Consider Screen Flow for admin-configurable forms
- **Heavy computation**: Move to Apex to avoid client-side performance issues
- **Non-reactive data**: Don't use @track for simple primitives (automatic since API v59)
