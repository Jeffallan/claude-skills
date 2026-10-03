# Checkout Customization

---

## When to Use

- Adding custom UI to checkout (banners, fields, upsells)
- Implementing custom discount logic with Shopify Functions
- Building post-purchase experiences
- Customizing shipping and payment options
- Checkout branding and localization

## When NOT to Use

- Full checkout replacement (not possible on Shopify)
- Theme-level cart customization (use Liquid)
- Pre-checkout flows (use theme or headless)
- Admin-side order processing (use Admin API)

---

## Checkout Extensibility Overview

### Extension Points

| Extension | Purpose | API Version |
|-----------|---------|-------------|
| `Checkout::Dynamic::Render` | Add UI anywhere in checkout | 2024.10+ |
| `Checkout::CartLineDetails::RenderAfter` | Below cart line items | 2024.10+ |
| `Checkout::DeliveryAddress::RenderBefore` | Before delivery address | 2024.10+ |
| `purchase.checkout.block.render` | Custom blocks in checkout | 2024.10+ |
| `purchase.thank-you.block.render` | Thank you page | 2024.10+ |
| `purchase.post-purchase.render` | Post-purchase upsell | 2024.10+ |

### Project Setup

```bash
# Create checkout extension
npm run shopify app generate extension -- --type checkout_ui

# Extension structure
extensions/
└── checkout-ui/
    ├── src/
    │   └── Checkout.tsx    # Main extension component
    ├── locales/
    │   └── en.default.json # Translations
    ├── shopify.extension.toml
    └── package.json
```

---

## Checkout UI Extensions

### Configuration

```toml
# extensions/checkout-ui/shopify.extension.toml
api_version = "2024-10"

[[extensions]]
type = "ui_extension"
name = "Custom Checkout Banner"
handle = "custom-checkout-banner"

[[extensions.targeting]]
module = "./src/Checkout.tsx"
target = "purchase.checkout.block.render"

[extensions.capabilities]
api_access = true
network_access = true
block_progress = true

[extensions.settings]
  [[extensions.settings.fields]]
  key = "banner_text"
  type = "single_line_text_field"
  name = "Banner Text"
  description = "Text to display in the banner"

  [[extensions.settings.fields]]
  key = "banner_status"
  type = "single_line_text_field"
  name = "Banner Status"
  description = "info, warning, success, or critical"
```

### Basic Extension Component

```tsx
// extensions/checkout-ui/src/Checkout.tsx
import {
  reactExtension,
  Banner,
  useSettings,
  useTranslate,
  BlockStack,
  Text,
  useExtensionCapability,
  useBuyerJourneyIntercept,
} from "@shopify/ui-extensions-react/checkout";

export default reactExtension("purchase.checkout.block.render", () => (
  <CheckoutBanner />
));

function CheckoutBanner() {
  const translate = useTranslate();
  const { banner_text, banner_status } = useSettings();

  return (
    <Banner
      status={banner_status || "info"}
      title={banner_text || translate("default_banner_title")}
    />
  );
}
```

### Cart Line Item Extension

```tsx
// extensions/cart-upsell/src/CartLineUpsell.tsx
import {
  reactExtension,
  useCartLines,
  useApplyCartLinesChange,
  Button,
  Text,
  InlineStack,
  Image,
  BlockStack,
  Divider,
} from "@shopify/ui-extensions-react/checkout";

export default reactExtension(
  "purchase.checkout.cart-line-list.render-after",
  () => <CartUpsell />
);

function CartUpsell() {
  const cartLines = useCartLines();
  const applyCartLinesChange = useApplyCartLinesChange();

  // Example: Suggest complementary product based on cart contents
  const upsellProduct = getUpsellRecommendation(cartLines);

  if (!upsellProduct) return null;

  const handleAddToCart = async () => {
    const result = await applyCartLinesChange({
      type: "addCartLine",
      merchandiseId: upsellProduct.variantId,
      quantity: 1,
    });

    if (result.type === "error") {
      console.error("Failed to add item:", result.message);
    }
  };

  return (
    <BlockStack spacing="loose">
      <Divider />
      <Text emphasis="bold">Complete your order</Text>
      <InlineStack spacing="base" blockAlignment="center">
        <Image
          source={upsellProduct.image}
          accessibilityDescription={upsellProduct.title}
          aspectRatio={1}
          cornerRadius="base"
        />
        <BlockStack spacing="none">
          <Text>{upsellProduct.title}</Text>
          <Text appearance="subdued">{upsellProduct.price}</Text>
        </BlockStack>
        <Button kind="secondary" onPress={handleAddToCart}>
          Add
        </Button>
      </InlineStack>
    </BlockStack>
  );
}

function getUpsellRecommendation(cartLines: CartLine[]) {
  // Logic to determine upsell based on cart contents
  // This would typically call your backend or use metafields
  return null; // Implement based on your business logic
}
```

