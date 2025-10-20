---
name: NestJS Expert
description: Expert in NestJS framework for building scalable Node.js server-side applications. Use when working with NestJS, TypeScript backend development, dependency injection, decorators, modules, controllers, providers, guards, interceptors, pipes, or when the user mentions NestJS, Nest, or Node.js enterprise applications.
---

# NestJS Expert

A specialized skill for building enterprise-grade, scalable server-side applications with NestJS. This skill covers architecture, best practices, testing, and advanced NestJS features.

## Instructions

### Core Workflow

1. **Understand project requirements**
   - Ask about the application type (REST API, GraphQL, Microservices, WebSockets)
   - Identify database needs (PostgreSQL, MongoDB, MySQL, etc.)
   - Determine authentication requirements (JWT, OAuth, Passport)
   - Understand scaling and architecture needs

2. **Setup and structure**
   - Create proper module structure
   - Implement dependency injection correctly
   - Set up configuration management (@nestjs/config)
   - Configure logging and error handling
   - Set up validation pipes

3. **Implement features**
   - Create modules, controllers, services following best practices
   - Implement proper DTOs with class-validator
   - Set up database entities/models
   - Implement authentication and authorization
   - Add interceptors, guards, and pipes where appropriate

4. **Testing**
   - Write unit tests for services
   - Write E2E tests for controllers
   - Mock dependencies properly
   - Test guards, interceptors, and pipes

5. **Documentation and deployment**
   - Add Swagger/OpenAPI documentation
   - Configure for production (environment variables, logging)
   - Set up Docker and docker-compose if needed

### NestJS Architecture Best Practices

#### Module Organization

```typescript
// Feature module structure
src/
├── app.module.ts
├── main.ts
├── common/                    // Shared utilities
│   ├── decorators/
│   ├── filters/
│   ├── guards/
│   ├── interceptors/
│   └── pipes/
├── config/                    // Configuration
│   └── configuration.ts
└── features/                  // Feature modules
    ├── users/
    │   ├── dto/
    │   │   ├── create-user.dto.ts
    │   │   └── update-user.dto.ts
    │   ├── entities/
    │   │   └── user.entity.ts
    │   ├── users.controller.ts
    │   ├── users.service.ts
    │   ├── users.module.ts
    │   └── users.service.spec.ts
    └── auth/
        ├── guards/
        ├── strategies/
        ├── auth.controller.ts
        ├── auth.service.ts
        └── auth.module.ts
```

#### Controller Best Practices

```typescript
@Controller('users')
@ApiTags('users')
@UseGuards(JwtAuthGuard)
export class UsersController {
  constructor(private readonly usersService: UsersService) {}

  @Post()
  @ApiOperation({ summary: 'Create a new user' })
  @ApiResponse({ status: 201, description: 'User created', type: UserDto })
  @ApiResponse({ status: 400, description: 'Invalid input' })
  async create(@Body() createUserDto: CreateUserDto): Promise<UserDto> {
    return this.usersService.create(createUserDto);
  }

  @Get()
  @ApiOperation({ summary: 'Get all users' })
  @ApiQuery({ name: 'page', required: false, type: Number })
  @ApiQuery({ name: 'limit', required: false, type: Number })
  async findAll(
    @Query('page', new DefaultValuePipe(1), ParseIntPipe) page: number,
    @Query('limit', new DefaultValuePipe(10), ParseIntPipe) limit: number,
  ): Promise<PaginatedDto<UserDto>> {
    return this.usersService.findAll({ page, limit });
  }

  @Get(':id')
  @ApiOperation({ summary: 'Get user by ID' })
  @ApiParam({ name: 'id', type: 'string' })
  async findOne(@Param('id', ParseUUIDPipe) id: string): Promise<UserDto> {
    return this.usersService.findOne(id);
  }

  @Patch(':id')
  @ApiOperation({ summary: 'Update user' })
  async update(
    @Param('id', ParseUUIDPipe) id: string,
    @Body() updateUserDto: UpdateUserDto,
  ): Promise<UserDto> {
    return this.usersService.update(id, updateUserDto);
  }

  @Delete(':id')
  @HttpCode(HttpStatus.NO_CONTENT)
  @ApiOperation({ summary: 'Delete user' })
  async remove(@Param('id', ParseUUIDPipe) id: string): Promise<void> {
    await this.usersService.remove(id);
  }
}
```

#### Service Layer with Proper Error Handling

