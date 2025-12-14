# API Documentation: NestJS & Express

> Reference for: Code Documenter
> Load when: Documenting Node.js API frameworks

## NestJS (@nestjs/swagger)

NestJS requires explicit decorators for OpenAPI documentation.

### Controller Documentation

```typescript
import { Controller, Post, Body, Get, Param } from '@nestjs/common';
import {
  ApiTags,
  ApiOperation,
  ApiResponse,
  ApiParam,
  ApiBearerAuth,
} from '@nestjs/swagger';

@ApiTags('Users')
@ApiBearerAuth()
@Controller('users')
export class UsersController {
  @Post()
  @ApiOperation({ summary: 'Create a new user' })
  @ApiResponse({
    status: 201,
    description: 'User created successfully',
    type: UserDto,
  })
  @ApiResponse({
    status: 400,
    description: 'Invalid input data',
  })
  async create(@Body() dto: CreateUserDto): Promise<UserDto> {
    return this.usersService.create(dto);
  }

  @Get(':id')
  @ApiOperation({ summary: 'Get user by ID' })
  @ApiParam({
    name: 'id',
    description: 'User unique identifier',
    example: '123',
  })
  @ApiResponse({ status: 200, type: UserDto })
  @ApiResponse({ status: 404, description: 'User not found' })
  async findOne(@Param('id') id: string): Promise<UserDto> {
    return this.usersService.findOne(id);
  }
}
```

### DTO Documentation

```typescript
import { ApiProperty, ApiPropertyOptional } from '@nestjs/swagger';
import { IsEmail, IsString, MinLength } from 'class-validator';

export class CreateUserDto {
  @ApiProperty({
    description: "User's display name",
    example: 'John Doe',
    minLength: 1,
    maxLength: 100,
  })
  @IsString()
  @MinLength(1)
  name: string;

  @ApiProperty({
    description: "User's email address",
    example: 'john@example.com',
  })
  @IsEmail()
  email: string;

  @ApiPropertyOptional({
    description: 'Profile picture URL',
    example: 'https://example.com/avatar.jpg',
  })
  avatarUrl?: string;
}
```

## Express (swagger-jsdoc)

Express uses JSDoc comments with swagger annotations.

### Setup

```javascript
const swaggerJsdoc = require('swagger-jsdoc');
const swaggerUi = require('swagger-ui-express');

const options = {
  definition: {
    openapi: '3.0.0',
    info: {
      title: 'API Documentation',
      version: '1.0.0',
    },
  },
  apis: ['./routes/*.js'],
};

const specs = swaggerJsdoc(options);
app.use('/api-docs', swaggerUi.serve, swaggerUi.setup(specs));
```

### Route Documentation

```javascript
/**
 * @swagger
 * /users:
 *   post:
 *     summary: Create a new user
 *     tags: [Users]
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             $ref: '#/components/schemas/CreateUser'
 *     responses:
 *       201:
 *         description: User created successfully
 *         content:
 *           application/json:
 *             schema:
 *               $ref: '#/components/schemas/User'
 *       400:
 *         description: Invalid input
 */
router.post('/users', createUser);

/**
 * @swagger
 * /users/{id}:
 *   get:
 *     summary: Get user by ID
 *     tags: [Users]
 *     parameters:
 *       - in: path
 *         name: id
 *         required: true
 *         schema:
 *           type: string
 *         description: User ID
 *     responses:
 *       200:
 *         description: User found
 *         content:
 *           application/json:
 *             schema:
 *               $ref: '#/components/schemas/User'
 *       404:
 *         description: User not found
 */
router.get('/users/:id', getUser);
```

### Schema Documentation

```javascript
/**
 * @swagger
 * components:
 *   schemas:
 *     CreateUser:
 *       type: object
 *       required:
 *         - name
 *         - email
 *       properties:
 *         name:
 *           type: string
 *           description: User's display name
 *           example: John Doe
 *         email:
 *           type: string
 *           format: email
 *           description: User's email address
 *           example: john@example.com
 *     User:
 *       allOf:
 *         - $ref: '#/components/schemas/CreateUser'
 *         - type: object
 *           properties:
 *             id:
 *               type: string
 *               description: Unique identifier
 *             createdAt:
 *               type: string
 *               format: date-time
 */
```

## Quick Reference

| NestJS Decorator | Purpose |
|------------------|---------|
| `@ApiTags()` | Group endpoints |
| `@ApiOperation()` | Endpoint summary |
| `@ApiResponse()` | Response documentation |
| `@ApiParam()` | Path parameter |
| `@ApiQuery()` | Query parameter |
| `@ApiBody()` | Request body |
| `@ApiBearerAuth()` | Auth requirement |
| `@ApiProperty()` | DTO property |

| Express swagger-jsdoc | Purpose |
|-----------------------|---------|
| `@swagger` | Start swagger block |
| `tags` | Group endpoints |
| `summary` | Short description |
| `parameters` | Path/query params |
| `requestBody` | Request body schema |
| `responses` | Response schemas |
| `$ref` | Reference schema |