### Custom Form Fields

```tsx
// extensions/custom-fields/src/CustomFields.tsx
import {
  reactExtension,
  useApplyMetafieldsChange,
  useMetafield,
  TextField,
  Checkbox,
  BlockStack,
  Text,
  useBuyerJourneyIntercept,
} from "@shopify/ui-extensions-react/checkout";
import { useState } from "react";

export default reactExtension(
  "purchase.checkout.delivery-address.render-before",
  () => <DeliveryInstructions />
);

function DeliveryInstructions() {
  const [instructions, setInstructions] = useState("");
  const [leaveAtDoor, setLeaveAtDoor] = useState(false);
  const [error, setError] = useState("");

  const applyMetafieldsChange = useApplyMetafieldsChange();

  // Block checkout if validation fails
  useBuyerJourneyIntercept(({ canBlockProgress }) => {
    if (canBlockProgress && leaveAtDoor && !instructions) {
      return {
        behavior: "block",
        reason: "Please provide delivery instructions when leaving at door",
        errors: [
          {
            message: "Delivery instructions required",
            target: "$.cart.deliveryInstructions",
          },
        ],
      };
    }
    return { behavior: "allow" };
  });

  const handleInstructionsChange = async (value: string) => {
    setInstructions(value);
    setError("");

    await applyMetafieldsChange({
      type: "updateMetafield",
      namespace: "custom",
      key: "delivery_instructions",
      valueType: "string",
      value,
    });
  };

  const handleLeaveAtDoorChange = async (checked: boolean) => {
    setLeaveAtDoor(checked);

    await applyMetafieldsChange({
      type: "updateMetafield",
      namespace: "custom",
      key: "leave_at_door",
      valueType: "boolean",
      value: String(checked),
    });
  };

  return (
    <BlockStack spacing="base">
      <Text emphasis="bold">Delivery Preferences</Text>

      <Checkbox checked={leaveAtDoor} onChange={handleLeaveAtDoorChange}>
        Leave package at door
      </Checkbox>

      <TextField
        label="Delivery Instructions"
        value={instructions}
        onChange={handleInstructionsChange}
        error={error}
        multiline={3}
        maxLength={250}
      />
    </BlockStack>
  );
}
```

---

## Shopify Functions

### Discount Function

```bash
# Generate discount function
npm run shopify app generate extension -- --type product_discounts
```

```toml
# extensions/volume-discount/shopify.extension.toml
api_version = "2024-10"

[[extensions]]
name = "Volume Discount"
handle = "volume-discount"
type = "function"
description = "Apply discounts based on quantity"

[extensions.build]
command = "cargo wasi build --release"
path = "target/wasm32-wasip1/release/volume-discount.wasm"
watch = ["src/**/*.rs", "Cargo.toml"]

[extensions.ui]
enable_create = true

[[extensions.ui.paths]]
path = "create"
module = "./src/CreateDiscount.tsx"

[[extensions.ui.paths]]
path = "details"
module = "./src/DiscountDetails.tsx"

[extensions.input.variables]
namespace = "$app:volume-discount"
key = "config"
```