```typescript
@Injectable()
export class UsersService {
  private readonly logger = new Logger(UsersService.name);

  constructor(
    @InjectRepository(User)
    private readonly usersRepository: Repository<User>,
  ) {}

  async create(createUserDto: CreateUserDto): Promise<User> {
    try {
      const user = this.usersRepository.create(createUserDto);
      return await this.usersRepository.save(user);
    } catch (error) {
      this.logger.error(`Failed to create user: ${error.message}`, error.stack);

      if (error.code === '23505') { // PostgreSQL unique violation
        throw new ConflictException('User with this email already exists');
      }

      throw new InternalServerErrorException('Failed to create user');
    }
  }

  async findAll(options: PaginationOptions): Promise<PaginatedDto<User>> {
    const { page, limit } = options;
    const skip = (page - 1) * limit;

    const [users, total] = await this.usersRepository.findAndCount({
      skip,
      take: limit,
      order: { createdAt: 'DESC' },
    });

    return {
      data: users,
      meta: {
        page,
        limit,
        total,
        totalPages: Math.ceil(total / limit),
      },
    };
  }

  async findOne(id: string): Promise<User> {
    const user = await this.usersRepository.findOne({ where: { id } });

    if (!user) {
      throw new NotFoundException(`User with ID ${id} not found`);
    }

    return user;
  }

  async update(id: string, updateUserDto: UpdateUserDto): Promise<User> {
    const user = await this.findOne(id); // Reuse findOne for consistency

    Object.assign(user, updateUserDto);

    return await this.usersRepository.save(user);
  }

  async remove(id: string): Promise<void> {
    const result = await this.usersRepository.delete(id);

    if (result.affected === 0) {
      throw new NotFoundException(`User with ID ${id} not found`);
    }
  }
}
```

#### DTOs with Validation

```typescript
// create-user.dto.ts
import { ApiProperty } from '@nestjs/swagger';
import {
  IsEmail,
  IsString,
  MinLength,
  MaxLength,
  IsOptional,
  Matches
} from 'class-validator';

export class CreateUserDto {
  @ApiProperty({
    description: 'User email address',
    example: 'user@example.com',
  })
  @IsEmail()
  email: string;

  @ApiProperty({
    description: 'User password (min 8 characters, must contain uppercase, lowercase, and number)',
    example: 'SecurePass123',
    minLength: 8,
  })
  @IsString()
  @MinLength(8)
  @Matches(/((?=.*\d)|(?=.*\W+))(?![.\n])(?=.*[A-Z])(?=.*[a-z]).*$/, {
    message: 'Password must contain uppercase, lowercase, and number',
  })
  password: string;

  @ApiProperty({
    description: 'User full name',
    example: 'John Doe',
    minLength: 2,
    maxLength: 100,
  })
  @IsString()
  @MinLength(2)
  @MaxLength(100)
  name: string;

  @ApiProperty({
    description: 'User role',
    example: 'user',
    required: false,
    enum: ['user', 'admin'],
  })
  @IsOptional()
  @IsIn(['user', 'admin'])
  role?: string = 'user';
}

// update-user.dto.ts
import { PartialType, OmitType } from '@nestjs/swagger';
import { CreateUserDto } from './create-user.dto';

export class UpdateUserDto extends PartialType(
  OmitType(CreateUserDto, ['password'] as const)
) {}
```

#### Authentication with JWT

```typescript
// auth.service.ts
@Injectable()
export class AuthService {
  constructor(
    private usersService: UsersService,
    private jwtService: JwtService,
  ) {}

  async validateUser(email: string, password: string): Promise<any> {
    const user = await this.usersService.findByEmail(email);

    if (user && await bcrypt.compare(password, user.password)) {
      const { password, ...result } = user;
      return result;
    }

    return null;
  }

  async login(user: any) {
    const payload = { email: user.email, sub: user.id, role: user.role };

    return {
      access_token: this.jwtService.sign(payload),
      user: {
        id: user.id,
        email: user.email,
        name: user.name,
      },
    };
  }

  async register(createUserDto: CreateUserDto) {
    const hashedPassword = await bcrypt.hash(createUserDto.password, 10);

    const user = await this.usersService.create({
      ...createUserDto,
      password: hashedPassword,
    });

    return this.login(user);
  }
}

// jwt.strategy.ts
@Injectable()
export class JwtStrategy extends PassportStrategy(Strategy) {
  constructor(private configService: ConfigService) {
    super({
      jwtFromRequest: ExtractJwt.fromAuthHeaderAsBearerToken(),
      ignoreExpiration: false,
      secretOrKey: configService.get('JWT_SECRET'),
    });
  }

  async validate(payload: any) {
    return {
      userId: payload.sub,
      email: payload.email,
      role: payload.role
    };
  }
}

// jwt-auth.guard.ts
@Injectable()
export class JwtAuthGuard extends AuthGuard('jwt') {
  canActivate(context: ExecutionContext) {
    return super.canActivate(context);
  }

  handleRequest(err, user, info) {
    if (err || !user) {
      throw err || new UnauthorizedException();
    }
    return user;
  }
}
```

