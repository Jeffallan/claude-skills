# REST to GraphQL Migration Guide

> Reference for: GraphQL Architect
> Load when: REST to GraphQL, API migration, converting REST API, GraphQL adoption, modernizing REST endpoints, BFF pattern

---

## When to Use This Guide

**Migrate to GraphQL when:**
- Multiple round-trips required for complex UI views
- Over-fetching or under-fetching data is problematic
- Supporting diverse client needs (mobile, web, desktop)
- Team boundaries require federated API architecture
- Real-time subscriptions are core requirements
- Type safety across client-server boundary needed
- API versioning complexity is growing

**Success indicators:**
- Client applications make many sequential REST calls
- Different clients need different data shapes
- Mobile apps suffer from bandwidth constraints
- Frontend teams wait on backend API changes
- Multiple REST versions exist concurrently

## When NOT to Use GraphQL

**Stick with REST when:**
- Simple CRUD operations with stable clients
- File upload/download is primary use case
- HTTP caching is critical (CDN, browser cache)
- Team lacks GraphQL expertise and training budget
- Existing REST API is well-designed and sufficient
- Third-party integrations require REST endpoints
- Query complexity would create security risks

**Warning signs:**
- Team of 1-2 developers (operational overhead)
- Primarily server-to-server communication
- Static content delivery is the main requirement
- No complex data relationship navigation needed

---

## Concept Mapping: REST to GraphQL

| REST Concept | GraphQL Equivalent | Notes |
|--------------|-------------------|-------|
| GET /users | Query users | Read operations |
| GET /users/:id | Query user(id: ID!) | Single entity fetch |
| POST /users | Mutation createUser | Create operations |
| PUT /users/:id | Mutation updateUser | Update operations |
| DELETE /users/:id | Mutation deleteUser | Delete operations |
| PATCH /users/:id | Mutation updateUserPartial | Partial updates |
| Query params (?filter=...) | Field arguments | Filtering/sorting |
| URL path segments | Nested field selection | Data relationships |
| Multiple endpoints | Single query | Eliminate round-trips |
| Webhook callbacks | Subscriptions | Real-time updates |
| HTTP status codes | Errors array + data | Partial success model |
| API versioning | Schema evolution | Deprecation over versions |
| /users?include=posts | users { posts } | Eager loading control |
| Offset pagination | Cursor-based connections | Relay specification |
| Accept header | Operation selection | Content negotiation |
| OAuth/JWT tokens | Context authentication | Same auth patterns |

---

## Pattern 1: GET Endpoints to Queries

### REST Endpoint

```typescript
// GET /api/users/:id
interface UserResponse {
  id: string;
  name: string;
  email: string;
  created_at: string;
  posts: Array<{
    id: string;
    title: string;
    published: boolean;
  }>;
}

app.get('/api/users/:id', async (req, res) => {
  const user = await db.users.findById(req.params.id);
  const posts = await db.posts.findByUserId(user.id); // N+1 risk

  res.json({
    id: user.id,
    name: user.name,
    email: user.email,
    created_at: user.createdAt.toISOString(),
    posts: posts.map(p => ({
      id: p.id,
      title: p.title,
      published: p.published
    }))
  });
});
```

### GraphQL Schema

```graphql
type User {
  id: ID!
  name: String!
  email: String!
  createdAt: DateTime!
  posts: [Post!]!
}

type Post {
  id: ID!
  title: String!
  published: Boolean!
  author: User!
}

type Query {
  user(id: ID!): User
  users(filter: UserFilter, limit: Int = 20): [User!]!
}

input UserFilter {
  nameContains: String
  createdAfter: DateTime
}

scalar DateTime
```

### GraphQL Resolver with DataLoader