```rust
// extensions/volume-discount/src/main.rs
use shopify_function::prelude::*;
use shopify_function::Result;

use serde::{Deserialize, Serialize};

#[derive(Serialize, Deserialize, Default, PartialEq)]
#[serde(rename_all = "camelCase")]
struct Config {
    tiers: Vec<Tier>,
}

#[derive(Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "camelCase")]
struct Tier {
    quantity: i64,
    percentage: f64,
}

#[shopify_function_target(query_path = "src/run.graphql", schema_path = "schema.graphql")]
fn run(input: input::ResponseData) -> Result<output::FunctionRunResult> {
    let config: Config = input
        .discount_node
        .metafield
        .as_ref()
        .map(|m| serde_json::from_str(&m.value).unwrap_or_default())
        .unwrap_or_default();

    let mut discounts = vec![];

    for line in input.cart.lines {
        if let input::InputCartLinesMerchandise::ProductVariant(variant) = &line.merchandise {
            let quantity = line.quantity;

            // Find applicable tier
            let applicable_tier = config
                .tiers
                .iter()
                .filter(|t| quantity >= t.quantity)
                .max_by_key(|t| t.quantity);

            if let Some(tier) = applicable_tier {
                discounts.push(output::Discount {
                    value: output::Value::Percentage(output::Percentage {
                        value: Decimal(tier.percentage),
                    }),
                    targets: vec![output::Target::CartLine(output::CartLineTarget {
                        id: line.id.clone(),
                        quantity: None,
                    })],
                    message: Some(format!("{}% off for buying {} or more", tier.percentage, tier.quantity)),
                });
            }
        }
    }

    Ok(output::FunctionRunResult {
        discounts,
        discount_application_strategy: output::DiscountApplicationStrategy::FIRST,
    })
}
```

```graphql
# extensions/volume-discount/src/run.graphql
query RunInput {
  cart {
    lines {
      id
      quantity
      merchandise {
        ... on ProductVariant {
          id
          product {
            id
            handle
          }
        }
      }
    }
  }
  discountNode {
    metafield(namespace: "$app:volume-discount", key: "config") {
      value
    }
  }
}
```

### Shipping Customization Function

```rust
// extensions/shipping-customization/src/main.rs
use shopify_function::prelude::*;
use shopify_function::Result;

#[shopify_function_target(query_path = "src/run.graphql", schema_path = "schema.graphql")]
fn run(input: input::ResponseData) -> Result<output::FunctionRunResult> {
    let mut operations = vec![];

    // Example: Hide express shipping for PO Box addresses
    let is_po_box = input
        .cart
        .delivery_groups
        .iter()
        .any(|group| {
            group.delivery_address.as_ref().map_or(false, |addr| {
                addr.address1.as_ref().map_or(false, |a| {
                    a.to_lowercase().contains("po box") ||
                    a.to_lowercase().contains("p.o. box")
                })
            })
        });

    if is_po_box {
        for group in &input.cart.delivery_groups {
            for option in &group.delivery_options {
                if option.title.as_ref().map_or(false, |t| t.contains("Express")) {
                    operations.push(output::Operation::Hide(output::HideOperation {
                        delivery_option_handle: option.handle.clone(),
                    }));
                }
            }
        }
    }

    // Example: Rename shipping option based on cart value
    let cart_total: f64 = input.cart.cost.subtotal_amount.amount.parse().unwrap_or(0.0);

    if cart_total >= 100.0 {
        for group in &input.cart.delivery_groups {
            for option in &group.delivery_options {
                if option.title.as_ref().map_or(false, |t| t.contains("Standard")) {
                    operations.push(output::Operation::Rename(output::RenameOperation {
                        delivery_option_handle: option.handle.clone(),
                        title: Some("Free Standard Shipping".to_string()),
                    }));
                }
            }
        }
    }

    Ok(output::FunctionRunResult { operations })
}
```

### Payment Customization Function

