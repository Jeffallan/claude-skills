---
name: Django Expert
description: Expert in Django web framework for building robust Python applications. Use when working with Django, Django REST Framework, Django ORM, models, views, serializers, middleware, or when the user mentions Django, Python web development, or DRF.
---

# Django Expert

A specialized skill for building production-ready web applications with Django and Django REST Framework. This skill covers MVC architecture, ORM, REST APIs, authentication, and Django best practices.

## Instructions

### Core Workflow

1. **Understand requirements**
   - Identify if this is a traditional Django app or REST API (DRF)
   - Determine database requirements
   - Understand authentication needs
   - Identify third-party integrations

2. **Project structure**
   - Follow Django app-based architecture
   - Separate business logic from views
   - Use proper settings management (dev/prod)
   - Implement custom user models if needed

3. **Implement features**
   - Create models with proper relationships
   - Implement views/viewsets following best practices
   - Create serializers with proper validation (DRF)
   - Add authentication and permissions
   - Implement middleware and signals where appropriate

4. **Testing and documentation**
   - Write tests using Django's test framework
   - Document APIs with drf-spectacular
   - Configure for production deployment

### Django Project Structure

```
myproject/
├── manage.py
├── myproject/              # Project root
│   ├── __init__.py
│   ├── settings/          # Split settings
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── development.py
│   │   └── production.py
│   ├── urls.py
│   └── wsgi.py
├── apps/                   # All Django apps
│   ├── users/
│   │   ├── models.py
│   │   ├── views.py
│   │   ├── serializers.py  # DRF
│   │   ├── urls.py
│   │   ├── admin.py
│   │   ├── tests/
│   │   └── managers.py
│   └── products/
└── requirements/
    ├── base.txt
    ├── development.txt
    └── production.txt
```

### Model Best Practices

```python
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth.models import AbstractUser

# Custom User Model
class User(AbstractUser):
    """Custom user model with additional fields"""
    email = models.EmailField(unique=True)
    bio = models.TextField(max_length=500, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    class Meta:
        ordering = ['-date_joined']
        indexes = [
            models.Index(fields=['email']),
        ]

    def __str__(self):
        return self.email

# Model with relationships
class Product(models.Model):
    """Product model with proper field types and validation"""
    name = models.CharField(max_length=200, db_index=True)
    slug = models.SlugField(max_length=200, unique=True)
    description = models.TextField()
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    stock = models.PositiveIntegerField(default=0)
    available = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='products'
    )
    category = models.ForeignKey(
        'Category',
        on_delete=models.SET_NULL,
        null=True,
        related_name='products'
    )
    tags = models.ManyToManyField('Tag', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('product-detail', kwargs={'slug': self.slug})

    def is_in_stock(self):
        return self.available and self.stock > 0

# Custom Manager
class PublishedManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(status='published')

class Post(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
    ]

    title = models.CharField(max_length=200)
    content = models.TextField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='draft')

    objects = models.Manager()  # Default manager
    published = PublishedManager()  # Custom manager
```

### Django REST Framework

```python
# serializers.py
from rest_framework import serializers
from .models import Product, Category

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug']

class ProductSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        source='category',
        write_only=True
    )
    created_by_email = serializers.EmailField(source='created_by.email', read_only=True)

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'description', 'price', 'stock',
            'available', 'category', 'category_id', 'created_by_email',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['slug', 'created_at', 'updated_at']

    def validate_price(self, value):
        if value < 0:
            raise serializers.ValidationError("Price cannot be negative")
        return value

    def validate(self, data):
        # Cross-field validation
        if data.get('available') and data.get('stock', 0) == 0:
            raise serializers.ValidationError(
                "Product cannot be available with zero stock"
            )
        return data

# views.py (ViewSets)
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from django_filters.rest_framework import DjangoFilterBackend

class ProductViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing products.

    list: Get all products
    retrieve: Get a single product
    create: Create a new product
    update: Update a product
    destroy: Delete a product
    """
    queryset = Product.objects.select_related('category', 'created_by').all()
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'available']
    search_fields = ['name', 'description']
    ordering_fields = ['price', 'created_at']
    lookup_field = 'slug'

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['post'])
    def purchase(self, request, slug=None):
        """Custom action to purchase a product"""
        product = self.get_object()
        quantity = request.data.get('quantity', 1)

        if not product.is_in_stock():
            return Response(
                {'error': 'Product out of stock'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if product.stock < quantity:
            return Response(
                {'error': f'Only {product.stock} items available'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Process purchase logic here
        product.stock -= quantity
        product.save()

        return Response({'message': 'Purchase successful'})

    @action(detail=False, methods=['get'])
    def low_stock(self, request):
        """Get products with low stock"""
        low_stock_products = self.queryset.filter(stock__lt=10, available=True)
        serializer = self.get_serializer(low_stock_products, many=True)
        return Response(serializer.data)

# urls.py
from rest_framework.routers import DefaultRouter
from .views import ProductViewSet

router = DefaultRouter()
router.register(r'products', ProductViewSet, basename='product')

urlpatterns = router.urls
```

### Authentication & Permissions

```python
# Custom Permission
from rest_framework import permissions

class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to the owner
        return obj.created_by == request.user

# JWT Authentication (using Simple JWT)
# settings.py
from datetime import timedelta

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 10,
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
    ],
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
}

# views.py - Auth endpoints
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # Add custom claims
        token['email'] = user.email
        token['is_staff'] = user.is_staff
        return token

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
```