```typescript
import DataLoader from 'dataloader';
import { IResolvers } from '@graphql-tools/utils';

// Batch loading to prevent N+1 queries
const createPostsByUserIdLoader = (db: Database) =>
  new DataLoader<string, Post[]>(async (userIds) => {
    const posts = await db.posts.findByUserIds([...userIds]);

    // Group posts by userId
    const postsByUserId = userIds.map(id =>
      posts.filter(post => post.userId === id)
    );

    return postsByUserId;
  });

const createUserByIdLoader = (db: Database) =>
  new DataLoader<string, User>(async (ids) => {
    const users = await db.users.findByIds([...ids]);

    // Maintain order matching input ids
    return ids.map(id => users.find(user => user.id === id));
  });

interface Context {
  db: Database;
  loaders: {
    userById: DataLoader<string, User>;
    postsByUserId: DataLoader<string, Post[]>;
  };
}

const resolvers: IResolvers<any, Context> = {
  Query: {
    user: async (_, { id }, { loaders }) => {
      return loaders.userById.load(id);
    },

    users: async (_, { filter, limit }, { db }) => {
      return db.users.find(filter, { limit });
    },
  },

  User: {
    posts: async (user, _, { loaders }) => {
      // DataLoader batches and caches these calls
      return loaders.postsByUserId.load(user.id);
    },
  },

  Post: {
    author: async (post, _, { loaders }) => {
      return loaders.userById.load(post.userId);
    },
  },
};

// Apollo Server setup
import { ApolloServer } from '@apollo/server';
import { startStandaloneServer } from '@apollo/server/standalone';

const server = new ApolloServer<Context>({
  typeDefs,
  resolvers,
});

const { url } = await startStandaloneServer(server, {
  context: async ({ req }) => {
    const db = createDatabaseConnection();

    return {
      db,
      loaders: {
        userById: createUserByIdLoader(db),
        postsByUserId: createPostsByUserIdLoader(db),
      },
    };
  },
});
```

### Client Query Examples

```typescript
// Flexible field selection - client controls response shape
const MINIMAL_USER = gql`
  query GetUser($id: ID!) {
    user(id: $id) {
      id
      name
    }
  }
`;

const DETAILED_USER = gql`
  query GetUserWithPosts($id: ID!) {
    user(id: $id) {
      id
      name
      email
      createdAt
      posts {
        id
        title
        published
      }
    }
  }
`;

// Single query replacing multiple REST calls
const DASHBOARD_DATA = gql`
  query Dashboard($userId: ID!) {
    user(id: $userId) {
      name
      posts {
        id
        title
      }
    }

    # Would require separate REST endpoint
    users(filter: { createdAfter: "2025-01-01" }, limit: 5) {
      id
      name
    }
  }
`;
```

---

## Pattern 2: POST/PUT/DELETE to Mutations

### REST Endpoints

```typescript
// POST /api/users
app.post('/api/users', async (req, res) => {
  const { name, email, password } = req.body;

  if (!name || !email) {
    return res.status(400).json({ error: 'Missing required fields' });
  }

  const user = await db.users.create({ name, email, password });
  res.status(201).json(user);
});

// PUT /api/users/:id
app.put('/api/users/:id', async (req, res) => {
  const user = await db.users.update(req.params.id, req.body);
  res.json(user);
});

// DELETE /api/users/:id
app.delete('/api/users/:id', async (req, res) => {
  await db.users.delete(req.params.id);
  res.status(204).send();
});
```

### GraphQL Schema

```graphql
type Mutation {
  createUser(input: CreateUserInput!): CreateUserPayload!
  updateUser(input: UpdateUserInput!): UpdateUserPayload!
  deleteUser(id: ID!): DeleteUserPayload!
}

input CreateUserInput {
  name: String!
  email: String!
  password: String!
}

type CreateUserPayload {
  user: User
  errors: [UserError!]!
}

input UpdateUserInput {
  id: ID!
  name: String
  email: String
}

type UpdateUserPayload {
  user: User
  errors: [UserError!]!
}

type DeleteUserPayload {
  deletedId: ID
  errors: [UserError!]!
}

type UserError {
  field: String
  message: String!
  code: ErrorCode!
}

enum ErrorCode {
  VALIDATION_ERROR
  NOT_FOUND
  UNAUTHORIZED
  INTERNAL_ERROR
}
```

### GraphQL Mutation Resolvers

