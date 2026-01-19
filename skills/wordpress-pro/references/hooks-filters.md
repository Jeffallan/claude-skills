# Hooks & Filters

> Reference for: WordPress Pro
> Load when: Actions, filters, custom hooks, priorities, hook system

---

## WordPress Hook System

WordPress uses an event-driven architecture with two types of hooks:

| Hook Type | Purpose | Function |
|-----------|---------|----------|
| **Actions** | Execute code at specific points | `add_action()` / `do_action()` |
| **Filters** | Modify data before it's used | `add_filter()` / `apply_filters()` |

---

## Actions

Actions allow you to execute custom code at specific points in WordPress execution.

### Action Basics

```php
<?php
declare(strict_types=1);

/**
 * Register an action hook
 *
 * @param string   $hook_name     The name of the action
 * @param callable $callback      Function to execute
 * @param int      $priority      Order of execution (default: 10)
 * @param int      $accepted_args Number of arguments passed (default: 1)
 */
add_action('init', 'my_plugin_init', 10, 1);

/**
 * Execute custom code on init
 */
function my_plugin_init(): void {
    // Your code here
    register_post_type('product', [...]);
}

// Using anonymous functions (PHP 8.1+)
add_action('wp_footer', function(): void {
    echo '<!-- Custom footer content -->';
}, 99);

// Using class methods
class My_Plugin {
    public function __construct() {
        add_action('init', [$this, 'init']);
        add_action('admin_init', [$this, 'admin_init']);
    }

    public function init(): void {
        // Initialization code
    }

    public function admin_init(): void {
        // Admin initialization
    }
}

// Using static methods
add_action('init', [My_Plugin::class, 'static_init']);
```

### Essential Action Hooks

```php
<?php
/**
 * Execution order and common action hooks
 */

// === EARLY LOADING ===

// After WordPress loads but before headers sent
add_action('muplugins_loaded', function(): void {
    // Must-use plugins loaded
});

// After active plugins loaded
add_action('plugins_loaded', function(): void {
    // Safe to check for other plugins
    if (class_exists('WooCommerce')) {
        // WooCommerce is active
    }
});

// After theme functions.php loaded
add_action('after_setup_theme', function(): void {
    // Theme setup: add_theme_support, register_nav_menus, etc.
}, 10);

// === MAIN INITIALIZATION ===

// WordPress fully loaded, safe for most operations
add_action('init', function(): void {
    // Register post types, taxonomies, shortcodes
    // Load text domains
    // Start session if needed
}, 10);

// All widgets registered
add_action('widgets_init', function(): void {
    // Register widget areas
    register_sidebar([...]);
});

// === ADMIN HOOKS ===

// Admin area initializing
add_action('admin_init', function(): void {
    // Register settings, add capabilities
});

// Build admin menu
add_action('admin_menu', function(): void {
    // Add menu pages
    add_menu_page(...);
});

// Enqueue admin assets
add_action('admin_enqueue_scripts', function(string $hook_suffix): void {
    // $hook_suffix: e.g., 'post.php', 'settings_page_my-settings'
    if ($hook_suffix !== 'settings_page_my-settings') {
        return;
    }
    wp_enqueue_script('my-admin-script', ...);
}, 10, 1);

// === FRONTEND HOOKS ===

// Main query parsed, before template loaded
add_action('template_redirect', function(): void {
    // Check conditions, redirect if needed
    if (is_page('restricted') && !is_user_logged_in()) {
        wp_redirect(wp_login_url());
        exit;
    }
});

// Enqueue frontend assets
add_action('wp_enqueue_scripts', function(): void {
    wp_enqueue_style('my-style', ...);
    wp_enqueue_script('my-script', ...);
});

// Inside <head> tag
add_action('wp_head', function(): void {
    // Meta tags, inline styles
    echo '<meta name="custom" content="value" />';
}, 1); // Priority 1 = early in head

// Before </body> tag
add_action('wp_footer', function(): void {
    // Tracking scripts, modals
}, 99); // Priority 99 = late in footer

// === POST/PAGE HOOKS ===

// Before post is saved
add_action('pre_post_update', function(int $post_id, array $data): void {
    // Validate or modify before save
}, 10, 2);

// After post is saved (any status)
add_action('save_post', function(int $post_id, WP_Post $post, bool $update): void {
    // Skip autosaves
    if (defined('DOING_AUTOSAVE') && DOING_AUTOSAVE) {
        return;
    }

    // Skip revisions
    if (wp_is_post_revision($post_id)) {
        return;
    }

    // Skip specific post types
    if ($post->post_type !== 'my_post_type') {
        return;
    }

    // Update meta, trigger notifications, etc.
    update_post_meta($post_id, '_custom_meta', sanitize_text_field($_POST['custom_field'] ?? ''));
}, 10, 3);

// Post status transitions
add_action('transition_post_status', function(string $new_status, string $old_status, WP_Post $post): void {
    if ($new_status === 'publish' && $old_status !== 'publish') {
        // Post just published
        my_notify_subscribers($post);
    }
}, 10, 3);

// Post deleted (moved to trash)
add_action('wp_trash_post', function(int $post_id): void {
    // Clean up related data
});

// Post permanently deleted
add_action('before_delete_post', function(int $post_id, WP_Post $post): void {
    // Clean up custom tables, files, etc.
    global $wpdb;
    $wpdb->delete(
        $wpdb->prefix . 'my_table',
        ['post_id' => $post_id],
        ['%d']
    );
}, 10, 2);

// === USER HOOKS ===

// User registered
add_action('user_register', function(int $user_id, array $userdata): void {
    // Set default meta, send welcome email
    update_user_meta($user_id, 'welcome_dismissed', false);
}, 10, 2);

// User logged in
add_action('wp_login', function(string $user_login, WP_User $user): void {
    // Log login, update last login time
    update_user_meta($user->ID, 'last_login', current_time('mysql'));
}, 10, 2);

// User logged out
add_action('wp_logout', function(int $user_id): void {
    // Cleanup session data
}, 10, 1);

// === REST API HOOKS ===

// Register REST routes
add_action('rest_api_init', function(): void {
    register_rest_route('my-plugin/v1', '/items', [
        'methods'             => 'GET',
        'callback'            => 'my_plugin_get_items',
        'permission_callback' => '__return_true',
    ]);
});

// === CRON HOOKS ===

// Schedule custom cron event
add_action('init', function(): void {
    if (!wp_next_scheduled('my_plugin_daily_task')) {
        wp_schedule_event(time(), 'daily', 'my_plugin_daily_task');
    }
});

// Handle cron event
add_action('my_plugin_daily_task', function(): void {
    // Cleanup, sync, report generation, etc.
});
```

