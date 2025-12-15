# GraphQL Security

> Reference for: GraphQL Architect
> Load when: Query depth limiting, complexity analysis, authentication

## Query Depth Limiting

```typescript
import depthLimit from 'graphql-depth-limit';
import { ApolloServer } from '@apollo/server';

const server = new ApolloServer({
  typeDefs,
  resolvers,
  validationRules: [
    // Limit query depth to 7 levels
    depthLimit(7, {
      ignore: [
        '_service',
        '_entities',
        'pageInfo',
        'edges',
        'node',
      ],
    }),
  ],
});

// Example: This query would be rejected (depth > 7)
// query TooDeep {
//   user {
//     posts {
//       author {
//         posts {
//           author {
//             posts {
//               author {
//                 posts {  # Depth 7
//                   author { # Depth 8 - REJECTED
//                     name
//                   }
//                 }
//               }
//             }
//           }
//         }
//       }
//     }
//   }
// }
```

## Query Complexity Analysis

```typescript
import { createComplexityRule } from 'graphql-validation-complexity';
import { GraphQLError } from 'graphql';

// Define field complexities
const complexityRule = createComplexityRule({
  maximumComplexity: 1000,
  variables: {},
  onCost: (cost) => {
    console.log('Query cost:', cost);
  },
  createError(cost, documentNode) {
    return new GraphQLError(
      `Query too complex: ${cost}. Maximum allowed: 1000`,
      {
        extensions: {
          code: 'COMPLEXITY_LIMIT_EXCEEDED',
          cost,
          limit: 1000,
        },
      }
    );
  },
  estimators: [
    // Simple field: cost 1
    {
      estimateComplexity: ({ type }) => {
        if (type.toString() === 'String' || type.toString() === 'Int') {
          return 1;
        }
        return 0;
      },
    },
    // List field: cost based on `first` argument
    {
      estimateComplexity: ({ args, childComplexity }) => {
        const first = args.first || 10;
        return first * childComplexity;
      },
    },
  ],
});

const server = new ApolloServer({
  typeDefs,
  resolvers,
  validationRules: [complexityRule],
});
```

## Custom Complexity Directives

```graphql
# Schema definition
directive @cost(
  complexity: Int!
  multipliers: [String!]
) on FIELD_DEFINITION

type Query {
  # Simple query: cost 1
  user(id: ID!): User

  # List query: cost multiplied by `first` argument
  users(first: Int = 10): [User!]! @cost(complexity: 1, multipliers: ["first"])

  # Expensive query: cost 50
  analytics: Analytics! @cost(complexity: 50)
}

type User {
  id: ID!
  name: String! @cost(complexity: 1)

  # Related list: cost multiplied by `first`
  posts(first: Int = 10): [Post!]! @cost(complexity: 2, multipliers: ["first"])

  # Expensive computation
  recommendations: [User!]! @cost(complexity: 20)
}
```

```typescript
// Complexity calculator implementation
import { DirectiveNode } from 'graphql';

function calculateComplexity(
  field: any,
  args: Record<string, any>,
  childComplexity: number
): number {
  const costDirective = field.astNode?.directives?.find(
    (d: DirectiveNode) => d.name.value === 'cost'
  );

  if (!costDirective) {
    return 1 + childComplexity;
  }

  const complexity =
    costDirective.arguments?.find((a) => a.name.value === 'complexity')
      ?.value.value || 1;

  const multipliers =
    costDirective.arguments?.find((a) => a.name.value === 'multipliers')
      ?.value.values || [];

  let cost = complexity;
  for (const multiplier of multipliers) {
    const argValue = args[multiplier.value] || 1;
    cost *= argValue;
  }

  return cost + childComplexity;
}
```

## Rate Limiting

```typescript
import rateLimit from 'express-rate-limit';
import RedisStore from 'rate-limit-redis';
import Redis from 'ioredis';

// IP-based rate limiting
const limiter = rateLimit({
  store: new RedisStore({
    client: new Redis(),
  }),
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100, // 100 requests per window
  message: 'Too many requests from this IP',
  standardHeaders: true,
  legacyHeaders: false,
});

app.use('/graphql', limiter);

// User-based rate limiting (more sophisticated)
import { RateLimiterRedis } from 'rate-limiter-flexible';

const rateLimiter = new RateLimiterRedis({
  storeClient: new Redis(),
  points: 1000, // Number of points
  duration: 60, // Per 60 seconds
  blockDuration: 60 * 5, // Block for 5 minutes if exceeded
});

// In context creation
const server = new ApolloServer({
  typeDefs,
  resolvers,
  context: async ({ req }) => {
    const userId = getUserId(req);

    try {
      await rateLimiter.consume(userId, 1);
    } catch (error) {
      throw new GraphQLError('Rate limit exceeded', {
        extensions: {
          code: 'RATE_LIMIT_EXCEEDED',
          retryAfter: error.msBeforeNext / 1000,
        },
      });
    }

    return { userId };
  },
});
```

