# GraphQL Schema Design

> Reference for: GraphQL Architect
> Load when: Creating types, interfaces, unions, enums, input types

## Object Types

```graphql
"""
User account with authentication and profile information.
All users must have a unique email address.
"""
type User {
  "Unique user identifier"
  id: ID!
  "User's email address (unique)"
  email: String!
  "Display name (optional)"
  username: String
  "Account creation timestamp"
  createdAt: DateTime!
  "User's posts (paginated)"
  posts(first: Int = 10, after: String): PostConnection!
  "User's profile (nullable if not completed)"
  profile: Profile
}

type Profile {
  id: ID!
  bio: String
  avatarUrl: URL
  website: URL
  location: String
}

type Post {
  id: ID!
  title: String!
  content: String!
  author: User!
  publishedAt: DateTime
  status: PostStatus!
  tags: [Tag!]!
  comments(first: Int, after: String): CommentConnection!
}
```

## Interfaces

```graphql
"""
Common interface for all content that can be timestamped
"""
interface Timestamped {
  id: ID!
  createdAt: DateTime!
  updatedAt: DateTime!
}

"""
Interface for searchable content
"""
interface Searchable {
  id: ID!
  title: String!
  description: String
}

type Article implements Timestamped & Searchable {
  id: ID!
  title: String!
  description: String
  content: String!
  createdAt: DateTime!
  updatedAt: DateTime!
  author: User!
}

type Video implements Timestamped & Searchable {
  id: ID!
  title: String!
  description: String
  url: URL!
  duration: Int!
  createdAt: DateTime!
  updatedAt: DateTime!
  uploader: User!
}

# Query returning interface
type Query {
  search(query: String!): [Searchable!]!
}
```

## Union Types

```graphql
"""
Result of a content search - can be Article, Video, or Podcast
"""
union SearchResult = Article | Video | Podcast

"""
Notification types that users can receive
"""
union Notification = CommentNotification | LikeNotification | FollowNotification

type CommentNotification {
  id: ID!
  comment: Comment!
  post: Post!
  createdAt: DateTime!
}

type LikeNotification {
  id: ID!
  liker: User!
  post: Post!
  createdAt: DateTime!
}

type Query {
  searchContent(query: String!): [SearchResult!]!
  notifications(first: Int): [Notification!]!
}
```

## Enums

```graphql
"""
Post publication status
"""
enum PostStatus {
  DRAFT
  PUBLISHED
  ARCHIVED
  DELETED
}

"""
User role for authorization
"""
enum UserRole {
  ADMIN
  MODERATOR
  USER
  GUEST
}

"""
Sort direction for queries
"""
enum SortOrder {
  ASC
  DESC
}

type Query {
  posts(
    status: PostStatus
    orderBy: SortOrder = DESC
  ): [Post!]!
}
```

## Input Types

```graphql
"""
Input for creating a new user
"""
input CreateUserInput {
  email: String!
  password: String!
  username: String
  profile: ProfileInput
}

input ProfileInput {
  bio: String
  avatarUrl: URL
  website: URL
  location: String
}

"""
Input for updating a post
"""
input UpdatePostInput {
  title: String
  content: String
  status: PostStatus
  tags: [ID!]
}

"""
Pagination and filtering input
"""
input PostFilterInput {
  status: PostStatus
  authorId: ID
  tags: [String!]
  search: String
  createdAfter: DateTime
  createdBefore: DateTime
}

type Mutation {
  createUser(input: CreateUserInput!): User!
  updatePost(id: ID!, input: UpdatePostInput!): Post!
}

type Query {
  posts(filter: PostFilterInput, first: Int, after: String): PostConnection!
}
```

## Custom Scalars

```graphql
"""
ISO 8601 date-time string
"""
scalar DateTime

"""
Valid URL string
"""
scalar URL

"""
Valid email address
"""
scalar Email

"""
JSON object
"""
scalar JSON

"""
Positive integer
"""
scalar PositiveInt

type User {
  id: ID!
  email: Email!
  createdAt: DateTime!
  website: URL
  metadata: JSON
  age: PositiveInt
}
```

## Pagination Patterns

```graphql
"""
Cursor-based pagination (Relay specification)
"""
type PostConnection {
  edges: [PostEdge!]!
  pageInfo: PageInfo!
  totalCount: Int!
}

type PostEdge {
  node: Post!
  cursor: String!
}

type PageInfo {
  hasNextPage: Boolean!
  hasPreviousPage: Boolean!
  startCursor: String
  endCursor: String
}

type Query {
  posts(
    first: Int
    after: String
    last: Int
    before: String
  ): PostConnection!
}
```

## Nullable vs Non-Nullable Best Practices

```graphql
type User {
  # Non-nullable: guaranteed to exist
  id: ID!
  email: String!
  createdAt: DateTime!

  # Nullable: optional or may not exist yet
  username: String
  bio: String
  avatarUrl: URL

  # Non-null list of nullable items
  # List always exists but can be empty, items can be null
  tags: [String]!

  # Non-null list of non-null items
  # List always exists, all items guaranteed non-null
  roles: [UserRole!]!

  # Nullable list of non-null items
  # List may be null, but if exists, all items non-null
  posts: [Post!]
}

type Query {
  # Non-null: query always returns result (empty list if none)
  users: [User!]!

  # Nullable: may return null if not found
  user(id: ID!): User

  # Non-null: guaranteed to return result or error
  currentUser: User!
}
```

## Field Deprecation

```graphql
type User {
  id: ID!
  email: String!

  # Deprecated field with migration path
  name: String @deprecated(reason: "Use 'username' instead")
  username: String

  # Deprecated with specific date
  legacyId: String @deprecated(
    reason: "Migrating to UUID. Will be removed 2025-06-01"
  )
}
```

## Schema Documentation

```graphql
"""
User represents an authenticated account in the system.
Users can create posts, comments, and interact with content.

Example query:
```
query GetUser {
  user(id: "123") {
    email
    username
    posts(first: 10) {
      edges {
        node {
          title
        }
      }
    }
  }
}
```
"""
type User {
  "Unique identifier for the user"
  id: ID!

  "Email address (must be unique across all users)"
  email: String!

  "Optional display name (defaults to email if not set)"
  username: String
}
```

## Design Principles

1. **Nullable Fields**: Make fields nullable by default unless guaranteed to exist
2. **List Fields**: Use `[Type!]!` for lists that always exist with non-null items
3. **Documentation**: Document all types and fields with descriptions
4. **Naming**: Use camelCase for fields, PascalCase for types
5. **Interfaces**: Use interfaces for shared fields across types
6. **Unions**: Use unions for polymorphic return types
7. **Input Types**: Create separate input types for mutations
8. **Scalars**: Use custom scalars for domain-specific types
9. **Deprecation**: Mark deprecated fields, provide migration path
10. **Examples**: Include example queries in documentation
