# Express to NestJS Migration Guide

> Reference for: NestJS Expert
> Load when: Express migration, Express to NestJS, converting Express app, porting Node.js API, migrating from Express, rewriting Express application

---

## When to Use This Guide

**Use when:**
- Migrating existing Express.js applications to NestJS
- Modernizing legacy Node.js APIs with structured architecture
- Adding TypeScript and dependency injection to Express codebases
- Scaling Express applications requiring better organization
- Team needs enforced architectural patterns and conventions
- Application complexity justifies framework overhead

**When NOT to Use:**

- Simple CRUD APIs with < 10 endpoints (Express may be sufficient)
- Serverless functions requiring minimal cold start time
- Prototypes or MVPs where speed > structure
- Team lacks TypeScript experience and timeline is tight
- Performance-critical microservices where framework overhead matters
- Projects with unique architectural requirements conflicting with NestJS patterns

---

## Concept Mapping: Express → NestJS

| Express Concept | NestJS Equivalent | Key Difference |
|----------------|-------------------|----------------|
| `app.get('/path', handler)` | `@Get('/path')` decorator | Declarative vs imperative |
| Middleware functions | Guards, Interceptors, Pipes | Specialized by purpose |
| `req.params`, `req.body` | `@Param()`, `@Body()` decorators | Automatic injection |
| Manual `require()` | Dependency Injection | IoC container managed |
| `express.Router()` | Controller classes | Object-oriented grouping |
| `app.use(express.json())` | Built-in body parsing | Automatic configuration |
| Error handling middleware | Exception Filters | Class-based with inheritance |
| `app.listen(3000)` | `NestFactory.create()` | Bootstrap pattern |
| Custom validation | `class-validator` pipes | Decorator-based validation |
| Manual service instances | Provider registration | Singleton by default |

---

## Architecture Comparison

### Express Application Structure

```
src/
├── routes/
│   ├── users.js
│   └── posts.js
├── controllers/
│   ├── userController.js
│   └── postController.js
├── services/
│   ├── userService.js
│   └── postService.js
├── middleware/
│   ├── auth.js
│   └── errorHandler.js
└── app.js
```

### NestJS Application Structure

```
src/
├── users/
│   ├── users.controller.ts
│   ├── users.service.ts
│   ├── users.module.ts
│   ├── dto/
│   │   ├── create-user.dto.ts
│   │   └── update-user.dto.ts
│   └── entities/
│       └── user.entity.ts
├── posts/
│   ├── posts.controller.ts
│   ├── posts.service.ts
│   └── posts.module.ts
├── common/
│   ├── guards/
│   ├── interceptors/
│   └── filters/
├── app.module.ts
└── main.ts
```

---

## Migration Pattern: Route Handler → Controller

### Before: Express Route Handler

```typescript
// routes/users.js
const express = require('express');
const router = express.Router();
const UserService = require('../services/userService');

const userService = new UserService();

router.get('/', async (req, res, next) => {
  try {
    const page = parseInt(req.query.page) || 1;
    const limit = parseInt(req.query.limit) || 10;

    const users = await userService.findAll(page, limit);
    res.json({
      success: true,
      data: users,
      page,
      limit
    });
  } catch (error) {
    next(error);
  }
});

router.get('/:id', async (req, res, next) => {
  try {
    const user = await userService.findById(req.params.id);
    if (!user) {
      return res.status(404).json({
        success: false,
        message: 'User not found'
      });
    }
    res.json({ success: true, data: user });
  } catch (error) {
    next(error);
  }
});

router.post('/', async (req, res, next) => {
  try {
    const { email, name } = req.body;

    // Manual validation
    if (!email || !name) {
      return res.status(400).json({
        success: false,
        message: 'Email and name are required'
      });
    }

    const user = await userService.create({ email, name });
    res.status(201).json({ success: true, data: user });
  } catch (error) {
    next(error);
  }
});

module.exports = router;
```

### After: NestJS Controller

