# Storefront API

---

## When to Use

- Building headless storefronts with React, Next.js, or Hydrogen
- Creating custom checkout experiences
- Building mobile apps that connect to Shopify
- Implementing real-time inventory or pricing
- Creating PWAs with Shopify backend

## When NOT to Use

- Standard theme customization (use Liquid)
- Admin operations (use Admin API)
- Backend webhook processing (use Admin API)
- Simple product displays (Liquid is faster)

---

## API Fundamentals

### Authentication

```typescript
// Storefront API uses public access tokens (safe for client-side)
const STOREFRONT_ACCESS_TOKEN = 'your-storefront-access-token';
const SHOP_DOMAIN = 'your-store.myshopify.com';
const API_VERSION = '2024-10'; // Use latest stable version

// GraphQL endpoint
const endpoint = `https://${SHOP_DOMAIN}/api/${API_VERSION}/graphql.json`;

// Basic fetch wrapper
async function storefrontFetch<T>(query: string, variables?: Record<string, unknown>): Promise<T> {
  const response = await fetch(endpoint, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Shopify-Storefront-Access-Token': STOREFRONT_ACCESS_TOKEN,
    },
    body: JSON.stringify({ query, variables }),
  });

  const json = await response.json();

  if (json.errors) {
    throw new Error(json.errors.map((e: { message: string }) => e.message).join(', '));
  }

  return json.data;
}
```

### Rate Limits

- **Buyer-facing**: 2000 cost points per second (shared across all clients)
- **Each query has a cost**: Simple queries ~1-10 points, complex ~50-100+
- **Check cost in response**:

```typescript
// Include cost in query
const query = `
  query Products @inContext(country: US, language: EN) {
    products(first: 10) {
      edges { node { id title } }
    }
  }
`;

// Response includes:
// "extensions": {
//   "cost": {
//     "requestedQueryCost": 12,
//     "actualQueryCost": 12,
//     "throttleStatus": {
//       "maximumAvailable": 2000,
//       "currentlyAvailable": 1988,
//       "restoreRate": 100
//     }
//   }
// }
```

---

## Hydrogen 2024 (Remix-based)

### Project Setup

```bash
# Create new Hydrogen project
npm create @shopify/hydrogen@latest -- --template demo-store

# Project structure
hydrogen-storefront/
├── app/
│   ├── components/      # React components
│   ├── lib/             # Utilities, fragments
│   ├── routes/          # Remix routes
│   └── styles/          # CSS
├── public/              # Static assets
├── server.ts            # Entry point
└── hydrogen.config.ts   # Hydrogen config
```

### Hydrogen Configuration

```typescript
// hydrogen.config.ts
import {defineConfig} from '@shopify/hydrogen/config';

export default defineConfig({
  shopify: {
    storeDomain: 'your-store.myshopify.com',
    storefrontToken: process.env.PUBLIC_STOREFRONT_API_TOKEN!,
    storefrontApiVersion: '2024-10',
  },
  session: {
    storage: 'cookie', // or 'memory' for development
  },
});
```

### Route with Data Loading

```typescript
// app/routes/products.$handle.tsx
import {useLoaderData, type MetaFunction} from '@remix-run/react';
import {json, type LoaderFunctionArgs} from '@shopify/remix-oxygen';
import {
  Image,
  Money,
  VariantSelector,
  getSelectedProductOptions,
} from '@shopify/hydrogen';
import type {ProductQuery} from 'storefrontapi.generated';

export const meta: MetaFunction<typeof loader> = ({data}) => {
  return [{title: data?.product?.title ?? 'Product'}];
};

export async function loader({params, request, context}: LoaderFunctionArgs) {
  const {handle} = params;
  const {storefront} = context;

  const selectedOptions = getSelectedProductOptions(request);

  const {product} = await storefront.query<ProductQuery>(PRODUCT_QUERY, {
    variables: {
      handle,
      selectedOptions,
      country: context.storefront.i18n.country,
      language: context.storefront.i18n.language,
    },
  });

  if (!product?.id) {
    throw new Response('Product not found', {status: 404});
  }

  return json({product});
}

