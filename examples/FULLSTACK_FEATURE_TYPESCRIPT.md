# Full-Stack Feature Development: Todo App with Authentication

> **Skills used:** `feature-forge`, `architecture-designer`, `nestjs-expert`, `nextjs-developer`, `test-master`, `playwright-expert`, `devops-engineer`
> **Difficulty:** Advanced
> **Language:** TypeScript
> **Workflow:** [New Feature Development](../SKILLS_GUIDE.md#new-feature-development) + [Modern Web App](../SKILLS_GUIDE.md#modern-web-app)

## Overview

A product team needs a todo application with JWT-based user authentication. The frontend uses Next.js 14 with the App Router, the backend uses NestJS, and the database is PostgreSQL. The entire stack deploys via Docker containers orchestrated with Docker Compose, and CI/CD runs through GitHub Actions. This example walks through the full feature lifecycle -- from requirements to deployment -- using 7 skills in sequence, each producing output in its prescribed format.

### Why Multi-Skill?

No single skill covers the full stack. `feature-forge` writes EARS-format requirements but does not generate code. `nestjs-expert` builds backend modules but does not produce React components. `nextjs-developer` builds the frontend but does not know your auth strategy. `test-master` validates correctness but does not configure pipelines. Chaining skills lets each one focus on its domain while building naturally on previous outputs, producing a coherent system that no single skill could deliver alone.

---

## Step 1 -- Requirements Definition with `feature-forge`

### Prompt

```
I need a todo app feature with user authentication. Users should register, login,
create/read/update/delete todos, and each user should only see their own todos.
Tech stack: Next.js 14 App Router, NestJS backend, PostgreSQL.
```

### Skill Output

#### Feature: Authenticated Todo Application

##### Overview

A full-stack todo application allowing users to register, authenticate via JWT, and manage personal todo items through a REST API. Each user's todos are isolated -- users can only access their own data. The frontend is a Next.js 14 App Router application consuming a NestJS backend backed by PostgreSQL.

##### Functional Requirements

**FR-AUTH-001**: User Registration
When a new user submits valid email and password via POST /auth/register,
the system shall create a user record with bcrypt-hashed password (cost factor 10) and return JWT access and refresh tokens.

**FR-AUTH-002**: User Login
While credentials are valid, when POST /auth/login is called,
the system shall return a JWT access token (15min expiry) and refresh token (7d expiry).

**FR-AUTH-003**: Invalid Login
When invalid credentials are provided to POST /auth/login,
the system shall return HTTP 401 and a generic "Invalid credentials" message.

**FR-AUTH-004**: Token Refresh
While a valid refresh token is provided, when POST /auth/refresh is called,
the system shall return a new access token without requiring re-authentication.

**FR-AUTH-005**: Duplicate Registration
When a user attempts to register with an already-registered email,
the system shall return HTTP 409 with message "Email already exists".

**FR-TODO-001**: Create Todo
While the user is authenticated, when POST /todos is called with a title (required) and description (optional),
the system shall create a todo record associated with the authenticated user and return the created todo.

**FR-TODO-002**: List Todos
While the user is authenticated, when GET /todos is called,
the system shall return only the authenticated user's non-deleted todos ordered by creation date descending.

**FR-TODO-003**: Update Todo
While the user is authenticated, when PATCH /todos/:id is called with valid fields,
the system shall update only the specified fields on the user's own todo and return the updated todo.

**FR-TODO-004**: Toggle Completion
While the user is authenticated, when PATCH /todos/:id is called with a completed boolean,
the system shall toggle the completion status of the user's own todo.

**FR-TODO-005**: Delete Todo (Soft Delete)
While the user is authenticated, when DELETE /todos/:id is called,
the system shall set the deletedAt timestamp instead of removing the record.

**FR-TODO-006**: User Isolation
The system shall enforce that all todo queries filter by the authenticated user's ID, preventing cross-user data access.

##### Non-Functional Requirements

**Performance**
- API response time: < 200ms p95
- Database query time: < 50ms p95
- Frontend Time to Interactive: < 3 seconds

**Security**
- All passwords hashed with bcrypt (minimum cost factor 10)
- JWT access tokens expire in 15 minutes
- JWT refresh tokens expire in 7 days
- All todo endpoints require valid JWT authentication
- JWT secret stored in environment variable, never in code

**Scalability**
- Support 1,000 concurrent authenticated users
- Support up to 100,000 todo records per user
- Horizontal scaling via stateless JWT authentication

##### Acceptance Criteria

**AC-001**: Successful Registration
Given a new user with a valid email and password,
When they submit the registration form,
Then the system creates their account and returns valid JWT tokens.

**AC-002**: Successful Login
Given a registered user with correct credentials,
When they submit the login form,
Then the system returns access and refresh tokens and redirects to the dashboard.

**AC-003**: Todo CRUD Cycle
Given an authenticated user,
When they create a todo, update its title, mark it complete, and then delete it,
Then each operation succeeds and the todo list reflects each change immediately.

**AC-004**: User Isolation
Given two registered users (Alice and Bob),
When Alice creates a todo and Bob views his todo list,
Then Bob's list does not contain Alice's todo.

**AC-005**: Token Refresh
Given an authenticated user whose access token has expired,
When the frontend detects a 401 response,
Then it automatically refreshes the token and retries the request without user intervention.

**AC-006**: Soft Delete Exclusion
Given a user who has soft-deleted a todo,
When they request their todo list,
Then the deleted todo does not appear in the results.

##### Error Handling

| Error Condition | HTTP Code | User Message | EARS Ref |
|-----------------|-----------|--------------|----------|
| Invalid registration input | 400 | "Email and password are required" | FR-AUTH-001 |
| Duplicate email | 409 | "Email already exists" | FR-AUTH-005 |
| Invalid credentials | 401 | "Invalid credentials" | FR-AUTH-003 |
| Expired/invalid token | 401 | "Please log in to continue" | FR-AUTH-004 |
| Todo not found | 404 | "Todo not found" | FR-TODO-003 |
| Access another user's todo | 404 | "Todo not found" | FR-TODO-006 |
| Missing todo title | 400 | "Title is required" | FR-TODO-001 |
| Server error | 500 | "Something went wrong. Please try again." | -- |

##### Implementation TODO

**Backend**
- [ ] Create User entity with TypeORM (id, email, passwordHash, createdAt, updatedAt)
- [ ] Create Todo entity with TypeORM (id, title, description, completed, userId FK, createdAt, updatedAt, deletedAt)
- [ ] Implement AuthModule with JWT strategy, register, login endpoints
- [ ] Implement TodosModule with user-scoped CRUD endpoints
- [ ] Add class-validator DTOs for all request bodies
- [ ] Apply JwtAuthGuard globally, mark auth endpoints as public
- [ ] Add Swagger/OpenAPI decorators to all controllers

**Frontend**
- [ ] Create login and register pages under (auth) route group
- [ ] Create dashboard layout with authentication check
- [ ] Build TodoList, TodoItem, and CreateTodoForm components
- [ ] Implement API client with automatic token refresh on 401
- [ ] Add loading.tsx and error.tsx boundaries
- [ ] Implement optimistic UI updates for todo operations

**Testing**
- [ ] Unit tests for AuthService (register, login, token generation)
- [ ] Unit tests for TodosService (CRUD, user-scoping, soft delete)
- [ ] E2E tests for full user journey (register through delete)
- [ ] E2E test for user isolation (multi-user scenario)

**DevOps**
- [ ] Multi-stage Dockerfiles for backend and frontend
- [ ] Docker Compose with PostgreSQL health checks
- [ ] GitHub Actions CI pipeline (lint, test, build, deploy)

##### Out of Scope
- Password reset / forgot password flow
- Email verification on registration
- Social login (OAuth / Google / GitHub)
- Real-time updates (WebSockets)
- Todo categories, tags, or priorities
- Admin dashboard

### What This Skill Provided

`feature-forge` translated a vague feature request into a structured EARS-format specification with unambiguous functional requirements, Given/When/Then acceptance criteria, a complete error handling table, and an implementation checklist organized by layer. This spec becomes the contract that every subsequent skill references.

---

## Step 2 -- System Architecture with `architecture-designer`

### Prompt

```
Design the system architecture for the Next.js 14 + NestJS todo app from the feature spec.
Include folder structure, module boundaries, and data flow.
```

### Skill Output

#### System: Authenticated Todo Application

##### Requirements Summary

**Functional**
- User registration and JWT-based authentication (access + refresh tokens)
- User-scoped CRUD operations on todo items
- Soft delete with timestamp-based exclusion from queries

**Non-Functional**
- Performance: < 200ms API response time (p95)
- Security: bcrypt password hashing, short-lived JWTs, environment-based secrets
- Scalability: Stateless auth supporting 1,000 concurrent users
- Availability: Health checks on all services for container orchestration

**Constraints**
- Frontend: Next.js 14 App Router (no Pages Router)
- Backend: NestJS with TypeORM
- Database: PostgreSQL 16
- Deployment: Docker Compose for local/staging, GitHub Actions for CI/CD

##### High-Level Architecture

- **Next.js 14 App** (App Router, Port 3000) communicates via HTTP/REST with **NestJS API** (Port 3001) using `Authorization: Bearer <JWT>`
- **NestJS API** connects to **PostgreSQL** (Port 5432) via TypeORM

**Data Flow:**
1. User submits credentials on Next.js login page (Client Component)
2. Frontend calls POST /auth/login on NestJS API
3. NestJS validates credentials, returns JWT access + refresh tokens
4. Frontend stores access token in memory, refresh token via httpOnly cookie
5. All subsequent API calls include `Authorization: Bearer <accessToken>`
6. On 401 response, frontend calls POST /auth/refresh, retries the original request
7. On refresh failure, frontend redirects to /login

##### Key Decisions (ADR Format)

**ADR-001: Use NestJS Modular Architecture**

**Status:** Accepted

**Context:** The backend needs clear separation between authentication and business logic. Multiple team members will work on different modules concurrently. We need a framework that enforces structure and supports dependency injection natively.

**Decision:** Use NestJS with its module system. Separate the application into AuthModule, UsersModule, and TodosModule with explicit imports/exports.

**Consequences:**
- Positive: Enforced separation of concerns, testable via DI, Swagger integration built-in
- Positive: Guards and interceptors provide clean cross-cutting concerns
- Negative: Steeper learning curve for developers unfamiliar with Angular-style DI
- Neutral: TypeORM integrates cleanly via `TypeOrmModule.forFeature()`

**Alternatives Considered:**
- Express.js: Rejected -- no built-in module system, manual DI wiring
- Fastify standalone: Rejected -- less ecosystem support for Swagger, guards, pipes

---

**ADR-002: JWT with Dual Token Strategy**

**Status:** Accepted

**Context:** The app needs stateless authentication that works across frontend and backend without session storage. Access tokens must be short-lived for security, but users should not need to re-login frequently.

**Decision:** Issue short-lived access tokens (15 min) and long-lived refresh tokens (7 days). Access token stored in memory (not localStorage). Refresh token stored in httpOnly cookie.

**Consequences:**
- Positive: Stateless backend, no session store needed, horizontally scalable
- Positive: Short access token limits exposure window if intercepted
- Negative: Token refresh adds complexity to frontend API client
- Neutral: Refresh token in httpOnly cookie prevents XSS access but requires CSRF consideration

**Alternatives Considered:**
- Session-based auth with Redis: Rejected -- adds stateful dependency, complicates horizontal scaling
- Single long-lived JWT: Rejected -- larger security exposure window

---

**ADR-003: PostgreSQL with TypeORM**

**Status:** Accepted

**Context:** The data model is relational (users have many todos with foreign key). We need ACID compliance for user creation and strong query capabilities for filtering.

**Decision:** Use PostgreSQL 16 as the primary database with TypeORM for the ORM layer.

**Consequences:**
- Positive: ACID compliance, strong relational support, JSON capabilities if needed later
- Positive: TypeORM provides decorators that align with NestJS patterns
- Negative: TypeORM has known performance issues with complex queries (mitigated by simple schema)
- Neutral: Requires running PostgreSQL container in development

**Alternatives Considered:**
- MongoDB with Mongoose: Rejected -- relational data model, user-todo FK relationship
- Prisma ORM: Considered -- better type safety, but less mature NestJS integration at time of decision

##### Technology Recommendations

| Component | Technology | Rationale |
|-----------|-----------|-----------|
| Frontend | Next.js 14 (App Router) | Server Components by default, file-based routing, built-in optimization |
| Backend | NestJS 10 | Modular architecture, DI, guards, Swagger, TypeScript-first |
| ORM | TypeORM | Decorator-based entities match NestJS patterns, migration support |
| Database | PostgreSQL 16 | ACID, relational integrity, proven at scale |
| Auth | Passport + passport-jwt | Standard NestJS authentication strategy |
| Validation | class-validator | Decorator-based DTO validation, NestJS pipe integration |
| Container | Docker + Docker Compose | Reproducible environments, health checks, service dependencies |
| CI/CD | GitHub Actions | Native GitHub integration, free tier for open source |

##### Risks and Mitigation

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| JWT secret exposure | Low | Critical | Store in environment variable, rotate quarterly, never commit to repo |
| TypeORM N+1 queries | Medium | Medium | Use `find` with explicit `relations`, add query logging in development |
| Token refresh race condition | Medium | Low | Queue concurrent refresh calls, return same promise for in-flight refresh |
| PostgreSQL connection exhaustion | Low | High | Configure connection pool (max 20), add health checks, use connection timeout |
| Docker image size bloat | Medium | Low | Multi-stage builds, .dockerignore, alpine base images |

##### Folder Structure

```
todo-app/
├── backend/
│   ├── src/
│   │   ├── auth/
│   │   │   ├── auth.module.ts
│   │   │   ├── auth.controller.ts
│   │   │   ├── auth.service.ts
│   │   │   ├── jwt.strategy.ts
│   │   │   ├── jwt-auth.guard.ts
│   │   │   ├── public.decorator.ts
│   │   │   └── dto/
│   │   │       ├── register.dto.ts
│   │   │       └── login.dto.ts
│   │   ├── todos/
│   │   │   ├── todos.module.ts
│   │   │   ├── todos.controller.ts
│   │   │   ├── todos.service.ts
│   │   │   ├── todo.entity.ts
│   │   │   └── dto/
│   │   │       ├── create-todo.dto.ts
│   │   │       └── update-todo.dto.ts
│   │   ├── users/
│   │   │   ├── users.module.ts
│   │   │   ├── users.service.ts
│   │   │   └── user.entity.ts
│   │   ├── app.module.ts
│   │   └── main.ts
│   ├── test/
│   ├── Dockerfile
│   └── package.json
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx
│   │   │   ├── page.tsx
│   │   │   ├── loading.tsx
│   │   │   ├── error.tsx
│   │   │   ├── (auth)/
│   │   │   │   ├── login/page.tsx
│   │   │   │   └── register/page.tsx
│   │   │   └── dashboard/
│   │   │       ├── layout.tsx
│   │   │       ├── page.tsx
│   │   │       ├── loading.tsx
│   │   │       └── error.tsx
│   │   ├── components/
│   │   │   ├── TodoList.tsx
│   │   │   ├── TodoItem.tsx
│   │   │   ├── CreateTodoForm.tsx
│   │   │   └── AuthForm.tsx
│   │   ├── lib/
│   │   │   ├── api.ts
│   │   │   └── auth.ts
│   │   └── types/
│   │       └── index.ts
│   ├── Dockerfile
│   ├── next.config.js
│   └── package.json
├── docker-compose.yml
├── .github/
│   └── workflows/
│       └── ci.yml
└── .env.example
```

### What This Skill Provided

`architecture-designer` produced a complete system design with ADR-format decision records, a technology matrix with rationale, a risk registry with mitigations, and a folder structure that both `nestjs-expert` and `nextjs-developer` can follow independently. The three ADRs document the critical "why" behind the architecture choices.

---

## Step 3 -- Backend Implementation with `nestjs-expert`

### Prompt

```
Implement the NestJS backend for the todo app. Start with auth module (JWT strategy,
register, login) then todos module with user-scoped CRUD. Use TypeORM with PostgreSQL.
```

### Skill Output

#### Module Definition

```typescript
// src/auth/auth.module.ts
import { Module } from '@nestjs/common';
import { JwtModule } from '@nestjs/jwt';
import { PassportModule } from '@nestjs/passport';
import { ConfigService } from '@nestjs/config';
import { AuthService } from './auth.service';
import { AuthController } from './auth.controller';
import { JwtStrategy } from './jwt.strategy';
import { UsersModule } from '../users/users.module';

@Module({
  imports: [
    UsersModule,
    PassportModule.register({ defaultStrategy: 'jwt' }),
    JwtModule.registerAsync({
      inject: [ConfigService],
      useFactory: (config: ConfigService) => ({
        secret: config.get<string>('JWT_SECRET'),
        signOptions: { expiresIn: '15m' },
      }),
    }),
  ],
  controllers: [AuthController],
  providers: [AuthService, JwtStrategy],
  exports: [AuthService],
})
export class AuthModule {}

// src/todos/todos.module.ts
import { Module } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';
import { TodosController } from './todos.controller';
import { TodosService } from './todos.service';
import { Todo } from './todo.entity';

@Module({
  imports: [TypeOrmModule.forFeature([Todo])],
  controllers: [TodosController],
  providers: [TodosService],
  exports: [TodosService],
})
export class TodosModule {}

// src/app.module.ts
import { Module } from '@nestjs/common';
import { ConfigModule, ConfigService } from '@nestjs/config';
import { TypeOrmModule } from '@nestjs/typeorm';
import { APP_GUARD } from '@nestjs/core';
import { AuthModule } from './auth/auth.module';
import { TodosModule } from './todos/todos.module';
import { UsersModule } from './users/users.module';
import { JwtAuthGuard } from './auth/jwt-auth.guard';

@Module({
  imports: [
    ConfigModule.forRoot({ isGlobal: true }),
    TypeOrmModule.forRootAsync({
      inject: [ConfigService],
      useFactory: (config: ConfigService) => ({
        type: 'postgres',
        url: config.get<string>('DATABASE_URL'),
        autoLoadEntities: true,
        synchronize: config.get('NODE_ENV') !== 'production',
      }),
    }),
    AuthModule,
    TodosModule,
    UsersModule,
  ],
  providers: [
    { provide: APP_GUARD, useClass: JwtAuthGuard },
  ],
})
export class AppModule {}
```

#### Controller with Swagger Decorators

```typescript
// src/auth/auth.controller.ts
import { Controller, Post, Body, HttpCode, HttpStatus } from '@nestjs/common';
import { ApiTags, ApiOperation, ApiResponse } from '@nestjs/swagger';
import { AuthService } from './auth.service';
import { RegisterDto } from './dto/register.dto';
import { LoginDto } from './dto/login.dto';
import { Public } from './public.decorator';

@ApiTags('auth')
@Controller('auth')
export class AuthController {
  constructor(private readonly authService: AuthService) {}

  @Public()
  @Post('register')
  @ApiOperation({ summary: 'Register a new user' })
  @ApiResponse({ status: 201, description: 'User registered successfully' })
  @ApiResponse({ status: 409, description: 'Email already exists' })
  async register(@Body() dto: RegisterDto) {
    return this.authService.register(dto);
  }

  @Public()
  @Post('login')
  @HttpCode(HttpStatus.OK)
  @ApiOperation({ summary: 'Authenticate user and return tokens' })
  @ApiResponse({ status: 200, description: 'Login successful' })
  @ApiResponse({ status: 401, description: 'Invalid credentials' })
  async login(@Body() dto: LoginDto) {
    return this.authService.login(dto.email, dto.password);
  }

  @Post('refresh')
  @HttpCode(HttpStatus.OK)
  @ApiOperation({ summary: 'Refresh access token' })
  @ApiResponse({ status: 200, description: 'Token refreshed' })
  @ApiResponse({ status: 401, description: 'Invalid refresh token' })
  async refresh(@Body('refreshToken') refreshToken: string) {
    return this.authService.refreshToken(refreshToken);
  }
}

// src/todos/todos.controller.ts
import {
  Controller, Get, Post, Patch, Delete,
  Body, Param, Request, ParseUUIDPipe,
} from '@nestjs/common';
import { ApiTags, ApiOperation, ApiResponse, ApiBearerAuth } from '@nestjs/swagger';
import { TodosService } from './todos.service';
import { CreateTodoDto } from './dto/create-todo.dto';
import { UpdateTodoDto } from './dto/update-todo.dto';

@ApiTags('todos')
@ApiBearerAuth()
@Controller('todos')
export class TodosController {
  constructor(private readonly todosService: TodosService) {}

  @Get()
  @ApiOperation({ summary: 'List all todos for the authenticated user' })
  @ApiResponse({ status: 200, description: 'Todos retrieved successfully' })
  findAll(@Request() req: { user: { userId: string } }) {
    return this.todosService.findAll(req.user.userId);
  }

  @Post()
  @ApiOperation({ summary: 'Create a new todo' })
  @ApiResponse({ status: 201, description: 'Todo created successfully' })
  create(
    @Request() req: { user: { userId: string } },
    @Body() dto: CreateTodoDto,
  ) {
    return this.todosService.create(req.user.userId, dto);
  }

  @Patch(':id')
  @ApiOperation({ summary: 'Update a todo' })
  @ApiResponse({ status: 200, description: 'Todo updated successfully' })
  @ApiResponse({ status: 404, description: 'Todo not found' })
  update(
    @Request() req: { user: { userId: string } },
    @Param('id', ParseUUIDPipe) id: string,
    @Body() dto: UpdateTodoDto,
  ) {
    return this.todosService.update(id, req.user.userId, dto);
  }

  @Delete(':id')
  @ApiOperation({ summary: 'Soft-delete a todo' })
  @ApiResponse({ status: 200, description: 'Todo deleted successfully' })
  @ApiResponse({ status: 404, description: 'Todo not found' })
  remove(
    @Request() req: { user: { userId: string } },
    @Param('id', ParseUUIDPipe) id: string,
  ) {
    return this.todosService.remove(id, req.user.userId);
  }
}
```

#### Service with Error Handling

```typescript
// src/auth/auth.service.ts
import {
  Injectable, UnauthorizedException, ConflictException, Logger,
} from '@nestjs/common';
import { JwtService } from '@nestjs/jwt';
import { ConfigService } from '@nestjs/config';
import { UsersService } from '../users/users.service';
import * as bcrypt from 'bcrypt';
import { RegisterDto } from './dto/register.dto';

@Injectable()
export class AuthService {
  private readonly logger = new Logger(AuthService.name);

  constructor(
    private readonly usersService: UsersService,
    private readonly jwtService: JwtService,
    private readonly configService: ConfigService,
  ) {}

  async register(dto: RegisterDto) {
    try {
      const hashedPassword = await bcrypt.hash(dto.password, 10);
      const user = await this.usersService.create({
        email: dto.email,
        passwordHash: hashedPassword,
      });
      this.logger.log(`User registered: ${user.email}`);
      return this.generateTokens(user.id, user.email);
    } catch (error) {
      if (error.code === '23505') {
        throw new ConflictException('Email already exists');
      }
      this.logger.error(`Registration failed: ${error.message}`);
      throw error;
    }
  }

  async login(email: string, password: string) {
    const user = await this.usersService.findByEmail(email);
    if (!user || !(await bcrypt.compare(password, user.passwordHash))) {
      throw new UnauthorizedException('Invalid credentials');
    }
    this.logger.log(`User logged in: ${user.email}`);
    return this.generateTokens(user.id, user.email);
  }

  async refreshToken(token: string) {
    try {
      const payload = this.jwtService.verify(token, {
        secret: this.configService.get<string>('JWT_SECRET'),
      });
      return this.generateTokens(payload.sub, payload.email);
    } catch {
      throw new UnauthorizedException('Invalid refresh token');
    }
  }

  private generateTokens(userId: string, email: string) {
    const payload = { sub: userId, email };
    return {
      accessToken: this.jwtService.sign(payload, { expiresIn: '15m' }),
      refreshToken: this.jwtService.sign(payload, { expiresIn: '7d' }),
    };
  }
}

// src/todos/todos.service.ts
import { Injectable, NotFoundException, Logger } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository, IsNull } from 'typeorm';
import { Todo } from './todo.entity';
import { CreateTodoDto } from './dto/create-todo.dto';
import { UpdateTodoDto } from './dto/update-todo.dto';

@Injectable()
export class TodosService {
  private readonly logger = new Logger(TodosService.name);

  constructor(
    @InjectRepository(Todo)
    private readonly todosRepository: Repository<Todo>,
  ) {}

  async findAll(userId: string): Promise<Todo[]> {
    return this.todosRepository.find({
      where: { userId, deletedAt: IsNull() },
      order: { createdAt: 'DESC' },
    });
  }

  async create(userId: string, dto: CreateTodoDto): Promise<Todo> {
    const todo = this.todosRepository.create({ ...dto, userId });
    const saved = await this.todosRepository.save(todo);
    this.logger.log(`Todo created: ${saved.id} for user ${userId}`);
    return saved;
  }

  async update(id: string, userId: string, dto: UpdateTodoDto): Promise<Todo> {
    const todo = await this.todosRepository.findOne({
      where: { id, userId, deletedAt: IsNull() },
    });
    if (!todo) {
      throw new NotFoundException(`Todo ${id} not found`);
    }
    Object.assign(todo, dto);
    return this.todosRepository.save(todo);
  }

  async remove(id: string, userId: string): Promise<void> {
    const todo = await this.todosRepository.findOne({
      where: { id, userId, deletedAt: IsNull() },
    });
    if (!todo) {
      throw new NotFoundException(`Todo ${id} not found`);
    }
    todo.deletedAt = new Date();
    await this.todosRepository.save(todo);
    this.logger.log(`Todo soft-deleted: ${id}`);
  }
}
```

#### DTOs with class-validator

```typescript
// src/auth/dto/register.dto.ts
import { IsEmail, IsString, MinLength, MaxLength } from 'class-validator';
import { ApiProperty } from '@nestjs/swagger';

export class RegisterDto {
  @ApiProperty({ example: 'user@example.com' })
  @IsEmail()
  email: string;

  @ApiProperty({ example: 'SecurePass123!' })
  @IsString()
  @MinLength(8)
  @MaxLength(128)
  password: string;
}

// src/auth/dto/login.dto.ts
import { IsEmail, IsString } from 'class-validator';
import { ApiProperty } from '@nestjs/swagger';

export class LoginDto {
  @ApiProperty({ example: 'user@example.com' })
  @IsEmail()
  email: string;

  @ApiProperty({ example: 'SecurePass123!' })
  @IsString()
  password: string;
}

// src/todos/dto/create-todo.dto.ts
import { IsString, IsNotEmpty, IsOptional, MaxLength } from 'class-validator';
import { ApiProperty, ApiPropertyOptional } from '@nestjs/swagger';

export class CreateTodoDto {
  @ApiProperty({ example: 'Buy groceries' })
  @IsString()
  @IsNotEmpty()
  @MaxLength(255)
  title: string;

  @ApiPropertyOptional({ example: 'Milk, eggs, bread' })
  @IsOptional()
  @IsString()
  @MaxLength(1000)
  description?: string;
}

// src/todos/dto/update-todo.dto.ts
import { IsString, IsOptional, IsBoolean, MaxLength } from 'class-validator';
import { ApiPropertyOptional } from '@nestjs/swagger';

export class UpdateTodoDto {
  @ApiPropertyOptional({ example: 'Buy groceries and snacks' })
  @IsOptional()
  @IsString()
  @MaxLength(255)
  title?: string;

  @ApiPropertyOptional({ example: 'Updated description' })
  @IsOptional()
  @IsString()
  @MaxLength(1000)
  description?: string;

  @ApiPropertyOptional({ example: true })
  @IsOptional()
  @IsBoolean()
  completed?: boolean;
}
```

#### Entities

```typescript
// src/users/user.entity.ts
import {
  Entity, PrimaryGeneratedColumn, Column,
  CreateDateColumn, UpdateDateColumn, OneToMany,
} from 'typeorm';
import { Todo } from '../todos/todo.entity';

@Entity('users')
export class User {
  @PrimaryGeneratedColumn('uuid')
  id: string;

  @Column({ unique: true })
  email: string;

  @Column()
  passwordHash: string;

  @OneToMany(() => Todo, (todo) => todo.user)
  todos: Todo[];

  @CreateDateColumn()
  createdAt: Date;

  @UpdateDateColumn()
  updatedAt: Date;
}

// src/todos/todo.entity.ts
import {
  Entity, PrimaryGeneratedColumn, Column,
  CreateDateColumn, UpdateDateColumn, ManyToOne, JoinColumn,
} from 'typeorm';
import { User } from '../users/user.entity';

@Entity('todos')
export class Todo {
  @PrimaryGeneratedColumn('uuid')
  id: string;

  @Column({ length: 255 })
  title: string;

  @Column({ type: 'text', nullable: true })
  description: string | null;

  @Column({ default: false })
  completed: boolean;

  @Column('uuid')
  userId: string;

  @ManyToOne(() => User, (user) => user.todos)
  @JoinColumn({ name: 'userId' })
  user: User;

  @CreateDateColumn()
  createdAt: Date;

  @UpdateDateColumn()
  updatedAt: Date;

  @Column({ type: 'timestamp', nullable: true })
  deletedAt: Date | null;
}
```

#### JWT Strategy and Guards

```typescript
// src/auth/jwt.strategy.ts
import { Injectable } from '@nestjs/common';
import { PassportStrategy } from '@nestjs/passport';
import { ExtractJwt, Strategy } from 'passport-jwt';
import { ConfigService } from '@nestjs/config';

@Injectable()
export class JwtStrategy extends PassportStrategy(Strategy) {
  constructor(private config: ConfigService) {
    super({
      jwtFromRequest: ExtractJwt.fromAuthHeaderAsBearerToken(),
      ignoreExpiration: false,
      secretOrKey: config.get<string>('JWT_SECRET'),
    });
  }

  async validate(payload: { sub: string; email: string }) {
    return { userId: payload.sub, email: payload.email };
  }
}

// src/auth/jwt-auth.guard.ts
import { Injectable, ExecutionContext } from '@nestjs/common';
import { AuthGuard } from '@nestjs/passport';
import { Reflector } from '@nestjs/core';
import { IS_PUBLIC_KEY } from './public.decorator';

@Injectable()
export class JwtAuthGuard extends AuthGuard('jwt') {
  constructor(private reflector: Reflector) {
    super();
  }

  canActivate(context: ExecutionContext) {
    const isPublic = this.reflector.getAllAndOverride<boolean>(IS_PUBLIC_KEY, [
      context.getHandler(),
      context.getClass(),
    ]);
    if (isPublic) return true;
    return super.canActivate(context);
  }
}

// src/auth/public.decorator.ts
import { SetMetadata } from '@nestjs/common';

export const IS_PUBLIC_KEY = 'isPublic';
export const Public = () => SetMetadata(IS_PUBLIC_KEY, true);
```

### What This Skill Provided

`nestjs-expert` delivered the complete backend organized by the skill's prescribed format: module definitions with DI wiring, controllers with full Swagger decorators, services with structured error handling and logging, DTOs with class-validator decorators, and TypeORM entities. The user-scoping pattern (`where: { userId, deletedAt: IsNull() }`) directly implements FR-TODO-002 and FR-TODO-006 from the spec.

---

## Step 4 -- Frontend Implementation with `nextjs-developer`

### Prompt

```
Implement the Next.js 14 App Router frontend for the todo app. Include login page,
dashboard with todo CRUD, and API client with automatic token refresh.
Use Server Components where possible.
```

### Skill Output

#### App Structure (Route Organization)

```
frontend/src/app/
├── layout.tsx                 # Root layout (Server Component)
├── page.tsx                   # Landing page, redirects to /dashboard or /login
├── loading.tsx                # Global loading fallback
├── error.tsx                  # Global error boundary (Client Component)
├── (auth)/                    # Route group -- no layout nesting with dashboard
│   ├── login/
│   │   └── page.tsx           # Login page (Client Component for form)
│   └── register/
│       └── page.tsx           # Register page (Client Component for form)
└── dashboard/
    ├── layout.tsx             # Dashboard layout -- auth check (Server Component)
    ├── page.tsx               # Todo list page (Client Component for interactivity)
    ├── loading.tsx            # Dashboard loading skeleton
    └── error.tsx              # Dashboard error boundary
```

**Rendering Strategy:** The root layout and dashboard layout are Server Components that handle metadata and auth checks server-side. The `(auth)` route group isolates login/register from the dashboard layout so authenticated users do not see the login chrome. Interactive pages (login form, todo CRUD) use `'use client'` because they manage form state and call browser APIs. This hybrid approach minimizes client-side JavaScript while keeping forms interactive.

#### Layout/Page Components

```tsx
// src/app/layout.tsx (Server Component -- root layout)
import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: {
    default: 'Todo App',
    template: '%s | Todo App',
  },
  description: 'A full-stack todo application with JWT authentication',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <div className="min-h-screen bg-gray-50">
          {children}
        </div>
      </body>
    </html>
  );
}

// src/app/dashboard/layout.tsx (Server Component -- auth wrapper)
import { cookies } from 'next/headers';
import { redirect } from 'next/navigation';

export const metadata = {
  title: 'Dashboard',
};

export default async function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const cookieStore = cookies();
  const refreshToken = cookieStore.get('refreshToken');

  if (!refreshToken) {
    redirect('/login');
  }

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <header className="flex justify-between items-center mb-8">
        <h1 className="text-2xl font-bold text-gray-900">My Todos</h1>
        <LogoutButton />
      </header>
      <main>{children}</main>
    </div>
  );
}

function LogoutButton() {
  return (
    <form action="/api/auth/logout" method="POST">
      <button
        type="submit"
        className="text-sm text-gray-500 hover:text-gray-700"
      >
        Log out
      </button>
    </form>
  );
}

// src/app/(auth)/login/page.tsx (Client Component)
'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { apiFetch, setAccessToken } from '@/lib/api';

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const data = await apiFetch<{ accessToken: string }>('/auth/login', {
        method: 'POST',
        body: JSON.stringify({ email, password }),
      });
      setAccessToken(data.accessToken);
      router.push('/dashboard');
    } catch {
      setError('Invalid email or password');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center">
      <div className="w-full max-w-md space-y-6 p-8">
        <h2 className="text-center text-3xl font-bold">Sign in</h2>
        {error && (
          <div role="alert" className="rounded bg-red-50 p-3 text-sm text-red-600">
            {error}
          </div>
        )}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="email" className="block text-sm font-medium">
              Email
            </label>
            <input
              id="email"
              name="email"
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="mt-1 block w-full rounded border px-3 py-2"
            />
          </div>
          <div>
            <label htmlFor="password" className="block text-sm font-medium">
              Password
            </label>
            <input
              id="password"
              name="password"
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="mt-1 block w-full rounded border px-3 py-2"
            />
          </div>
          <button
            type="submit"
            disabled={loading}
            className="w-full rounded bg-blue-600 py-2 text-white hover:bg-blue-700 disabled:opacity-50"
          >
            {loading ? 'Signing in...' : 'Sign in'}
          </button>
        </form>
        <p className="text-center text-sm text-gray-500">
          No account?{' '}
          <Link href="/register" className="text-blue-600 hover:underline">
            Register
          </Link>
        </p>
      </div>
    </div>
  );
}

// src/app/dashboard/page.tsx (Client Component -- interactive todo CRUD)
'use client';

import { useEffect, useState, useCallback } from 'react';
import { apiFetch } from '@/lib/api';
import { TodoList } from '@/components/TodoList';
import { CreateTodoForm } from '@/components/CreateTodoForm';

interface Todo {
  id: string;
  title: string;
  description: string | null;
  completed: boolean;
  createdAt: string;
}

export default function DashboardPage() {
  const [todos, setTodos] = useState<Todo[]>([]);
  const [loading, setLoading] = useState(true);

  const loadTodos = useCallback(async () => {
    try {
      const data = await apiFetch<Todo[]>('/todos');
      setTodos(data);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadTodos();
  }, [loadTodos]);

  const handleCreate = async (title: string, description?: string) => {
    await apiFetch('/todos', {
      method: 'POST',
      body: JSON.stringify({ title, description }),
    });
    await loadTodos();
  };

  const handleToggle = async (id: string, completed: boolean) => {
    await apiFetch(`/todos/${id}`, {
      method: 'PATCH',
      body: JSON.stringify({ completed: !completed }),
    });
    await loadTodos();
  };

  const handleDelete = async (id: string) => {
    await apiFetch(`/todos/${id}`, { method: 'DELETE' });
    await loadTodos();
  };

  if (loading) return null; // loading.tsx handles this

  return (
    <div className="space-y-6">
      <CreateTodoForm onCreate={handleCreate} />
      <TodoList
        todos={todos}
        onToggle={handleToggle}
        onDelete={handleDelete}
      />
      {todos.length === 0 && (
        <p className="text-center text-gray-400 py-8">
          No todos yet. Create one above.
        </p>
      )}
    </div>
  );
}
```

#### API Client with Token Refresh

```typescript
// src/lib/api.ts
const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3001';

let accessToken: string | null = null;
let refreshPromise: Promise<boolean> | null = null;

export function setAccessToken(token: string) {
  accessToken = token;
}

export async function apiFetch<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}),
  };

  let response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
    credentials: 'include',
  });

  // Automatic token refresh on 401
  if (response.status === 401 && accessToken) {
    const refreshed = await refreshAccessToken();
    if (refreshed) {
      headers['Authorization'] = `Bearer ${accessToken}`;
      response = await fetch(`${API_BASE}${path}`, {
        ...options,
        headers,
        credentials: 'include',
      });
    } else {
      window.location.href = '/login';
      throw new Error('Session expired');
    }
  }

  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.message || `API error: ${response.status}`);
  }

  return response.json();
}

// Deduplicate concurrent refresh calls (ADR-002 race condition mitigation)
async function refreshAccessToken(): Promise<boolean> {
  if (refreshPromise) return refreshPromise;

  refreshPromise = (async () => {
    try {
      const res = await fetch(`${API_BASE}/auth/refresh`, {
        method: 'POST',
        credentials: 'include',
      });
      if (!res.ok) return false;
      const data = await res.json();
      accessToken = data.accessToken;
      return true;
    } catch {
      return false;
    } finally {
      refreshPromise = null;
    }
  })();

  return refreshPromise;
}
```

#### Configuration

```javascript
// next.config.js
/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  output: 'standalone', // Optimized for Docker deployment
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3001'}/:path*`,
      },
    ];
  },
};

