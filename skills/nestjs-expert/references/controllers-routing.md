# Controllers & Routing

> Reference for: NestJS Expert
> Load when: Creating controllers, routing, Swagger documentation

## Controller with Swagger

```typescript
import {
  Controller, Get, Post, Patch, Delete,
  Body, Param, Query, HttpCode, HttpStatus, UseGuards
} from '@nestjs/common';
import { ApiTags, ApiOperation, ApiResponse, ApiParam, ApiQuery } from '@nestjs/swagger';
import { ParseUUIDPipe, ParseIntPipe } from '@nestjs/common';

@Controller('users')
@ApiTags('users')
@UseGuards(JwtAuthGuard)
export class UsersController {
  constructor(private readonly usersService: UsersService) {}

  @Post()
  @ApiOperation({ summary: 'Create user' })
  @ApiResponse({ status: 201, type: UserDto })
  @ApiResponse({ status: 400, description: 'Validation failed' })
  create(@Body() dto: CreateUserDto): Promise<UserDto> {
    return this.usersService.create(dto);
  }

  @Get()
  @ApiOperation({ summary: 'Get all users' })
  @ApiQuery({ name: 'page', required: false, type: Number })
  @ApiQuery({ name: 'limit', required: false, type: Number })
  findAll(
    @Query('page', new ParseIntPipe({ optional: true })) page = 1,
    @Query('limit', new ParseIntPipe({ optional: true })) limit = 20,
  ): Promise<UserDto[]> {
    return this.usersService.findAll({ page, limit });
  }

  @Get(':id')
  @ApiParam({ name: 'id', type: 'string', format: 'uuid' })
  @ApiResponse({ status: 200, type: UserDto })
  @ApiResponse({ status: 404, description: 'User not found' })
  findOne(@Param('id', ParseUUIDPipe) id: string): Promise<UserDto> {
    return this.usersService.findOne(id);
  }

  @Patch(':id')
  update(
    @Param('id', ParseUUIDPipe) id: string,
    @Body() dto: UpdateUserDto,
  ): Promise<UserDto> {
    return this.usersService.update(id, dto);
  }

  @Delete(':id')
  @HttpCode(HttpStatus.NO_CONTENT)
  remove(@Param('id', ParseUUIDPipe) id: string): Promise<void> {
    return this.usersService.remove(id);
  }
}
```

## Nested Routes

```typescript
@Controller('posts/:postId/comments')
@ApiTags('comments')
export class CommentsController {
  @Get()
  findAll(@Param('postId', ParseUUIDPipe) postId: string) {
    return this.commentsService.findByPost(postId);
  }

  @Post()
  create(
    @Param('postId', ParseUUIDPipe) postId: string,
    @Body() dto: CreateCommentDto,
  ) {
    return this.commentsService.create(postId, dto);
  }
}
```

## Global Prefix & Versioning

```typescript
// main.ts
const app = await NestFactory.create(AppModule);
app.setGlobalPrefix('api');
app.enableVersioning({ type: VersioningType.URI });

// controller.ts
@Controller({ path: 'users', version: '1' })  // /api/v1/users
export class UsersV1Controller {}

@Controller({ path: 'users', version: '2' })  // /api/v2/users
export class UsersV2Controller {}
```

## Quick Reference

| Decorator | Purpose |
|-----------|---------|
| `@Controller('path')` | Define route prefix |
| `@Get()`, `@Post()` | HTTP method |
| `@Param('name')` | Path parameter |
| `@Query('name')` | Query parameter |
| `@Body()` | Request body |
| `@HttpCode(201)` | Override status code |
| `@ApiTags()` | Swagger grouping |
| `@ApiOperation()` | Endpoint description |
| `@ApiResponse()` | Document response |
