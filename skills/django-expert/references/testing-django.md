# Testing Django

## APITestCase

```python
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse

class ProductAPITest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123'
        )
        self.category = Category.objects.create(name='Tech', slug='tech')
        self.product = Product.objects.create(
            name='Laptop',
            slug='laptop',
            price=999.99,
            stock=10,
            category=self.category,
            created_by=self.user
        )

    def test_list_products(self):
        url = reverse('product-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_create_product_authenticated(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('product-list')
        data = {
            'name': 'Phone',
            'price': 499.99,
            'stock': 5,
            'category_id': self.category.id
        }

        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Product.objects.count(), 2)

    def test_create_product_unauthenticated(self):
        url = reverse('product-list')
        response = self.client.post(url, {'name': 'Test'})

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
```

## Model Tests

```python
from django.test import TestCase
from django.core.exceptions import ValidationError

class ProductModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            username='test',
            password='pass'
        )
        self.category = Category.objects.create(name='Tech', slug='tech')

    def test_product_creation(self):
        product = Product.objects.create(
            name='Test Product',
            slug='test-product',
            price=100,
            category=self.category,
            created_by=self.user
        )

        self.assertEqual(str(product), 'Test Product')
        self.assertEqual(product.stock, 0)  # Default

    def test_product_slug_unique(self):
        Product.objects.create(
            name='First', slug='test', price=10,
            category=self.category, created_by=self.user
        )

        with self.assertRaises(Exception):
            Product.objects.create(
                name='Second', slug='test', price=20,
                category=self.category, created_by=self.user
            )
```

## Fixtures

```python
# fixtures/products.json
[
  {
    "model": "products.category",
    "pk": 1,
    "fields": {"name": "Electronics", "slug": "electronics"}
  },
  {
    "model": "products.product",
    "pk": 1,
    "fields": {
      "name": "Laptop",
      "slug": "laptop",
      "price": "999.99",
      "category": 1
    }
  }
]

# In test
class ProductTest(TestCase):
    fixtures = ['products.json']

    def test_with_fixture(self):
        product = Product.objects.get(slug='laptop')
        self.assertEqual(product.name, 'Laptop')
```

## Factory Boy

```python
import factory
from factory.django import DjangoModelFactory

class UserFactory(DjangoModelFactory):
    class Meta:
        model = User

    email = factory.Sequence(lambda n: f'user{n}@example.com')
    username = factory.Sequence(lambda n: f'user{n}')
    password = factory.PostGenerationMethodCall('set_password', 'testpass')

class ProductFactory(DjangoModelFactory):
    class Meta:
        model = Product

    name = factory.Faker('word')
    slug = factory.LazyAttribute(lambda o: slugify(o.name))
    price = factory.Faker('pydecimal', left_digits=3, right_digits=2, positive=True)
    created_by = factory.SubFactory(UserFactory)

# Usage
class ProductTest(TestCase):
    def test_with_factory(self):
        product = ProductFactory(price=100)
        self.assertEqual(product.price, 100)
```

## Testing JWT

```python
class JWTAuthTest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            username='test',
            password='testpass123'
        )

    def test_obtain_token(self):
        response = self.client.post('/api/token/', {
            'email': 'test@example.com',
            'password': 'testpass123'
        })

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_access_protected_endpoint(self):
        response = self.client.post('/api/token/', {
            'email': 'test@example.com',
            'password': 'testpass123'
        })
        token = response.data['access']

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = self.client.get('/api/protected/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
```

## Quick Reference

| Method | Purpose |
|--------|---------|
| `force_authenticate()` | Skip auth |
| `credentials()` | Set headers |
| `reverse()` | URL by name |
| `fixtures` | Load test data |

| Assertion | Check |
|-----------|-------|
| `assertEqual()` | Exact match |
| `assertContains()` | Response contains |
| `assertRaises()` | Exception raised |