```typescript
const resolvers: IResolvers<any, Context> = {
  Mutation: {
    createUser: async (_, { input }, { db, user }) => {
      try {
        // Validation
        if (!isValidEmail(input.email)) {
          return {
            user: null,
            errors: [{
              field: 'email',
              message: 'Invalid email format',
              code: 'VALIDATION_ERROR',
            }],
          };
        }

        // Check for duplicate
        const existing = await db.users.findByEmail(input.email);
        if (existing) {
          return {
            user: null,
            errors: [{
              field: 'email',
              message: 'Email already registered',
              code: 'VALIDATION_ERROR',
            }],
          };
        }

        const hashedPassword = await bcrypt.hash(input.password, 10);
        const newUser = await db.users.create({
          name: input.name,
          email: input.email,
          password: hashedPassword,
        });

        return {
          user: newUser,
          errors: [],
        };
      } catch (error) {
        return {
          user: null,
          errors: [{
            message: 'Failed to create user',
            code: 'INTERNAL_ERROR',
          }],
        };
      }
    },

    updateUser: async (_, { input }, { db, user }) => {
      if (!user || user.id !== input.id) {
        return {
          user: null,
          errors: [{
            message: 'Unauthorized',
            code: 'UNAUTHORIZED',
          }],
        };
      }

      const updated = await db.users.update(input.id, {
        ...(input.name && { name: input.name }),
        ...(input.email && { email: input.email }),
      });

      return {
        user: updated,
        errors: [],
      };
    },

    deleteUser: async (_, { id }, { db, user }) => {
      if (!user || user.id !== id) {
        return {
          deletedId: null,
          errors: [{ message: 'Unauthorized', code: 'UNAUTHORIZED' }],
        };
      }

      await db.users.delete(id);

      return {
        deletedId: id,
        errors: [],
      };
    },
  },
};
```

### Client Mutation Examples

```typescript
const CREATE_USER = gql`
  mutation CreateUser($input: CreateUserInput!) {
    createUser(input: $input) {
      user {
        id
        name
        email
        createdAt
      }
      errors {
        field
        message
        code
      }
    }
  }
`;

// Usage with error handling
const [createUser] = useMutation(CREATE_USER);

const handleSubmit = async (formData) => {
  const { data } = await createUser({
    variables: {
      input: formData,
    },
  });

  if (data.createUser.errors.length > 0) {
    // Handle validation errors
    data.createUser.errors.forEach(error => {
      setFieldError(error.field, error.message);
    });
  } else {
    // Success - use the returned user
    navigate(`/users/${data.createUser.user.id}`);
  }
};
```

---

## Pattern 3: Pagination Migration

### REST Offset Pagination

```typescript
// GET /api/posts?page=2&limit=20
app.get('/api/posts', async (req, res) => {
  const page = parseInt(req.query.page) || 1;
  const limit = parseInt(req.query.limit) || 20;
  const offset = (page - 1) * limit;

  const posts = await db.posts.find({
    limit,
    offset,
  });

  const total = await db.posts.count();

  res.json({
    data: posts,
    pagination: {
      page,
      limit,
      total,
      totalPages: Math.ceil(total / limit),
    },
  });
});
```

### GraphQL Cursor-Based Pagination (Relay Connections)

```graphql
type Query {
  posts(
    first: Int
    after: String
    last: Int
    before: String
    filter: PostFilter
  ): PostConnection!
}

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

input PostFilter {
  published: Boolean
  authorId: ID
  titleContains: String
}
```

### Cursor Pagination Resolver

