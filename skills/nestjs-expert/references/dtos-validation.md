# DTOs & Validation

> Reference for: NestJS Expert
> Load when: Creating DTOs, validation, class-validator

## DTO Patterns

```typescript
import {
  IsEmail, IsString, IsOptional, IsBoolean, IsInt,
  MinLength, MaxLength, Min, Max, IsUUID, IsEnum,
  IsArray, ArrayMinSize, ValidateNested, Matches
} from 'class-validator';
import { Type, Transform } from 'class-transformer';
import { ApiProperty, ApiPropertyOptional, PartialType, OmitType, PickType } from '@nestjs/swagger';

export class CreateUserDto {
  @ApiProperty({ example: 'user@example.com' })
  @IsEmail()
  email: string;

  @ApiProperty({ minLength: 8 })
  @IsString()
  @MinLength(8)
  @Matches(/^(?=.*[A-Z])(?=.*\d)/, { message: 'Password must contain uppercase and digit' })
  password: string;

  @ApiProperty()
  @IsString()
  @MinLength(2)
  @MaxLength(50)
  name: string;

  @ApiPropertyOptional({ enum: UserRole, default: UserRole.USER })
  @IsOptional()
  @IsEnum(UserRole)
  role?: UserRole = UserRole.USER;
}

// Partial for updates (all fields optional)
export class UpdateUserDto extends PartialType(
  OmitType(CreateUserDto, ['password'] as const)
) {}

// Pick specific fields
export class LoginDto extends PickType(CreateUserDto, ['email', 'password'] as const) {}
```

## Nested Validation

```typescript
export class CreateOrderDto {
  @ApiProperty({ type: [OrderItemDto] })
  @IsArray()
  @ArrayMinSize(1)
  @ValidateNested({ each: true })
  @Type(() => OrderItemDto)
  items: OrderItemDto[];

  @ApiProperty({ type: AddressDto })
  @ValidateNested()
  @Type(() => AddressDto)
  shippingAddress: AddressDto;
}

export class OrderItemDto {
  @IsUUID()
  productId: string;

  @IsInt()
  @Min(1)
  @Max(100)
  quantity: number;
}
```

## Custom Validation

```typescript
import { registerDecorator, ValidationOptions, ValidationArguments } from 'class-validator';

// Custom decorator
export function IsStrongPassword(options?: ValidationOptions) {
  return function (object: object, propertyName: string) {
    registerDecorator({
      name: 'isStrongPassword',
      target: object.constructor,
      propertyName,
      options,
      validator: {
        validate(value: string) {
          return /^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[@$!%*?&]).{8,}$/.test(value);
        },
        defaultMessage(): string {
          return 'Password must contain uppercase, lowercase, digit, and special character';
        },
      },
    });
  };
}

// Usage
@IsStrongPassword()
password: string;
```

## Transform & Sanitize

```typescript
export class QueryDto {
  @Transform(({ value }) => parseInt(value, 10))
  @IsInt()
  @Min(1)
  page: number = 1;

  @Transform(({ value }) => value?.trim().toLowerCase())
  @IsString()
  @IsOptional()
  search?: string;

  @Transform(({ value }) => value === 'true')
  @IsBoolean()
  isActive: boolean = true;
}
```

## Enable Validation Globally

```typescript
// main.ts
app.useGlobalPipes(new ValidationPipe({
  whitelist: true,           // Strip unknown properties
  forbidNonWhitelisted: true, // Throw on unknown properties
  transform: true,            // Auto-transform types
  transformOptions: {
    enableImplicitConversion: true,
  },
}));
```

## Quick Reference

| Decorator | Purpose |
|-----------|---------|
| `@IsString()` | String type |
| `@IsEmail()` | Valid email |
| `@MinLength(n)` | Min string length |
| `@IsInt()`, `@Min(n)` | Integer validation |
| `@IsEnum(Enum)` | Enum value |
| `@IsOptional()` | Optional field |
| `@ValidateNested()` | Validate nested object |
| `@Type(() => Class)` | Transform to class |
| `@Transform()` | Custom transform |
| `PartialType()` | All fields optional |
| `OmitType()` | Exclude fields |
| `PickType()` | Include only fields |