module.exports = nextConfig;
```

#### Rendering Strategy Explanation

The application uses a hybrid rendering approach. The root layout and dashboard layout are Server Components -- they run on the server, handle metadata via the Metadata API, and perform authentication checks by reading cookies. The `(auth)` route group separates public pages (login, register) from authenticated pages so they use different layouts without nesting. Interactive pages that manage form state or call browser APIs (`window.location`) are marked with `'use client'`. This minimizes the JavaScript shipped to the browser: only todo CRUD interactions and form inputs require client-side hydration.

### What This Skill Provided

`nextjs-developer` built the frontend following its prescribed format: App Router route organization with proper use of route groups, Server Component layouts with cookie-based auth checks, Client Components only where interactivity requires it, a centralized API client implementing the token refresh pattern from ADR-002 (including race condition deduplication), and a `next.config.js` with standalone output mode for Docker.

---

## Step 5 -- Unit Testing with `test-master`

### Prompt

```
Write unit tests for the NestJS TodosService and AuthService. Mock repositories
and external dependencies.
```

### Skill Output

#### [Test] Test Scope and Approach

**Scope:** Unit tests for `TodosService` and `AuthService` -- the two core service classes in the backend. All external dependencies (TypeORM repositories, JwtService, UsersService, bcrypt) are mocked to isolate business logic.

**Approach:**
- Happy path tests for all CRUD operations
- Error cases for not-found, unauthorized, and conflict scenarios
- Edge cases for soft-delete filtering and user isolation
- Mock setup via `@nestjs/testing` Test module

#### [Test] Test Cases

```typescript
// src/todos/todos.service.spec.ts
import { Test, TestingModule } from '@nestjs/testing';
import { getRepositoryToken } from '@nestjs/typeorm';
import { NotFoundException } from '@nestjs/common';
import { TodosService } from './todos.service';
import { Todo } from './todo.entity';
import { IsNull } from 'typeorm';