```typescript
import { encodeCursor, decodeCursor } from './cursor-utils';

const resolvers: IResolvers = {
  Query: {
    posts: async (_, args, { db }) => {
      const { first, after, last, before, filter } = args;

      // Validate pagination args
      if (first && last) {
        throw new Error('Cannot specify both first and last');
      }

      const limit = first || last || 20;
      const isForward = !!first || !last;

      // Decode cursor to get offset
      let offset = 0;
      if (after) {
        offset = decodeCursor(after) + 1;
      } else if (before) {
        offset = Math.max(0, decodeCursor(before) - limit);
      }

      // Fetch one extra to determine hasNextPage
      const posts = await db.posts.find({
        filter,
        limit: limit + 1,
        offset,
        orderBy: { createdAt: isForward ? 'DESC' : 'ASC' },
      });

      const hasMore = posts.length > limit;
      const nodes = hasMore ? posts.slice(0, limit) : posts;

      if (!isForward) {
        nodes.reverse();
      }

      const edges = nodes.map((post, index) => ({
        node: post,
        cursor: encodeCursor(offset + index),
      }));

      const totalCount = await db.posts.count(filter);

      return {
        edges,
        pageInfo: {
          hasNextPage: isForward ? hasMore : offset > 0,
          hasPreviousPage: !isForward ? hasMore : offset > 0,
          startCursor: edges[0]?.cursor,
          endCursor: edges[edges.length - 1]?.cursor,
        },
        totalCount,
      };
    },
  },
};

// cursor-utils.ts
export const encodeCursor = (offset: number): string => {
  return Buffer.from(`cursor:${offset}`).toString('base64');
};

export const decodeCursor = (cursor: string): number => {
  const decoded = Buffer.from(cursor, 'base64').toString('utf-8');
  return parseInt(decoded.replace('cursor:', ''));
};
```

### Client Pagination Query

```typescript
const POSTS_QUERY = gql`
  query Posts($first: Int!, $after: String, $filter: PostFilter) {
    posts(first: $first, after: $after, filter: $filter) {
      edges {
        node {
          id
          title
          published
          author {
            name
          }
        }
        cursor
      }
      pageInfo {
        hasNextPage
        endCursor
      }
      totalCount
    }
  }
`;

// Infinite scroll implementation
const PostList = () => {
  const { data, loading, fetchMore } = useQuery(POSTS_QUERY, {
    variables: { first: 20 },
  });

  const loadMore = () => {
    fetchMore({
      variables: {
        after: data.posts.pageInfo.endCursor,
      },
      updateQuery: (prev, { fetchMoreResult }) => {
        if (!fetchMoreResult) return prev;

        return {
          posts: {
            ...fetchMoreResult.posts,
            edges: [
              ...prev.posts.edges,
              ...fetchMoreResult.posts.edges,
            ],
          },
        };
      },
    });
  };

  return (
    <div>
      {data?.posts.edges.map(({ node }) => (
        <PostCard key={node.id} post={node} />
      ))}

      {data?.posts.pageInfo.hasNextPage && (
        <button onClick={loadMore}>Load More</button>
      )}
    </div>
  );
};
```

---

## Pattern 4: Authentication Translation

### REST Authentication

```typescript
// REST middleware
app.use(async (req, res, next) => {
  const token = req.headers.authorization?.replace('Bearer ', '');

  if (token) {
    try {
      const payload = jwt.verify(token, process.env.JWT_SECRET);
      req.user = await db.users.findById(payload.userId);
    } catch (error) {
      return res.status(401).json({ error: 'Invalid token' });
    }
  }

  next();
});
```

### GraphQL Authentication Context

```typescript
import { ApolloServer } from '@apollo/server';
import { GraphQLError } from 'graphql';

interface AuthContext {
  user: User | null;
  requireAuth: () => User;
}

const server = new ApolloServer<AuthContext>({
  typeDefs,
  resolvers,
});

await startStandaloneServer(server, {
  context: async ({ req }) => {
    const token = req.headers.authorization?.replace('Bearer ', '');
    let user: User | null = null;

    if (token) {
      try {
        const payload = jwt.verify(token, process.env.JWT_SECRET);
        user = await db.users.findById(payload.userId);
      } catch (error) {
        // Token invalid - continue with user = null
      }
    }

    return {
      user,
      db,
      loaders: createLoaders(db),

      // Helper to enforce authentication
      requireAuth: (): User => {
        if (!user) {
          throw new GraphQLError('Authentication required', {
            extensions: { code: 'UNAUTHENTICATED' },
          });
        }
        return user;
      },
    };
  },
});
```

### Field-Level Authorization