```typescript
// users/dto/create-user.dto.ts
import { IsEmail, IsNotEmpty, IsString, MinLength } from 'class-validator';

export class CreateUserDto {
  @IsEmail()
  @IsNotEmpty()
  email: string;

  @IsString()
  @MinLength(2)
  name: string;
}

// users/dto/pagination-query.dto.ts
import { IsOptional, IsInt, Min, Max } from 'class-validator';
import { Type } from 'class-transformer';

export class PaginationQueryDto {
  @IsOptional()
  @Type(() => Number)
  @IsInt()
  @Min(1)
  page?: number = 1;

  @IsOptional()
  @Type(() => Number)
  @IsInt()
  @Min(1)
  @Max(100)
  limit?: number = 10;
}

// users/users.controller.ts
import {
  Controller,
  Get,
  Post,
  Body,
  Param,
  Query,
  HttpCode,
  HttpStatus,
  ParseIntPipe,
} from '@nestjs/common';
import { UsersService } from './users.service';
import { CreateUserDto } from './dto/create-user.dto';
import { PaginationQueryDto } from './dto/pagination-query.dto';

@Controller('users')
export class UsersController {
  constructor(private readonly usersService: UsersService) {}

  @Get()
  async findAll(@Query() query: PaginationQueryDto) {
    const users = await this.usersService.findAll(query.page, query.limit);
    return {
      success: true,
      data: users,
      page: query.page,
      limit: query.limit,
    };
  }

  @Get(':id')
  async findOne(@Param('id', ParseIntPipe) id: number) {
    const user = await this.usersService.findById(id);
    return { success: true, data: user };
  }

  @Post()
  @HttpCode(HttpStatus.CREATED)
  async create(@Body() createUserDto: CreateUserDto) {
    const user = await this.usersService.create(createUserDto);
    return { success: true, data: user };
  }
}
```

---

## Migration Pattern: Middleware → Guards/Interceptors

### Before: Express Authentication Middleware

```typescript
// middleware/auth.js
const jwt = require('jsonwebtoken');

function authMiddleware(req, res, next) {
  const token = req.headers.authorization?.split(' ')[1];

  if (!token) {
    return res.status(401).json({
      success: false,
      message: 'No token provided'
    });
  }

  try {
    const decoded = jwt.verify(token, process.env.JWT_SECRET);
    req.user = decoded;
    next();
  } catch (error) {
    return res.status(401).json({
      success: false,
      message: 'Invalid token'
    });
  }
}

// Usage in routes
router.get('/profile', authMiddleware, async (req, res) => {
  const user = await userService.findById(req.user.id);
  res.json({ success: true, data: user });
});
```

### After: NestJS Guard

```typescript
// common/guards/jwt-auth.guard.ts
import {
  Injectable,
  CanActivate,
  ExecutionContext,
  UnauthorizedException,
} from '@nestjs/common';
import { JwtService } from '@nestjs/jwt';
import { Request } from 'express';

@Injectable()
export class JwtAuthGuard implements CanActivate {
  constructor(private jwtService: JwtService) {}

  async canActivate(context: ExecutionContext): Promise<boolean> {
    const request = context.switchToHttp().getRequest<Request>();
    const token = this.extractTokenFromHeader(request);

    if (!token) {
      throw new UnauthorizedException('No token provided');
    }

    try {
      const payload = await this.jwtService.verifyAsync(token);
      request['user'] = payload;
    } catch {
      throw new UnauthorizedException('Invalid token');
    }

    return true;
  }

  private extractTokenFromHeader(request: Request): string | undefined {
    const [type, token] = request.headers.authorization?.split(' ') ?? [];
    return type === 'Bearer' ? token : undefined;
  }
}

// Usage in controller
import { UseGuards } from '@nestjs/common';
import { JwtAuthGuard } from '../common/guards/jwt-auth.guard';

@Controller('users')
export class UsersController {
  @Get('profile')
  @UseGuards(JwtAuthGuard)
  async getProfile(@Request() req) {
    return this.usersService.findById(req.user.id);
  }
}
```

### Before: Express Logging Middleware

```typescript
// middleware/logger.js
function loggerMiddleware(req, res, next) {
  const start = Date.now();

  res.on('finish', () => {
    const duration = Date.now() - start;
    console.log(`${req.method} ${req.path} - ${res.statusCode} - ${duration}ms`);
  });

  next();
}

// app.js
app.use(loggerMiddleware);
```

### After: NestJS Interceptor

