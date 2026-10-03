# App Development

---

## When to Use

- Building custom Shopify apps for merchants
- Creating public apps for the Shopify App Store
- Integrating third-party services with Shopify
- Automating merchant workflows
- Building embedded admin experiences

## When NOT to Use

- Theme customization (use Liquid)
- Customer-facing storefronts (use Storefront API)
- Simple product displays (use Liquid or Storefront API)
- Checkout-only customizations (use Checkout Extensions)

---

## App Architecture Overview

### App Types

| Type | Use Case | Distribution |
|------|----------|--------------|
| Custom App | Single merchant, private | Manual install |
| Public App | App Store listing | Shopify review |
| Sales Channel | Custom storefront | App Store |
| Embedded App | Admin integration | Either |

### Modern Stack (2024+)

```bash
# Create new Shopify app with Remix template
npm create @shopify/app@latest

# Project structure
shopify-app/
├── app/
│   ├── routes/              # Remix routes
│   │   ├── app._index.tsx   # Main app page
│   │   ├── app.products.tsx # Products page
│   │   └── webhooks.tsx     # Webhook handlers
│   ├── shopify.server.ts    # Shopify API client
│   └── db.server.ts         # Database client
├── extensions/              # App extensions
├── prisma/                  # Database schema
├── shopify.app.toml         # App configuration
└── package.json
```

---

## App Configuration

### shopify.app.toml

```toml
# shopify.app.toml
scopes = "read_products,write_products,read_orders,write_orders,read_customers"

[access_scopes]
# Use optional scopes for granular permissions
optional = ["read_inventory", "write_inventory"]

[auth]
redirect_urls = [
  "https://your-app.com/auth/callback",
  "https://your-app.com/auth/shopify/callback"
]

[webhooks]
api_version = "2024-10"

  [[webhooks.subscriptions]]
  topics = ["products/create", "products/update", "products/delete"]
  uri = "/webhooks"

  [[webhooks.subscriptions]]
  topics = ["orders/create"]
  uri = "/webhooks"

  [[webhooks.subscriptions]]
  topics = ["app/uninstalled"]
  uri = "/webhooks"

[app_proxy]
url = "https://your-app.com/api/proxy"
subpath = "apps"
prefix = "your-app"

[pos]
embedded = false

[build]
automatically_update_urls_on_dev = true
dev_store_url = "your-dev-store.myshopify.com"

[app]
name = "Your App Name"
handle = "your-app-handle"
```

---

## OAuth Implementation

### Authentication Flow

```typescript
// app/shopify.server.ts
import "@shopify/shopify-app-remix/adapters/node";
import {
  ApiVersion,
  AppDistribution,
  shopifyApp,
  DeliveryMethod,
} from "@shopify/shopify-app-remix/server";
import { PrismaSessionStorage } from "@shopify/shopify-app-session-storage-prisma";
import prisma from "./db.server";

const shopify = shopifyApp({
  apiKey: process.env.SHOPIFY_API_KEY!,
  apiSecretKey: process.env.SHOPIFY_API_SECRET!,
  appUrl: process.env.SHOPIFY_APP_URL!,
  scopes: process.env.SCOPES?.split(","),
  apiVersion: ApiVersion.October24,
  distribution: AppDistribution.AppStore,
  sessionStorage: new PrismaSessionStorage(prisma),
  webhooks: {
    APP_UNINSTALLED: {
      deliveryMethod: DeliveryMethod.Http,
      callbackUrl: "/webhooks",
    },
    PRODUCTS_CREATE: {
      deliveryMethod: DeliveryMethod.Http,
      callbackUrl: "/webhooks",
    },
    ORDERS_CREATE: {
      deliveryMethod: DeliveryMethod.Http,
      callbackUrl: "/webhooks",
    },
  },
  hooks: {
    afterAuth: async ({ session, admin }) => {
      // Register webhooks after OAuth
      shopify.registerWebhooks({ session });

      // Perform post-install setup
      await setupShop(session, admin);
    },
  },
});

async function setupShop(session: Session, admin: AdminApiContext) {
  // Store merchant data
  await prisma.shop.upsert({
    where: { shopDomain: session.shop },
    update: { accessToken: session.accessToken },
    create: {
      shopDomain: session.shop,
      accessToken: session.accessToken!,
      installedAt: new Date(),
    },
  });
}

export default shopify;
export const apiVersion = ApiVersion.October24;
export const addDocumentResponseHeaders = shopify.addDocumentResponseHeaders;
export const authenticate = shopify.authenticate;
export const unauthenticated = shopify.unauthenticated;
export const login = shopify.login;
export const registerWebhooks = shopify.registerWebhooks;
export const sessionStorage = shopify.sessionStorage;
```