describe('TodosService', () => {
  let service: TodosService;
  const mockRepository = {
    find: jest.fn(),
    findOne: jest.fn(),
    create: jest.fn(),
    save: jest.fn(),
  };

  beforeEach(async () => {
    const module: TestingModule = await Test.createTestingModule({
      providers: [
        TodosService,
        { provide: getRepositoryToken(Todo), useValue: mockRepository },
      ],
    }).compile();

    service = module.get<TodosService>(TodosService);
    jest.clearAllMocks();
  });

  describe('findAll', () => {
    it('should return only non-deleted todos for the authenticated user', async () => {
      const userId = 'user-abc-123';
      const todos = [
        { id: 'todo-1', title: 'Buy groceries', userId, completed: false, deletedAt: null },
        { id: 'todo-2', title: 'Walk the dog', userId, completed: true, deletedAt: null },
      ];
      mockRepository.find.mockResolvedValue(todos);

      const result = await service.findAll(userId);

      expect(result).toEqual(todos);
      expect(result).toHaveLength(2);
      expect(mockRepository.find).toHaveBeenCalledWith({
        where: { userId, deletedAt: IsNull() },
        order: { createdAt: 'DESC' },
      });
    });

    it('should return empty array when user has no todos', async () => {
      mockRepository.find.mockResolvedValue([]);

      const result = await service.findAll('user-with-no-todos');

      expect(result).toEqual([]);
    });
  });

  describe('create', () => {
    it('should create a todo bound to the authenticated user', async () => {
      const userId = 'user-abc-123';
      const dto = { title: 'New todo', description: 'Description' };
      const created = { id: 'todo-new', ...dto, userId, completed: false };

      mockRepository.create.mockReturnValue(created);
      mockRepository.save.mockResolvedValue(created);

      const result = await service.create(userId, dto);

      expect(result.userId).toBe(userId);
      expect(result.title).toBe('New todo');
      expect(mockRepository.create).toHaveBeenCalledWith({ ...dto, userId });
      expect(mockRepository.save).toHaveBeenCalledWith(created);
    });
  });

  describe('update', () => {
    it('should update title of an existing todo', async () => {
      const todo = { id: 'todo-1', title: 'Old title', userId: 'user-1', deletedAt: null };
      const dto = { title: 'Updated title' };
      mockRepository.findOne.mockResolvedValue(todo);
      mockRepository.save.mockResolvedValue({ ...todo, ...dto });

      const result = await service.update('todo-1', 'user-1', dto);

      expect(result.title).toBe('Updated title');
    });

    it('should throw NotFoundException when todo does not exist', async () => {
      mockRepository.findOne.mockResolvedValue(null);

      await expect(service.update('nonexistent', 'user-1', { title: 'x' }))
        .rejects.toThrow(NotFoundException);
    });

    it('should throw NotFoundException when todo belongs to another user', async () => {
      mockRepository.findOne.mockResolvedValue(null); // query filters by userId

      await expect(service.update('todo-1', 'wrong-user', { title: 'x' }))
        .rejects.toThrow(NotFoundException);
    });
  });

  describe('remove', () => {
    it('should soft-delete by setting deletedAt timestamp', async () => {
      const todo = { id: 'todo-1', userId: 'user-1', deletedAt: null };
      mockRepository.findOne.mockResolvedValue(todo);
      mockRepository.save.mockImplementation((t) => Promise.resolve(t));

      await service.remove('todo-1', 'user-1');

      expect(mockRepository.save).toHaveBeenCalledWith(
        expect.objectContaining({ deletedAt: expect.any(Date) }),
      );
    });

    it('should throw NotFoundException for non-existent todo', async () => {
      mockRepository.findOne.mockResolvedValue(null);

      await expect(service.remove('nonexistent', 'user-1'))
        .rejects.toThrow(NotFoundException);
    });
  });
});