export default function Product() {
  const {product} = useLoaderData<typeof loader>();
  const {title, descriptionHtml, featuredImage, variants} = product;

  return (
    <div className="product-page">
      <div className="product-image">
        {featuredImage && (
          <Image
            data={featuredImage}
            sizes="(min-width: 768px) 50vw, 100vw"
            aspectRatio="1/1"
          />
        )}
      </div>

      <div className="product-info">
        <h1>{title}</h1>

        <VariantSelector
          handle={product.handle}
          options={product.options}
          variants={variants}
        >
          {({option}) => (
            <div key={option.name} className="option-group">
              <h3>{option.name}</h3>
              <div className="option-values">
                {option.values.map(({value, isAvailable, to}) => (
                  <a
                    key={value}
                    href={to}
                    className={`option-value ${!isAvailable ? 'unavailable' : ''}`}
                  >
                    {value}
                  </a>
                ))}
              </div>
            </div>
          )}
        </VariantSelector>

        <ProductPrice selectedVariant={product.selectedVariant} />

        <AddToCartButton
          lines={[
            {
              merchandiseId: product.selectedVariant?.id,
              quantity: 1,
            },
          ]}
          disabled={!product.selectedVariant?.availableForSale}
        />

        <div
          className="product-description"
          dangerouslySetInnerHTML={{__html: descriptionHtml}}
        />
      </div>
    </div>
  );
}

const PRODUCT_QUERY = `#graphql
  query Product(
    $handle: String!
    $selectedOptions: [SelectedOptionInput!]!
    $country: CountryCode
    $language: LanguageCode
  ) @inContext(country: $country, language: $language) {
    product(handle: $handle) {
      id
      title
      handle
      descriptionHtml
      featuredImage {
        url
        altText
        width
        height
      }
      options {
        name
        values
      }
      selectedVariant: variantBySelectedOptions(selectedOptions: $selectedOptions) {
        id
        availableForSale
        price {
          amount
          currencyCode
        }
        compareAtPrice {
          amount
          currencyCode
        }
        selectedOptions {
          name
          value
        }
      }
      variants(first: 100) {
        nodes {
          id
          availableForSale
          selectedOptions {
            name
            value
          }
        }
      }
    }
  }
`;
```

---

## Core GraphQL Patterns

### Products Query with Pagination

```graphql
query Products(
  $first: Int!
  $after: String
  $query: String
  $sortKey: ProductSortKeys
  $reverse: Boolean
  $country: CountryCode
  $language: LanguageCode
) @inContext(country: $country, language: $language) {
  products(
    first: $first
    after: $after
    query: $query
    sortKey: $sortKey
    reverse: $reverse
  ) {
    pageInfo {
      hasNextPage
      endCursor
    }
    edges {
      node {
        id
        handle
        title
        description
        priceRange {
          minVariantPrice {
            amount
            currencyCode
          }
          maxVariantPrice {
            amount
            currencyCode
          }
        }
        featuredImage {
          url(transform: { maxWidth: 400, maxHeight: 400 })
          altText
        }
        variants(first: 1) {
          nodes {
            id
            availableForSale
          }
        }
      }
    }
  }
}
```

### Collection with Filters

```graphql
query Collection(
  $handle: String!
  $first: Int!
  $after: String
  $filters: [ProductFilter!]
  $sortKey: ProductCollectionSortKeys
  $reverse: Boolean
  $country: CountryCode
  $language: LanguageCode
) @inContext(country: $country, language: $language) {
  collection(handle: $handle) {
    id
    title
    description
    image {
      url
      altText
    }
    products(
      first: $first
      after: $after
      filters: $filters
      sortKey: $sortKey
      reverse: $reverse
    ) {
      filters {
        id
        label
        type
        values {
          id
          label
          count
          input
        }
      }
      pageInfo {
        hasNextPage
        endCursor
      }
      nodes {
        ...ProductCard
      }
    }
  }
}

fragment ProductCard on Product {
  id
  handle
  title
  featuredImage {
    url(transform: { maxWidth: 300 })
    altText
  }
  priceRange {
    minVariantPrice {
      amount
      currencyCode
    }
  }
  variants(first: 1) {
    nodes {
      availableForSale
    }
  }
}
```

### Cart Operations

```typescript
// Create cart
const CREATE_CART = `#graphql
  mutation CartCreate($input: CartInput!, $country: CountryCode, $language: LanguageCode)
  @inContext(country: $country, language: $language) {
    cartCreate(input: $input) {
      cart {
        ...CartFragment
      }
      userErrors {
        field
        message
      }
    }
  }
`;

// Add to cart
const ADD_TO_CART = `#graphql
  mutation CartLinesAdd($cartId: ID!, $lines: [CartLineInput!]!, $country: CountryCode, $language: LanguageCode)
  @inContext(country: $country, language: $language) {
    cartLinesAdd(cartId: $cartId, lines: $lines) {
      cart {
        ...CartFragment
      }
      userErrors {
        field
        message
      }
    }
  }
`;

