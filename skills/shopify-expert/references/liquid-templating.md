# Liquid Templating

> Reference for: Shopify Expert
> Load when: Theme development, template customization, section schemas, Liquid syntax

---

## When to Use

- Building or customizing Shopify Online Store 2.0 themes
- Creating custom sections and blocks with JSON schemas
- Implementing product, collection, and page templates
- Working with metafields and metaobjects in templates
- Building dynamic content with Liquid logic

## When NOT to Use

- Headless commerce (use Storefront API instead)
- App development (use Remix/React with Admin API)
- Complex business logic (use Shopify Functions)

---

## Theme Architecture (Online Store 2.0)

### Directory Structure

```
theme/
├── assets/               # CSS, JS, images
├── config/
│   ├── settings_schema.json  # Theme settings
│   └── settings_data.json    # Setting values
├── layout/
│   ├── theme.liquid      # Main layout
│   └── password.liquid   # Password page layout
├── locales/              # Translation files
├── sections/             # Reusable sections
├── snippets/             # Reusable partials
├── templates/
│   ├── customers/        # Account templates
│   ├── index.json        # Homepage
│   ├── product.json      # Product pages
│   ├── collection.json   # Collection pages
│   └── page.json         # Custom pages
└── blocks/               # App blocks (optional)
```

### JSON Templates (Online Store 2.0)

```json
// templates/product.json
{
  "sections": {
    "main": {
      "type": "main-product",
      "settings": {
        "enable_sticky_info": true,
        "media_size": "large"
      },
      "blocks": {
        "title": { "type": "title" },
        "price": { "type": "price" },
        "variant_picker": { "type": "variant_picker" },
        "buy_buttons": { "type": "buy_buttons" }
      },
      "block_order": ["title", "price", "variant_picker", "buy_buttons"]
    },
    "recommendations": {
      "type": "product-recommendations",
      "settings": {
        "heading": "You may also like",
        "products_to_show": 4
      }
    }
  },
  "order": ["main", "recommendations"]
}
```

---

## Section Schema Patterns

### Complete Section with Blocks

```liquid
{% comment %}
  sections/featured-collection.liquid
{% endcomment %}

<section class="featured-collection section-{{ section.id }}">
  <div class="container">
    {% if section.settings.heading != blank %}
      <h2 class="section-heading">{{ section.settings.heading }}</h2>
    {% endif %}

    <div class="product-grid columns-{{ section.settings.columns }}">
      {% for product in section.settings.collection.products limit: section.settings.products_to_show %}
        {% render 'product-card', product: product, show_vendor: section.settings.show_vendor %}
      {% endfor %}
    </div>

    {% for block in section.blocks %}
      {% case block.type %}
        {% when 'custom_badge' %}
          <div class="custom-badge" {{ block.shopify_attributes }}>
            {{ block.settings.badge_text }}
          </div>
        {% when 'countdown' %}
          <div class="countdown-timer"
               data-end-date="{{ block.settings.end_date }}"
               {{ block.shopify_attributes }}>
          </div>
      {% endcase %}
    {% endfor %}
  </div>
</section>

{% schema %}
{
  "name": "Featured Collection",
  "tag": "section",
  "class": "featured-collection-section",
  "limit": 3,
  "settings": [
    {
      "type": "text",
      "id": "heading",
      "label": "Heading",
      "default": "Featured Products"
    },
    {
      "type": "collection",
      "id": "collection",
      "label": "Collection"
    },
    {
      "type": "range",
      "id": "products_to_show",
      "min": 2,
      "max": 12,
      "step": 1,
      "default": 4,
      "label": "Products to show"
    },
    {
      "type": "select",
      "id": "columns",
      "label": "Columns",
      "options": [
        { "value": "2", "label": "2 columns" },
        { "value": "3", "label": "3 columns" },
        { "value": "4", "label": "4 columns" }
      ],
      "default": "4"
    },
    {
      "type": "checkbox",
      "id": "show_vendor",
      "label": "Show vendor",
      "default": false
    }
  ],
  "blocks": [
    {
      "type": "custom_badge",
      "name": "Custom Badge",
      "limit": 1,
      "settings": [
        {
          "type": "text",
          "id": "badge_text",
          "label": "Badge Text",
          "default": "Sale"
        }
      ]
    },
    {
      "type": "countdown",
      "name": "Countdown Timer",
      "limit": 1,
      "settings": [
        {
          "type": "text",
          "id": "end_date",
          "label": "End Date (ISO format)",
          "info": "Example: 2025-12-31T23:59:59"
        }
      ]
    }
  ],
  "presets": [
    {
      "name": "Featured Collection",
      "blocks": []
    }
  ]
}
{% endschema %}

{% stylesheet %}
  .featured-collection {
    padding: 40px 0;
  }
{% endstylesheet %}

{% javascript %}
  // Section-specific JavaScript
{% endjavascript %}
```

