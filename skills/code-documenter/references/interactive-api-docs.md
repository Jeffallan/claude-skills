# Interactive API Documentation

> Reference for: Code Documenter
> Load when: Building API portals, interactive consoles, multi-protocol APIs, SDK docs

## OpenAPI 3.1 Advanced Features

### Reusable Components

```yaml
openapi: 3.1.0
info:
  title: Users API
  version: 2.0.0

components:
  # Reusable schemas
  schemas:
    User:
      type: object
      required: [id, email]
      properties:
        id:
          type: string
          format: uuid
          example: "123e4567-e89b-12d3-a456-426614174000"
        email:
          type: string
          format: email
          example: "user@example.com"

    Error:
      type: object
      properties:
        code:
          type: string
        message:
          type: string
        details:
          type: object

    PaginatedResponse:
      type: object
      properties:
        data:
          type: array
          items: {}
        total:
          type: integer
        page:
          type: integer

  # Reusable parameters
  parameters:
    PageParam:
      name: page
      in: query
      schema:
        type: integer
        default: 1
        minimum: 1

    LimitParam:
      name: limit
      in: query
      schema:
        type: integer
        default: 20
        minimum: 1
        maximum: 100

  # Security schemes
  securitySchemes:
    BearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT

    ApiKeyAuth:
      type: apiKey
      in: header
      name: X-API-Key

    OAuth2:
      type: oauth2
      flows:
        authorizationCode:
          authorizationUrl: https://api.example.com/oauth/authorize
          tokenUrl: https://api.example.com/oauth/token
          scopes:
            read:users: Read user data
            write:users: Modify user data

  # Reusable responses
  responses:
    NotFound:
      description: Resource not found
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/Error'

    Unauthorized:
      description: Authentication required
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/Error'

paths:
  /users:
    get:
      summary: List users
      parameters:
        - $ref: '#/components/parameters/PageParam'
        - $ref: '#/components/parameters/LimitParam'
      security:
        - BearerAuth: []
      responses:
        '200':
          description: Success
          content:
            application/json:
              schema:
                allOf:
                  - $ref: '#/components/schemas/PaginatedResponse'
                  - type: object
                    properties:
                      data:
                        type: array
                        items:
                          $ref: '#/components/schemas/User'
```

## Interactive Documentation Portals

### Swagger UI Customization

```javascript
// Custom Swagger UI
const swaggerUi = require('swagger-ui-express');
const swaggerDocument = require('./openapi.json');

const options = {
  customCss: '.swagger-ui .topbar { display: none }',
  customSiteTitle: "API Docs",
  customfavIcon: "/favicon.ico",
  swaggerOptions: {
    persistAuthorization: true,
    displayRequestDuration: true,
    filter: true,
    tryItOutEnabled: true,
    requestInterceptor: (req) => {
      req.headers['X-Custom-Header'] = 'value';
      return req;
    },
  },
};

app.use('/api-docs', swaggerUi.serve, swaggerUi.setup(swaggerDocument, options));
```

### Redoc (Modern Alternative)

```html
<!DOCTYPE html>
<html>
<head>
  <title>API Documentation</title>
  <link href="https://fonts.googleapis.com/css?family=Montserrat:300,400,700|Roboto:300,400,700" rel="stylesheet">
</head>
<body>
  <redoc spec-url='./openapi.yaml'
    hide-download-button
    required-props-first
    native-scrollbars
    theme='{
      "colors": {
        "primary": {
          "main": "#4285F4"
        }
      },
      "typography": {
        "fontSize": "16px",
        "fontFamily": "Roboto, sans-serif"
      }
    }'>
  </redoc>
  <script src="https://cdn.redoc.ly/redoc/latest/bundles/redoc.standalone.js"></script>
</body>
</html>
```

### Stoplight Elements

```javascript
import { API } from '@stoplight/elements';
import '@stoplight/elements/styles.min.css';

function App() {
  return (
    <API
      apiDescriptionUrl="./openapi.yaml"
      router="hash"
      layout="sidebar"
      tryItCredentialsPolicy="include"
    />
  );
}
```

## Multi-Protocol Documentation

### GraphQL Schema Documentation

```graphql
"""
User account in the system
"""
type User {
  """
  Unique user identifier
  """
  id: ID!

  """
  User's email address (unique)
  @example "user@example.com"
  """
  email: String!

  """
  Display name
  @example "John Doe"
  """
  name: String!

  """
  User's posts (paginated)
  """
  posts(
    """Number of items per page (max 100)"""
    limit: Int = 20
    """Page offset"""
    offset: Int = 0
  ): PostConnection!
}

type Query {
  """
  Fetch a user by ID
  """
  user(
    """User's unique identifier"""
    id: ID!
  ): User

  """
  Search users by name or email
  """
  searchUsers(
    """Search query"""
    query: String!
    """Maximum results to return"""
    limit: Int = 10
  ): [User!]!
}

type Mutation {
  """
  Create a new user account
  """
  createUser(
    """User creation input"""
    input: CreateUserInput!
  ): CreateUserPayload!
}

"""
Input for creating a user
"""
input CreateUserInput {
  """User's email address"""
  email: String!
  """Display name"""
  name: String!
}
```