## Authentication

```typescript
import jwt from 'jsonwebtoken';
import { GraphQLError } from 'graphql';

// JWT verification
function verifyToken(token: string): User | null {
  try {
    const decoded = jwt.verify(token, process.env.JWT_SECRET!);
    return decoded as User;
  } catch (error) {
    return null;
  }
}

// Context with authentication
const server = new ApolloServer({
  typeDefs,
  resolvers,
  context: async ({ req }): Promise<Context> => {
    const authHeader = req.headers.authorization || '';
    const token = authHeader.replace('Bearer ', '');

    let user: User | null = null;
    if (token) {
      user = verifyToken(token);
    }

    return {
      user,
      dataSources: createDataSources(),
    };
  },
});

// Protected resolvers
const resolvers = {
  Query: {
    me: (parent, args, context: Context) => {
      if (!context.user) {
        throw new GraphQLError('Unauthorized', {
          extensions: { code: 'UNAUTHENTICATED' },
        });
      }
      return context.user;
    },
  },

  Mutation: {
    createPost: (parent, args, context: Context) => {
      if (!context.user) {
        throw new GraphQLError('Unauthorized', {
          extensions: { code: 'UNAUTHENTICATED' },
        });
      }

      return context.dataSources.posts.create({
        ...args.input,
        authorId: context.user.id,
      });
    },
  },
};
```

## Authorization Patterns

```typescript
// Directive-based authorization
import { mapSchema, getDirective, MapperKind } from '@graphql-tools/utils';
import { defaultFieldResolver } from 'graphql';

function authDirective(directiveName: string) {
  return (schema: GraphQLSchema) =>
    mapSchema(schema, {
      [MapperKind.OBJECT_FIELD]: (fieldConfig) => {
        const authDirective = getDirective(
          schema,
          fieldConfig,
          directiveName
        )?.[0];

        if (authDirective) {
          const { requires } = authDirective;
          const { resolve = defaultFieldResolver } = fieldConfig;

          fieldConfig.resolve = async (source, args, context, info) => {
            // Check if user has required role
            if (!context.user) {
              throw new GraphQLError('Unauthorized', {
                extensions: { code: 'UNAUTHENTICATED' },
              });
            }

            if (requires && !context.user.roles.includes(requires)) {
              throw new GraphQLError('Forbidden', {
                extensions: {
                  code: 'FORBIDDEN',
                  requiredRole: requires,
                },
              });
            }

            return resolve(source, args, context, info);
          };
        }

        return fieldConfig;
      },
    });
}

// Schema with directives
const typeDefs = gql`
  directive @auth(requires: Role) on FIELD_DEFINITION

  enum Role {
    ADMIN
    USER
    GUEST
  }

  type Query {
    publicData: String!
    userData: String! @auth(requires: USER)
    adminData: String! @auth(requires: ADMIN)
  }
`;

const schema = authDirective('auth')(makeExecutableSchema({ typeDefs, resolvers }));
```

## Field-Level Authorization

```typescript
// Row-level security
const resolvers = {
  Query: {
    posts: async (parent, args, context: Context) => {
      // Filter based on user permissions
      const posts = await context.dataSources.posts.findAll();

      return posts.filter((post) => {
        // Public posts visible to all
        if (post.isPublic) return true;

        // Private posts only visible to author
        if (context.user?.id === post.authorId) return true;

        // Check if user is admin
        if (context.user?.roles.includes('ADMIN')) return true;

        return false;
      });
    },
  },

  Post: {
    // Hide email unless viewer is author or admin
    authorEmail: (post: Post, args, context: Context) => {
      if (!context.user) return null;

      if (
        context.user.id === post.authorId ||
        context.user.roles.includes('ADMIN')
      ) {
        return post.authorEmail;
      }

      return null;
    },
  },
};
```

