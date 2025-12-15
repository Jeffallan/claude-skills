# GraphQL Resolvers

> Reference for: GraphQL Architect
> Load when: Resolver patterns, context, DataLoader, N+1 prevention

## Basic Resolver Pattern

```typescript
import { GraphQLResolveInfo } from 'graphql';

// Resolver signature
type Resolver<TSource, TArgs, TContext, TReturn> = (
  parent: TSource,
  args: TArgs,
  context: TContext,
  info: GraphQLResolveInfo
) => Promise<TReturn> | TReturn;

// User resolvers
const resolvers = {
  Query: {
    user: async (
      parent,
      args: { id: string },
      context: Context
    ): Promise<User | null> => {
      return context.dataSources.users.findById(args.id);
    },

    users: async (
      parent,
      args: { first?: number; after?: string },
      context: Context
    ): Promise<User[]> => {
      return context.dataSources.users.findAll(args);
    },
  },

  Mutation: {
    createUser: async (
      parent,
      args: { input: CreateUserInput },
      context: Context
    ): Promise<User> => {
      if (!context.user) {
        throw new Error('Unauthorized');
      }
      return context.dataSources.users.create(args.input);
    },
  },
};
```

## Context Setup

```typescript
import { Request } from 'express';
import { User } from './models';
import { DataSources } from './datasources';

export interface Context {
  user: User | null;
  dataSources: DataSources;
  loaders: Loaders;
  req: Request;
  authToken: string | null;
}

// Apollo Server context
const server = new ApolloServer({
  typeDefs,
  resolvers,
  context: async ({ req }): Promise<Context> => {
    // Extract auth token
    const authToken = req.headers.authorization?.replace('Bearer ', '') || null;

    // Verify user
    let user: User | null = null;
    if (authToken) {
      user = await verifyToken(authToken);
    }

    // Create data sources
    const dataSources = new DataSources({
      db: prisma,
      redis: redisClient,
    });

    // Create DataLoaders
    const loaders = createLoaders(dataSources);

    return {
      user,
      dataSources,
      loaders,
      req,
      authToken,
    };
  },
});
```

## DataLoader for N+1 Prevention

```typescript
import DataLoader from 'dataloader';

// Create loaders
export function createLoaders(dataSources: DataSources): Loaders {
  return {
    userLoader: new DataLoader<string, User>(
      async (ids: readonly string[]) => {
        const users = await dataSources.users.findByIds([...ids]);
        // Return in same order as input ids
        return ids.map(id => users.find(u => u.id === id) || null);
      },
      {
        cache: true,
        batchScheduleFn: (callback) => setTimeout(callback, 10),
      }
    ),

    postsByAuthorLoader: new DataLoader<string, Post[]>(
      async (authorIds: readonly string[]) => {
        const posts = await dataSources.posts.findByAuthorIds([...authorIds]);
        // Group by author
        return authorIds.map(authorId =>
          posts.filter(p => p.authorId === authorId)
        );
      }
    ),
  };
}

// Field resolver using DataLoader
const resolvers = {
  Post: {
    author: async (
      post: Post,
      args,
      context: Context
    ): Promise<User> => {
      // Batches multiple requests into single DB query
      return context.loaders.userLoader.load(post.authorId);
    },
  },

  User: {
    posts: async (
      user: User,
      args,
      context: Context
    ): Promise<Post[]> => {
      return context.loaders.postsByAuthorLoader.load(user.id);
    },
  },
};
```

## Field Resolvers

```typescript
const resolvers = {
  User: {
    // Simple field resolver
    fullName: (user: User): string => {
      return `${user.firstName} ${user.lastName}`;
    },

    // Async field resolver with DB query
    postCount: async (
      user: User,
      args,
      context: Context
    ): Promise<number> => {
      return context.dataSources.posts.countByAuthor(user.id);
    },

    // Field resolver with arguments
    posts: async (
      user: User,
      args: { first?: number; status?: PostStatus },
      context: Context
    ): Promise<Post[]> => {
      return context.dataSources.posts.findByAuthor(user.id, {
        limit: args.first,
        status: args.status,
      });
    },

    // Nullable field with conditional logic
    profile: async (
      user: User,
      args,
      context: Context
    ): Promise<Profile | null> => {
      if (!user.hasProfile) return null;
      return context.loaders.profileLoader.load(user.id);
    },
  },
};
```

## Interface Resolvers

```typescript
const resolvers = {
  // Interface type resolver
  Searchable: {
    __resolveType(obj: Article | Video | Podcast): string {
      if ('content' in obj) return 'Article';
      if ('duration' in obj) return 'Video';
      if ('audioUrl' in obj) return 'Podcast';
      throw new Error('Unknown Searchable type');
    },
  },

  // Common interface fields (shared resolvers)
  Article: {
    id: (article: Article) => article.id,
    title: (article: Article) => article.title,
    description: (article: Article) => article.description,
  },

  Video: {
    id: (video: Video) => video.id,
    title: (video: Video) => video.title,
    description: (video: Video) => video.description,
  },
};
```