**GraphQL Playground:**
```javascript
const { ApolloServer } = require('apollo-server');

const server = new ApolloServer({
  typeDefs,
  resolvers,
  introspection: true,  // Enable in dev
  playground: {
    settings: {
      'editor.theme': 'dark',
      'editor.fontSize': 14,
    },
  },
});
```

### WebSocket Protocol Documentation

```yaml
# AsyncAPI 2.0
asyncapi: 2.5.0
info:
  title: Chat WebSocket API
  version: 1.0.0
  description: Real-time chat messaging

channels:
  chat/{roomId}:
    parameters:
      roomId:
        description: Chat room identifier
        schema:
          type: string

    subscribe:
      summary: Receive messages
      message:
        oneOf:
          - $ref: '#/components/messages/ChatMessage'
          - $ref: '#/components/messages/UserJoined'

    publish:
      summary: Send a message
      message:
        $ref: '#/components/messages/ChatMessage'

components:
  messages:
    ChatMessage:
      name: message
      payload:
        type: object
        properties:
          userId:
            type: string
          content:
            type: string
          timestamp:
            type: string
            format: date-time

    UserJoined:
      name: userJoined
      payload:
        type: object
        properties:
          userId:
            type: string
          username:
            type: string
```

### gRPC Documentation

```protobuf
syntax = "proto3";

package users.v1;

// User service manages user accounts
service UserService {
  // Get a user by ID
  // Returns: User object or NOT_FOUND error
  rpc GetUser(GetUserRequest) returns (User) {}

  // List all users with pagination
  // Returns: Paginated list of users
  rpc ListUsers(ListUsersRequest) returns (ListUsersResponse) {}

  // Create a new user
  // Returns: Created user or ALREADY_EXISTS error
  rpc CreateUser(CreateUserRequest) returns (User) {}

  // Stream user updates in real-time
  // Returns: Stream of user update events
  rpc WatchUsers(WatchUsersRequest) returns (stream UserEvent) {}
}

// User account
message User {
  // Unique identifier
  string id = 1;

  // Email address (unique, required)
  string email = 2;

  // Display name
  string name = 3;

  // Account creation timestamp
  google.protobuf.Timestamp created_at = 4;
}
```

## SDK Documentation Strategies

### Multi-Language Examples

```markdown
# Create User

## Python
```python
from myapi import Client

client = Client(api_key="your_key")
user = client.users.create(
    name="John Doe",
    email="john@example.com"
)
print(user.id)
```

## TypeScript
```typescript
import { Client } from '@myapi/sdk';

const client = new Client({ apiKey: 'your_key' });
const user = await client.users.create({
  name: 'John Doe',
  email: 'john@example.com',
});
console.log(user.id);
```

## Go
```go
import "github.com/myapi/sdk-go"

client := sdk.NewClient("your_key")
user, err := client.Users.Create(ctx, &sdk.CreateUserInput{
    Name:  "John Doe",
    Email: "john@example.com",
})
if err != nil {
    log.Fatal(err)
}
fmt.Println(user.ID)
```

## Ruby
```ruby
require 'myapi'

client = MyAPI::Client.new(api_key: 'your_key')
user = client.users.create(
  name: 'John Doe',
  email: 'john@example.com'
)
puts user.id
```
```

### SDK Reference Template

```markdown
# Users SDK

## Installation
```bash
npm install @myapi/sdk
```

## Configuration
```typescript
import { Client } from '@myapi/sdk';

const client = new Client({
  apiKey: process.env.API_KEY,
  baseUrl: 'https://api.example.com',  // Optional
  timeout: 30000,  // Optional, default 30s
});
```

## Methods

### `client.users.create(data)`
Create a new user.

**Parameters:**
- `data.name` (string, required) - User's display name
- `data.email` (string, required) - User's email address

**Returns:** Promise<User>

**Throws:**
- `ValidationError` - Invalid input data
- `ConflictError` - Email already exists
- `AuthenticationError` - Invalid API key

**Example:**
```typescript
const user = await client.users.create({
  name: 'John Doe',
  email: 'john@example.com',
});
```

## Error Handling
```typescript
import { ValidationError, ConflictError } from '@myapi/sdk';

try {
  await client.users.create(data);
} catch (error) {
  if (error instanceof ValidationError) {
    console.error('Invalid data:', error.fields);
  } else if (error instanceof ConflictError) {
    console.error('User already exists');
  }
}
```
```

## Quick Reference

| Tool | Protocol | Features |
|------|----------|----------|
| Swagger UI | REST | Try-it-out, auth |
| Redoc | REST | Clean, responsive |
| Stoplight | REST | Modern, mock server |
| GraphQL Playground | GraphQL | Explorer, history |
| AsyncAPI Studio | WebSocket | Visual editor |
| grpcui | gRPC | Interactive console |