### Removing Actions

```php
<?php
/**
 * Remove actions added by WordPress or other plugins
 */

// Remove default WordPress actions
remove_action('wp_head', 'wp_generator');
remove_action('wp_head', 'wlwmanifest_link');
remove_action('wp_head', 'rsd_link');
remove_action('wp_head', 'wp_shortlink_wp_head');
remove_action('wp_head', 'print_emoji_detection_script', 7);
remove_action('wp_print_styles', 'print_emoji_styles');

// Remove action from a class (must match exact instance)
// If original: add_action('init', [$instance, 'method'], 10);
// Need to access same $instance to remove

// Remove using class name for static methods
remove_action('init', [Some_Class::class, 'static_method'], 10);

// Remove all callbacks from a hook
remove_all_actions('some_hook');

// Check if action is hooked
if (has_action('init', 'some_callback')) {
    // Callback is registered
}
```

---

## Filters

Filters modify data before it's used or displayed.

### Filter Basics

```php
<?php
declare(strict_types=1);

/**
 * Register a filter hook
 *
 * @param string   $hook_name     The name of the filter
 * @param callable $callback      Function to filter data
 * @param int      $priority      Order of execution (default: 10)
 * @param int      $accepted_args Number of arguments passed (default: 1)
 */
add_filter('the_content', 'my_plugin_modify_content', 10, 1);

/**
 * Modify post content
 *
 * @param string $content The post content
 * @return string Modified content
 */
function my_plugin_modify_content(string $content): string {
    // Always return the filtered value
    if (is_single() && in_the_loop()) {
        $content .= '<div class="post-cta">Subscribe for more!</div>';
    }
    return $content;
}

// Filter with multiple arguments
add_filter('post_thumbnail_html', function(
    string $html,
    int $post_id,
    int $thumbnail_id,
    string $size,
    string $attr
): string {
    // Add lazy loading
    return str_replace('<img', '<img loading="lazy"', $html);
}, 10, 5);
```