---

## Liquid Filters and Tags

### Essential Object Access

```liquid
{% comment %} Product object {% endcomment %}
{{ product.title }}
{{ product.description }}
{{ product.price | money }}
{{ product.compare_at_price | money }}
{{ product.featured_image | image_url: width: 600 }}
{{ product.url }}
{{ product.vendor }}
{{ product.type }}
{{ product.tags | join: ', ' }}

{% comment %} Variant handling {% endcomment %}
{% for variant in product.variants %}
  <option
    value="{{ variant.id }}"
    {% if variant.available == false %}disabled{% endif %}
    data-price="{{ variant.price }}"
  >
    {{ variant.title }} - {{ variant.price | money }}
  </option>
{% endfor %}

{% comment %} Check availability {% endcomment %}
{% if product.available %}
  {% if product.variants.size > 1 %}
    {% comment %} Show variant picker {% endcomment %}
  {% else %}
    {% comment %} Show add to cart {% endcomment %}
  {% endif %}
{% else %}
  <span class="sold-out">Sold Out</span>
{% endif %}
```

### Image Handling (Modern Syntax)

```liquid
{% comment %} Responsive images with srcset {% endcomment %}
{{ product.featured_image | image_url: width: 800 | image_tag:
  srcset: product.featured_image | image_url: width: 400 | append: ' 400w, ' |
          append: product.featured_image | image_url: width: 800 | append: ' 800w, ' |
          append: product.featured_image | image_url: width: 1200 | append: ' 1200w',
  sizes: '(max-width: 768px) 100vw, 50vw',
  loading: 'lazy',
  alt: product.featured_image.alt | escape
}}

{% comment %} Simple responsive image {% endcomment %}
{{
  product.featured_image | image_url: width: 600 | image_tag:
    loading: 'lazy',
    widths: '200, 400, 600, 800',
    alt: product.title
}}

{% comment %} Background image with focal point {% endcomment %}
<div
  class="hero-image"
  style="background-image: url('{{ section.settings.image | image_url: width: 1920 }}');
         background-position: {{ section.settings.image.presentation.focal_point }};"
>
</div>
```

### Metafield Access

```liquid
{% comment %} Product metafields {% endcomment %}
{% assign care_instructions = product.metafields.custom.care_instructions %}
{% if care_instructions %}
  <div class="care-instructions">
    {{ care_instructions.value }}
  </div>
{% endif %}

{% comment %} Metafield with type checking {% endcomment %}
{% assign size_chart = product.metafields.custom.size_chart %}
{% if size_chart.type == 'file_reference' %}
  <img src="{{ size_chart.value | image_url: width: 800 }}" alt="Size Chart">
{% endif %}

{% comment %} List metafield {% endcomment %}
{% assign features = product.metafields.custom.features.value %}
{% if features.size > 0 %}
  <ul class="product-features">
    {% for feature in features %}
      <li>{{ feature }}</li>
    {% endfor %}
  </ul>
{% endif %}

{% comment %} Metaobject reference {% endcomment %}
{% assign designer = product.metafields.custom.designer.value %}
{% if designer %}
  <div class="designer-info">
    <h4>{{ designer.name.value }}</h4>
    <p>{{ designer.bio.value }}</p>
    {% if designer.photo.value %}
      {{ designer.photo.value | image_url: width: 200 | image_tag }}
    {% endif %}
  </div>
{% endif %}
```

### Collection Filtering and Sorting

```liquid
{% comment %} Active filters display {% endcomment %}
{% for filter in collection.filters %}
  {% if filter.active_values.size > 0 %}
    <div class="active-filter">
      <strong>{{ filter.label }}:</strong>
      {% for value in filter.active_values %}
        <a href="{{ value.url_to_remove }}" class="remove-filter">
          {{ value.label }} &times;
        </a>
      {% endfor %}
    </div>
  {% endif %}
{% endfor %}

{% comment %} Filter form {% endcomment %}
<form id="filters-form">
  {% for filter in collection.filters %}
    <div class="filter-group">
      <h4>{{ filter.label }}</h4>

      {% case filter.type %}
        {% when 'list' %}
          {% for value in filter.values %}
            <label>
              <input
                type="checkbox"
                name="{{ filter.param_name }}"
                value="{{ value.value }}"
                {% if value.active %}checked{% endif %}
                {% if value.count == 0 %}disabled{% endif %}
              >
              {{ value.label }} ({{ value.count }})
            </label>
          {% endfor %}

        {% when 'price_range' %}
          <input
            type="range"
            name="{{ filter.param_name }}"
            min="{{ filter.range_min | money_without_currency }}"
            max="{{ filter.range_max | money_without_currency }}"
            value="{{ filter.max_value.value | money_without_currency }}"
          >
      {% endcase %}
    </div>
  {% endfor %}
</form>

{% comment %} Sort options {% endcomment %}
<select name="sort_by" id="sort-by">
  {% for option in collection.sort_options %}
    <option
      value="{{ option.value }}"
      {% if collection.sort_by == option.value %}selected{% endif %}
    >
      {{ option.name }}
    </option>
  {% endfor %}
</select>
```