// Update cart line
const UPDATE_CART_LINES = `#graphql
  mutation CartLinesUpdate($cartId: ID!, $lines: [CartLineUpdateInput!]!, $country: CountryCode, $language: LanguageCode)
  @inContext(country: $country, language: $language) {
    cartLinesUpdate(cartId: $cartId, lines: $lines) {
      cart {
        ...CartFragment
      }
      userErrors {
        field
        message
      }
    }
  }
`;

// Remove from cart
const REMOVE_FROM_CART = `#graphql
  mutation CartLinesRemove($cartId: ID!, $lineIds: [ID!]!, $country: CountryCode, $language: LanguageCode)
  @inContext(country: $country, language: $language) {
    cartLinesRemove(cartId: $cartId, lineIds: $lineIds) {
      cart {
        ...CartFragment
      }
      userErrors {
        field
        message
      }
    }
  }
`;

// Cart fragment for consistent data
const CART_FRAGMENT = `#graphql
  fragment CartFragment on Cart {
    id
    checkoutUrl
    totalQuantity
    cost {
      subtotalAmount {
        amount
        currencyCode
      }
      totalAmount {
        amount
        currencyCode
      }
      totalTaxAmount {
        amount
        currencyCode
      }
    }
    lines(first: 100) {
      nodes {
        id
        quantity
        cost {
          totalAmount {
            amount
            currencyCode
          }
        }
        merchandise {
          ... on ProductVariant {
            id
            title
            image {
              url(transform: { maxWidth: 100 })
              altText
            }
            product {
              title
              handle
            }
            price {
              amount
              currencyCode
            }
          }
        }
        attributes {
          key
          value
        }
      }
    }
    discountCodes {
      code
      applicable
    }
  }
`;
```

---

## Customer Authentication

### Customer Account API (2024+)

```typescript
// New Customer Account API for headless auth
const CUSTOMER_LOGIN = `#graphql
  mutation CustomerAccessTokenCreate($input: CustomerAccessTokenCreateInput!) {
    customerAccessTokenCreate(input: $input) {
      customerAccessToken {
        accessToken
        expiresAt
      }
      customerUserErrors {
        code
        field
        message
      }
    }
  }
`;

// Get customer with token
const GET_CUSTOMER = `#graphql
  query Customer($customerAccessToken: String!) {
    customer(customerAccessToken: $customerAccessToken) {
      id
      firstName
      lastName
      email
      phone
      acceptsMarketing
      defaultAddress {
        ...AddressFragment
      }
      addresses(first: 10) {
        nodes {
          ...AddressFragment
        }
      }
      orders(first: 10, sortKey: PROCESSED_AT, reverse: true) {
        nodes {
          id
          orderNumber
          processedAt
          financialStatus
          fulfillmentStatus
          totalPrice {
            amount
            currencyCode
          }
          lineItems(first: 5) {
            nodes {
              title
              quantity
              variant {
                image {
                  url(transform: { maxWidth: 100 })
                }
              }
            }
          }
        }
      }
    }
  }

  fragment AddressFragment on MailingAddress {
    id
    address1
    address2
    city
    province
    country
    zip
    phone
  }
`;

// Customer registration
const CUSTOMER_CREATE = `#graphql
  mutation CustomerCreate($input: CustomerCreateInput!) {
    customerCreate(input: $input) {
      customer {
        id
        email
        firstName
        lastName
      }
      customerUserErrors {
        code
        field
        message
      }
    }
  }
`;
```

---

## Internationalization

### Market-Aware Queries

```typescript
// Always use @inContext directive for localization
const LOCALIZED_PRODUCTS = `#graphql
  query Products($country: CountryCode!, $language: LanguageCode!)
  @inContext(country: $country, language: $language) {
    products(first: 10) {
      nodes {
        title  # Returns translated title
        priceRange {
          minVariantPrice {
            amount      # Returns price in local currency
            currencyCode
          }
        }
      }
    }
  }
`;

// Get available markets
const GET_LOCALIZATION = `#graphql
  query Localization {
    localization {
      availableCountries {
        isoCode
        name
        currency {
          isoCode
          name
          symbol
        }
        availableLanguages {
          isoCode
          name
        }
      }
      country {
        isoCode
        name
        currency {
          isoCode
          symbol
        }
      }
      language {
        isoCode
        name
      }
    }
  }
`;
```

### Hydrogen Localization

```typescript
// app/routes/($locale).products._index.tsx
import {type LoaderFunctionArgs} from '@shopify/remix-oxygen';