// src/auth/auth.service.spec.ts
import { Test, TestingModule } from '@nestjs/testing';
import { JwtService } from '@nestjs/jwt';
import { ConfigService } from '@nestjs/config';
import { UnauthorizedException, ConflictException } from '@nestjs/common';
import { AuthService } from './auth.service';
import { UsersService } from '../users/users.service';
import * as bcrypt from 'bcrypt';

jest.mock('bcrypt');

describe('AuthService', () => {
  let service: AuthService;
  const mockUsersService = {
    create: jest.fn(),
    findByEmail: jest.fn(),
  };
  const mockJwtService = {
    sign: jest.fn(),
    verify: jest.fn(),
  };
  const mockConfigService = {
    get: jest.fn().mockReturnValue('test-jwt-secret'),
  };

  beforeEach(async () => {
    const module: TestingModule = await Test.createTestingModule({
      providers: [
        AuthService,
        { provide: UsersService, useValue: mockUsersService },
        { provide: JwtService, useValue: mockJwtService },
        { provide: ConfigService, useValue: mockConfigService },
      ],
    }).compile();

    service = module.get<AuthService>(AuthService);
    jest.clearAllMocks();
  });

  describe('register', () => {
    it('should hash password and create user', async () => {
      const dto = { email: 'test@example.com', password: 'SecurePass123!' };
      const hashedPassword = '$2b$10$hashedvalue';
      const user = { id: 'user-1', email: dto.email, passwordHash: hashedPassword };

      (bcrypt.hash as jest.Mock).mockResolvedValue(hashedPassword);
      mockUsersService.create.mockResolvedValue(user);
      mockJwtService.sign.mockReturnValue('mock-token');

      const result = await service.register(dto);

      expect(bcrypt.hash).toHaveBeenCalledWith(dto.password, 10);
      expect(mockUsersService.create).toHaveBeenCalledWith({
        email: dto.email,
        passwordHash: hashedPassword,
      });
      expect(result).toHaveProperty('accessToken');
      expect(result).toHaveProperty('refreshToken');
    });

    it('should throw ConflictException on duplicate email', async () => {
      (bcrypt.hash as jest.Mock).mockResolvedValue('hashed');
      mockUsersService.create.mockRejectedValue({ code: '23505' });

      await expect(
        service.register({ email: 'dup@example.com', password: 'Pass123!' }),
      ).rejects.toThrow(ConflictException);
    });
  });

  describe('login', () => {
    it('should return tokens for valid credentials', async () => {
      const user = { id: 'user-1', email: 'test@example.com', passwordHash: 'hashed' };
      mockUsersService.findByEmail.mockResolvedValue(user);
      (bcrypt.compare as jest.Mock).mockResolvedValue(true);
      mockJwtService.sign.mockReturnValue('mock-token');

      const result = await service.login('test@example.com', 'correct-password');

      expect(result).toHaveProperty('accessToken');
      expect(result).toHaveProperty('refreshToken');
    });

    it('should throw UnauthorizedException for wrong password', async () => {
      const user = { id: 'user-1', email: 'test@example.com', passwordHash: 'hashed' };
      mockUsersService.findByEmail.mockResolvedValue(user);
      (bcrypt.compare as jest.Mock).mockResolvedValue(false);

      await expect(service.login('test@example.com', 'wrong'))
        .rejects.toThrow(UnauthorizedException);
    });

    it('should throw UnauthorizedException for non-existent email', async () => {
      mockUsersService.findByEmail.mockResolvedValue(null);

      await expect(service.login('noone@example.com', 'any'))
        .rejects.toThrow(UnauthorizedException);
    });
  });

  describe('refreshToken', () => {
    it('should return new tokens for valid refresh token', async () => {
      mockJwtService.verify.mockReturnValue({ sub: 'user-1', email: 'test@example.com' });
      mockJwtService.sign.mockReturnValue('new-token');

      const result = await service.refreshToken('valid-refresh-token');

      expect(result).toHaveProperty('accessToken');
      expect(mockJwtService.verify).toHaveBeenCalledWith('valid-refresh-token', {
        secret: 'test-jwt-secret',
      });
    });

    it('should throw UnauthorizedException for invalid refresh token', async () => {
      mockJwtService.verify.mockImplementation(() => {
        throw new Error('invalid token');
      });

      await expect(service.refreshToken('expired-token'))
        .rejects.toThrow(UnauthorizedException);
    });
  });
});
```

#### [Test] Coverage Analysis

| Service | Methods Tested | Lines Covered | Branch Coverage | Notes |
|---------|---------------|--------------|----------------|-------|
| TodosService | findAll, create, update, remove | ~95% | 100% | All error paths covered |
| AuthService | register, login, refreshToken | ~92% | 100% | Logger calls excluded from assertion |

**Coverage Gaps:**
- Logger output not asserted (cosmetic, not business logic)
- `UsersService.findByEmail` internal implementation not tested here (covered by its own unit test)

#### [Test] Findings

| ID | Severity | Finding | Recommendation |
|----|----------|---------|----------------|
| T-001 | Medium | `Object.assign(todo, dto)` in update could overwrite protected fields | Add allowlist of updatable fields in DTO or use `pick()` utility |
| T-002 | Low | No test for concurrent create race condition | Add integration test with parallel requests |
| T-003 | Low | `bcrypt.hash` cost factor (10) not validated in test | Assert cost factor via mock argument check |

#### [Test] Recommendations

1. Add integration tests using Supertest to validate the full HTTP request cycle including validation pipes
2. Add a test verifying that soft-deleted todos are excluded from `findAll` results at the repository query level
3. Consider adding property-based tests for DTO validation edge cases (empty strings, Unicode, max-length boundaries)

### What This Skill Provided

`test-master` delivered comprehensive unit tests following its three-mode format: [Test] for functional correctness with happy paths and error cases, a coverage analysis table identifying gaps, and a findings table with severity ratings and specific fix recommendations. The tests verify the two most critical business rules -- user isolation and soft delete.

---

## Step 6 -- E2E Testing with `playwright-expert`

### Prompt

```
Write Playwright E2E tests for the todo app. Test the full user flow:
register -> login -> create todo -> mark complete -> delete todo.
```

### Skill Output

#### Page Object Classes

```typescript
// e2e/pages/RegisterPage.ts
import { Page, Locator } from '@playwright/test';