### Essential Filter Hooks

```php
<?php
/**
 * Common filter hooks
 */

// === CONTENT FILTERS ===

// Modify post title
add_filter('the_title', function(string $title, int $post_id): string {
    if (is_admin()) {
        return $title;
    }
    // Add icon for featured posts
    if (get_post_meta($post_id, '_is_featured', true)) {
        $title = '&#9733; ' . $title;
    }
    return $title;
}, 10, 2);

// Modify post content
add_filter('the_content', function(string $content): string {
    // Add social sharing after content
    if (is_singular('post') && in_the_loop() && is_main_query()) {
        $content .= my_plugin_get_share_buttons();
    }
    return $content;
});

// Modify excerpt length
add_filter('excerpt_length', function(int $length): int {
    return 30; // words
});

// Modify excerpt "more" text
add_filter('excerpt_more', function(string $more): string {
    return '&hellip; <a href="' . esc_url(get_permalink()) . '">Read more</a>';
});

// === QUERY FILTERS ===

// Modify main query
add_filter('pre_get_posts', function(WP_Query $query): void {
    if (is_admin() || !$query->is_main_query()) {
        return;
    }

    // Exclude category from blog
    if ($query->is_home()) {
        $query->set('cat', '-5'); // Exclude category ID 5
    }

    // Custom archive ordering
    if ($query->is_post_type_archive('product')) {
        $query->set('orderby', 'menu_order');
        $query->set('order', 'ASC');
    }
});

// Modify search results
add_filter('posts_search', function(string $search, WP_Query $query): string {
    if (!$query->is_search() || !$query->is_main_query()) {
        return $search;
    }
    // Customize search SQL
    return $search;
}, 10, 2);

// === TEMPLATE FILTERS ===

// Override template file
add_filter('template_include', function(string $template): string {
    if (is_singular('product')) {
        $custom = locate_template('templates/single-product.php');
        if ($custom) {
            return $custom;
        }
    }
    return $template;
});

// Add body classes
add_filter('body_class', function(array $classes): array {
    if (is_user_logged_in()) {
        $classes[] = 'logged-in-user';
    }
    if (wp_is_mobile()) {
        $classes[] = 'is-mobile';
    }
    return $classes;
});

// Add post classes
add_filter('post_class', function(array $classes, array $class, int $post_id): array {
    if (has_post_thumbnail($post_id)) {
        $classes[] = 'has-thumbnail';
    }
    return $classes;
}, 10, 3);

// === ADMIN FILTERS ===

// Modify admin columns
add_filter('manage_product_posts_columns', function(array $columns): array {
    $new_columns = [];
    foreach ($columns as $key => $value) {
        $new_columns[$key] = $value;
        if ($key === 'title') {
            $new_columns['price'] = __('Price', 'my-plugin');
            $new_columns['sku'] = __('SKU', 'my-plugin');
        }
    }
    return $new_columns;
});

// Populate custom columns
add_action('manage_product_posts_custom_column', function(string $column, int $post_id): void {
    switch ($column) {
        case 'price':
            echo esc_html(get_post_meta($post_id, '_price', true));
            break;
        case 'sku':
            echo esc_html(get_post_meta($post_id, '_sku', true));
            break;
    }
}, 10, 2);

// Make columns sortable
add_filter('manage_edit-product_sortable_columns', function(array $columns): array {
    $columns['price'] = 'price';
    $columns['sku'] = 'sku';
    return $columns;
});

// === URL/LINK FILTERS ===

// Modify permalink structure
add_filter('post_type_link', function(string $permalink, WP_Post $post): string {
    if ($post->post_type !== 'product') {
        return $permalink;
    }
    // Add category to permalink
    $terms = get_the_terms($post->ID, 'product_category');
    if ($terms && !is_wp_error($terms)) {
        $permalink = str_replace('%product_category%', $terms[0]->slug, $permalink);
    }
    return $permalink;
}, 10, 2);

// Modify upload directory
add_filter('upload_dir', function(array $uploads): array {
    // Custom upload path for specific post types
    if (isset($_POST['post_id'])) {
        $post_type = get_post_type((int) $_POST['post_id']);
        if ($post_type === 'product') {
            $uploads['subdir'] = '/products' . $uploads['subdir'];
            $uploads['path'] = $uploads['basedir'] . $uploads['subdir'];
            $uploads['url'] = $uploads['baseurl'] . $uploads['subdir'];
        }
    }
    return $uploads;
});

// === SECURITY FILTERS ===

// Modify allowed HTML in wp_kses
add_filter('wp_kses_allowed_html', function(array $allowed, string $context): array {
    if ($context === 'post') {
        $allowed['iframe'] = [
            'src'             => true,
            'width'           => true,
            'height'          => true,
            'frameborder'     => true,
            'allowfullscreen' => true,
        ];
    }
    return $allowed;
}, 10, 2);

// Modify authentication
add_filter('authenticate', function(?WP_User $user, string $username, string $password): WP_User|WP_Error|null {
    // Block login for specific conditions
    if ($username === 'admin') {
        return new WP_Error('invalid_username', __('Direct admin login is disabled.', 'my-plugin'));
    }
    return $user;
}, 30, 3);

// === REST API FILTERS ===

// Modify REST response
add_filter('rest_prepare_post', function(WP_REST_Response $response, WP_Post $post, WP_REST_Request $request): WP_REST_Response {
    // Add custom field to response
    $response->data['reading_time'] = my_plugin_calculate_reading_time($post->post_content);
    return $response;
}, 10, 3);
```

