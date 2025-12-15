# Apollo Federation

> Reference for: GraphQL Architect
> Load when: Apollo Federation, subgraphs, entities, directives

## Subgraph Setup

```typescript
// users-subgraph/schema.graphql
extend schema
  @link(url: "https://specs.apollo.dev/federation/v2.5", import: ["@key", "@shareable"])

type User @key(fields: "id") {
  id: ID!
  email: String!
  username: String!
  createdAt: DateTime!
}

type Query {
  user(id: ID!): User
  users: [User!]!
}

// users-subgraph/resolvers.ts
import { ApolloServer } from '@apollo/server';
import { buildSubgraphSchema } from '@apollo/subgraph';
import { readFileSync } from 'fs';

const typeDefs = readFileSync('./schema.graphql', 'utf8');

const resolvers = {
  User: {
    __resolveReference: async (
      reference: { id: string },
      context: Context
    ): Promise<User> => {
      return context.dataSources.users.findById(reference.id);
    },
  },

  Query: {
    user: async (parent, args: { id: string }, context: Context) => {
      return context.dataSources.users.findById(args.id);
    },
    users: async (parent, args, context: Context) => {
      return context.dataSources.users.findAll();
    },
  },
};

const server = new ApolloServer({
  schema: buildSubgraphSchema([{ typeDefs, resolvers }]),
});
```

## Entity Keys and References

```graphql
# products-subgraph/schema.graphql
extend schema
  @link(url: "https://specs.apollo.dev/federation/v2.5", import: [
    "@key",
    "@shareable",
    "@interfaceObject"
  ])

# Single key field
type Product @key(fields: "id") {
  id: ID!
  name: String!
  price: Float!
  sku: String! @shareable
}

# Composite key
type Variant @key(fields: "productId sku") {
  productId: ID!
  sku: String!
  size: String!
  color: String!
}

# Multiple keys (different ways to identify)
type Review @key(fields: "id") @key(fields: "productId authorId") {
  id: ID!
  productId: ID!
  authorId: ID!
  rating: Int!
  content: String!
}
```

## Extending Types Across Subgraphs

```graphql
# users-subgraph: owns User
type User @key(fields: "id") {
  id: ID!
  email: String!
  username: String!
}

# posts-subgraph: extends User with posts
extend type User @key(fields: "id") {
  id: ID! @external
  posts: [Post!]!
}

type Post @key(fields: "id") {
  id: ID!
  title: String!
  content: String!
  authorId: ID!
  author: User!
}
```

```typescript
// posts-subgraph/resolvers.ts
const resolvers = {
  User: {
    // Reference resolver: fetch User stub by id
    __resolveReference: async (
      reference: { id: string },
      context: Context
    ) => {
      return { id: reference.id };
    },

    // Field resolver: resolve posts for User
    posts: async (user: { id: string }, args, context: Context) => {
      return context.dataSources.posts.findByAuthor(user.id);
    },
  },

  Post: {
    // Resolve author as User entity reference
    author: (post: Post) => {
      return { __typename: 'User', id: post.authorId };
    },
  },
};
```

## Federation Directives

```graphql
extend schema
  @link(url: "https://specs.apollo.dev/federation/v2.5", import: [
    "@key",
    "@requires",
    "@provides",
    "@external",
    "@shareable",
    "@override",
    "@inaccessible",
    "@tag"
  ])

# @key: Define entity with primary key
type Product @key(fields: "id") {
  id: ID!
  name: String!
}

# @external: Field defined in another subgraph
extend type User @key(fields: "id") {
  id: ID! @external
  email: String! @external
  isVerified: Boolean! @external
}

# @requires: Field needs external data
extend type User @key(fields: "id") {
  id: ID! @external
  email: String! @external
  isVerified: Boolean! @external
  # Can only compute if we have email and isVerified
  canPost: Boolean! @requires(fields: "email isVerified")
}

# @provides: Optimization hint
type Post @key(fields: "id") {
  id: ID!
  author: User! @provides(fields: "username")
}

# @shareable: Field can be resolved by multiple subgraphs
type Product @key(fields: "id") {
  id: ID!
  sku: String! @shareable
  name: String!
}

# @override: Migration between subgraphs
type Product @key(fields: "id") {
  id: ID!
  # Override from legacy-subgraph
  price: Float! @override(from: "legacy-subgraph")
}

# @inaccessible: Hide from supergraph
type User @key(fields: "id") {
  id: ID!
  email: String!
  internalId: String! @inaccessible
}

# @tag: Organize schema
type Query {
  products: [Product!]! @tag(name: "public")
  adminUsers: [User!]! @tag(name: "admin")
}
```

## Gateway Configuration