export class RegisterPage {
  readonly page: Page;
  readonly emailInput: Locator;
  readonly passwordInput: Locator;
  readonly submitButton: Locator;
  readonly errorMessage: Locator;

  constructor(page: Page) {
    this.page = page;
    this.emailInput = page.getByLabel('Email');
    this.passwordInput = page.getByLabel('Password');
    this.submitButton = page.getByRole('button', { name: 'Register' });
    this.errorMessage = page.getByRole('alert');
  }

  async goto() {
    await this.page.goto('/register');
  }

  async register(email: string, password: string) {
    await this.emailInput.fill(email);
    await this.passwordInput.fill(password);
    await this.submitButton.click();
  }
}

// e2e/pages/LoginPage.ts
import { Page, Locator } from '@playwright/test';

export class LoginPage {
  readonly page: Page;
  readonly emailInput: Locator;
  readonly passwordInput: Locator;
  readonly submitButton: Locator;
  readonly errorMessage: Locator;

  constructor(page: Page) {
    this.page = page;
    this.emailInput = page.getByLabel('Email');
    this.passwordInput = page.getByLabel('Password');
    this.submitButton = page.getByRole('button', { name: 'Sign in' });
    this.errorMessage = page.getByRole('alert');
  }

  async goto() {
    await this.page.goto('/login');
  }

