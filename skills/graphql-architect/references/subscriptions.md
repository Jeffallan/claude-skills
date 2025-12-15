# GraphQL Subscriptions

> Reference for: GraphQL Architect
> Load when: Real-time updates, WebSocket, pub/sub patterns

## Basic Subscription Setup

```typescript
// schema.graphql
type Subscription {
  postCreated: Post!
  postUpdated(id: ID!): Post!
  commentAdded(postId: ID!): Comment!
  userOnline: User!
}

type Post {
  id: ID!
  title: String!
  content: String!
  author: User!
}

type Comment {
  id: ID!
  content: String!
  author: User!
  post: Post!
}

// server.ts
import { createServer } from 'http';
import { ApolloServer } from '@apollo/server';
import { expressMiddleware } from '@apollo/server/express4';
import { ApolloServerPluginDrainHttpServer } from '@apollo/server/plugin/drainHttpServer';
import { makeExecutableSchema } from '@graphql-tools/schema';
import { WebSocketServer } from 'ws';
import { useServer } from 'graphql-ws/lib/use/ws';
import express from 'express';

const schema = makeExecutableSchema({ typeDefs, resolvers });

const app = express();
const httpServer = createServer(app);

// WebSocket server for subscriptions
const wsServer = new WebSocketServer({
  server: httpServer,
  path: '/graphql',
});

const serverCleanup = useServer(
  {
    schema,
    context: async (ctx, msg, args) => {
      // Extract auth from connection params
      const token = ctx.connectionParams?.authorization;
      const user = token ? await verifyToken(token) : null;
      return { user };
    },
  },
  wsServer
);

const server = new ApolloServer({
  schema,
  plugins: [
    ApolloServerPluginDrainHttpServer({ httpServer }),
    {
      async serverWillStart() {
        return {
          async drainServer() {
            await serverCleanup.dispose();
          },
        };
      },
    },
  ],
});

await server.start();
app.use('/graphql', express.json(), expressMiddleware(server));

httpServer.listen(4000);
```

## PubSub Implementation

```typescript
// pubsub.ts
import { RedisPubSub } from 'graphql-redis-subscriptions';
import Redis from 'ioredis';

// In-memory (development only)
import { PubSub } from 'graphql-subscriptions';
export const pubsub = new PubSub();

// Redis (production)
const options = {
  host: process.env.REDIS_HOST || 'localhost',
  port: parseInt(process.env.REDIS_PORT || '6379'),
  retryStrategy: (times: number) => Math.min(times * 50, 2000),
};

export const pubsub = new RedisPubSub({
  publisher: new Redis(options),
  subscriber: new Redis(options),
});

// Strongly typed event names
export const EVENTS = {
  POST_CREATED: 'POST_CREATED',
  POST_UPDATED: 'POST_UPDATED',
  COMMENT_ADDED: 'COMMENT_ADDED',
  USER_ONLINE: 'USER_ONLINE',
} as const;
```

## Subscription Resolvers

