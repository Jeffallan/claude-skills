# Common Patterns

> Reference for: Fullstack Guardian
> Load when: Implementing standard features

## API + Frontend Flow

```
User Action → Frontend Validation → API Call → Backend Validation
→ Business Logic → Database → Response → UI Update
```

## CRUD Implementation

### Create

```typescript
// Frontend
const createUser = async (data: CreateUserDto) => {
  const response = await fetch('/api/users', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!response.ok) throw await response.json();
  return response.json();
};

// Backend (NestJS)
@Post()
async create(@Body() dto: CreateUserDto): Promise<User> {
  return this.userService.create(dto);
}
```

### Read (List with Pagination)

```typescript
// Frontend
const { data, isLoading } = useQuery({
  queryKey: ['users', page, limit],
  queryFn: () => fetch(`/api/users?page=${page}&limit=${limit}`).then(r => r.json()),
});

// Backend
@Get()
async findAll(
  @Query('page', new DefaultValuePipe(1), ParseIntPipe) page: number,
  @Query('limit', new DefaultValuePipe(20), ParseIntPipe) limit: number,
): Promise<PaginatedResponse<User>> {
  return this.userService.findAll({ page, limit });
}
```

### Update

```typescript
// Frontend with optimistic update
const updateUser = useMutation({
  mutationFn: (data: UpdateUserDto) => api.patch(`/users/${id}`, data),
  onMutate: async (newData) => {
    await queryClient.cancelQueries(['user', id]);
    const previous = queryClient.getQueryData(['user', id]);
    queryClient.setQueryData(['user', id], (old) => ({ ...old, ...newData }));
    return { previous };
  },
  onError: (err, newData, context) => {
    queryClient.setQueryData(['user', id], context.previous);
  },
});

// Backend
@Patch(':id')
async update(
  @Param('id') id: string,
  @Body() dto: UpdateUserDto,
): Promise<User> {
  return this.userService.update(id, dto);
}
```

### Delete

```typescript
// Frontend with confirmation
const handleDelete = async () => {
  if (!confirm('Are you sure?')) return;
  await api.delete(`/users/${id}`);
  router.push('/users');
};

// Backend (soft delete)
@Delete(':id')
@HttpCode(204)
async remove(@Param('id') id: string): Promise<void> {
  await this.userService.softDelete(id);
}
```

## Form Handling

```typescript
// React Hook Form + Zod
const schema = z.object({
  name: z.string().min(1, 'Required'),
  email: z.string().email('Invalid email'),
});

function UserForm({ onSubmit }: Props) {
  const { register, handleSubmit, formState: { errors } } = useForm({
    resolver: zodResolver(schema),
  });

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <input {...register('name')} />
      {errors.name && <span>{errors.name.message}</span>}

      <input {...register('email')} />
      {errors.email && <span>{errors.email.message}</span>}

      <button type="submit">Save</button>
    </form>
  );
}
```

## Quick Reference

| Pattern | Frontend | Backend |
|---------|----------|---------|
| Create | POST + form | Validate + insert |
| Read | GET + query | Paginate + filter |
| Update | PATCH + optimistic | Validate + update |
| Delete | DELETE + confirm | Soft delete |
| Auth | Token storage | JWT middleware |
| Upload | FormData | Multer/streaming |