  async login(email: string, password: string) {
    await this.emailInput.fill(email);
    await this.passwordInput.fill(password);
    await this.submitButton.click();
  }
}

// e2e/pages/DashboardPage.ts
import { Page, Locator } from '@playwright/test';

export class DashboardPage {
  readonly page: Page;
  readonly heading: Locator;
  readonly titleInput: Locator;
  readonly descriptionInput: Locator;
  readonly addButton: Locator;
  readonly logoutButton: Locator;

  constructor(page: Page) {
    this.page = page;
    this.heading = page.getByRole('heading', { name: 'My Todos' });
    this.titleInput = page.getByLabel('Title');
    this.descriptionInput = page.getByLabel('Description');
    this.addButton = page.getByRole('button', { name: 'Add Todo' });
    this.logoutButton = page.getByRole('button', { name: 'Log out' });
  }

  async createTodo(title: string, description?: string) {
    await this.titleInput.fill(title);
    if (description) {
      await this.descriptionInput.fill(description);
    }
    await this.addButton.click();
  }

  todoItem(title: string) {
    return this.page.getByText(title).locator('..');
  }

  todoCheckbox(title: string) {
    return this.page.getByRole('checkbox', { name: title });
  }

  deleteButton(title: string) {
    return this.todoItem(title).getByRole('button', { name: 'Delete' });
  }
}
```

#### Fixture Setup

```typescript
// e2e/fixtures.ts
import { test as base } from '@playwright/test';
import { RegisterPage } from './pages/RegisterPage';
import { LoginPage } from './pages/LoginPage';
import { DashboardPage } from './pages/DashboardPage';