### Middleware & Signals

```python
# middleware.py
import logging

logger = logging.getLogger(__name__)

class RequestLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Log request
        logger.info(f"{request.method} {request.path}")

        response = self.get_response(request)

        # Log response
        logger.info(f"{request.method} {request.path} - {response.status_code}")

        return response

# signals.py
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from .models import Product

@receiver(post_save, sender=Product)
def product_saved(sender, instance, created, **kwargs):
    if created:
        # Send notification or perform action when product is created
        logger.info(f"New product created: {instance.name}")
    else:
        # Product was updated
        logger.info(f"Product updated: {instance.name}")

@receiver(pre_delete, sender=Product)
def product_deleted(sender, instance, **kwargs):
    # Cleanup before deletion
    if instance.avatar:
        instance.avatar.delete(save=False)
```

### Testing

```python
# tests/test_models.py
from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.products.models import Product, Category

User = get_user_model()

class ProductModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123'
        )
        self.category = Category.objects.create(name='Electronics', slug='electronics')
        self.product = Product.objects.create(
            name='Laptop',
            slug='laptop',
            description='A great laptop',
            price=999.99,
            stock=10,
            created_by=self.user,
            category=self.category
        )

    def test_product_creation(self):
        self.assertEqual(self.product.name, 'Laptop')
        self.assertEqual(str(self.product), 'Laptop')

    def test_is_in_stock(self):
        self.assertTrue(self.product.is_in_stock())

        self.product.stock = 0
        self.assertFalse(self.product.is_in_stock())

# tests/test_api.py
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.urls import reverse

class ProductAPITest(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123'
        )
        self.category = Category.objects.create(name='Electronics', slug='electronics')

    def test_create_product_authenticated(self):
        self.client.force_authenticate(user=self.user)

        url = reverse('product-list')
        data = {
            'name': 'New Product',
            'description': 'Product description',
            'price': 99.99,
            'stock': 50,
            'category_id': self.category.id
        }

        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Product.objects.count(), 1)
        self.assertEqual(Product.objects.first().name, 'New Product')

    def test_list_products(self):
        Product.objects.create(
            name='Product 1',
            slug='product-1',
            description='Description',
            price=50.00,
            stock=10,
            created_by=self.user,
            category=self.category
        )

        url = reverse('product-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
```

### Performance Optimization

```python
# Use select_related and prefetch_related
# Bad
products = Product.objects.all()
for product in products:
    print(product.category.name)  # N+1 query problem

# Good
products = Product.objects.select_related('category', 'created_by').all()
for product in products:
    print(product.category.name)  # Single query

# For many-to-many
products = Product.objects.prefetch_related('tags').all()

# Database indexes in models
class Meta:
    indexes = [
        models.Index(fields=['slug']),
        models.Index(fields=['-created_at']),
        models.Index(fields=['category', '-created_at']),
    ]

# Caching with Redis
from django.core.cache import cache
from django.views.decorators.cache import cache_page

@cache_page(60 * 15)  # Cache for 15 minutes
def product_list(request):
    products = Product.objects.all()
    return render(request, 'products/list.html', {'products': products})

# Cache querysets
def get_products():
    products = cache.get('all_products')
    if products is None:
        products = list(Product.objects.select_related('category').all())
        cache.set('all_products', products, 60 * 15)
    return products
```

## Critical Rules

### Always Do
- Use environment variables for sensitive data
- Implement proper model validation
- Use select_related/prefetch_related to avoid N+1 queries
- Write tests for models, views, and APIs
- Use database indexes for frequently queried fields
- Implement proper authentication and permissions
- Document APIs with drf-spectacular
- Use Django's ORM efficiently
- Handle errors gracefully with proper HTTP status codes

### Never Do
- Never store passwords in plain text
- Never expose Django secret key
- Never use raw SQL unless absolutely necessary
- Never skip migrations
- Never commit sensitive data
- Never trust user input without validation
- Never use DEBUG=True in production
- Never ignore database optimization

## Knowledge Base

- **Django Core**: Models, Views, Templates, Forms, Admin
- **Django REST Framework**: Serializers, ViewSets, Permissions, Authentication
- **ORM**: QuerySets, Managers, Aggregation, F/Q expressions
- **Authentication**: JWT, Session, OAuth
- **Testing**: Django TestCase, APITestCase
- **Performance**: Query optimization, Caching, Database indexing
- **Security**: CSRF, XSS, SQL injection prevention
- **Deployment**: WSGI, Gunicorn, Nginx, Docker

## Integration with Other Skills

- **Works with**: Fullstack Guardian, Test Master, DevOps Engineer
- **Complements**: FastAPI Expert (alternative Python framework), Code Documenter

## Best Practices Summary

1. **Models**: Use proper field types, validators, indexes
2. **Serializers**: Validate thoroughly, use nested serializers wisely
3. **ViewSets**: Use appropriate mixins, implement custom actions
4. **Permissions**: Layer permissions appropriately
5. **Testing**: High test coverage for business logic
6. **Performance**: Query optimization, caching, pagination
7. **Security**: HTTPS, CSRF tokens, proper authentication
8. **Documentation**: DRF self-documenting + drf-spectacular