```typescript
import { GraphQLFieldResolver } from 'graphql';

// Authorization directive
const resolvers: IResolvers = {
  Query: {
    me: (_, __, { requireAuth }) => {
      const user = requireAuth();
      return user;
    },

    users: (_, __, { user }) => {
      // Optional auth - different data based on auth state
      if (user?.role === 'ADMIN') {
        return db.users.findAll();
      }

      // Public view - limited fields
      return db.users.findPublic();
    },
  },

  User: {
    email: (user, _, { user: currentUser }) => {
      // Field-level privacy
      if (currentUser?.id === user.id || currentUser?.role === 'ADMIN') {
        return user.email;
      }
      return null;
    },
  },
};
```

---

## BFF (Backend for Frontend) Architecture

### Multi-Client GraphQL Gateway

```typescript
// Schema stitching for different clients
import { stitchSchemas } from '@graphql-tools/stitch';

// Mobile-optimized schema
const mobileSchema = makeExecutableSchema({
  typeDefs: `
    type Query {
      # Denormalized for fewer round-trips
      dashboard: MobileDashboard!
    }

    type MobileDashboard {
      user: User!
      recentPosts: [Post!]!
      notifications: [Notification!]!
      # All data needed for mobile home screen
    }
  `,
  resolvers: mobileResolvers,
});

// Web-optimized schema
const webSchema = makeExecutableSchema({
  typeDefs: `
    type Query {
      # Granular for efficient caching
      user(id: ID!): User
      posts(filter: PostFilter): PostConnection!
      notifications(unreadOnly: Boolean): [Notification!]!
    }
  `,
  resolvers: webResolvers,
});

// Client-specific servers
const mobileServer = new ApolloServer({
  schema: mobileSchema,
  introspection: true,
});

const webServer = new ApolloServer({
  schema: webSchema,
  introspection: true,
});

// Route based on client header
app.use('/graphql', (req, res) => {
  const client = req.headers['x-client-type'];

  if (client === 'mobile') {
    return mobileServer.handleRequest(req, res);
  }

  return webServer.handleRequest(req, res);
});
```

---

## Incremental Migration Strategy

### Phase 1: GraphQL Wrapper (Weeks 1-2)

```typescript
// Wrap existing REST endpoints with GraphQL
const resolvers: IResolvers = {
  Query: {
    user: async (_, { id }) => {
      // Call existing REST API internally
      const response = await fetch(`http://localhost:3000/api/users/${id}`);
      return response.json();
    },
  },
};

// Allows GraphQL adoption without backend rewrites
// Clients can start using GraphQL immediately
```

### Phase 2: Parallel Implementation (Weeks 3-6)

```typescript
// Implement GraphQL resolvers with direct DB access
// Keep REST endpoints running
const resolvers: IResolvers = {
  Query: {
    user: async (_, { id }, { db }) => {
      // New implementation - direct database
      return db.users.findById(id);
    },
  },
};

// Feature flag to route traffic
const USE_GRAPHQL = process.env.GRAPHQL_ENABLED === 'true';

app.get('/api/users/:id', async (req, res) => {
  if (USE_GRAPHQL) {
    // Forward to GraphQL
    const result = await graphqlServer.executeOperation({
      query: `query GetUser($id: ID!) { user(id: $id) { ... } }`,
      variables: { id: req.params.id },
    });
    return res.json(result.data?.user);
  }

  // Legacy REST implementation
  const user = await db.users.findById(req.params.id);
  res.json(user);
});
```

### Phase 3: Client Migration (Weeks 7-12)

```typescript
// Gradual client migration with monitoring
import { setContext } from '@apollo/client/link/context';

const migrationLink = setContext((_, { headers }) => {
  return {
    headers: {
      ...headers,
      'x-graphql-migration': 'phase-3',
    },
  };
});

// A/B test GraphQL vs REST in production
// Monitor performance, errors, client satisfaction
```

### Phase 4: REST Deprecation (Week 13+)

```typescript
// Deprecate REST endpoints gradually
app.get('/api/users/:id', (req, res) => {
  res.status(410).json({
    error: 'This endpoint is deprecated',
    message: 'Please use GraphQL endpoint at /graphql',
    migrationGuide: 'https://docs.example.com/graphql-migration',
    sunsetDate: '2025-06-01',
  });
});