#### Role-Based Access Control

```typescript
// roles.decorator.ts
export const ROLES_KEY = 'roles';
export const Roles = (...roles: string[]) => SetMetadata(ROLES_KEY, roles);

// roles.guard.ts
@Injectable()
export class RolesGuard implements CanActivate {
  constructor(private reflector: Reflector) {}

  canActivate(context: ExecutionContext): boolean {
    const requiredRoles = this.reflector.getAllAndOverride<string[]>(
      ROLES_KEY,
      [context.getHandler(), context.getClass()],
    );

    if (!requiredRoles) {
      return true;
    }

    const { user } = context.switchToHttp().getRequest();
    return requiredRoles.some((role) => user.role === role);
  }
}

// Usage
@Controller('admin')
@UseGuards(JwtAuthGuard, RolesGuard)
export class AdminController {
  @Get('users')
  @Roles('admin')
  getAllUsers() {
    // Only accessible by admins
  }
}
```

#### Custom Interceptor (Logging)

```typescript
@Injectable()
export class LoggingInterceptor implements NestInterceptor {
  private readonly logger = new Logger(LoggingInterceptor.name);

  intercept(context: ExecutionContext, next: CallHandler): Observable<any> {
    const request = context.switchToHttp().getRequest();
    const { method, url, body } = request;
    const now = Date.now();

    this.logger.log(`Incoming Request: ${method} ${url}`);

    return next.handle().pipe(
      tap(() => {
        const response = context.switchToHttp().getResponse();
        const delay = Date.now() - now;

        this.logger.log(
          `Outgoing Response: ${method} ${url} ${response.statusCode} - ${delay}ms`
        );
      }),
      catchError((error) => {
        const delay = Date.now() - now;
        this.logger.error(
          `Request Failed: ${method} ${url} - ${delay}ms`,
          error.stack
        );
        throw error;
      }),
    );
  }
}
```

#### Exception Filters

```typescript
@Catch(HttpException)
export class HttpExceptionFilter implements ExceptionFilter {
  private readonly logger = new Logger(HttpExceptionFilter.name);

  catch(exception: HttpException, host: ArgumentsHost) {
    const ctx = host.switchToHttp();
    const response = ctx.getResponse<Response>();
    const request = ctx.getRequest<Request>();
    const status = exception.getStatus();
    const exceptionResponse = exception.getResponse();

    const errorResponse = {
      statusCode: status,
      timestamp: new Date().toISOString(),
      path: request.url,
      method: request.method,
      message:
        typeof exceptionResponse === 'string'
          ? exceptionResponse
          : (exceptionResponse as any).message || 'Internal server error',
    };

    this.logger.error(
      `${request.method} ${request.url}`,
      JSON.stringify(errorResponse),
      exception.stack,
    );

    response.status(status).json(errorResponse);
  }
}

// Register globally in main.ts
app.useGlobalFilters(new HttpExceptionFilter());
```

#### Configuration Management

```typescript
// configuration.ts
export default () => ({
  port: parseInt(process.env.PORT, 10) || 3000,
  database: {
    host: process.env.DATABASE_HOST || 'localhost',
    port: parseInt(process.env.DATABASE_PORT, 10) || 5432,
    username: process.env.DATABASE_USER,
    password: process.env.DATABASE_PASSWORD,
    database: process.env.DATABASE_NAME,
  },
  jwt: {
    secret: process.env.JWT_SECRET,
    expiresIn: process.env.JWT_EXPIRES_IN || '1d',
  },
  redis: {
    host: process.env.REDIS_HOST || 'localhost',
    port: parseInt(process.env.REDIS_PORT, 10) || 6379,
  },
});

// app.module.ts
@Module({
  imports: [
    ConfigModule.forRoot({
      isGlobal: true,
      load: [configuration],
      validationSchema: Joi.object({
        NODE_ENV: Joi.string()
          .valid('development', 'production', 'test')
          .default('development'),
        PORT: Joi.number().default(3000),
        DATABASE_HOST: Joi.string().required(),
        DATABASE_PORT: Joi.number().default(5432),
        JWT_SECRET: Joi.string().required(),
      }),
    }),
  ],
})
export class AppModule {}
```

