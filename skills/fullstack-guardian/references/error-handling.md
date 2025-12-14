# Error Handling Patterns

> Reference for: Fullstack Guardian
> Load when: Implementing error handling

## Frontend Error Handling

```typescript
// React with async/await
async function handleSubmit(data: FormData) {
  setLoading(true);
  setError(null);

  try {
    const result = await api.updateProfile(data);
    showSuccess('Profile updated');
    return result;
  } catch (error) {
    if (error.status === 401) {
      redirect('/login');
    } else if (error.status === 403) {
      showError('Not authorized');
    } else if (error.status === 422) {
      setValidationErrors(error.errors);
    } else {
      showError('Something went wrong');
      reportError(error); // Send to error tracking
    }
  } finally {
    setLoading(false);
  }
}
```

```typescript
// Custom hook for API calls
function useApi<T>(fn: () => Promise<T>) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<Error | null>(null);
  const [loading, setLoading] = useState(false);

  const execute = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await fn();
      setData(result);
      return result;
    } catch (e) {
      setError(e as Error);
      throw e;
    } finally {
      setLoading(false);
    }
  }, [fn]);

  return { data, error, loading, execute };
}
```

## Backend Error Handling

```python
# FastAPI
from fastapi import HTTPException

@router.put("/users/{user_id}")
async def update_user(
    user_id: int,
    data: UserUpdate,
    current_user: User = Depends(get_current_user)
):
    if current_user.id != user_id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized")

    try:
        return await user_service.update(user_id, data)
    except UserNotFound:
        raise HTTPException(status_code=404, detail="User not found")
    except EmailTaken:
        raise HTTPException(status_code=422, detail="Email already in use")
```

```typescript
// NestJS
@Put(':id')
async updateUser(
  @Param('id') id: string,
  @Body() dto: UpdateUserDto,
  @CurrentUser() user: User,
) {
  if (user.id !== id && !user.isAdmin) {
    throw new ForbiddenException('Not authorized');
  }

  try {
    return await this.userService.update(id, dto);
  } catch (error) {
    if (error instanceof UserNotFoundError) {
      throw new NotFoundException('User not found');
    }
    if (error instanceof EmailTakenError) {
      throw new UnprocessableEntityException('Email already in use');
    }
    throw error;
  }
}
```

## Error Response Format

```typescript
// Consistent error shape
interface ApiError {
  error: string;
  message: string;
  details?: Record<string, string[]>;
  requestId?: string;
}

// Example responses
{ "error": "VALIDATION_ERROR", "message": "Invalid input", "details": { "email": ["Invalid format"] } }
{ "error": "NOT_FOUND", "message": "User not found" }
{ "error": "FORBIDDEN", "message": "Not authorized to perform this action" }
```

## Quick Reference

| HTTP Code | When to Use | Example |
|-----------|-------------|---------|
| 400 | Invalid request format | Malformed JSON |
| 401 | Not authenticated | Missing/invalid token |
| 403 | Not authorized | Wrong permissions |
| 404 | Resource not found | User doesn't exist |
| 409 | Conflict | Duplicate email |
| 422 | Validation failed | Invalid email format |
| 429 | Rate limited | Too many requests |
| 500 | Server error | Unhandled exception |