```typescript
import { withFilter } from 'graphql-subscriptions';
import { pubsub, EVENTS } from './pubsub';

const resolvers = {
  Subscription: {
    // Simple subscription
    postCreated: {
      subscribe: () => pubsub.asyncIterator([EVENTS.POST_CREATED]),
    },

    // Filtered subscription
    postUpdated: {
      subscribe: withFilter(
        () => pubsub.asyncIterator([EVENTS.POST_UPDATED]),
        (payload, variables) => {
          // Only send updates for specific post
          return payload.postUpdated.id === variables.id;
        }
      ),
    },

    // Filtered with authorization
    commentAdded: {
      subscribe: withFilter(
        (parent, args, context) => {
          // Check auth before subscribing
          if (!context.user) {
            throw new Error('Unauthorized');
          }
          return pubsub.asyncIterator([EVENTS.COMMENT_ADDED]);
        },
        async (payload, variables, context) => {
          // Filter by post and check permissions
          if (payload.commentAdded.postId !== variables.postId) {
            return false;
          }

          // Check if user has access to post
          const post = await context.dataSources.posts.findById(
            variables.postId
          );
          return post && post.isPublic || post.authorId === context.user.id;
        }
      ),
    },

    // Complex subscription with multiple filters
    userOnline: {
      subscribe: withFilter(
        () => pubsub.asyncIterator([EVENTS.USER_ONLINE]),
        (payload, variables, context) => {
          // Only notify friends
          return context.user.friends.includes(payload.userOnline.id);
        }
      ),
    },
  },

  Mutation: {
    createPost: async (parent, args, context) => {
      const post = await context.dataSources.posts.create(args.input);

      // Publish event
      await pubsub.publish(EVENTS.POST_CREATED, {
        postCreated: post,
      });

      return post;
    },

    updatePost: async (parent, args: { id: string; input: any }, context) => {
      const post = await context.dataSources.posts.update(
        args.id,
        args.input
      );

      await pubsub.publish(EVENTS.POST_UPDATED, {
        postUpdated: post,
      });

      return post;
    },

    addComment: async (parent, args, context) => {
      const comment = await context.dataSources.comments.create(args.input);

      await pubsub.publish(EVENTS.COMMENT_ADDED, {
        commentAdded: comment,
      });

      return comment;
    },
  },
};
```

## Advanced Filtering

```typescript
// Type-safe payload
interface PostCreatedPayload {
  postCreated: Post;
  tags: string[];
  isPublic: boolean;
}

const resolvers = {
  Subscription: {
    postCreated: {
      subscribe: withFilter(
        () => pubsub.asyncIterator([EVENTS.POST_CREATED]),
        async (
          payload: PostCreatedPayload,
          variables: { tags?: string[]; authorId?: string },
          context: Context
        ) => {
          // Filter by tags
          if (variables.tags && variables.tags.length > 0) {
            const hasMatchingTag = payload.tags.some(tag =>
              variables.tags!.includes(tag)
            );
            if (!hasMatchingTag) return false;
          }

          // Filter by author
          if (variables.authorId) {
            if (payload.postCreated.authorId !== variables.authorId) {
              return false;
            }
          }

          // Check permissions
          if (!payload.isPublic) {
            return (
              context.user?.id === payload.postCreated.authorId ||
              context.user?.isAdmin
            );
          }

          return true;
        }
      ),
    },
  },
};
```

## Connection Management

```typescript
import { useServer } from 'graphql-ws/lib/use/ws';

const wsServer = useServer(
  {
    schema,

    // Connection lifecycle
    onConnect: async (ctx) => {
      console.log('Client connected');
      const token = ctx.connectionParams?.authorization;

      if (!token) {
        throw new Error('Missing auth token');
      }

      const user = await verifyToken(token);
      if (!user) {
        throw new Error('Invalid token');
      }

      return { user };
    },

    onDisconnect: (ctx, code, reason) => {
      console.log('Client disconnected', code, reason);
    },

    // Subscription lifecycle
    onSubscribe: async (ctx, msg) => {
      console.log('Client subscribed', msg.payload.operationName);

      // Rate limiting
      const subscriptionCount = getUserSubscriptionCount(ctx.user.id);
      if (subscriptionCount >= 10) {
        throw new Error('Too many subscriptions');
      }

      return { ctx, msg };
    },

    onComplete: (ctx, msg) => {
      console.log('Subscription completed', msg.id);
    },

    // Keep-alive
    connectionInitWaitTimeout: 10000,

    // Context per subscription
    context: async (ctx, msg, args) => {
      const user = ctx.extra.user;
      return {
        user,
        dataSources: createDataSources(),
        subscriptionId: msg.id,
      };
    },
  },
  wsServer
);
```

## Subscription Patterns