## Query Allowlisting

```typescript
// Persisted queries (automatic allowlisting)
import { createPersistedQueryLink } from '@apollo/client/link/persisted-queries';
import { createHash } from 'crypto';

// Client side
const link = createPersistedQueryLink({
  sha256: (query) => createHash('sha256').update(query).digest('hex'),
  useGETForHashedQueries: true,
});

// Server side
import { ApolloServerPluginInlineTrace } from '@apollo/server/plugin/inlineTrace';

const server = new ApolloServer({
  typeDefs,
  resolvers,
  persistedQueries: {
    cache: new Map(), // or Redis
  },
  // Only allow persisted queries in production
  allowBatchedHttpRequests: false,
  introspection: process.env.NODE_ENV !== 'production',
});

// Manual allowlist
const allowedOperations = new Set([
  'GetUser',
  'GetPosts',
  'CreatePost',
  'UpdatePost',
]);

const server = new ApolloServer({
  typeDefs,
  resolvers,
  plugins: [
    {
      async requestDidStart() {
        return {
          async didResolveOperation(requestContext) {
            const operationName = requestContext.operationName;

            if (!operationName || !allowedOperations.has(operationName)) {
              throw new GraphQLError('Operation not allowed', {
                extensions: { code: 'OPERATION_NOT_ALLOWED' },
              });
            }
          },
        };
      },
    },
  ],
});
```

## Input Validation

```typescript
import { z } from 'zod';

// Zod schema for input validation
const CreatePostSchema = z.object({
  title: z.string().min(3).max(200),
  content: z.string().min(10).max(10000),
  tags: z.array(z.string()).max(5),
  isPublic: z.boolean(),
});

const resolvers = {
  Mutation: {
    createPost: async (
      parent,
      args: { input: any },
      context: Context
    ) => {
      // Validate input
      const validationResult = CreatePostSchema.safeParse(args.input);

      if (!validationResult.success) {
        throw new GraphQLError('Invalid input', {
          extensions: {
            code: 'BAD_USER_INPUT',
            validationErrors: validationResult.error.errors,
          },
        });
      }

      const input = validationResult.data;
      return context.dataSources.posts.create(input);
    },
  },
};
```

## Introspection Control

```typescript
// Disable introspection in production
import { ApolloServer } from '@apollo/server';
import { ApolloServerPluginLandingPageDisabled } from '@apollo/server/plugin/disabled';

const server = new ApolloServer({
  typeDefs,
  resolvers,
  introspection: process.env.NODE_ENV !== 'production',
  plugins:
    process.env.NODE_ENV === 'production'
      ? [ApolloServerPluginLandingPageDisabled()]
      : [],
});

// Conditional introspection (admin only)
const server = new ApolloServer({
  typeDefs,
  resolvers,
  introspection: false, // Disable by default
  plugins: [
    {
      async requestDidStart({ request, contextValue }) {
        // Allow introspection for admins
        if (
          request.operationName === 'IntrospectionQuery' &&
          !contextValue.user?.isAdmin
        ) {
          throw new GraphQLError('Introspection disabled', {
            extensions: { code: 'FORBIDDEN' },
          });
        }
      },
    },
  ],
});
```

## CSRF Protection

```typescript
import csrf from 'csurf';

// CSRF protection for mutations
const csrfProtection = csrf({ cookie: true });

app.post('/graphql', csrfProtection, expressMiddleware(server));

// Client must send CSRF token
// fetch('/graphql', {
//   method: 'POST',
//   headers: {
//     'CSRF-Token': csrfToken,
//   },
//   body: JSON.stringify({ query }),
// });
```

## Security Best Practices

1. **Depth Limiting**: Prevent deeply nested queries
2. **Complexity Analysis**: Calculate and limit query cost
3. **Rate Limiting**: Limit requests per user/IP
4. **Authentication**: Verify user identity in context
5. **Authorization**: Check permissions in resolvers
6. **Input Validation**: Validate all mutation inputs
7. **Query Allowlisting**: Use persisted queries in production
8. **Introspection Control**: Disable in production
9. **Error Sanitization**: Don't expose sensitive data in errors
10. **CORS Configuration**: Restrict allowed origins
11. **HTTPS Only**: Always use HTTPS in production
12. **Audit Logging**: Log sensitive operations