```typescript
// common/interceptors/logging.interceptor.ts
import {
  Injectable,
  NestInterceptor,
  ExecutionContext,
  CallHandler,
  Logger,
} from '@nestjs/common';
import { Observable } from 'rxjs';
import { tap } from 'rxjs/operators';

@Injectable()
export class LoggingInterceptor implements NestInterceptor {
  private readonly logger = new Logger(LoggingInterceptor.name);

  intercept(context: ExecutionContext, next: CallHandler): Observable<any> {
    const request = context.switchToHttp().getRequest();
    const { method, url } = request;
    const start = Date.now();

    return next.handle().pipe(
      tap(() => {
        const response = context.switchToHttp().getResponse();
        const duration = Date.now() - start;
        this.logger.log(
          `${method} ${url} - ${response.statusCode} - ${duration}ms`,
        );
      }),
    );
  }
}

// main.ts - Apply globally
import { NestFactory } from '@nestjs/core';
import { AppModule } from './app.module';
import { LoggingInterceptor } from './common/interceptors/logging.interceptor';

async function bootstrap() {
  const app = await NestFactory.create(AppModule);
  app.useGlobalInterceptors(new LoggingInterceptor());
  await app.listen(3000);
}
bootstrap();
```

---

## Migration Pattern: Dependency Injection

### Before: Express Manual Instantiation

```typescript
// services/userService.js
const UserRepository = require('../repositories/userRepository');
const EmailService = require('./emailService');

class UserService {
  constructor() {
    this.userRepository = new UserRepository();
    this.emailService = new EmailService();
  }

  async create(userData) {
    const user = await this.userRepository.create(userData);
    await this.emailService.sendWelcomeEmail(user.email);
    return user;
  }
}

module.exports = UserService;

// controllers/userController.js
const UserService = require('../services/userService');
const userService = new UserService();

async function createUser(req, res) {
  const user = await userService.create(req.body);
  res.json({ success: true, data: user });
}
```

### After: NestJS Dependency Injection

```typescript
// users/users.repository.ts
import { Injectable } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository } from 'typeorm';
import { User } from './entities/user.entity';

@Injectable()
export class UsersRepository {
  constructor(
    @InjectRepository(User)
    private readonly repository: Repository<User>,
  ) {}

  async create(userData: Partial<User>): Promise<User> {
    const user = this.repository.create(userData);
    return this.repository.save(user);
  }

  async findById(id: number): Promise<User | null> {
    return this.repository.findOne({ where: { id } });
  }
}

// email/email.service.ts
import { Injectable, Logger } from '@nestjs/common';

@Injectable()
export class EmailService {
  private readonly logger = new Logger(EmailService.name);

  async sendWelcomeEmail(email: string): Promise<void> {
    this.logger.log(`Sending welcome email to ${email}`);
    // Email sending logic
  }
}

// users/users.service.ts
import { Injectable, NotFoundException } from '@nestjs/common';
import { UsersRepository } from './users.repository';
import { EmailService } from '../email/email.service';
import { CreateUserDto } from './dto/create-user.dto';
import { User } from './entities/user.entity';

@Injectable()
export class UsersService {
  constructor(
    private readonly usersRepository: UsersRepository,
    private readonly emailService: EmailService,
  ) {}

  async create(createUserDto: CreateUserDto): Promise<User> {
    const user = await this.usersRepository.create(createUserDto);
    await this.emailService.sendWelcomeEmail(user.email);
    return user;
  }

  async findById(id: number): Promise<User> {
    const user = await this.usersRepository.findById(id);
    if (!user) {
      throw new NotFoundException(`User with ID ${id} not found`);
    }
    return user;
  }
}

// users/users.module.ts
import { Module } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';
import { UsersController } from './users.controller';
import { UsersService } from './users.service';
import { UsersRepository } from './users.repository';
import { User } from './entities/user.entity';
import { EmailModule } from '../email/email.module';

@Module({
  imports: [TypeOrmModule.forFeature([User]), EmailModule],
  controllers: [UsersController],
  providers: [UsersService, UsersRepository],
  exports: [UsersService],
})
export class UsersModule {}
```

---

## Migration Pattern: Error Handling

### Before: Express Error Middleware