```rust
// extensions/payment-customization/src/main.rs
use shopify_function::prelude::*;
use shopify_function::Result;

#[shopify_function_target(query_path = "src/run.graphql", schema_path = "schema.graphql")]
fn run(input: input::ResponseData) -> Result<output::FunctionRunResult> {
    let mut operations = vec![];

    // Example: Hide Cash on Delivery for international orders
    let is_international = input
        .cart
        .delivery_groups
        .iter()
        .any(|group| {
            group.delivery_address.as_ref().map_or(false, |addr| {
                addr.country_code.as_ref().map_or(false, |c| c != "US")
            })
        });

    if is_international {
        for method in &input.payment_methods {
            if method.name.contains("Cash on Delivery") || method.name.contains("COD") {
                operations.push(output::Operation::Hide(output::HideOperation {
                    payment_method_id: method.id.clone(),
                }));
            }
        }
    }

    // Example: Reorder payment methods based on cart total
    let cart_total: f64 = input.cart.cost.subtotal_amount.amount.parse().unwrap_or(0.0);

    if cart_total >= 500.0 {
        // Move "Pay Later" options to top for high-value orders
        for method in &input.payment_methods {
            if method.name.contains("Affirm") || method.name.contains("Klarna") {
                operations.push(output::Operation::Move(output::MoveOperation {
                    payment_method_id: method.id.clone(),
                    index: 0,
                }));
            }
        }
    }

    Ok(output::FunctionRunResult { operations })
}
```

---

## Post-Purchase Extensions

### Post-Purchase Upsell

```tsx
// extensions/post-purchase/src/PostPurchase.tsx
import {
  extend,
  render,
  useExtensionInput,
  BlockStack,
  Button,
  CalloutBanner,
  Heading,
  Image,
  Text,
  TextContainer,
  Layout,
  View,
} from "@shopify/post-purchase-ui-extensions-react";

extend("Checkout::PostPurchase::ShouldRender", async ({ inputData, storage }) => {
  // Decide whether to show post-purchase page
  const { initialPurchase } = inputData;

  // Skip for orders under $50
  const orderTotal = parseFloat(initialPurchase.totalPriceSet.shopMoney.amount);
  if (orderTotal < 50) {
    return { render: false };
  }

  // Fetch upsell offer from your backend
  const response = await fetch("https://your-app.com/api/upsell", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      orderId: initialPurchase.referenceId,
      lineItems: initialPurchase.lineItems,
    }),
  });

  const { offer } = await response.json();

  if (!offer) {
    return { render: false };
  }

  // Store offer data for render phase
  await storage.update({ offer });

  return { render: true };
});

render("Checkout::PostPurchase::Render", () => <PostPurchaseOffer />);

function PostPurchaseOffer() {
  const {
    storage,
    inputData,
    calculateChangeset,
    applyChangeset,
    done,
  } = useExtensionInput();

  const [loading, setLoading] = useState(false);
  const [accepted, setAccepted] = useState(false);

  const offer = storage.initialData.offer;

  const handleAccept = async () => {
    setLoading(true);

    // Calculate price with the upsell item
    const changeset = await calculateChangeset({
      changes: [
        {
          type: "add_variant",
          variantId: offer.variantId,
          quantity: 1,
          discount: {
            value: offer.discountPercentage,
            valueType: "percentage",
            title: "Post-purchase discount",
          },
        },
      ],
    });

    // Apply the upsell to the order
    await applyChangeset(changeset.token);

    setAccepted(true);
    setLoading(false);

    // Track conversion
    await fetch("https://your-app.com/api/upsell/accepted", {
      method: "POST",
      body: JSON.stringify({ orderId: inputData.initialPurchase.referenceId }),
    });

    // Wait a moment then proceed
    setTimeout(() => done(), 2000);
  };

  const handleDecline = () => {
    done();
  };

  if (accepted) {
    return (
      <BlockStack spacing="loose" alignment="center">
        <CalloutBanner title="Added to your order!">
          <Text>{offer.title} has been added to your order.</Text>
        </CalloutBanner>
      </BlockStack>
    );
  }

  return (
    <BlockStack spacing="loose">
      <CalloutBanner title="Exclusive offer just for you!">
        <Text>Get {offer.discountPercentage}% off this item when you add it now.</Text>
      </CalloutBanner>

      <Layout
        media={[
          { viewportSize: "small", sizes: [1, 1] },
          { viewportSize: "medium", sizes: [1, 1] },
          { viewportSize: "large", sizes: [1, 1] },
        ]}
      >
        <View>
          <Image source={offer.image} />
        </View>
        <View>
          <BlockStack spacing="base">
            <Heading>{offer.title}</Heading>
            <TextContainer>
              <Text>{offer.description}</Text>
            </TextContainer>
            <Text emphasis="bold">
              <Text appearance="subdued" role="deletion">
                {offer.originalPrice}
              </Text>{" "}
              {offer.discountedPrice}
            </Text>
            <BlockStack spacing="tight">
              <Button onPress={handleAccept} loading={loading}>
                Add to order - {offer.discountedPrice}
              </Button>
              <Button plain onPress={handleDecline}>
                No thanks
              </Button>
            </BlockStack>
          </BlockStack>
        </View>
      </Layout>
    </BlockStack>
  );
}
```