### Protected Routes

```typescript
// app/routes/app._index.tsx
import { json, type LoaderFunctionArgs } from "@remix-run/node";
import { useLoaderData } from "@remix-run/react";
import { Page, Layout, Card, DataTable } from "@shopify/polaris";
import { authenticate } from "../shopify.server";

export async function loader({ request }: LoaderFunctionArgs) {
  const { admin, session } = await authenticate.admin(request);

  // Make Admin API requests
  const response = await admin.graphql(`
    query {
      shop {
        name
        email
        myshopifyDomain
        plan {
          displayName
        }
      }
      products(first: 10) {
        edges {
          node {
            id
            title
            status
            totalInventory
          }
        }
      }
    }
  `);

  const data = await response.json();

  return json({
    shop: data.data.shop,
    products: data.data.products.edges.map((edge: any) => edge.node),
  });
}

export default function Index() {
  const { shop, products } = useLoaderData<typeof loader>();

  const rows = products.map((product: any) => [
    product.title,
    product.status,
    product.totalInventory,
  ]);

  return (
    <Page title={`Welcome to ${shop.name}`}>
      <Layout>
        <Layout.Section>
          <Card>
            <DataTable
              columnContentTypes={["text", "text", "numeric"]}
              headings={["Product", "Status", "Inventory"]}
              rows={rows}
            />
          </Card>
        </Layout.Section>
      </Layout>
    </Page>
  );
}
```

---

## Admin API (GraphQL)

### Products CRUD

```typescript
// Create product
const CREATE_PRODUCT = `
  mutation productCreate($input: ProductInput!) {
    productCreate(input: $input) {
      product {
        id
        title
        handle
        variants(first: 10) {
          edges {
            node {
              id
              price
              sku
            }
          }
        }
      }
      userErrors {
        field
        message
      }
    }
  }
`;

// Usage
const response = await admin.graphql(CREATE_PRODUCT, {
  variables: {
    input: {
      title: "New Product",
      descriptionHtml: "<p>Product description</p>",
      vendor: "Your Brand",
      productType: "T-Shirt",
      tags: ["new", "featured"],
      variants: [
        {
          price: "29.99",
          sku: "SKU-001",
          inventoryManagement: "SHOPIFY",
          inventoryPolicy: "DENY",
          options: ["Small", "Blue"],
        },
        {
          price: "29.99",
          sku: "SKU-002",
          options: ["Medium", "Blue"],
        },
      ],
      options: ["Size", "Color"],
    },
  },
});

// Update product
const UPDATE_PRODUCT = `
  mutation productUpdate($input: ProductInput!) {
    productUpdate(input: $input) {
      product {
        id
        title
      }
      userErrors {
        field
        message
      }
    }
  }
`;

// Bulk operations for large datasets
const BULK_MUTATION = `
  mutation bulkOperationRunMutation($mutation: String!, $stagedUploadPath: String!) {
    bulkOperationRunMutation(mutation: $mutation, stagedUploadPath: $stagedUploadPath) {
      bulkOperation {
        id
        status
      }
      userErrors {
        field
        message
      }
    }
  }