---

## Cart and Checkout Integration

### Cart Form Pattern

```liquid
{% comment %} snippets/product-form.liquid {% endcomment %}

{% form 'product', product, id: 'product-form', class: 'product-form', data-product-form: '' %}
  <input type="hidden" name="id" value="{{ product.selected_or_first_available_variant.id }}">

  {% unless product.has_only_default_variant %}
    {% for option in product.options_with_values %}
      <div class="product-option">
        <label for="Option-{{ option.name | handleize }}">
          {{ option.name }}
        </label>

        <select
          id="Option-{{ option.name | handleize }}"
          name="options[{{ option.name }}]"
          data-option-index="{{ forloop.index0 }}"
        >
          {% for value in option.values %}
            <option
              value="{{ value }}"
              {% if option.selected_value == value %}selected{% endif %}
            >
              {{ value }}
            </option>
          {% endfor %}
        </select>
      </div>
    {% endfor %}
  {% endunless %}

  <div class="quantity-selector">
    <label for="Quantity">Quantity</label>
    <input
      type="number"
      id="Quantity"
      name="quantity"
      value="1"
      min="1"
      max="{{ product.selected_or_first_available_variant.inventory_quantity | default: 99 }}"
    >
  </div>

  {% comment %} Line item properties {% endcomment %}
  {% if product.metafields.custom.enable_personalization %}
    <div class="personalization">
      <label for="personalization-text">Add personalization</label>
      <input
        type="text"
        id="personalization-text"
        name="properties[Personalization]"
        maxlength="50"
      >
    </div>
  {% endif %}

  <button
    type="submit"
    name="add"
    {% unless product.available %}disabled{% endunless %}
    class="add-to-cart-button"
  >
    {% if product.available %}
      Add to Cart - {{ product.selected_or_first_available_variant.price | money }}
    {% else %}
      Sold Out
    {% endif %}
  </button>
{% endform %}

<script type="application/json" id="product-json">
  {{ product | json }}
</script>
```

### AJAX Cart Updates

```liquid
{% comment %} snippets/cart-drawer.liquid {% endcomment %}

<div id="cart-drawer" class="cart-drawer" aria-hidden="true">
  <div class="cart-drawer__header">
    <h2>Your Cart ({{ cart.item_count }})</h2>
    <button type="button" class="cart-drawer__close" aria-label="Close cart">
      &times;
    </button>
  </div>

  <div class="cart-drawer__content">
    {% if cart.item_count > 0 %}
      <form action="{{ routes.cart_url }}" method="post" id="cart-drawer-form">
        {% for item in cart.items %}
          <div class="cart-item" data-line="{{ forloop.index }}">
            <img
              src="{{ item.image | image_url: width: 150 }}"
              alt="{{ item.title | escape }}"
              width="75"
              height="75"
              loading="lazy"
            >

            <div class="cart-item__details">
              <a href="{{ item.url }}">{{ item.product.title }}</a>
              {% unless item.product.has_only_default_variant %}
                <span class="cart-item__variant">{{ item.variant.title }}</span>
              {% endunless %}

              {% if item.properties.size > 0 %}
                {% for property in item.properties %}
                  {% unless property.last == blank %}
                    <span class="cart-item__property">
                      {{ property.first }}: {{ property.last }}
                    </span>
                  {% endunless %}
                {% endfor %}
              {% endif %}

              <div class="cart-item__quantity">
                <button type="button" data-quantity-minus>-</button>
                <input
                  type="number"
                  name="updates[]"
                  value="{{ item.quantity }}"
                  min="0"
                  data-line="{{ forloop.index }}"
                >
                <button type="button" data-quantity-plus>+</button>
              </div>

              <span class="cart-item__price">{{ item.final_line_price | money }}</span>
            </div>

            <a href="{{ item.url_to_remove }}" class="cart-item__remove" aria-label="Remove">
              Remove
            </a>
          </div>
        {% endfor %}

        <div class="cart-drawer__footer">
          {% if cart.cart_level_discount_applications.size > 0 %}
            <div class="cart-discounts">
              {% for discount in cart.cart_level_discount_applications %}
                <span class="discount">
                  {{ discount.title }}: -{{ discount.total_allocated_amount | money }}
                </span>
              {% endfor %}
            </div>
          {% endif %}

          <div class="cart-subtotal">
            <span>Subtotal</span>
            <span>{{ cart.total_price | money }}</span>
          </div>

          <p class="cart-note">Shipping and taxes calculated at checkout</p>

          <button type="submit" name="checkout" class="checkout-button">
            Checkout
          </button>
        </div>
      </form>
    {% else %}
      <p class="cart-empty">Your cart is empty</p>
      <a href="{{ routes.all_products_collection_url }}" class="continue-shopping">
        Continue Shopping
      </a>
    {% endif %}
  </div>
</div>
```