```typescript
// middleware/errorHandler.js
function errorHandler(err, req, res, next) {
  console.error(err.stack);

  if (err.name === 'ValidationError') {
    return res.status(400).json({
      success: false,
      message: 'Validation failed',
      errors: err.errors
    });
  }

  if (err.name === 'UnauthorizedError') {
    return res.status(401).json({
      success: false,
      message: 'Unauthorized'
    });
  }

  res.status(500).json({
    success: false,
    message: 'Internal server error'
  });
}

// app.js
app.use(errorHandler);
```

### After: NestJS Exception Filter

```typescript
// common/filters/http-exception.filter.ts
import {
  ExceptionFilter,
  Catch,
  ArgumentsHost,
  HttpException,
  HttpStatus,
  Logger,
} from '@nestjs/common';
import { Request, Response } from 'express';

@Catch()
export class HttpExceptionFilter implements ExceptionFilter {
  private readonly logger = new Logger(HttpExceptionFilter.name);

  catch(exception: unknown, host: ArgumentsHost) {
    const ctx = host.switchToHttp();
    const response = ctx.getResponse<Response>();
    const request = ctx.getRequest<Request>();

    let status = HttpStatus.INTERNAL_SERVER_ERROR;
    let message = 'Internal server error';
    let errors: any = undefined;

    if (exception instanceof HttpException) {
      status = exception.getStatus();
      const exceptionResponse = exception.getResponse();

      if (typeof exceptionResponse === 'object') {
        message = (exceptionResponse as any).message || message;
        errors = (exceptionResponse as any).errors;
      } else {
        message = exceptionResponse;
      }
    } else if (exception instanceof Error) {
      message = exception.message;
      this.logger.error(exception.stack);
    }

    response.status(status).json({
      success: false,
      statusCode: status,
      message,
      errors,
      timestamp: new Date().toISOString(),
      path: request.url,
    });
  }
}

// main.ts
import { NestFactory } from '@nestjs/core';
import { AppModule } from './app.module';
import { HttpExceptionFilter } from './common/filters/http-exception.filter';

async function bootstrap() {
  const app = await NestFactory.create(AppModule);
  app.useGlobalFilters(new HttpExceptionFilter());
  await app.listen(3000);
}
bootstrap();
```

---

## Migration Pattern: Validation

### Before: Express with express-validator

```typescript
// routes/users.js
const { body, validationResult } = require('express-validator');

router.post(
  '/',
  [
    body('email').isEmail().normalizeEmail(),
    body('name').trim().isLength({ min: 2, max: 50 }),
    body('age').optional().isInt({ min: 0, max: 120 }),
  ],
  async (req, res, next) => {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      return res.status(400).json({
        success: false,
        errors: errors.array()
      });
    }

    try {
      const user = await userService.create(req.body);
      res.status(201).json({ success: true, data: user });
    } catch (error) {
      next(error);
    }
  }
);
```

### After: NestJS with class-validator

```typescript
// users/dto/create-user.dto.ts
import {
  IsEmail,
  IsNotEmpty,
  IsString,
  MinLength,
  MaxLength,
  IsOptional,
  IsInt,
  Min,
  Max,
} from 'class-validator';
import { Transform } from 'class-transformer';

export class CreateUserDto {
  @IsEmail()
  @IsNotEmpty()
  @Transform(({ value }) => value.toLowerCase().trim())
  email: string;

  @IsString()
  @MinLength(2)
  @MaxLength(50)
  @Transform(({ value }) => value.trim())
  name: string;

  @IsOptional()
  @IsInt()
  @Min(0)
  @Max(120)
  age?: number;
}

// users/users.controller.ts
import { Controller, Post, Body, ValidationPipe } from '@nestjs/common';
import { UsersService } from './users.service';
import { CreateUserDto } from './dto/create-user.dto';

@Controller('users')
export class UsersController {
  constructor(private readonly usersService: UsersService) {}

  @Post()
  async create(@Body(ValidationPipe) createUserDto: CreateUserDto) {
    const user = await this.usersService.create(createUserDto);
    return { success: true, data: user };
  }
}

// main.ts - Global validation pipe
import { ValidationPipe } from '@nestjs/common';

async function bootstrap() {
  const app = await NestFactory.create(AppModule);
  app.useGlobalPipes(
    new ValidationPipe({
      whitelist: true, // Strip non-whitelisted properties
      forbidNonWhitelisted: true, // Throw error for non-whitelisted
      transform: true, // Auto-transform payloads to DTO instances
      transformOptions: {
        enableImplicitConversion: true,
      },
    }),
  );
  await app.listen(3000);
}
```

