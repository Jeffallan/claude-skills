# Models & ORM

## Model Design

```python
from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    email = models.EmailField(unique=True)
    bio = models.TextField(blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    class Meta:
        indexes = [models.Index(fields=['email'])]

class Product(models.Model):
    name = models.CharField(max_length=200, db_index=True)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    category = models.ForeignKey(
        'Category', on_delete=models.SET_NULL,
        null=True, related_name='products'
    )
    tags = models.ManyToManyField('Tag', related_name='products', blank=True)
    created_by = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='products'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['is_active', '-created_at']),
        ]

    def __str__(self) -> str:
        return self.name
```

## Query Optimization

```python
# ❌ N+1 Problem
for product in Product.objects.all():
    print(product.category.name)  # Query per product

# ✅ select_related (ForeignKey, OneToOne)
products = Product.objects.select_related('category', 'created_by').all()

# ✅ prefetch_related (ManyToMany, reverse FK)
products = Product.objects.prefetch_related('tags').all()

# Combined
products = Product.objects.select_related(
    'category', 'created_by'
).prefetch_related('tags').all()
```

## Efficient Queries

```python
# Only fetch needed fields
users = User.objects.only('id', 'email').all()
users = User.objects.defer('bio', 'avatar').all()

# Aggregations
from django.db.models import Count, Avg, Sum, F, Q

Product.objects.aggregate(
    avg_price=Avg('price'),
    total_stock=Sum('stock'),
)

# Annotate with counts
categories = Category.objects.annotate(
    product_count=Count('products')
).filter(product_count__gt=0)

# F expressions (database-level operations)
Product.objects.update(price=F('price') * 1.1)  # 10% increase

# Q objects (complex queries)
Product.objects.filter(
    Q(price__lt=100) | Q(stock__gt=50),
    is_active=True
)
```

## Custom Manager

```python
class ProductManager(models.Manager):
    def active(self):
        return self.filter(is_active=True)

    def in_stock(self):
        return self.filter(stock__gt=0)

    def with_related(self):
        return self.select_related('category').prefetch_related('tags')

class Product(models.Model):
    # ... fields ...
    objects = ProductManager()

# Usage
Product.objects.active().in_stock().with_related()
```

## Bulk Operations

```python
# Bulk create
Product.objects.bulk_create([
    Product(name='A', price=10),
    Product(name='B', price=20),
], batch_size=1000)

# Bulk update
Product.objects.filter(category=old).update(category=new)

# Bulk update specific instances
products = list(Product.objects.filter(is_active=True))
for p in products:
    p.stock += 10
Product.objects.bulk_update(products, ['stock'], batch_size=1000)
```

## Quick Reference

| Method | Use Case |
|--------|----------|
| `select_related()` | FK, OneToOne |
| `prefetch_related()` | ManyToMany, reverse FK |
| `only()` / `defer()` | Partial field loading |
| `annotate()` | Add computed fields |
| `aggregate()` | Single-row aggregates |
| `F()` | Database-level operations |
| `Q()` | Complex queries |
| `bulk_create()` | Mass insert |
| `update()` | Mass update |