## Union Resolvers

```typescript
const resolvers = {
  // Union type resolver
  SearchResult: {
    __resolveType(
      obj: Article | Video | Podcast,
      context: Context,
      info: GraphQLResolveInfo
    ): string {
      if ('content' in obj) return 'Article';
      if ('duration' in obj && 'url' in obj) return 'Video';
      if ('audioUrl' in obj) return 'Podcast';
      throw new Error('Unknown SearchResult type');
    },
  },

  Query: {
    searchContent: async (
      parent,
      args: { query: string },
      context: Context
    ): Promise<(Article | Video | Podcast)[]> => {
      // Return mixed array of different types
      const [articles, videos, podcasts] = await Promise.all([
        context.dataSources.articles.search(args.query),
        context.dataSources.videos.search(args.query),
        context.dataSources.podcasts.search(args.query),
      ]);
      return [...articles, ...videos, ...podcasts];
    },
  },
};
```

## Error Handling

```typescript
import { GraphQLError } from 'graphql';
import { ApolloServerErrorCode } from '@apollo/server/errors';

const resolvers = {
  Query: {
    user: async (
      parent,
      args: { id: string },
      context: Context
    ): Promise<User> => {
      const user = await context.dataSources.users.findById(args.id);

      if (!user) {
        throw new GraphQLError('User not found', {
          extensions: {
            code: 'USER_NOT_FOUND',
            http: { status: 404 },
            userId: args.id,
          },
        });
      }

      return user;
    },
  },

  Mutation: {
    updateUser: async (
      parent,
      args: { id: string; input: UpdateUserInput },
      context: Context
    ): Promise<User> => {
      // Check authentication
      if (!context.user) {
        throw new GraphQLError('Unauthorized', {
          extensions: {
            code: ApolloServerErrorCode.UNAUTHENTICATED,
            http: { status: 401 },
          },
        });
      }

      // Check authorization
      if (context.user.id !== args.id && !context.user.isAdmin) {
        throw new GraphQLError('Forbidden', {
          extensions: {
            code: ApolloServerErrorCode.FORBIDDEN,
            http: { status: 403 },
          },
        });
      }

      try {
        return await context.dataSources.users.update(args.id, args.input);
      } catch (error) {
        throw new GraphQLError('Failed to update user', {
          extensions: {
            code: 'UPDATE_FAILED',
            originalError: error,
          },
        });
      }
    },
  },
};
```

## Pagination Resolvers

```typescript
import { encodeCursor, decodeCursor } from './utils/cursor';

const resolvers = {
  Query: {
    posts: async (
      parent,
      args: { first?: number; after?: string },
      context: Context
    ): Promise<PostConnection> => {
      const limit = Math.min(args.first || 10, 100);
      const cursor = args.after ? decodeCursor(args.after) : null;

      // Fetch one extra to determine hasNextPage
      const posts = await context.dataSources.posts.findAll({
        limit: limit + 1,
        cursor,
      });

      const hasNextPage = posts.length > limit;
      const edges = posts.slice(0, limit).map(post => ({
        node: post,
        cursor: encodeCursor(post.id),
      }));

      return {
        edges,
        pageInfo: {
          hasNextPage,
          hasPreviousPage: !!cursor,
          startCursor: edges[0]?.cursor || null,
          endCursor: edges[edges.length - 1]?.cursor || null,
        },
        totalCount: await context.dataSources.posts.count(),
      };
    },
  },
};
```

## Batching Patterns

```typescript
// Batch multiple queries
class UserDataSource {
  private db: PrismaClient;

  async findByIds(ids: string[]): Promise<User[]> {
    // Single query instead of N queries
    return this.db.user.findMany({
      where: { id: { in: ids } },
    });
  }

  async findByEmails(emails: string[]): Promise<User[]> {
    return this.db.user.findMany({
      where: { email: { in: emails } },
    });
  }
}

// DataLoader with caching
const userLoader = new DataLoader<string, User>(
  async (ids) => {
    console.log('Batching user queries:', ids.length);
    const users = await dataSources.users.findByIds([...ids]);
    return ids.map(id => users.find(u => u.id === id) || null);
  },
  {
    cache: true,
    maxBatchSize: 100,
    batchScheduleFn: (callback) => setTimeout(callback, 10),
  }
);
```

## Resolver Best Practices

1. **Use DataLoader**: Always batch and cache database queries
2. **Avoid N+1**: Use DataLoader for all foreign key relationships
3. **Type Safety**: Use TypeScript for resolver type safety
4. **Error Handling**: Throw GraphQLError with proper codes and extensions
5. **Authorization**: Check permissions in resolvers, not data sources
6. **Pagination**: Implement cursor-based pagination for lists
7. **Context**: Keep context creation lightweight
8. **Caching**: Use DataLoader caching per request
9. **Batching**: Batch queries with DataLoader or in data source
10. **Testing**: Unit test resolvers with mocked context