---

## Migration Pattern: Testing

### Before: Express with Mocha/Chai

```typescript
// test/users.test.js
const request = require('supertest');
const { expect } = require('chai');
const app = require('../src/app');

describe('Users API', () => {
  describe('POST /users', () => {
    it('should create a new user', async () => {
      const userData = {
        email: 'test@example.com',
        name: 'Test User'
      };

      const response = await request(app)
        .post('/users')
        .send(userData)
        .expect(201);

      expect(response.body.success).to.be.true;
      expect(response.body.data).to.have.property('id');
      expect(response.body.data.email).to.equal(userData.email);
    });

    it('should return 400 for invalid email', async () => {
      const response = await request(app)
        .post('/users')
        .send({ email: 'invalid', name: 'Test' })
        .expect(400);

      expect(response.body.success).to.be.false;
    });
  });
});
```

### After: NestJS with Jest

```typescript
// users/users.controller.spec.ts
import { Test, TestingModule } from '@nestjs/testing';
import { UsersController } from './users.controller';
import { UsersService } from './users.service';
import { CreateUserDto } from './dto/create-user.dto';

describe('UsersController', () => {
  let controller: UsersController;
  let service: UsersService;

  const mockUsersService = {
    create: jest.fn(),
    findById: jest.fn(),
    findAll: jest.fn(),
  };

  beforeEach(async () => {
    const module: TestingModule = await Test.createTestingModule({
      controllers: [UsersController],
      providers: [
        {
          provide: UsersService,
          useValue: mockUsersService,
        },
      ],
    }).compile();

    controller = module.get<UsersController>(UsersController);
    service = module.get<UsersService>(UsersService);
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  describe('create', () => {
    it('should create a new user', async () => {
      const createUserDto: CreateUserDto = {
        email: 'test@example.com',
        name: 'Test User',
      };

      const expectedUser = {
        id: 1,
        ...createUserDto,
        createdAt: new Date(),
      };

      mockUsersService.create.mockResolvedValue(expectedUser);

      const result = await controller.create(createUserDto);

      expect(result.success).toBe(true);
      expect(result.data).toEqual(expectedUser);
      expect(service.create).toHaveBeenCalledWith(createUserDto);
      expect(service.create).toHaveBeenCalledTimes(1);
    });
  });

  describe('findOne', () => {
    it('should return a user by id', async () => {
      const userId = 1;
      const expectedUser = {
        id: userId,
        email: 'test@example.com',
        name: 'Test User',
      };

      mockUsersService.findById.mockResolvedValue(expectedUser);

      const result = await controller.findOne(userId);

      expect(result.data).toEqual(expectedUser);
      expect(service.findById).toHaveBeenCalledWith(userId);
    });
  });
});

// users/users.service.spec.ts
import { Test, TestingModule } from '@nestjs/testing';
import { NotFoundException } from '@nestjs/common';
import { UsersService } from './users.service';
import { UsersRepository } from './users.repository';
import { EmailService } from '../email/email.service';

describe('UsersService', () => {
  let service: UsersService;
  let repository: UsersRepository;
  let emailService: EmailService;

  const mockUsersRepository = {
    create: jest.fn(),
    findById: jest.fn(),
  };

  const mockEmailService = {
    sendWelcomeEmail: jest.fn(),
  };

  beforeEach(async () => {
    const module: TestingModule = await Test.createTestingModule({
      providers: [
        UsersService,
        {
          provide: UsersRepository,
          useValue: mockUsersRepository,
        },
        {
          provide: EmailService,
          useValue: mockEmailService,
        },
      ],
    }).compile();

    service = module.get<UsersService>(UsersService);
    repository = module.get<UsersRepository>(UsersRepository);
    emailService = module.get<EmailService>(EmailService);
  });

  describe('create', () => {
    it('should create user and send welcome email', async () => {
      const createUserDto = {
        email: 'test@example.com',
        name: 'Test User',
      };

      const createdUser = { id: 1, ...createUserDto };

      mockUsersRepository.create.mockResolvedValue(createdUser);
      mockEmailService.sendWelcomeEmail.mockResolvedValue(undefined);

      const result = await service.create(createUserDto);

      expect(result).toEqual(createdUser);
      expect(repository.create).toHaveBeenCalledWith(createUserDto);
      expect(emailService.sendWelcomeEmail).toHaveBeenCalledWith(
        createUserDto.email,
      );
    });
  });

  describe('findById', () => {
    it('should throw NotFoundException when user not found', async () => {
      mockUsersRepository.findById.mockResolvedValue(null);

      await expect(service.findById(999)).rejects.toThrow(NotFoundException);
      await expect(service.findById(999)).rejects.toThrow(
        'User with ID 999 not found',
      );
    });
  });
});

// E2E Testing
// test/users.e2e-spec.ts
import { Test, TestingModule } from '@nestjs/testing';
import { INestApplication, ValidationPipe } from '@nestjs/common';
import * as request from 'supertest';
import { AppModule } from '../src/app.module';

describe('UsersController (e2e)', () => {
  let app: INestApplication;

  beforeAll(async () => {
    const moduleFixture: TestingModule = await Test.createTestingModule({
      imports: [AppModule],
    }).compile();

    app = moduleFixture.createNestApplication();
    app.useGlobalPipes(new ValidationPipe());
    await app.init();
  });

  afterAll(async () => {
    await app.close();
  });

  describe('/users (POST)', () => {
    it('should create a new user', () => {
      return request(app.getHttpServer())
        .post('/users')
        .send({
          email: 'test@example.com',
          name: 'Test User',
        })
        .expect(201)
        .expect((res) => {
          expect(res.body.success).toBe(true);
          expect(res.body.data).toHaveProperty('id');
          expect(res.body.data.email).toBe('test@example.com');
        });
    });

    it('should return 400 for invalid email', () => {
      return request(app.getHttpServer())
        .post('/users')
        .send({
          email: 'invalid-email',
          name: 'Test',
        })
        .expect(400);
    });
  });
});
```

