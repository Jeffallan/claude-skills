# Testing Patterns

> Reference for: NestJS Expert
> Load when: Writing tests, Jest, mocking, E2E testing

## Unit Test Setup

```typescript
import { Test, TestingModule } from '@nestjs/testing';
import { getRepositoryToken } from '@nestjs/typeorm';
import { Repository } from 'typeorm';
import { NotFoundException } from '@nestjs/common';

describe('UsersService', () => {
  let service: UsersService;
  let repo: jest.Mocked<Repository<User>>;

  beforeEach(async () => {
    const module: TestingModule = await Test.createTestingModule({
      providers: [
        UsersService,
        {
          provide: getRepositoryToken(User),
          useValue: {
            create: jest.fn(),
            save: jest.fn(),
            findOne: jest.fn(),
            delete: jest.fn(),
          },
        },
      ],
    }).compile();

    service = module.get(UsersService);
    repo = module.get(getRepositoryToken(User));
  });

  afterEach(() => jest.clearAllMocks());
});
```

## Service Tests

```typescript
describe('create', () => {
  it('should create user', async () => {
    const dto = { email: 'test@test.com', password: 'pass', name: 'Test' };
    const user = { id: '1', ...dto };

    repo.create.mockReturnValue(user as User);
    repo.save.mockResolvedValue(user as User);

    const result = await service.create(dto);

    expect(repo.create).toHaveBeenCalledWith(dto);
    expect(repo.save).toHaveBeenCalledWith(user);
    expect(result).toEqual(user);
  });
});

describe('findOne', () => {
  it('should return user', async () => {
    const user = { id: '1', email: 'test@test.com' };
    repo.findOne.mockResolvedValue(user as User);

    const result = await service.findOne('1');
    expect(result).toEqual(user);
  });

  it('should throw NotFoundException', async () => {
    repo.findOne.mockResolvedValue(null);
    await expect(service.findOne('1')).rejects.toThrow(NotFoundException);
  });
});
```

## Controller Tests

```typescript
describe('UsersController', () => {
  let controller: UsersController;
  let service: jest.Mocked<UsersService>;

  beforeEach(async () => {
    const module = await Test.createTestingModule({
      controllers: [UsersController],
      providers: [
        {
          provide: UsersService,
          useValue: {
            create: jest.fn(),
            findOne: jest.fn(),
          },
        },
      ],
    }).compile();

    controller = module.get(UsersController);
    service = module.get(UsersService);
  });

  it('should create user', async () => {
    const dto = { email: 'test@test.com', password: 'pass', name: 'Test' };
    const user = { id: '1', ...dto };
    service.create.mockResolvedValue(user as User);

    const result = await controller.create(dto);
    expect(result).toEqual(user);
  });
});
```

## E2E Tests

```typescript
import { INestApplication } from '@nestjs/common';
import * as request from 'supertest';

describe('UsersController (e2e)', () => {
  let app: INestApplication;
  let authToken: string;

  beforeAll(async () => {
    const moduleFixture = await Test.createTestingModule({
      imports: [AppModule],
    }).compile();

    app = moduleFixture.createNestApplication();
    app.useGlobalPipes(new ValidationPipe({ whitelist: true }));
    await app.init();

    // Get auth token
    const response = await request(app.getHttpServer())
      .post('/auth/login')
      .send({ email: 'test@test.com', password: 'password' });
    authToken = response.body.access_token;
  });

  afterAll(() => app.close());

  it('/users (POST)', () => {
    return request(app.getHttpServer())
      .post('/users')
      .set('Authorization', `Bearer ${authToken}`)
      .send({ email: 'new@test.com', password: 'Test1234', name: 'New' })
      .expect(201)
      .expect((res) => {
        expect(res.body.email).toBe('new@test.com');
      });
  });

  it('/users/:id (GET) - 404', () => {
    return request(app.getHttpServer())
      .get('/users/nonexistent-id')
      .set('Authorization', `Bearer ${authToken}`)
      .expect(404);
  });
});
```

## Mock Factory

```typescript
export const createMockRepository = <T>() => ({
  create: jest.fn(),
  save: jest.fn(),
  find: jest.fn(),
  findOne: jest.fn(),
  update: jest.fn(),
  delete: jest.fn(),
  createQueryBuilder: jest.fn(() => ({
    where: jest.fn().mockReturnThis(),
    andWhere: jest.fn().mockReturnThis(),
    getOne: jest.fn(),
    getMany: jest.fn(),
  })),
});
```

## Quick Reference

| Pattern | Use Case |
|---------|----------|
| `Test.createTestingModule()` | Create test module |
| `jest.fn()` | Mock function |
| `mockResolvedValue()` | Mock async return |
| `mockReturnValue()` | Mock sync return |
| `supertest` | E2E HTTP testing |
| `beforeAll` / `afterAll` | Setup/teardown |