```typescript
// gateway/server.ts
import { ApolloGateway, IntrospectAndCompose } from '@apollo/gateway';
import { ApolloServer } from '@apollo/server';

const gateway = new ApolloGateway({
  supergraphSdl: new IntrospectAndCompose({
    subgraphs: [
      { name: 'users', url: 'http://localhost:4001/graphql' },
      { name: 'posts', url: 'http://localhost:4002/graphql' },
      { name: 'products', url: 'http://localhost:4003/graphql' },
    ],
    // Poll for schema updates
    pollIntervalInMs: 10000,
  }),

  // Error handling
  serviceHealthCheck: true,

  // Query planning debug
  debug: process.env.NODE_ENV === 'development',
});

const server = new ApolloServer({
  gateway,

  // Context propagation to subgraphs
  context: async ({ req }) => {
    const token = req.headers.authorization || '';
    return { token };
  },
});

await server.listen(4000);
console.log('Gateway ready at http://localhost:4000');
```

## Managed Federation (Apollo Studio)

```typescript
// gateway/server.ts with managed federation
import { ApolloGateway } from '@apollo/gateway';
import { ApolloServer } from '@apollo/server';

const gateway = new ApolloGateway({
  // No subgraph URLs needed - fetched from Apollo Studio
  // Schema composition happens in Apollo Studio
  async supergraphSdl({ update }) {
    // Fetch from Apollo Uplink
    const supergraphSdl = await fetchSupergraphSdl();
    return {
      supergraphSdl,
      cleanup: async () => {},
    };
  },
});

// Subgraph reporting to Apollo Studio
import { ApolloServerPluginInlineTrace } from '@apollo/server/plugin/inlineTrace';

const subgraphServer = new ApolloServer({
  schema: buildSubgraphSchema([{ typeDefs, resolvers }]),
  plugins: [
    ApolloServerPluginInlineTrace(),
  ],
});
```

## Value Types vs Entities

```graphql
# Value type: no @key, resolved entirely by one subgraph
type Address {
  street: String!
  city: String!
  country: String!
  postalCode: String!
}

# Entity: has @key, can be extended by other subgraphs
type User @key(fields: "id") {
  id: ID!
  email: String!
  # Value type embedded in entity
  address: Address
}

# Another subgraph can extend User but not Address
extend type User @key(fields: "id") {
  id: ID! @external
  orders: [Order!]!
}
```

## Interface Objects

```graphql
# accounts-subgraph
type User implements Account @key(fields: "id") {
  id: ID!
  email: String!
  role: String!
}

type AdminUser implements Account @key(fields: "id") {
  id: ID!
  email: String!
  role: String!
  permissions: [String!]!
}

interface Account {
  id: ID!
  email: String!
  role: String!
}

# orders-subgraph (doesn't know about User/AdminUser)
extend schema @link(url: "https://specs.apollo.dev/federation/v2.5", import: ["@key", "@interfaceObject"])

type Order @key(fields: "id") {
  id: ID!
  account: Account!
}

# Use @interfaceObject to reference Account without knowing implementations
type Account @key(fields: "id") @interfaceObject {
  id: ID!
}
```

## Query Planning Optimization

```graphql
# Inefficient: requires multiple roundtrips
type Query {
  user(id: ID!): User
}

type User @key(fields: "id") {
  id: ID!
  posts: [Post!]!
}

extend type Post @key(fields: "id") {
  id: ID! @external
  author: User!
}

# Better: provide data to avoid extra fetch
type Post @key(fields: "id") {
  id: ID!
  authorId: ID!
  # Optimization: provide username directly
  author: User! @provides(fields: "username")
}

# Gateway can fulfill some User fields from Post subgraph
# without fetching from User subgraph
```

## Error Handling in Federation

```typescript
const resolvers = {
  User: {
    __resolveReference: async (
      reference: { id: string },
      context: Context
    ) => {
      try {
        const user = await context.dataSources.users.findById(reference.id);
        if (!user) {
          // Return null for missing entity (soft error)
          return null;
        }
        return user;
      } catch (error) {
        // Hard error propagates to client
        throw new GraphQLError('Failed to resolve user', {
          extensions: {
            code: 'USER_RESOLUTION_FAILED',
            userId: reference.id,
          },
        });
      }
    },
  },
};
```

## Federation Best Practices

1. **Entity Design**: Use @key for types that need to be extended
2. **Subgraph Boundaries**: Align with team/service boundaries
3. **Shared Types**: Use @shareable for truly shared fields
4. **Migration**: Use @override for gradual subgraph migration
5. **Performance**: Use @provides to optimize query planning
6. **Value Types**: Use plain types for embedded data
7. **Composition**: Test schema composition in CI/CD
8. **Versioning**: Use managed federation for safe deployments
9. **Monitoring**: Track query planning and resolver performance
10. **Documentation**: Document entity ownership and extension patterns