---

## Incremental Migration Strategy

### Strategy 1: Strangler Fig Pattern (Recommended)

Gradually replace Express routes with NestJS while both run simultaneously.

**Cross-reference:** See `/Users/dmitry/Projects/claude-skills/skills/legacy-modernizer/references/strangler-fig-pattern.md` for detailed implementation.

```typescript
// main.ts - Running both Express and NestJS
import { NestFactory } from '@nestjs/core';
import { AppModule } from './app.module';
import * as express from 'express';
import { expressApp } from './legacy/express-app';

async function bootstrap() {
  const nestApp = await NestFactory.create(AppModule);

  // Proxy middleware to route between NestJS and Express
  const app = express();

  // NestJS routes (new implementation)
  app.use('/api/v2', nestApp.getHttpAdapter().getInstance());

  // Express routes (legacy)
  app.use('/api', expressApp);

  await app.listen(3000);
}
bootstrap();
```

**Migration steps:**
1. Set up NestJS alongside Express
2. Migrate one module at a time to NestJS
3. Route new endpoints to NestJS, old to Express
4. Update frontend/clients to use new endpoints
5. Remove Express routes once fully migrated
6. Decommission Express app

### Strategy 2: Module-by-Module Migration

Migrate complete feature modules sequentially.

```
Phase 1: Authentication (Week 1-2)
- Migrate auth middleware → Guards
- Migrate JWT handling → @nestjs/jwt
- Test authentication flows
- Deploy with feature flag

Phase 2: Users Module (Week 3-4)
- Migrate user routes → Controllers
- Migrate user service → Providers
- Add validation with DTOs
- Write tests

Phase 3: Posts Module (Week 5-6)
...
```

### Strategy 3: Adapter Pattern for Gradual DI Migration

Wrap Express services in NestJS providers during transition.

```typescript
// Adapter for legacy Express service
import { Injectable } from '@nestjs/common';
const LegacyUserService = require('../legacy/services/userService');

@Injectable()
export class UserServiceAdapter {
  private legacyService = new LegacyUserService();

  async findAll(): Promise<any[]> {
    return this.legacyService.findAll();
  }

  async create(data: any): Promise<any> {
    return this.legacyService.create(data);
  }
}

// Use in NestJS controller while migrating
@Controller('users')
export class UsersController {
  constructor(private readonly userService: UserServiceAdapter) {}

  @Get()
  async findAll() {
    return this.userService.findAll();
  }
}
```