// Eventually remove REST entirely
```

---

## Common Pitfalls

### Pitfall 1: N+1 Query Problem

```typescript
// BAD - Causes N+1 queries
const resolvers = {
  User: {
    posts: async (user, _, { db }) => {
      // Called once per user - N queries if you fetch N users
      return db.posts.findByUserId(user.id);
    },
  },
};

// GOOD - Use DataLoader
const resolvers = {
  User: {
    posts: async (user, _, { loaders }) => {
      // Batched and cached
      return loaders.postsByUserId.load(user.id);
    },
  },
};
```

### Pitfall 2: Exposing Database Schema Directly

```typescript
// BAD - Tightly coupled to database
type User {
  user_id: Int!          # Database column name
  first_name: String     # Database structure leaks
  last_name: String
  created_at: String     # Raw DB type
}

// GOOD - API-first design
type User {
  id: ID!                # Abstract identifier
  name: String!          # Computed from first + last
  createdAt: DateTime!   # Proper type
}
```

### Pitfall 3: Missing Error Handling

```typescript
// BAD - Errors kill entire response
const resolvers = {
  Query: {
    dashboard: async () => {
      const user = await fetchUser();     // Throws on error
      const posts = await fetchPosts();   // Never reached if user fails
      return { user, posts };
    },
  },
};

// GOOD - Partial success model
const resolvers = {
  Query: {
    dashboard: async () => {
      return {};  // Return empty object
    },
  },

  Dashboard: {
    user: async (_, __, context) => {
      try {
        return await fetchUser();
      } catch (error) {
        return null;  // Client still gets posts
      }
    },

    posts: async () => {
      try {
        return await fetchPosts();
      } catch (error) {
        return [];  // Graceful degradation
      }
    },
  },
};
```

### Pitfall 4: Ignoring Query Complexity

```typescript
// BAD - No limits on query depth/complexity
// Client can write expensive queries that DOS the server

// GOOD - Implement complexity limits
import { createComplexityLimitRule } from 'graphql-validation-complexity';

const server = new ApolloServer({
  typeDefs,
  resolvers,
  validationRules: [
    createComplexityLimitRule(1000, {
      onCost: (cost) => {
        console.log('Query cost:', cost);
      },
    }),
  ],
});

// Assign costs to fields
const typeDefs = `
  type Query {
    users: [User!]! @cost(complexity: 10)
    user(id: ID!): User @cost(complexity: 1)
  }

  type User {
    posts: [Post!]! @cost(complexity: 5, multipliers: ["first"])
  }
`;
```

### Pitfall 5: Over-Normalization

```typescript
// BAD - Too granular, requires many queries
type Query {
  userName(id: ID!): String
  userEmail(id: ID!): String
  userPosts(userId: ID!): [Post!]!
}

// GOOD - Logical grouping
type Query {
  user(id: ID!): User
}

type User {
  name: String!
  email: String!
  posts: [Post!]!
}
```

---

## Cross-References

**Related Skills:**
- **graphql-architect/references/schema-design.md** - Type system patterns and schema structure
- **graphql-architect/references/federation-guide.md** - Multi-service GraphQL architecture
- **backend-developer** - REST API implementation patterns
- **api-designer** - API design principles and consistency

**When to Escalate:**
- Federation across microservices → See federation-guide.md
- Schema design questions → See schema-design.md
- Complex subscription requirements → Consult graphql-architect
- Performance optimization → Partner with performance-engineer

---

## Migration Checklist

- [ ] Identify most-used REST endpoints
- [ ] Map REST resources to GraphQL types
- [ ] Design schema following best practices
- [ ] Implement DataLoaders for all relations
- [ ] Add authentication/authorization
- [ ] Implement pagination (cursor-based)
- [ ] Set up query complexity limits
- [ ] Create client migration plan
- [ ] Monitor performance metrics
- [ ] Document GraphQL queries for clients
- [ ] Train team on GraphQL patterns
- [ ] Plan REST endpoint sunset timeline

**Migration complete when:**
- All critical paths use GraphQL
- REST endpoints deprecated with sunset dates
- Client applications fully migrated
- Performance metrics meet or exceed REST baseline
- Team confident in GraphQL maintenance