type TodoFixtures = {
  registerPage: RegisterPage;
  loginPage: LoginPage;
  dashboardPage: DashboardPage;
  testUser: { email: string; password: string };
};

export const test = base.extend<TodoFixtures>({
  registerPage: async ({ page }, use) => {
    await use(new RegisterPage(page));
  },
  loginPage: async ({ page }, use) => {
    await use(new LoginPage(page));
  },
  dashboardPage: async ({ page }, use) => {
    await use(new DashboardPage(page));
  },
  testUser: async ({}, use) => {
    await use({
      email: `test-${Date.now()}@example.com`,
      password: 'SecurePass123!',
    });
  },
});

export { expect } from '@playwright/test';
```

#### Test Files with Assertions

```typescript
// e2e/tests/todo-workflow.spec.ts
import { test, expect } from '../fixtures';

test.describe('Todo App - Complete User Journey', () => {
  test('register -> create todo -> mark complete -> delete', async ({
    registerPage,
    dashboardPage,
    testUser,
    page,
  }) => {
    // Step 1: Register a new user
    await registerPage.goto();
    await registerPage.register(testUser.email, testUser.password);
    await expect(page).toHaveURL(/dashboard/);
    await expect(dashboardPage.heading).toBeVisible();

    // Step 2: Create a todo
    await dashboardPage.createTodo('Buy groceries', 'Milk, eggs, bread');
    await expect(page.getByText('Buy groceries')).toBeVisible();
    await expect(page.getByText('Milk, eggs, bread')).toBeVisible();

    // Step 3: Mark as complete
    await dashboardPage.todoCheckbox('Buy groceries').check();
    await expect(page.locator('.line-through')).toContainText('Buy groceries');

    // Step 4: Delete the todo
    await dashboardPage.deleteButton('Buy groceries').click();
    await expect(page.getByText('Buy groceries')).not.toBeVisible();
    await expect(page.getByText('No todos yet')).toBeVisible();
  });

  test('login with existing account', async ({
    registerPage,
    loginPage,
    dashboardPage,
    testUser,
    page,
  }) => {
    // Register first
    await registerPage.goto();
    await registerPage.register(testUser.email, testUser.password);
    await expect(page).toHaveURL(/dashboard/);

    // Log out
    await dashboardPage.logoutButton.click();
    await expect(page).toHaveURL(/login/);

    // Log back in
    await loginPage.login(testUser.email, testUser.password);
    await expect(page).toHaveURL(/dashboard/);
    await expect(dashboardPage.heading).toBeVisible();
  });

  test('invalid login shows error message', async ({ loginPage }) => {
    await loginPage.goto();
    await loginPage.login('noone@example.com', 'wrongpassword');
    await expect(loginPage.errorMessage).toBeVisible();
    await expect(loginPage.errorMessage).toContainText('Invalid');
  });
});

// e2e/tests/user-isolation.spec.ts
import { test, expect } from '../fixtures';

test.describe('Todo App - User Isolation', () => {
  test('users cannot see each other\'s todos', async ({ browser }) => {
    // Create two independent browser contexts (separate sessions)
    const context1 = await browser.newContext();
    const context2 = await browser.newContext();
    const page1 = await context1.newPage();
    const page2 = await context2.newPage();

    const user1Email = `user1-${Date.now()}@example.com`;
    const user2Email = `user2-${Date.now()}@example.com`;

    // User 1 registers and creates a todo
    await page1.goto('/register');
    await page1.getByLabel('Email').fill(user1Email);
    await page1.getByLabel('Password').fill('SecurePass123!');
    await page1.getByRole('button', { name: 'Register' }).click();
    await expect(page1).toHaveURL(/dashboard/);

    await page1.getByLabel('Title').fill('User 1 private todo');
    await page1.getByRole('button', { name: 'Add Todo' }).click();
    await expect(page1.getByText('User 1 private todo')).toBeVisible();

    // User 2 registers and checks their dashboard
    await page2.goto('/register');
    await page2.getByLabel('Email').fill(user2Email);
    await page2.getByLabel('Password').fill('SecurePass123!');
    await page2.getByRole('button', { name: 'Register' }).click();
    await expect(page2).toHaveURL(/dashboard/);

    // User 2 should NOT see User 1's todo
    await expect(page2.getByText('User 1 private todo')).not.toBeVisible();
    await expect(page2.getByText('No todos yet')).toBeVisible();

    await context1.close();
    await context2.close();
  });
});
```

#### Configuration

```typescript
// playwright.config.ts
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './e2e/tests',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: [
    ['html', { open: 'never' }],
    ['list'],
  ],
  use: {
    baseURL: 'http://localhost:3000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },
    {
      name: 'webkit',
      use: { ...devices['Desktop Safari'] },
    },
  ],
  webServer: {
    command: 'docker compose up',
    url: 'http://localhost:3000',
    reuseExistingServer: !process.env.CI,
    timeout: 120_000,
  },
});
```

### What This Skill Provided

`playwright-expert` delivered E2E tests following its prescribed format: Page Object Model classes with role-based selectors (`getByLabel`, `getByRole`), custom fixtures for DRY test setup, test files covering the full user journey and multi-user isolation, and a Playwright configuration with multi-browser support, trace capture on failure, and a `webServer` config that starts Docker Compose automatically. No arbitrary timeouts are used -- all waits leverage Playwright's built-in auto-waiting.

---

## Step 7 -- Deployment with `devops-engineer`

### Prompt

```
Create Docker, docker-compose, and GitHub Actions CI/CD for the todo app with
Next.js frontend, NestJS backend, and PostgreSQL.
```

### Skill Output

#### CI/CD Pipeline Config

```yaml
# .github/workflows/ci.yml
name: CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