#### Testing

```typescript
// users.service.spec.ts
describe('UsersService', () => {
  let service: UsersService;
  let repository: Repository<User>;

  beforeEach(async () => {
    const module: TestingModule = await Test.createTestingModule({
      providers: [
        UsersService,
        {
          provide: getRepositoryToken(User),
          useClass: Repository,
        },
      ],
    }).compile();

    service = module.get<UsersService>(UsersService);
    repository = module.get<Repository<User>>(getRepositoryToken(User));
  });

  describe('create', () => {
    it('should create a user', async () => {
      const createUserDto: CreateUserDto = {
        email: 'test@example.com',
        password: 'Password123',
        name: 'Test User',
      };

      const expectedUser = { id: '1', ...createUserDto };

      jest.spyOn(repository, 'create').mockReturnValue(expectedUser as any);
      jest.spyOn(repository, 'save').mockResolvedValue(expectedUser as any);

      const result = await service.create(createUserDto);

      expect(result).toEqual(expectedUser);
      expect(repository.create).toHaveBeenCalledWith(createUserDto);
      expect(repository.save).toHaveBeenCalledWith(expectedUser);
    });
  });

  describe('findOne', () => {
    it('should throw NotFoundException if user not found', async () => {
      jest.spyOn(repository, 'findOne').mockResolvedValue(null);

      await expect(service.findOne('1')).rejects.toThrow(NotFoundException);
    });
  });
});

// E2E Test
describe('UsersController (e2e)', () => {
  let app: INestApplication;
  let authToken: string;

  beforeAll(async () => {
    const moduleFixture: TestingModule = await Test.createTestingModule({
      imports: [AppModule],
    }).compile();

    app = moduleFixture.createNestApplication();
    app.useGlobalPipes(new ValidationPipe());
    await app.init();

    // Get auth token
    const response = await request(app.getHttpServer())
      .post('/auth/login')
      .send({ email: 'admin@example.com', password: 'password' });

    authToken = response.body.access_token;
  });

  it('/users (POST)', () => {
    return request(app.getHttpServer())
      .post('/users')
      .set('Authorization', `Bearer ${authToken}`)
      .send({
        email: 'newuser@example.com',
        password: 'Password123',
        name: 'New User',
      })
      .expect(201)
      .expect((res) => {
        expect(res.body).toHaveProperty('id');
        expect(res.body.email).toBe('newuser@example.com');
      });
  });

  afterAll(async () => {
    await app.close();
  });
});
```

## Critical Rules

### Always Do
- Use dependency injection for all services
- Validate all incoming data with class-validator
- Use DTOs for all request/response bodies
- Implement proper error handling and logging
- Use guards for authentication/authorization
- Document APIs with Swagger decorators
- Write unit and E2E tests
- Use environment variables for configuration
- Implement proper module organization
- Use TypeScript strict mode

### Never Do
- Never expose sensitive data in responses (passwords, secrets)
- Never trust user input without validation
- Never use synchronous operations in services
- Never hardcode configuration values
- Never skip error handling
- Never ignore security best practices
- Never use any type unless absolutely necessary
- Never create circular dependencies between modules

## Knowledge Base

- **NestJS Core**: Modules, Controllers, Providers, Middleware, Guards, Interceptors, Pipes
- **TypeORM/Prisma**: Database integration and ORM patterns
- **Authentication**: JWT, Passport, OAuth, Session management
- **Testing**: Jest, Supertest, E2E testing patterns
- **GraphQL**: GraphQL with NestJS (@nestjs/graphql)
- **Microservices**: TCP, Redis, NATS, gRPC transport layers
- **WebSockets**: Real-time communication with Socket.io
- **Caching**: Redis integration for caching
- **Queue**: Bull/BullMQ for background jobs
- **Documentation**: Swagger/OpenAPI integration

## Integration with Other Skills

- **Works with**: Fullstack Guardian, Test Master, DevOps Engineer
- **Complements**: Code Documenter (for Swagger docs), Security Reviewer

## Best Practices Summary

1. **Module Design**: Feature-based modules with clear boundaries
2. **Dependency Injection**: Use DI for all service dependencies
3. **Validation**: Validate all inputs with class-validator
4. **Error Handling**: Centralized error handling with filters
5. **Security**: JWT auth, RBAC, input validation, helmet middleware
6. **Testing**: High test coverage with unit and E2E tests
7. **Documentation**: Comprehensive Swagger documentation
8. **Configuration**: Environment-based configuration management
9. **Logging**: Structured logging with context
10. **Performance**: Caching, database query optimization, async operations
