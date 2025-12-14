# Services & Dependency Injection

> Reference for: NestJS Expert
> Load when: Creating services, dependency injection, providers

## Service Pattern

```typescript
import { Injectable, Logger, NotFoundException, ConflictException } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository } from 'typeorm';

@Injectable()
export class UsersService {
  private readonly logger = new Logger(UsersService.name);

  constructor(
    @InjectRepository(User)
    private readonly repo: Repository<User>,
    private readonly emailService: EmailService,
  ) {}

  async create(dto: CreateUserDto): Promise<User> {
    try {
      const user = this.repo.create(dto);
      const saved = await this.repo.save(user);
      await this.emailService.sendWelcome(saved.email);
      return saved;
    } catch (error) {
      if (error.code === '23505') {
        throw new ConflictException('Email already exists');
      }
      this.logger.error(`Failed to create user: ${error.message}`);
      throw error;
    }
  }

  async findOne(id: string): Promise<User> {
    const user = await this.repo.findOne({ where: { id } });
    if (!user) {
      throw new NotFoundException(`User ${id} not found`);
    }
    return user;
  }

  async update(id: string, dto: UpdateUserDto): Promise<User> {
    const user = await this.findOne(id);
    Object.assign(user, dto);
    return this.repo.save(user);
  }

  async remove(id: string): Promise<void> {
    const result = await this.repo.delete(id);
    if (result.affected === 0) {
      throw new NotFoundException(`User ${id} not found`);
    }
  }
}
```

## Module with Providers

```typescript
@Module({
  imports: [TypeOrmModule.forFeature([User])],
  controllers: [UsersController],
  providers: [UsersService],
  exports: [UsersService],  // Make available to other modules
})
export class UsersModule {}
```

## Custom Providers

```typescript
// Value provider
{ provide: 'API_KEY', useValue: process.env.API_KEY }

// Factory provider
{
  provide: 'CONFIG',
  useFactory: (configService: ConfigService) => ({
    apiUrl: configService.get('API_URL'),
  }),
  inject: [ConfigService],
}

// Class provider
{ provide: LoggerService, useClass: CustomLoggerService }

// Async factory
{
  provide: 'DATABASE_CONNECTION',
  useFactory: async () => {
    const connection = await createConnection();
    return connection;
  },
}
```

## Injection Patterns

```typescript
// Constructor injection (preferred)
constructor(private readonly usersService: UsersService) {}

// Token injection
constructor(@Inject('API_KEY') private apiKey: string) {}

// Optional injection
constructor(@Optional() private readonly cache?: CacheService) {}

// Property injection (use sparingly)
@Inject() private readonly logger: Logger;
```

## Scope

```typescript
// Default: Singleton (shared across app)
@Injectable()
export class SharedService {}

// Request-scoped: New instance per request
@Injectable({ scope: Scope.REQUEST })
export class RequestService {
  constructor(@Inject(REQUEST) private request: Request) {}
}

// Transient: New instance every injection
@Injectable({ scope: Scope.TRANSIENT })
export class HelperService {}
```

## Quick Reference

| Pattern | Use When |
|---------|----------|
| Constructor DI | Most cases (recommended) |
| `@Inject(token)` | Non-class tokens |
| `@Optional()` | Optional dependency |
| Factory provider | Dynamic configuration |
| Scope.REQUEST | Per-request state |