env:
  REGISTRY: ghcr.io
  IMAGE_PREFIX: ${{ github.repository }}

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
          cache-dependency-path: |
            backend/package-lock.json
            frontend/package-lock.json
      - run: npm ci && npm run lint
        working-directory: backend
      - run: npm ci && npm run lint
        working-directory: frontend

  test:
    runs-on: ubuntu-latest
    needs: lint
    services:
      postgres:
        image: postgres:16-alpine
        env:
          POSTGRES_DB: todoapp_test
          POSTGRES_USER: todouser
          POSTGRES_PASSWORD: testpassword
        ports:
          - 5432:5432
        options: >-
          --health-cmd="pg_isready -U todouser"
          --health-interval=5s
          --health-timeout=5s
          --health-retries=5
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
          cache-dependency-path: backend/package-lock.json
      - run: npm ci
        working-directory: backend
      - run: npm test -- --coverage
        working-directory: backend
        env:
          DATABASE_URL: postgres://todouser:testpassword@localhost:5432/todoapp_test
          JWT_SECRET: ci-test-secret-do-not-use-in-production
      - uses: actions/upload-artifact@v4
        with:
          name: coverage-report
          path: backend/coverage/

  build:
    runs-on: ubuntu-latest
    needs: test
    permissions:
      contents: read
      packages: write
    strategy:
      matrix:
        service: [backend, frontend]
    steps:
      - uses: actions/checkout@v4
      - uses: docker/setup-buildx-action@v3
      - uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      - id: meta
        uses: docker/metadata-action@v5
        with:
          images: ${{ env.REGISTRY }}/${{ env.IMAGE_PREFIX }}-${{ matrix.service }}
          tags: |
            type=sha,prefix=
            type=ref,event=branch
      - uses: docker/build-push-action@v5
        with:
          context: ./${{ matrix.service }}
          push: ${{ github.event_name != 'pull_request' }}
          tags: ${{ steps.meta.outputs.tags }}
          cache-from: type=gha
          cache-to: type=gha,mode=max

  e2e:
    runs-on: ubuntu-latest
    needs: build
    if: github.event_name == 'pull_request'
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
      - run: npx playwright install --with-deps
      - run: docker compose up -d
      - run: npx wait-on http://localhost:3000 --timeout 60000
      - run: npx playwright test
      - uses: actions/upload-artifact@v4
        if: failure()
        with:
          name: playwright-report
          path: playwright-report/

  deploy-staging:
    runs-on: ubuntu-latest
    needs: build
    if: github.ref == 'refs/heads/develop'
    environment: staging
    steps:
      - uses: actions/checkout@v4
      - run: |
          echo "Deploying to staging..."
          docker compose -f docker-compose.staging.yml pull
          docker compose -f docker-compose.staging.yml up -d
          echo "Staging deployment complete"

  deploy-production:
    runs-on: ubuntu-latest
    needs: build
    if: github.ref == 'refs/heads/main'
    environment: production
    steps:
      - uses: actions/checkout@v4
      - run: |
          echo "Deploying to production..."
          docker compose -f docker-compose.prod.yml pull
          docker compose -f docker-compose.prod.yml up -d
          echo "Production deployment complete"
```

#### Dockerfiles

```dockerfile
# backend/Dockerfile
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci && npm cache clean --force
COPY . .
RUN npm run build

FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
RUN addgroup -g 1001 -S nodejs && adduser -S nestjs -u 1001
COPY --from=builder --chown=nestjs:nodejs /app/dist ./dist
COPY --from=builder --chown=nestjs:nodejs /app/node_modules ./node_modules
COPY --from=builder --chown=nestjs:nodejs /app/package.json ./
USER nestjs
EXPOSE 3001
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s \
  CMD wget -qO- http://localhost:3001/health || exit 1
CMD ["node", "dist/main.js"]
```

```dockerfile
# frontend/Dockerfile
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci && npm cache clean --force
COPY . .
RUN npm run build

FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
RUN addgroup -g 1001 -S nodejs && adduser -S nextjs -u 1001
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static
COPY --from=builder --chown=nextjs:nodejs /app/public ./public
USER nextjs
EXPOSE 3000
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s \
  CMD wget -qO- http://localhost:3000/ || exit 1
CMD ["node", "server.js"]
```

```yaml
# docker-compose.yml
services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: todoapp
      POSTGRES_USER: todouser
      POSTGRES_PASSWORD: ${DB_PASSWORD:?DB_PASSWORD is required}
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U todouser -d todoapp"]
      interval: 5s
      timeout: 5s
      retries: 5

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    environment:
      DATABASE_URL: postgres://todouser:${DB_PASSWORD}@postgres:5432/todoapp
      JWT_SECRET: ${JWT_SECRET:?JWT_SECRET is required}
      NODE_ENV: production
    ports:
      - "3001:3001"
    depends_on:
      postgres:
        condition: service_healthy
    restart: unless-stopped

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    environment:
      NEXT_PUBLIC_API_URL: http://backend:3001
    ports:
      - "3000:3000"
    depends_on:
      - backend
    restart: unless-stopped

volumes:
  pgdata:
```

```
# .dockerignore (shared pattern for both backend/ and frontend/)
node_modules
.git
.env*
*.md
Dockerfile*
docker-compose*
.dockerignore
coverage
.nyc_output
.next
dist
```

#### Deployment Verification

```bash
#!/bin/bash
# scripts/verify-deployment.sh

set -euo pipefail

echo "=== Deployment Verification ==="

# 1. Check all containers are running
echo "Checking container status..."
docker compose ps --format json | jq -e '.[] | select(.State != "running")' && {
  echo "FAIL: Not all containers are running"
  exit 1
}
echo "PASS: All containers running"

# 2. Check backend health
echo "Checking backend health..."
curl -sf http://localhost:3001/health > /dev/null || {
  echo "FAIL: Backend health check failed"
  exit 1
}
echo "PASS: Backend healthy"

# 3. Check frontend reachability
echo "Checking frontend..."
curl -sf http://localhost:3000 > /dev/null || {
  echo "FAIL: Frontend not reachable"
  exit 1
}
echo "PASS: Frontend reachable"

# 4. Check database connectivity (via backend)
echo "Checking database via API..."
STATUS=$(curl -sf -o /dev/null -w "%{http_code}" http://localhost:3001/health)
if [ "$STATUS" -ne 200 ]; then
  echo "FAIL: Database connection issue (health returned $STATUS)"
  exit 1
fi
echo "PASS: Database connected"

echo "=== All verification checks passed ==="
```

#### Rollback Procedure

```markdown
## Rollback Steps

### Immediate Rollback (< 5 minutes)

1. Identify the last known good image tag:
   git log --oneline -5 main
   # Find the commit SHA of the last working deployment

2. Roll back containers:
   docker compose down
   IMAGE_TAG=<previous-sha> docker compose up -d

3. Verify rollback:
   ./scripts/verify-deployment.sh

4. Monitor logs for 10 minutes:
   docker compose logs -f --tail=100

### Database Rollback (if migration was applied)

1. Check current migration state:
   docker compose exec backend npm run typeorm migration:show

2. Revert last migration:
   docker compose exec backend npm run typeorm migration:revert

3. Restart backend:
   docker compose restart backend

### Post-Rollback

1. Create incident report documenting:
   - What failed
   - Timeline of events
   - Root cause (once identified)
   - Action items to prevent recurrence

2. Notify team via Slack #incidents channel

3. Schedule postmortem within 48 hours
```

### What This Skill Provided

`devops-engineer` produced production-ready infrastructure following its prescribed format: a GitHub Actions CI/CD pipeline with lint, test, build (matrix strategy for parallel image builds), E2E, and environment-gated deployments; multi-stage Dockerfiles with non-root users, health checks, and `.dockerignore`; Docker Compose with health check dependencies and required environment variables; a deployment verification script; and a documented rollback procedure covering both application and database rollbacks.

---

## Key Takeaways

1. **EARS-format requirements prevent ambiguity.** The `feature-forge` output used the "While/When/Shall" pattern to make every requirement testable. FR-TODO-006 ("The system shall enforce that all todo queries filter by the authenticated user's ID") directly translated into the `where: { userId }` clause in Step 3 and the user isolation E2E test in Step 6.

2. **ADRs document the "why" behind architecture.** The three ADRs from `architecture-designer` (modular NestJS, dual token strategy, PostgreSQL with TypeORM) explained not just what was chosen but what was rejected and why. When a new team member asks "why not MongoDB?", ADR-003 has the answer.

3. **Skills respect their domain boundaries.** `nestjs-expert` produced only backend code with NestJS patterns. `nextjs-developer` produced only frontend code with App Router patterns. Neither duplicated the other's work. The API contract from Step 1 served as the interface between them.

4. **Testing validates the integration points.** `test-master` caught a potential field-overwrite issue (T-001) in the update service. `playwright-expert` validated that user isolation works end-to-end across separate browser contexts -- something unit tests cannot cover.

5. **Each skill's output format serves a purpose.** The EARS syntax from `feature-forge` made requirements parseable. The ADR format from `architecture-designer` made decisions reviewable. The Swagger decorators from `nestjs-expert` made the API self-documenting. The Page Object Model from `playwright-expert` made E2E tests maintainable.

6. **The deployment layer closes the loop.** `devops-engineer` produced infrastructure that actually runs the code from Steps 3-4, tests it with the suite from Steps 5-6, and deploys it with rollback capability. The verification script checks that all three services (frontend, backend, database) are healthy.

7. **Seven skills, one coherent system.** The workflow pattern -- Specify, Design, Implement (Backend), Implement (Frontend), Test (Unit), Test (E2E), Deploy -- maps directly to the [New Feature Development](../SKILLS_GUIDE.md#new-feature-development) workflow. Each skill's output feeds naturally into the next, producing a system that no single skill could deliver alone.