---

## Common Pitfalls

### 1. Over-engineering Simple Applications

**Problem:** Migrating a 500-line Express app to full NestJS with modules, DTOs, repositories, guards, etc.

**Solution:** Evaluate if NestJS complexity is justified. Consider keeping simple APIs in Express.

### 2. Not Understanding Dependency Injection Lifecycle

**Problem:**
```typescript
// WRONG - Creates new instance, bypassing DI
@Injectable()
export class UsersService {
  constructor() {
    this.emailService = new EmailService(); // Don't do this!
  }
}
```

**Solution:**
```typescript
// CORRECT - Let NestJS inject dependencies
@Injectable()
export class UsersService {
  constructor(private readonly emailService: EmailService) {}
}
```

### 3. Mixing Middleware and Guards Incorrectly

**Problem:** Using Express middleware for authentication instead of Guards, losing NestJS benefits.

**Solution:** Use Guards for authentication/authorization, Interceptors for logging/transformation, Middleware only for Express-specific needs.

### 4. Ignoring Validation Pipes

**Problem:** Manual validation in controllers like Express.

```typescript
// WRONG - Manual validation
@Post()
async create(@Body() body: any) {
  if (!body.email) {
    throw new BadRequestException('Email required');
  }
  // ...
}
```

**Solution:**
```typescript
// CORRECT - Use DTOs with class-validator
@Post()
async create(@Body() createUserDto: CreateUserDto) {
  // Validation happens automatically
  return this.usersService.create(createUserDto);
}
```

### 5. Not Leveraging Module Imports/Exports

**Problem:** Circular dependencies and tightly coupled modules.

**Solution:** Properly structure module imports/exports. Use forwardRef() for circular dependencies.

```typescript
@Module({
  imports: [TypeOrmModule.forFeature([User]), EmailModule],
  providers: [UsersService, UsersRepository],
  exports: [UsersService], // Export for other modules
})
export class UsersModule {}
```

### 6. Forgetting to Enable CORS

**Problem:** CORS working in Express but failing in NestJS.

**Solution:**
```typescript
// main.ts
const app = await NestFactory.create(AppModule);
app.enableCors({
  origin: process.env.ALLOWED_ORIGINS?.split(','),
  credentials: true,
});
```

### 7. Incorrect Exception Handling

**Problem:** Using Express error middleware patterns.

**Solution:** Use NestJS built-in exceptions and filters.

```typescript
// Throw NestJS exceptions
throw new NotFoundException('User not found');
throw new BadRequestException('Invalid input');
throw new UnauthorizedException('Invalid credentials');
```

### 8. Not Configuring ValidationPipe Globally

**Problem:** Validation inconsistent across endpoints.

**Solution:**
```typescript
// main.ts
app.useGlobalPipes(
  new ValidationPipe({
    whitelist: true,
    forbidNonWhitelisted: true,
    transform: true,
  }),
);
```

---

## Migration Checklist

**Pre-Migration:**
- [ ] Audit existing Express codebase structure
- [ ] Document all routes and dependencies
- [ ] Identify shared services and utilities
- [ ] Plan module boundaries
- [ ] Set up NestJS project structure

**During Migration:**
- [ ] Migrate DTOs and validation rules
- [ ] Convert route handlers to controllers
- [ ] Refactor services for dependency injection
- [ ] Implement guards for authentication
- [ ] Create interceptors for cross-cutting concerns
- [ ] Add exception filters
- [ ] Write unit tests for each component
- [ ] Write e2e tests for critical flows

**Post-Migration:**
- [ ] Performance testing and optimization
- [ ] Update API documentation
- [ ] Configure logging and monitoring
- [ ] Set up CI/CD for NestJS
- [ ] Train team on NestJS patterns
- [ ] Remove Express dependencies
- [ ] Refactor for NestJS best practices

---

## Additional Resources

- NestJS Official Documentation: https://docs.nestjs.com
- NestJS Migration Guide: https://docs.nestjs.com/migration-guide
- class-validator Decorators: https://github.com/typestack/class-validator
- TypeORM with NestJS: https://docs.nestjs.com/techniques/database
- Testing Guide: https://docs.nestjs.com/fundamentals/testing
