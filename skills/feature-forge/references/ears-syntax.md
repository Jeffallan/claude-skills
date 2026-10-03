# EARS Syntax

## EARS Format

Easy Approach to Requirements Syntax for clear, unambiguous requirements.

### Basic Pattern

```
While <precondition>, when <trigger>, the system shall <response>.
```

### Pattern Types

**Ubiquitous (Always True)**
```
The system shall [action].
```
Example: The system shall encrypt all passwords using bcrypt.

**Event-Driven**
```
When [trigger], the system shall [action].
```
Example: When the user clicks "Submit", the system shall save the form data.

**State-Driven**
```
While [state], the system shall [action].
```
Example: While the user is logged in, the system shall display the dashboard.

**Conditional (Most Common)**
```
While [state], when [trigger], the system shall [action].
```
Example: While the cart contains items, when the user clicks "Checkout", the system shall navigate to the payment page.

**Optional**
```
Where [feature enabled], the system shall [action].
```
Example: Where two-factor authentication is enabled, the system shall require a verification code.

## Examples by Domain

### Authentication

```markdown
**FR-AUTH-001**: Login
While credentials are valid, when POST /auth/login is called,
the system shall return JWT access token (15min) and refresh token (7d).

**FR-AUTH-002**: Invalid Login
When invalid credentials are provided,
the system shall return 401 and increment failed login counter.

**FR-AUTH-003**: Account Lockout
While failed login count exceeds 5, when login is attempted,
the system shall reject the attempt and require password reset.
```

### E-commerce

```markdown
**FR-CART-001**: Add to Cart
While user is logged in, when they click "Add to Cart",
the system shall add the item and update the cart badge count.

**FR-CART-002**: Apply Coupon
While the cart contains items, when a valid coupon code is applied,
the system shall reduce the total by the discount amount.

**FR-ORDER-001**: Checkout
While payment method is valid, when user confirms order,
the system shall create order, charge payment, and send confirmation email.
```

### Data Management

```markdown
**FR-EXPORT-001**: CSV Export
While user has data access permission, when they click "Export",
the system shall generate a CSV file and initiate download.

**FR-DELETE-001**: Soft Delete
When a resource is deleted,
the system shall set deleted_at timestamp instead of removing the record.
```

## Quick Reference

| Type | Structure | Use When |
|------|-----------|----------|
| Ubiquitous | shall [action] | Always applies |
| Event | When [X], shall | On trigger |
| State | While [X], shall | Continuous state |
| Conditional | While [X], when [Y], shall | State + trigger |
| Optional | Where [X], shall | Feature flag |