### Removing Filters

```php
<?php
/**
 * Remove filters
 */

// Remove wpautop (auto paragraphs)
remove_filter('the_content', 'wpautop');
remove_filter('the_excerpt', 'wpautop');

// Remove wptexturize (smart quotes)
remove_filter('the_content', 'wptexturize');
remove_filter('the_title', 'wptexturize');
remove_filter('comment_text', 'wptexturize');

// Remove specific filter (must match priority)
remove_filter('the_content', 'some_callback', 10);

// Remove all filters from a hook
remove_all_filters('the_content');

// Check if filter is applied
if (has_filter('the_content', 'some_callback')) {
    // Filter is registered
}
```

---

## Creating Custom Hooks

Allow other developers to extend your plugin/theme.

### Custom Actions

```php
<?php
declare(strict_types=1);

namespace MyPlugin;

/**
 * Example: Custom hooks in a plugin
 */
class OrderProcessor {

    /**
     * Process an order with custom hooks
     */
    public function process_order(array $order_data): int {
        // Allow modification of order data before processing
        $order_data = apply_filters('my_plugin_pre_process_order', $order_data);

        // Action before order creation
        do_action('my_plugin_before_create_order', $order_data);

        // Create the order
        $order_id = $this->create_order($order_data);

        if ($order_id) {
            // Action after successful order creation
            do_action('my_plugin_order_created', $order_id, $order_data);

            // Process payment
            $payment_result = $this->process_payment($order_id);

            if ($payment_result) {
                // Action after successful payment
                do_action('my_plugin_payment_complete', $order_id, $payment_result);
            } else {
                // Action on payment failure
                do_action('my_plugin_payment_failed', $order_id);
            }
        }

        // Action after all processing complete
        do_action('my_plugin_after_process_order', $order_id, $order_data);

        return $order_id;
    }

    /**
     * Get order total with filter
     */
    public function get_order_total(int $order_id): float {
        $subtotal = $this->calculate_subtotal($order_id);
        $shipping = $this->calculate_shipping($order_id);
        $tax = $this->calculate_tax($order_id);

        $total = $subtotal + $shipping + $tax;

        // Allow modification of total (for discounts, fees, etc.)
        return (float) apply_filters('my_plugin_order_total', $total, $order_id, [
            'subtotal' => $subtotal,
            'shipping' => $shipping,
            'tax'      => $tax,
        ]);
    }

    /**
     * Generate email content with filter
     */
    public function get_order_email_content(int $order_id): string {
        $order = $this->get_order($order_id);

        $content = sprintf(
            __('Order #%d has been placed.', 'my-plugin'),
            $order_id
        );

        // Allow complete override or modification
        return apply_filters('my_plugin_order_email_content', $content, $order_id, $order);
    }
}

/**
 * Example usage by another developer
 */

// Add discount to order total
add_filter('my_plugin_order_total', function(float $total, int $order_id, array $components): float {
    // Apply 10% discount for orders over $100
    if ($total > 100) {
        $total *= 0.9;
    }
    return $total;
}, 10, 3);

// Send notification on order creation
add_action('my_plugin_order_created', function(int $order_id, array $order_data): void {
    // Send Slack notification
    my_send_slack_notification("New order #{$order_id} created!");
}, 10, 2);

// Custom email content
add_filter('my_plugin_order_email_content', function(string $content, int $order_id, object $order): string {
    // Add custom footer
    $content .= "\n\nThank you for your business!";
    return $content;
}, 10, 3);
```