`;
```

### Orders Management

```typescript
// Fetch orders with fulfillment status
const GET_ORDERS = `
  query getOrders($first: Int!, $query: String) {
    orders(first: $first, query: $query, sortKey: CREATED_AT, reverse: true) {
      edges {
        node {
          id
          name
          createdAt
          displayFinancialStatus
          displayFulfillmentStatus
          totalPriceSet {
            shopMoney {
              amount
              currencyCode
            }
          }
          customer {
            firstName
            lastName
            email
          }
          lineItems(first: 5) {
            edges {
              node {
                title
                quantity
                variant {
                  id
                  sku
                }
              }
            }
          }
          shippingAddress {
            address1
            city
            province
            country
            zip
          }
        }
      }
      pageInfo {
        hasNextPage
        endCursor
      }
    }
  }
`;

// Create fulfillment
const CREATE_FULFILLMENT = `
  mutation fulfillmentCreate($fulfillment: FulfillmentInput!) {
    fulfillmentCreate(fulfillment: $fulfillment) {
      fulfillment {
        id
        status
        trackingInfo {
          number
          url
        }
      }
      userErrors {
        field
        message
      }
    }
  }
`;
```

### Metafields

```typescript
// Set product metafields
const SET_METAFIELDS = `
  mutation metafieldsSet($metafields: [MetafieldsSetInput!]!) {
    metafieldsSet(metafields: $metafields) {
      metafields {
        id
        namespace
        key
        value
        type
      }
      userErrors {
        field
        message
      }
    }
  }
`;

// Usage
await admin.graphql(SET_METAFIELDS, {
  variables: {
    metafields: [
      {
        ownerId: "gid://shopify/Product/123456789",
        namespace: "custom",
        key: "care_instructions",
        value: "Machine wash cold",
        type: "single_line_text_field",
      },
      {
        ownerId: "gid://shopify/Product/123456789",
        namespace: "custom",
        key: "features",
        value: JSON.stringify(["Organic cotton", "Fair trade", "Eco-friendly"]),
        type: "list.single_line_text_field",
      },
    ],
  },
});

// Read metafields
const GET_PRODUCT_METAFIELDS = `
  query getProductMetafields($id: ID!) {
    product(id: $id) {
      metafields(first: 20) {
        edges {
          node {
            id
            namespace
            key
            value
            type
          }
        }
      }
    }
  }
`;
```

---

## Webhook Handling

### Webhook Route

```typescript
// app/routes/webhooks.tsx
import type { ActionFunctionArgs } from "@remix-run/node";
import { authenticate } from "../shopify.server";
import db from "../db.server";

export async function action({ request }: ActionFunctionArgs) {
  const { topic, shop, session, admin, payload } =
    await authenticate.webhook(request);

  console.log(`Received ${topic} webhook for ${shop}`);

  switch (topic) {
    case "APP_UNINSTALLED":
      await handleAppUninstalled(shop);
      break;

    case "PRODUCTS_CREATE":
      await handleProductCreate(shop, payload);
      break;

    case "PRODUCTS_UPDATE":
      await handleProductUpdate(shop, payload);
      break;

    case "ORDERS_CREATE":
      await handleOrderCreate(shop, payload, admin);
      break;

    case "CUSTOMERS_DATA_REQUEST":
      await handleDataRequest(shop, payload);
      break;

    case "CUSTOMERS_REDACT":
      await handleCustomerRedact(shop, payload);
      break;

    case "SHOP_REDACT":
      await handleShopRedact(shop, payload);
      break;

    default:
      console.log(`Unhandled webhook topic: ${topic}`);
  }

  return new Response("OK", { status: 200 });
}

async function handleAppUninstalled(shop: string) {
  // Clean up shop data
  await db.shop.delete({
    where: { shopDomain: shop },
  });
}

async function handleProductCreate(shop: string, payload: any) {
  // Sync product to your database
  await db.product.create({
    data: {
      shopDomain: shop,
      shopifyId: payload.admin_graphql_api_id,
      title: payload.title,
      handle: payload.handle,
      status: payload.status,
    },
  });
}

async function handleOrderCreate(shop: string, payload: any, admin: any) {
  // Process new order
  const order = {
    id: payload.admin_graphql_api_id,
    orderNumber: payload.order_number,
    totalPrice: payload.total_price,
    customer: payload.customer,
    lineItems: payload.line_items,
  };

  // Example: Add order note
  await admin.graphql(`
    mutation addOrderNote($id: ID!, $note: String!) {
      orderUpdate(input: { id: $id, note: $note }) {
        order { id }
        userErrors { field message }
      }
    }
  `, {
    variables: {
      id: order.id,
      note: "Processed by Your App",
    },
  });
}

// GDPR webhooks (required for public apps)
async function handleDataRequest(shop: string, payload: any) {
  // Return customer data
  const customerId = payload.customer.id;
  // Gather and return all customer data
}

async function handleCustomerRedact(shop: string, payload: any) {
  // Delete customer data
  const customerId = payload.customer.id;
  await db.customerData.deleteMany({
    where: { shopDomain: shop, customerId: String(customerId) },
  });
}

async function handleShopRedact(shop: string, payload: any) {
  // Delete all shop data (48 hours after uninstall)
  await db.shop.delete({ where: { shopDomain: shop } });
}
```

