# TypeScript JSDoc

> Reference for: Code Documenter
> Load when: Documenting TypeScript/JavaScript code

## Function Documentation

```typescript
/**
 * Calculate total cost including tax.
 *
 * @param items - List of items to calculate total for
 * @param taxRate - Tax rate as decimal (e.g., 0.08 for 8%)
 * @returns Total cost including tax
 * @throws {Error} If taxRate is negative or items is empty
 *
 * @example
 * ```typescript
 * const total = calculateTotal(items, 0.08);
 * console.log(total); // 108.00
 * ```
 */
function calculateTotal(items: Item[], taxRate = 0): number {
```

## Class Documentation

```typescript
/**
 * Service for managing user operations.
 *
 * Handles CRUD operations and integrates with authentication system.
 *
 * @example
 * ```typescript
 * const service = new UserService(db, cache);
 * const user = await service.create(userData);
 * ```
 */
class UserService {
  /**
   * Create a new UserService instance.
   *
   * @param db - Database connection
   * @param cache - Redis cache client
   */
  constructor(
    private readonly db: Database,
    private readonly cache: Cache,
  ) {}
}
```

## Interface Documentation

```typescript
/**
 * User data transfer object.
 *
 * @interface UserDto
 */
interface UserDto {
  /** Unique user identifier */
  id: string;

  /** User's email address (unique) */
  email: string;

  /** User's display name */
  name: string;

  /** Account creation timestamp */
  createdAt: Date;
}
```

## Generic Types

```typescript
/**
 * Paginated response wrapper.
 *
 * @template T - Type of items in the data array
 */
interface PaginatedResponse<T> {
  /** Array of items for current page */
  data: T[];

  /** Total number of items across all pages */
  total: number;

  /** Current page number (1-indexed) */
  page: number;

  /** Number of items per page */
  limit: number;
}
```

## Async Functions

```typescript
/**
 * Fetch user by ID from database.
 *
 * @param id - User's unique identifier
 * @returns Promise resolving to user data or null if not found
 * @throws {DatabaseError} If connection fails
 *
 * @async
 */
async function findUserById(id: string): Promise<User | null> {
```

## Quick Reference

| Tag | Purpose | Example |
|-----|---------|---------|
| `@param` | Parameter description | `@param name - User's name` |
| `@returns` | Return value | `@returns User object` |
| `@throws` | Exception thrown | `@throws {Error} If invalid` |
| `@example` | Usage example | Code block |
| `@see` | Reference link | `@see UserService` |
| `@deprecated` | Mark deprecated | `@deprecated Use v2 instead` |
| `@template` | Generic type param | `@template T - Item type` |
| `@async` | Async function | Mark async |
| `@private` | Private member | Internal use |
| `@readonly` | Read-only property | Cannot modify |

## Common Patterns

```typescript
// Optional parameters
/** @param [options] - Optional configuration */

// Default values
/** @param [limit=10] - Items per page (default: 10) */

// Multiple types
/** @param input - Input value (string or number) */

// Callback parameters
/**
 * @callback FilterFn
 * @param item - Item to filter
 * @returns Whether item passes filter
 */
```