### Custom Filter with Default Value

```php
<?php
/**
 * Create filter with sensible defaults
 */

/**
 * Get items per page with filter
 */
function my_plugin_get_items_per_page(): int {
    $default = 10;

    /**
     * Filter the number of items per page
     *
     * @since 1.0.0
     *
     * @param int $items_per_page Number of items. Default 10.
     */
    return (int) apply_filters('my_plugin_items_per_page', $default);
}

/**
 * Get allowed file types with filter
 */
function my_plugin_get_allowed_file_types(): array {
    $defaults = ['jpg', 'jpeg', 'png', 'gif', 'pdf'];

    /**
     * Filter allowed file types for upload
     *
     * @since 1.0.0
     *
     * @param array $types Array of allowed file extensions.
     */
    return (array) apply_filters('my_plugin_allowed_file_types', $defaults);
}

/**
 * Check if feature is enabled with filter
 */
function my_plugin_is_feature_enabled(string $feature): bool {
    $enabled_features = [
        'dark_mode'    => true,
        'analytics'    => true,
        'beta_feature' => false,
    ];

    $is_enabled = $enabled_features[$feature] ?? false;

    /**
     * Filter whether a feature is enabled
     *
     * @since 1.0.0
     *
     * @param bool   $is_enabled Whether the feature is enabled.
     * @param string $feature    The feature slug.
     */
    return (bool) apply_filters('my_plugin_feature_enabled', $is_enabled, $feature);
}
```

---

## Hook Priority & Order

```php
<?php
/**
 * Priority determines execution order
 * Lower number = runs earlier
 * Default priority: 10
 */

// Runs first (priority 1)
add_action('init', 'my_first_function', 1);

// Runs with default priority (10)
add_action('init', 'my_default_function');
add_action('init', 'my_default_function_2'); // Runs after, same priority

// Runs last (priority 999)
add_action('init', 'my_last_function', 999);

/**
 * Filter priority example: Modify content
 */

// First: Add wrapper
add_filter('the_content', function(string $content): string {
    return '<div class="content-wrapper">' . $content . '</div>';
}, 5);

// Default: Add sharing buttons
add_filter('the_content', function(string $content): string {
    return $content . '<div class="share-buttons">...</div>';
}, 10);

// Late: Final output processing
add_filter('the_content', function(string $content): string {
    // Do final cleanup
    return $content;
}, 99);
```

---

## Best Practices

### Do

- Document custom hooks with PHPDoc comments
- Use prefixed hook names (`my_plugin_*`)
- Provide sensible default values for filters
- Pass relevant context to hooks (post ID, data arrays)
- Check `has_filter()`/`has_action()` before calling expensive operations
- Use appropriate priorities (don't default to 10 when order matters)
- Type hint callback parameters and return values (PHP 8.1+)
- Use namespaced functions or class methods as callbacks

### Do Not

- Remove core WordPress hooks without understanding consequences
- Create hooks that pass sensitive data (passwords, tokens)
- Rely on global variables in callbacks
- Forget to return filtered values
- Use anonymous functions when removal might be needed
- Create circular hook dependencies
- Add too many hooks at low priorities (performance impact)
- Modify data passed by reference unexpectedly

### Security Considerations

```php
<?php
/**
 * Security in hooks
 */

// Always validate/sanitize data from hooks
add_filter('my_plugin_user_input', function(mixed $input): string {
    return sanitize_text_field((string) $input);
});

// Check capabilities in action callbacks
add_action('my_plugin_admin_action', function(): void {
    if (!current_user_can('manage_options')) {
        wp_die(__('Unauthorized', 'my-plugin'));
    }
    // Proceed with admin action
});

// Verify nonces for form submissions
add_action('admin_post_my_plugin_save', function(): void {
    if (!wp_verify_nonce($_POST['_wpnonce'] ?? '', 'my_plugin_save')) {
        wp_die(__('Security check failed', 'my-plugin'));
    }
    // Process form
});
```