---

## Localization and Markets

### Multi-language Support

```liquid
{% comment %} Language/currency selector {% endcomment %}
{% form 'localization', id: 'localization-form' %}
  {% if localization.available_languages.size > 1 %}
    <div class="language-selector">
      <label for="language-select">{{ 'general.language' | t }}</label>
      <select id="language-select" name="locale_code">
        {% for language in localization.available_languages %}
          <option
            value="{{ language.iso_code }}"
            {% if language.iso_code == localization.language.iso_code %}selected{% endif %}
          >
            {{ language.endonym_name | capitalize }}
          </option>
        {% endfor %}
      </select>
    </div>
  {% endif %}

  {% if localization.available_countries.size > 1 %}
    <div class="country-selector">
      <label for="country-select">{{ 'general.country' | t }}</label>
      <select id="country-select" name="country_code">
        {% for country in localization.available_countries %}
          <option
            value="{{ country.iso_code }}"
            {% if country.iso_code == localization.country.iso_code %}selected{% endif %}
          >
            {{ country.name }} ({{ country.currency.iso_code }} {{ country.currency.symbol }})
          </option>
        {% endfor %}
      </select>
    </div>
  {% endif %}

  <button type="submit">{{ 'general.update' | t }}</button>
{% endform %}

{% comment %} Using translations {% endcomment %}
<h1>{{ 'products.product.add_to_cart' | t }}</h1>
<p>{{ 'products.product.quantity' | t: quantity: product.quantity }}</p>

{% comment %} Pluralization {% endcomment %}
{{ 'cart.items_count' | t: count: cart.item_count }}
```

---

## Performance Best Practices

### Lazy Loading Sections

```liquid
{% comment %} Defer non-critical sections {% endcomment %}
<div
  id="product-recommendations"
  data-url="{{ routes.product_recommendations_url }}?product_id={{ product.id }}&limit=4"
>
  {% comment %} Content loaded via JavaScript {% endcomment %}
</div>

<script>
  document.addEventListener('DOMContentLoaded', function() {
    const container = document.getElementById('product-recommendations');
    if (container && 'IntersectionObserver' in window) {
      const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            fetch(container.dataset.url)
              .then(response => response.text())
              .then(html => {
                container.innerHTML = html;
              });
            observer.unobserve(entry.target);
          }
        });
      }, { rootMargin: '200px' });
      observer.observe(container);
    }
  });
</script>
```

### Avoiding Common Mistakes

```liquid
{% comment %} BAD: N+1 queries in loop {% endcomment %}
{% for product in collection.products %}
  {% assign designer = product.metafields.custom.designer.value %}
  {{ designer.name }} {%- comment -%} Each iteration queries metaobject {%- endcomment -%}
{% endfor %}

{% comment %} GOOD: Use includes with proper caching {% endcomment %}
{% for product in collection.products %}
  {% render 'product-card', product: product %}
{% endfor %}

{% comment %} BAD: Unnecessary assigns {% endcomment %}
{% assign title = product.title %}
{{ title }}

{% comment %} GOOD: Direct access {% endcomment %}
{{ product.title }}

{% comment %} BAD: String concatenation in loop {% endcomment %}
{% assign classes = '' %}
{% for tag in product.tags %}
  {% assign classes = classes | append: ' tag-' | append: tag | handleize %}
{% endfor %}

{% comment %} GOOD: Use capture {% endcomment %}
{% capture classes %}
  {% for tag in product.tags %} tag-{{ tag | handleize }}{% endfor %}
{% endcapture %}
```

---

## Related References

- **Storefront API** - For headless implementations
- **Performance Optimization** - Detailed performance patterns
- **Checkout Customization** - Post-purchase and checkout extensions