```typescript
// Pattern 1: Entity updates
type Subscription {
  entityUpdated(id: ID!): Entity!
}

// Pattern 2: Collection updates
type Subscription {
  entityAdded: Entity!
  entityDeleted: ID!
}

// Pattern 3: Stream of events
type Subscription {
  events(types: [EventType!]): Event!
}

// Pattern 4: Live query (with intervals)
type Subscription {
  liveQuery(query: String!): [SearchResult!]!
}

// resolvers.ts
const resolvers = {
  Subscription: {
    // Live query implementation
    liveQuery: {
      subscribe: async function* (parent, args, context) {
        while (true) {
          const results = await context.dataSources.search(args.query);
          yield { liveQuery: results };
          await new Promise(resolve => setTimeout(resolve, 5000));
        }
      },
    },
  },
};
```

## Error Handling

```typescript
const resolvers = {
  Subscription: {
    postCreated: {
      subscribe: withFilter(
        () => pubsub.asyncIterator([EVENTS.POST_CREATED]),
        async (payload, variables, context) => {
          try {
            // Check permissions
            if (!context.user) {
              throw new GraphQLError('Unauthorized', {
                extensions: { code: 'UNAUTHENTICATED' },
              });
            }

            return true;
          } catch (error) {
            // Log error but don't propagate to client
            console.error('Subscription filter error:', error);
            return false;
          }
        }
      ),

      // Resolve subscription payload
      resolve: (payload) => {
        try {
          return payload.postCreated;
        } catch (error) {
          throw new GraphQLError('Failed to resolve subscription', {
            extensions: { code: 'SUBSCRIPTION_RESOLVE_ERROR' },
          });
        }
      },
    },
  },
};
```

## Client Usage

```typescript
// Apollo Client setup
import { ApolloClient, InMemoryCache, split, HttpLink } from '@apollo/client';
import { GraphQLWsLink } from '@apollo/client/link/subscriptions';
import { getMainDefinition } from '@apollo/client/utilities';
import { createClient } from 'graphql-ws';

const httpLink = new HttpLink({
  uri: 'http://localhost:4000/graphql',
});

const wsLink = new GraphQLWsLink(
  createClient({
    url: 'ws://localhost:4000/graphql',
    connectionParams: {
      authorization: `Bearer ${token}`,
    },
  })
);

const splitLink = split(
  ({ query }) => {
    const definition = getMainDefinition(query);
    return (
      definition.kind === 'OperationDefinition' &&
      definition.operation === 'subscription'
    );
  },
  wsLink,
  httpLink
);

const client = new ApolloClient({
  link: splitLink,
  cache: new InMemoryCache(),
});

// Subscribe to events
const subscription = client
  .subscribe({
    query: gql`
      subscription OnPostCreated {
        postCreated {
          id
          title
          author {
            username
          }
        }
      }
    `,
  })
  .subscribe({
    next: (data) => console.log('New post:', data),
    error: (err) => console.error('Subscription error:', err),
    complete: () => console.log('Subscription completed'),
  });

// Unsubscribe
subscription.unsubscribe();
```

## Scaling Subscriptions

```typescript
// Use Redis for multi-instance deployments
import { RedisPubSub } from 'graphql-redis-subscriptions';

// Horizontal scaling pattern
const pubsub = new RedisPubSub({
  publisher: new Redis(redisConfig),
  subscriber: new Redis(redisConfig),
  // Channel prefix for isolation
  publisherPrefix: 'graphql:pub:',
  subscriberPrefix: 'graphql:sub:',
});

// Connection limit per instance
const MAX_CONNECTIONS_PER_INSTANCE = 10000;

// Load balancing with sticky sessions
// Ensure same user connects to same server instance
// for connection state management
```

## Subscription Best Practices

1. **Authentication**: Always validate auth in onConnect and filters
2. **Authorization**: Check permissions in withFilter
3. **Rate Limiting**: Limit subscriptions per user
4. **Filtering**: Use withFilter for server-side filtering
5. **Cleanup**: Always clean up subscriptions on disconnect
6. **Scaling**: Use Redis PubSub for multi-instance deployments
7. **Error Handling**: Gracefully handle errors in filters and resolvers
8. **Testing**: Test subscription lifecycle and filtering
9. **Monitoring**: Track active connections and subscription count
10. **Performance**: Avoid N+1 in subscription resolvers