---

## App Bridge 4.0

### Setup

```typescript
// app/root.tsx
import { AppProvider } from "@shopify/shopify-app-remix/react";
import polarisStyles from "@shopify/polaris/build/esm/styles.css?url";

export const links = () => [{ rel: "stylesheet", href: polarisStyles }];

export default function App() {
  const { apiKey } = useLoaderData<typeof loader>();

  return (
    <html>
      <head>
        <Meta />
        <Links />
      </head>
      <body>
        <AppProvider isEmbeddedApp apiKey={apiKey}>
          <Outlet />
        </AppProvider>
        <Scripts />
      </body>
    </html>
  );
}
```

### App Bridge Actions

```typescript
// Using App Bridge in components
import { useAppBridge } from "@shopify/app-bridge-react";
import { Redirect } from "@shopify/app-bridge/actions";

function MyComponent() {
  const app = useAppBridge();

  const redirectToProduct = (productId: string) => {
    const redirect = Redirect.create(app);
    redirect.dispatch(Redirect.Action.ADMIN_PATH, {
      path: `/products/${productId}`,
    });
  };

  const openResourcePicker = async () => {
    const selection = await app.resourcePicker({
      type: "product",
      multiple: true,
      filter: {
        variants: false,
        archived: false,
      },
    });

    if (selection) {
      console.log("Selected products:", selection);
    }
  };

  return (
    <Button onClick={openResourcePicker}>Select Products</Button>
  );
}
```

### Toast Notifications

```typescript
import { useAppBridge } from "@shopify/app-bridge-react";
import { Toast } from "@shopify/app-bridge/actions";

function SaveButton() {
  const app = useAppBridge();

  const handleSave = async () => {
    try {
      await saveData();
      const toast = Toast.create(app, {
        message: "Settings saved successfully",
        duration: 3000,
      });
      toast.dispatch(Toast.Action.SHOW);
    } catch (error) {
      const toast = Toast.create(app, {
        message: "Error saving settings",
        duration: 5000,
        isError: true,
      });
      toast.dispatch(Toast.Action.SHOW);
    }
  };

  return <Button primary onClick={handleSave}>Save</Button>;
}
```

---

## Polaris Design System

### Common Patterns