---

## Checkout Branding API

### Customize Checkout Appearance

```typescript
// Using Admin API to set checkout branding
const UPDATE_CHECKOUT_BRANDING = `
  mutation checkoutBrandingUpsert($checkoutBrandingInput: CheckoutBrandingInput!, $checkoutProfileId: ID!) {
    checkoutBrandingUpsert(checkoutBrandingInput: $checkoutBrandingInput, checkoutProfileId: $checkoutProfileId) {
      checkoutBranding {
        customizations {
          headingLevel1 {
            typography {
              font
              size
              weight
            }
          }
          primaryButton {
            background
            cornerRadius
            blockPadding
          }
          control {
            cornerRadius
            border
          }
        }
        designSystem {
          colors {
            schemes {
              scheme1 {
                base {
                  background
                  text
                  accent
                }
                primaryButton {
                  background
                  text
                }
              }
            }
          }
          typography {
            primary {
              shopifyFontGroup {
                name
              }
            }
            secondary {
              shopifyFontGroup {
                name
              }
            }
          }
          cornerRadius {
            base
            small
            large
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

// Example branding configuration
const brandingInput = {
  designSystem: {
    colors: {
      schemes: {
        scheme1: {
          base: {
            background: "#FFFFFF",
            text: "#1A1A1A",
            accent: "#0066CC",
          },
          primaryButton: {
            background: "#0066CC",
            text: "#FFFFFF",
          },
          control: {
            background: "#F5F5F5",
            border: "#CCCCCC",
          },
        },
      },
    },
    typography: {
      primary: {
        shopifyFontGroup: {
          name: "Inter",
        },
      },
    },
    cornerRadius: {
      base: 8,
      small: 4,
      large: 16,
    },
  },
  customizations: {
    primaryButton: {
      cornerRadius: "LARGE",
      blockPadding: "BASE",
    },
    headingLevel1: {
      typography: {
        size: "EXTRA_LARGE",
        weight: "BOLD",
      },
    },
  },
};
```

---

## Testing Extensions

### Local Development

```bash
# Start development server with extension preview
npm run shopify app dev

# Test specific extension
npm run shopify app dev --checkout-cart-url="https://your-store.myshopify.com/cart/123:1"

# Generate preview URL
npm run shopify app dev --tunnel-url="https://your-ngrok-url.ngrok.io"
```

### Extension Testing Best Practices

1. **Use sandbox checkout profiles** - Test without affecting production
2. **Test all buyer journeys** - Guest, logged in, express checkout
3. **Test error states** - Network failures, validation errors
4. **Test internationalization** - Multiple languages and currencies
5. **Performance test** - Extension should load in <100ms

```typescript
// Test file for checkout extension
import { describe, it, expect } from "vitest";
import { render } from "@shopify/ui-extensions/test-utilities";
import { CheckoutBanner } from "./Checkout";

describe("CheckoutBanner", () => {
  it("renders with default settings", () => {
    const { root } = render(<CheckoutBanner />);

    expect(root).toContainReactComponent("Banner", {
      status: "info",
    });
  });

  it("displays custom banner text from settings", () => {
    const { root } = render(<CheckoutBanner />, {
      settings: {
        banner_text: "Free shipping on orders over $50!",
        banner_status: "success",
      },
    });

    expect(root).toContainReactComponent("Banner", {
      title: "Free shipping on orders over $50!",
      status: "success",
    });
  });
});
```

---

## Related References

- **App Development** - For backend webhook handling
- **Storefront API** - For headless checkout flows
- **Liquid Templating** - For pre-checkout cart customization