export async function loader({params, context}: LoaderFunctionArgs) {
  const {locale} = params;
  const {storefront} = context;

  // Storefront client automatically handles locale from route
  const {products} = await storefront.query(PRODUCTS_QUERY, {
    variables: {
      country: storefront.i18n.country,
      language: storefront.i18n.language,
    },
  });

  return json({products});
}

// server.ts - Configure i18n
const i18n = {
  default: {language: 'EN', country: 'US'},
  subfolders: [
    {language: 'FR', country: 'FR', pathPrefix: '/fr-fr'},
    {language: 'DE', country: 'DE', pathPrefix: '/de-de'},
    {language: 'EN', country: 'GB', pathPrefix: '/en-gb'},
  ],
};
```

---

## Search and Predictive Search

```graphql
# Full search
query Search($query: String!, $first: Int!, $types: [SearchType!]) {
  search(query: $query, first: $first, types: $types) {
    totalCount
    nodes {
      ... on Product {
        __typename
        id
        handle
        title
        featuredImage {
          url(transform: { maxWidth: 200 })
        }
        priceRange {
          minVariantPrice {
            amount
            currencyCode
          }
        }
      }
      ... on Article {
        __typename
        id
        handle
        title
        blog {
          handle
        }
      }
      ... on Page {
        __typename
        id
        handle
        title
      }
    }
  }
}

# Predictive search (faster, for autocomplete)
query PredictiveSearch($query: String!, $limit: Int!) {
  predictiveSearch(query: $query, limit: $limit, limitScope: EACH) {
    products {
      id
      handle
      title
      featuredImage {
        url(transform: { maxWidth: 100 })
      }
      priceRange {
        minVariantPrice {
          amount
          currencyCode
        }
      }
    }
    collections {
      id
      handle
      title
    }
    queries {
      text
      styledText
    }
  }
}
```

---

## Performance Optimization

### Query Best Practices

```typescript
// BAD: Over-fetching
const BAD_QUERY = `#graphql
  query Product($handle: String!) {
    product(handle: $handle) {
      id
      title
      description
      descriptionHtml
      vendor
      productType
      tags
      # Fetching ALL variants when you only need first
      variants(first: 250) {
        nodes {
          id
          title
          price { amount currencyCode }
          compareAtPrice { amount currencyCode }
          image { url altText width height }
          selectedOptions { name value }
          sku
          barcode
          weight
          weightUnit
        }
      }
      # Fetching ALL images
      images(first: 250) {
        nodes {
          url
          altText
          width
          height
        }
      }
    }
  }
`;

// GOOD: Fetch only what you need
const GOOD_QUERY = `#graphql
  query Product($handle: String!) {
    product(handle: $handle) {
      id
      title
      descriptionHtml
      featuredImage {
        url(transform: { maxWidth: 800 })
        altText
      }
      # Only fetch what's visible
      variants(first: 10) {
        nodes {
          id
          availableForSale
          price { amount currencyCode }
          selectedOptions { name value }
        }
      }
    }
  }
`;

// Use fragments for reusability and consistency
const PRODUCT_CARD_FRAGMENT = `#graphql
  fragment ProductCard on Product {
    id
    handle
    title
    featuredImage {
      url(transform: { maxWidth: 300, maxHeight: 300 })
      altText
    }
    priceRange {
      minVariantPrice {
        amount
        currencyCode
      }
    }
    variants(first: 1) {
      nodes {
        availableForSale
      }
    }
  }
`;
```

### Caching Strategies

```typescript
// Hydrogen caching
export async function loader({context}: LoaderFunctionArgs) {
  const {storefront} = context;

  // Short cache for frequently changing data
  const {products} = await storefront.query(PRODUCTS_QUERY, {
    cache: storefront.CacheShort(), // ~1 minute
  });

  // Long cache for static content
  const {menu} = await storefront.query(MENU_QUERY, {
    cache: storefront.CacheLong(), // ~1 hour
  });

  // No cache for user-specific data
  const {customer} = await storefront.query(CUSTOMER_QUERY, {
    cache: storefront.CacheNone(),
  });

  return json({products, menu, customer});
}
```

---

## Related References

- **Liquid Templating** - For theme-based implementations
- **App Development** - For Admin API and backend integration
- **Checkout Customization** - For checkout extensions with Storefront API
- **Performance Optimization** - Detailed performance patterns
