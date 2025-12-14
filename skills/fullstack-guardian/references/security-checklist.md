# Security Checklist

> Reference for: Fullstack Guardian
> Load when: Implementing any feature

## Per-Feature Security Checklist

| Category | Check | Action |
|----------|-------|--------|
| **Auth** | Endpoint requires authentication? | Add auth middleware/guard |
| **Authz** | User authorized for this action? | Check ownership/role |
| **Input** | All input validated and sanitized? | Use schemas, sanitize |
| **Output** | Sensitive data excluded from response? | Filter response fields |
| **Rate Limit** | Endpoint rate limited? | Add rate limiter |
| **Logging** | Security events logged? | Log auth failures, changes |

## Authentication Patterns

```typescript
// NestJS Guard
@UseGuards(JwtAuthGuard)
@Get('profile')
async getProfile(@CurrentUser() user: User) {
  return this.userService.findById(user.id);
}

// Express Middleware
app.get('/profile', authenticate, (req, res) => {
  res.json(req.user);
});
```

```python
# FastAPI Dependency
@router.get("/profile")
async def get_profile(current_user: User = Depends(get_current_user)):
    return current_user
```

## Authorization Patterns

```typescript
// Resource ownership check
async updatePost(postId: string, userId: string, data: UpdatePostDto) {
  const post = await this.postRepo.findById(postId);

  if (post.authorId !== userId) {
    throw new ForbiddenException('Not authorized to edit this post');
  }

  return this.postRepo.update(postId, data);
}

// Role-based check
@Roles('admin')
@UseGuards(RolesGuard)
@Delete(':id')
async deleteUser(@Param('id') id: string) {
  return this.userService.delete(id);
}
```

## Input Validation

```typescript
// Zod schema
const CreateUserSchema = z.object({
  email: z.string().email(),
  name: z.string().min(1).max(100),
  password: z.string().min(12),
});

// Use in endpoint
const validated = CreateUserSchema.parse(req.body);
```

```python
# Pydantic model
class CreateUser(BaseModel):
    email: EmailStr
    name: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=12)
```

## Rate Limiting

```typescript
// Express rate-limit
import rateLimit from 'express-rate-limit';

const authLimiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 5, // 5 attempts
  message: 'Too many login attempts',
});

app.post('/login', authLimiter, loginHandler);
```

## Quick Reference

| Risk | Mitigation |
|------|------------|
| SQL Injection | Parameterized queries |
| XSS | Output encoding, CSP |
| CSRF | CSRF tokens, SameSite cookies |
| IDOR | Authorization checks |
| Brute Force | Rate limiting |
| Data Exposure | Response filtering |