```typescript
import {
  Page,
  Layout,
  Card,
  FormLayout,
  TextField,
  Select,
  Button,
  Banner,
  Modal,
  ResourceList,
  ResourceItem,
  Avatar,
  TextStyle,
  Stack,
  Badge,
  Pagination,
} from "@shopify/polaris";

function SettingsPage() {
  const [formState, setFormState] = useState({
    apiKey: "",
    environment: "production",
  });
  const [loading, setLoading] = useState(false);
  const [showModal, setShowModal] = useState(false);

  return (
    <Page
      title="App Settings"
      primaryAction={{
        content: "Save",
        loading: loading,
        onAction: handleSave,
      }}
      secondaryActions={[
        { content: "Reset", onAction: handleReset },
      ]}
    >
      <Layout>
        <Layout.Section>
          <Banner
            title="Configuration required"
            status="warning"
            action={{ content: "Learn more", url: "/docs" }}
          >
            Please configure your API settings to enable all features.
          </Banner>
        </Layout.Section>

        <Layout.AnnotatedSection
          title="API Configuration"
          description="Configure your external API connection."
        >
          <Card>
            <Card.Section>
              <FormLayout>
                <TextField
                  label="API Key"
                  value={formState.apiKey}
                  onChange={(value) => setFormState({ ...formState, apiKey: value })}
                  type="password"
                  autoComplete="off"
                />
                <Select
                  label="Environment"
                  options={[
                    { label: "Production", value: "production" },
                    { label: "Sandbox", value: "sandbox" },
                  ]}
                  value={formState.environment}
                  onChange={(value) => setFormState({ ...formState, environment: value })}
                />
              </FormLayout>
            </Card.Section>
          </Card>
        </Layout.AnnotatedSection>

        <Layout.Section>
          <Card title="Connected Products">
            <ResourceList
              items={products}
              renderItem={(item) => (
                <ResourceItem
                  id={item.id}
                  media={<Avatar customer size="medium" source={item.image} />}
                  accessibilityLabel={`View details for ${item.title}`}
                >
                  <Stack>
                    <Stack.Item fill>
                      <TextStyle variation="strong">{item.title}</TextStyle>
                    </Stack.Item>
                    <Badge status={item.synced ? "success" : "warning"}>
                      {item.synced ? "Synced" : "Pending"}
                    </Badge>
                  </Stack>
                </ResourceItem>
              )}
            />
          </Card>
        </Layout.Section>
      </Layout>

      <Modal
        open={showModal}
        onClose={() => setShowModal(false)}
        title="Confirm action"
        primaryAction={{
          content: "Confirm",
          destructive: true,
          onAction: handleConfirm,
        }}
        secondaryActions={[
          { content: "Cancel", onAction: () => setShowModal(false) },
        ]}
      >
        <Modal.Section>
          Are you sure you want to proceed?
        </Modal.Section>
      </Modal>
    </Page>
  );
}
```

---

## Testing

### Unit Tests

```typescript
// tests/webhooks.test.ts
import { describe, it, expect, vi } from "vitest";
import { action } from "../app/routes/webhooks";

describe("Webhook handlers", () => {
  it("handles product create webhook", async () => {
    const mockRequest = new Request("https://app.com/webhooks", {
      method: "POST",
      headers: {
        "X-Shopify-Topic": "products/create",
        "X-Shopify-Shop-Domain": "test-shop.myshopify.com",
        "X-Shopify-Hmac-Sha256": "valid-hmac",
      },
      body: JSON.stringify({
        id: 123456789,
        title: "Test Product",
        handle: "test-product",
      }),
    });

    const response = await action({ request: mockRequest, params: {}, context: {} });
    expect(response.status).toBe(200);
  });
});
```

### Development

```bash
# Start development server with hot reload
npm run dev

# Generate GraphQL types
npm run shopify app generate types

# Test webhooks locally
npm run shopify app webhook trigger --topic PRODUCTS_CREATE

# Deploy to Shopify
npm run deploy
```

---

## Related References

- **Storefront API** - For customer-facing features
- **Checkout Customization** - For checkout extensions
- **Liquid Templating** - For theme app extensions
