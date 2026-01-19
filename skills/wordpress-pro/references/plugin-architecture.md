# Plugin Architecture

> Reference for: WordPress Pro
> Load when: Structure, activation, settings API, updates, plugin development

---

## Plugin Structure

### Minimal Plugin Structure

```
plugin-name/
├── plugin-name.php        # Main plugin file with header
├── uninstall.php          # Cleanup on uninstall
├── includes/
│   ├── class-plugin-name.php
│   ├── class-activator.php
│   ├── class-deactivator.php
│   └── class-loader.php
├── admin/
│   ├── class-admin.php
│   ├── css/
│   └── js/
├── public/
│   ├── class-public.php
│   ├── css/
│   └── js/
├── languages/
│   └── plugin-name.pot
└── README.txt
```

### Full Plugin Structure (Enterprise)

```
plugin-name/
├── plugin-name.php
├── uninstall.php
├── composer.json
├── phpcs.xml.dist
├── phpunit.xml.dist
├── includes/
│   ├── class-plugin.php           # Main plugin class
│   ├── class-activator.php        # Activation logic
│   ├── class-deactivator.php      # Deactivation logic
│   ├── class-loader.php           # Hook loader
│   ├── class-i18n.php             # Internationalization
│   ├── Traits/
│   │   └── Singleton.php
│   ├── Interfaces/
│   │   ├── Registrable.php
│   │   └── Hookable.php
│   ├── Services/
│   │   └── class-api-service.php
│   └── Repositories/
│       └── class-data-repository.php
├── admin/
│   ├── class-admin.php
│   ├── class-settings.php
│   ├── partials/
│   │   └── settings-page.php
│   ├── css/
│   └── js/
├── public/
│   ├── class-frontend.php
│   ├── partials/
│   ├── css/
│   └── js/
├── blocks/
│   └── custom-block/
├── templates/
│   └── single-custom-type.php
├── languages/
├── tests/
│   ├── bootstrap.php
│   └── unit/
└── vendor/
```

---

## Main Plugin File

### Plugin Header

```php
<?php
/**
 * Plugin Name:       Plugin Name
 * Plugin URI:        https://example.com/plugin-name
 * Description:       A brief description of what this plugin does.
 * Version:           1.0.0
 * Requires at least: 6.4
 * Requires PHP:      8.1
 * Author:            Author Name
 * Author URI:        https://example.com
 * License:           GPL v2 or later
 * License URI:       https://www.gnu.org/licenses/gpl-2.0.html
 * Text Domain:       plugin-name
 * Domain Path:       /languages
 * Update URI:        https://example.com/plugin-name
 *
 * @package PluginName
 */

declare(strict_types=1);

namespace PluginName;

// Prevent direct access
defined('ABSPATH') || exit;

// Plugin constants
define('PLUGIN_NAME_VERSION', '1.0.0');
define('PLUGIN_NAME_FILE', __FILE__);
define('PLUGIN_NAME_PATH', plugin_dir_path(__FILE__));
define('PLUGIN_NAME_URL', plugin_dir_url(__FILE__));
define('PLUGIN_NAME_BASENAME', plugin_basename(__FILE__));

// Autoloader
if (file_exists(PLUGIN_NAME_PATH . 'vendor/autoload.php')) {
    require_once PLUGIN_NAME_PATH . 'vendor/autoload.php';
}

// Manual includes if no autoloader
require_once PLUGIN_NAME_PATH . 'includes/class-plugin.php';
require_once PLUGIN_NAME_PATH . 'includes/class-activator.php';
require_once PLUGIN_NAME_PATH . 'includes/class-deactivator.php';

/**
 * Plugin activation hook
 */
function activate(): void {
    Activator::activate();
}
register_activation_hook(__FILE__, __NAMESPACE__ . '\\activate');

/**
 * Plugin deactivation hook
 */
function deactivate(): void {
    Deactivator::deactivate();
}
register_deactivation_hook(__FILE__, __NAMESPACE__ . '\\deactivate');

/**
 * Initialize the plugin
 */
function init(): void {
    $plugin = new Plugin();
    $plugin->run();
}
add_action('plugins_loaded', __NAMESPACE__ . '\\init');
```

---

## Activation & Deactivation

### Activator Class

```php
<?php
declare(strict_types=1);

namespace PluginName;

/**
 * Fired during plugin activation
 */
class Activator {

    /**
     * Activation tasks
     */
    public static function activate(): void {
        // Check requirements
        self::check_requirements();

        // Create database tables
        self::create_tables();

        // Set default options
        self::set_default_options();

        // Schedule cron events
        self::schedule_events();

        // Add capabilities
        self::add_capabilities();

        // Flush rewrite rules (if registering CPT/taxonomy)
        flush_rewrite_rules();

        // Set activation flag for welcome notice
        set_transient('plugin_name_activated', true, 30);
    }

    /**
     * Check system requirements
     */
    private static function check_requirements(): void {
        if (version_compare(PHP_VERSION, '8.1', '<')) {
            deactivate_plugins(PLUGIN_NAME_BASENAME);
            wp_die(
                esc_html__('This plugin requires PHP 8.1 or higher.', 'plugin-name'),
                'Plugin Activation Error',
                ['back_link' => true]
            );
        }

        global $wp_version;
        if (version_compare($wp_version, '6.4', '<')) {
            deactivate_plugins(PLUGIN_NAME_BASENAME);
            wp_die(
                esc_html__('This plugin requires WordPress 6.4 or higher.', 'plugin-name'),
                'Plugin Activation Error',
                ['back_link' => true]
            );
        }
    }

    /**
     * Create custom database tables
     */
    private static function create_tables(): void {
        global $wpdb;

        $charset_collate = $wpdb->get_charset_collate();
        $table_name = $wpdb->prefix . 'plugin_name_data';

        $sql = "CREATE TABLE IF NOT EXISTS {$table_name} (
            id bigint(20) unsigned NOT NULL AUTO_INCREMENT,
            user_id bigint(20) unsigned NOT NULL DEFAULT 0,
            data_key varchar(191) NOT NULL,
            data_value longtext,
            created_at datetime DEFAULT CURRENT_TIMESTAMP,
            updated_at datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            PRIMARY KEY (id),
            KEY user_id (user_id),
            KEY data_key (data_key)
        ) {$charset_collate};";

        require_once ABSPATH . 'wp-admin/includes/upgrade.php';
        dbDelta($sql);

        // Store DB version
        update_option('plugin_name_db_version', PLUGIN_NAME_VERSION);
    }

    /**
     * Set default options
     */
    private static function set_default_options(): void {
        $defaults = [
            'enabled'          => true,
            'api_key'          => '',
            'cache_duration'   => 3600,
            'items_per_page'   => 10,
            'allowed_roles'    => ['administrator', 'editor'],
        ];

        if (get_option('plugin_name_settings') === false) {
            add_option('plugin_name_settings', $defaults);
        }
    }

    /**
     * Schedule cron events
     */
    private static function schedule_events(): void {
        if (!wp_next_scheduled('plugin_name_daily_cleanup')) {
            wp_schedule_event(time(), 'daily', 'plugin_name_daily_cleanup');
        }
    }

    /**
     * Add custom capabilities
     */
    private static function add_capabilities(): void {
        $admin = get_role('administrator');
        if ($admin) {
            $admin->add_cap('manage_plugin_name');
            $admin->add_cap('edit_plugin_name_data');
        }
    }
}
```

### Deactivator Class

```php
<?php
declare(strict_types=1);

namespace PluginName;

/**
 * Fired during plugin deactivation
 */
class Deactivator {

    /**
     * Deactivation tasks
     */
    public static function deactivate(): void {
        // Clear scheduled events
        self::clear_scheduled_events();

        // Clear transients
        self::clear_transients();

        // Flush rewrite rules
        flush_rewrite_rules();

        // Note: Do NOT delete options or tables here
        // That should only happen in uninstall.php
    }

    /**
     * Clear all scheduled cron events
     */
    private static function clear_scheduled_events(): void {
        $timestamp = wp_next_scheduled('plugin_name_daily_cleanup');
        if ($timestamp) {
            wp_unschedule_event($timestamp, 'plugin_name_daily_cleanup');
        }

        // Clear all instances of our events
        wp_clear_scheduled_hook('plugin_name_daily_cleanup');
    }

    /**
     * Clear transients
     */
    private static function clear_transients(): void {
        global $wpdb;

        // Clear specific transients
        delete_transient('plugin_name_cache');
        delete_transient('plugin_name_activated');

        // Clear all plugin transients (use with caution)
        $wpdb->query(
            $wpdb->prepare(
                "DELETE FROM {$wpdb->options} WHERE option_name LIKE %s OR option_name LIKE %s",
                '_transient_plugin_name_%',
                '_transient_timeout_plugin_name_%'
            )
        );
    }
}
```

### uninstall.php

```php
<?php
/**
 * Uninstall script - runs when plugin is deleted
 *
 * @package PluginName
 */

// If uninstall not called from WordPress, exit
if (!defined('WP_UNINSTALL_PLUGIN')) {
    exit;
}

// Check if we should preserve data
$settings = get_option('plugin_name_settings', []);
$preserve_data = $settings['preserve_data_on_uninstall'] ?? false;

if (!$preserve_data) {
    global $wpdb;

    // Delete options
    delete_option('plugin_name_settings');
    delete_option('plugin_name_db_version');

    // Delete user meta
    $wpdb->query("DELETE FROM {$wpdb->usermeta} WHERE meta_key LIKE 'plugin_name_%'");

    // Delete post meta
    $wpdb->query("DELETE FROM {$wpdb->postmeta} WHERE meta_key LIKE '_plugin_name_%'");

    // Delete custom tables
    $wpdb->query("DROP TABLE IF EXISTS {$wpdb->prefix}plugin_name_data");

    // Delete transients
    $wpdb->query(
        $wpdb->prepare(
            "DELETE FROM {$wpdb->options} WHERE option_name LIKE %s OR option_name LIKE %s",
            '_transient_plugin_name_%',
            '_transient_timeout_plugin_name_%'
        )
    );

    // Remove capabilities
    $roles = ['administrator', 'editor'];
    foreach ($roles as $role_name) {
        $role = get_role($role_name);
        if ($role) {
            $role->remove_cap('manage_plugin_name');
            $role->remove_cap('edit_plugin_name_data');
        }
    }

    // Clear any cached data
    wp_cache_flush();
}
```

---

## Settings API

### Settings Class

```php
<?php
declare(strict_types=1);

namespace PluginName\Admin;

/**
 * Plugin settings management
 */
class Settings {

    private const OPTION_GROUP = 'plugin_name_settings';
    private const OPTION_NAME = 'plugin_name_settings';
    private const PAGE_SLUG = 'plugin-name-settings';

    /**
     * Initialize settings
     */
    public function init(): void {
        add_action('admin_menu', [$this, 'add_menu_page']);
        add_action('admin_init', [$this, 'register_settings']);
    }

    /**
     * Add admin menu page
     */
    public function add_menu_page(): void {
        add_options_page(
            __('Plugin Name Settings', 'plugin-name'),
            __('Plugin Name', 'plugin-name'),
            'manage_options',
            self::PAGE_SLUG,
            [$this, 'render_settings_page']
        );
    }

    /**
     * Register all settings
     */
    public function register_settings(): void {
        register_setting(
            self::OPTION_GROUP,
            self::OPTION_NAME,
            [
                'type'              => 'array',
                'sanitize_callback' => [$this, 'sanitize_settings'],
                'default'           => $this->get_defaults(),
            ]
        );

        // General section
        add_settings_section(
            'plugin_name_general',
            __('General Settings', 'plugin-name'),
            [$this, 'render_general_section'],
            self::PAGE_SLUG
        );

        // API section
        add_settings_section(
            'plugin_name_api',
            __('API Settings', 'plugin-name'),
            [$this, 'render_api_section'],
            self::PAGE_SLUG
        );

        // Fields
        $this->add_fields();
    }

    /**
     * Add settings fields
     */
    private function add_fields(): void {
        // Enable field
        add_settings_field(
            'enabled',
            __('Enable Plugin', 'plugin-name'),
            [$this, 'render_checkbox_field'],
            self::PAGE_SLUG,
            'plugin_name_general',
            [
                'label_for'   => 'enabled',
                'description' => __('Enable or disable the plugin functionality.', 'plugin-name'),
            ]
        );

        // Items per page
        add_settings_field(
            'items_per_page',
            __('Items Per Page', 'plugin-name'),
            [$this, 'render_number_field'],
            self::PAGE_SLUG,
            'plugin_name_general',
            [
                'label_for'   => 'items_per_page',
                'min'         => 1,
                'max'         => 100,
                'description' => __('Number of items to display per page.', 'plugin-name'),
            ]
        );

        // API Key
        add_settings_field(
            'api_key',
            __('API Key', 'plugin-name'),
            [$this, 'render_text_field'],
            self::PAGE_SLUG,
            'plugin_name_api',
            [
                'label_for'   => 'api_key',
                'type'        => 'password',
                'description' => __('Enter your API key for external service.', 'plugin-name'),
            ]
        );

        // Cache duration
        add_settings_field(
            'cache_duration',
            __('Cache Duration', 'plugin-name'),
            [$this, 'render_select_field'],
            self::PAGE_SLUG,
            'plugin_name_api',
            [
                'label_for'   => 'cache_duration',
                'options'     => [
                    '900'   => __('15 minutes', 'plugin-name'),
                    '1800'  => __('30 minutes', 'plugin-name'),
                    '3600'  => __('1 hour', 'plugin-name'),
                    '86400' => __('1 day', 'plugin-name'),
                ],
                'description' => __('How long to cache API responses.', 'plugin-name'),
            ]
        );
    }

    /**
     * Get default settings
     */
    private function get_defaults(): array {
        return [
            'enabled'        => true,
            'api_key'        => '',
            'cache_duration' => 3600,
            'items_per_page' => 10,
        ];
    }

    /**
     * Sanitize settings
     */
    public function sanitize_settings(array $input): array {
        $sanitized = [];

        $sanitized['enabled'] = !empty($input['enabled']);

        $sanitized['api_key'] = sanitize_text_field($input['api_key'] ?? '');

        $sanitized['cache_duration'] = absint($input['cache_duration'] ?? 3600);
        if (!in_array($sanitized['cache_duration'], [900, 1800, 3600, 86400], true)) {
            $sanitized['cache_duration'] = 3600;
        }

        $sanitized['items_per_page'] = absint($input['items_per_page'] ?? 10);
        $sanitized['items_per_page'] = max(1, min(100, $sanitized['items_per_page']));

        return $sanitized;
    }

    /**
     * Render settings page
     */
    public function render_settings_page(): void {
        if (!current_user_can('manage_options')) {
            return;
        }

        // Show success message
        if (isset($_GET['settings-updated'])) {
            add_settings_error(
                self::OPTION_GROUP,
                'settings_updated',
                __('Settings saved.', 'plugin-name'),
                'updated'
            );
        }
        ?>
        <div class="wrap">
            <h1><?php echo esc_html(get_admin_page_title()); ?></h1>

            <?php settings_errors(self::OPTION_GROUP); ?>

            <form action="options.php" method="post">
                <?php
                settings_fields(self::OPTION_GROUP);
                do_settings_sections(self::PAGE_SLUG);
                submit_button(__('Save Settings', 'plugin-name'));
                ?>
            </form>
        </div>
        <?php
    }

    /**
     * Render general section description
     */
    public function render_general_section(): void {
        echo '<p>' . esc_html__('Configure general plugin settings.', 'plugin-name') . '</p>';
    }

    /**
     * Render API section description
     */
    public function render_api_section(): void {
        echo '<p>' . esc_html__('Configure API connection settings.', 'plugin-name') . '</p>';
    }

    /**
     * Render checkbox field
     */
    public function render_checkbox_field(array $args): void {
        $options = get_option(self::OPTION_NAME, $this->get_defaults());
        $value = $options[$args['label_for']] ?? false;
        ?>
        <input type="checkbox"
               id="<?php echo esc_attr($args['label_for']); ?>"
               name="<?php echo esc_attr(self::OPTION_NAME . '[' . $args['label_for'] . ']'); ?>"
               value="1"
               <?php checked($value, true); ?>
        />
        <?php if (!empty($args['description'])): ?>
            <p class="description"><?php echo esc_html($args['description']); ?></p>
        <?php endif;
    }

    /**
     * Render text field
     */
    public function render_text_field(array $args): void {
        $options = get_option(self::OPTION_NAME, $this->get_defaults());
        $value = $options[$args['label_for']] ?? '';
        $type = $args['type'] ?? 'text';
        ?>
        <input type="<?php echo esc_attr($type); ?>"
               id="<?php echo esc_attr($args['label_for']); ?>"
               name="<?php echo esc_attr(self::OPTION_NAME . '[' . $args['label_for'] . ']'); ?>"
               value="<?php echo esc_attr($value); ?>"
               class="regular-text"
        />
        <?php if (!empty($args['description'])): ?>
            <p class="description"><?php echo esc_html($args['description']); ?></p>
        <?php endif;
    }

    /**
     * Render number field
     */
    public function render_number_field(array $args): void {
        $options = get_option(self::OPTION_NAME, $this->get_defaults());
        $value = $options[$args['label_for']] ?? 0;
        ?>
        <input type="number"
               id="<?php echo esc_attr($args['label_for']); ?>"
               name="<?php echo esc_attr(self::OPTION_NAME . '[' . $args['label_for'] . ']'); ?>"
               value="<?php echo esc_attr($value); ?>"
               min="<?php echo esc_attr($args['min'] ?? 0); ?>"
               max="<?php echo esc_attr($args['max'] ?? 100); ?>"
               class="small-text"
        />
        <?php if (!empty($args['description'])): ?>
            <p class="description"><?php echo esc_html($args['description']); ?></p>
        <?php endif;
    }

    /**
     * Render select field
     */
    public function render_select_field(array $args): void {
        $options = get_option(self::OPTION_NAME, $this->get_defaults());
        $value = $options[$args['label_for']] ?? '';
        ?>
        <select id="<?php echo esc_attr($args['label_for']); ?>"
                name="<?php echo esc_attr(self::OPTION_NAME . '[' . $args['label_for'] . ']'); ?>">
            <?php foreach ($args['options'] as $key => $label): ?>
                <option value="<?php echo esc_attr($key); ?>" <?php selected($value, $key); ?>>
                    <?php echo esc_html($label); ?>
                </option>
            <?php endforeach; ?>
        </select>
        <?php if (!empty($args['description'])): ?>
            <p class="description"><?php echo esc_html($args['description']); ?></p>
        <?php endif;
    }
}
```

---

## Custom Post Types & Taxonomies

### Registering Custom Post Types

```php
<?php
declare(strict_types=1);

namespace PluginName;

/**
 * Register custom post types and taxonomies
 */
class CustomPostTypes {

    /**
     * Initialize
     */
    public function init(): void {
        add_action('init', [$this, 'register_post_types']);
        add_action('init', [$this, 'register_taxonomies']);
    }

    /**
     * Register custom post type
     */
    public function register_post_types(): void {
        $labels = [
            'name'                  => _x('Products', 'Post Type General Name', 'plugin-name'),
            'singular_name'         => _x('Product', 'Post Type Singular Name', 'plugin-name'),
            'menu_name'             => __('Products', 'plugin-name'),
            'name_admin_bar'        => __('Product', 'plugin-name'),
            'archives'              => __('Product Archives', 'plugin-name'),
            'attributes'            => __('Product Attributes', 'plugin-name'),
            'parent_item_colon'     => __('Parent Product:', 'plugin-name'),
            'all_items'             => __('All Products', 'plugin-name'),
            'add_new_item'          => __('Add New Product', 'plugin-name'),
            'add_new'               => __('Add New', 'plugin-name'),
            'new_item'              => __('New Product', 'plugin-name'),
            'edit_item'             => __('Edit Product', 'plugin-name'),
            'update_item'           => __('Update Product', 'plugin-name'),
            'view_item'             => __('View Product', 'plugin-name'),
            'view_items'            => __('View Products', 'plugin-name'),
            'search_items'          => __('Search Product', 'plugin-name'),
            'not_found'             => __('Not found', 'plugin-name'),
            'not_found_in_trash'    => __('Not found in Trash', 'plugin-name'),
            'featured_image'        => __('Featured Image', 'plugin-name'),
            'set_featured_image'    => __('Set featured image', 'plugin-name'),
            'remove_featured_image' => __('Remove featured image', 'plugin-name'),
            'use_featured_image'    => __('Use as featured image', 'plugin-name'),
            'insert_into_item'      => __('Insert into product', 'plugin-name'),
            'uploaded_to_this_item' => __('Uploaded to this product', 'plugin-name'),
            'items_list'            => __('Products list', 'plugin-name'),
            'items_list_navigation' => __('Products list navigation', 'plugin-name'),
            'filter_items_list'     => __('Filter products list', 'plugin-name'),
        ];

        $args = [
            'label'               => __('Product', 'plugin-name'),
            'description'         => __('Product custom post type', 'plugin-name'),
            'labels'              => $labels,
            'supports'            => ['title', 'editor', 'thumbnail', 'excerpt', 'custom-fields', 'revisions'],
            'taxonomies'          => ['product_category', 'product_tag'],
            'hierarchical'        => false,
            'public'              => true,
            'show_ui'             => true,
            'show_in_menu'        => true,
            'menu_position'       => 20,
            'menu_icon'           => 'dashicons-products',
            'show_in_admin_bar'   => true,
            'show_in_nav_menus'   => true,
            'can_export'          => true,
            'has_archive'         => 'products',
            'exclude_from_search' => false,
            'publicly_queryable'  => true,
            'capability_type'     => 'post',
            'show_in_rest'        => true,  // Enable Gutenberg
            'rest_base'           => 'products',
            'rewrite'             => [
                'slug'       => 'product',
                'with_front' => false,
            ],
            'template'            => [
                ['core/image', ['align' => 'wide']],
                ['core/paragraph', ['placeholder' => 'Product description...']],
            ],
            'template_lock'       => false,  // 'all', 'insert', false
        ];

        register_post_type('product', $args);
    }

    /**
     * Register custom taxonomies
     */
    public function register_taxonomies(): void {
        // Product Category (hierarchical like categories)
        $category_labels = [
            'name'              => _x('Product Categories', 'taxonomy general name', 'plugin-name'),
            'singular_name'     => _x('Product Category', 'taxonomy singular name', 'plugin-name'),
            'search_items'      => __('Search Product Categories', 'plugin-name'),
            'all_items'         => __('All Product Categories', 'plugin-name'),
            'parent_item'       => __('Parent Product Category', 'plugin-name'),
            'parent_item_colon' => __('Parent Product Category:', 'plugin-name'),
            'edit_item'         => __('Edit Product Category', 'plugin-name'),
            'update_item'       => __('Update Product Category', 'plugin-name'),
            'add_new_item'      => __('Add New Product Category', 'plugin-name'),
            'new_item_name'     => __('New Product Category Name', 'plugin-name'),
            'menu_name'         => __('Categories', 'plugin-name'),
        ];

        register_taxonomy('product_category', ['product'], [
            'hierarchical'      => true,
            'labels'            => $category_labels,
            'show_ui'           => true,
            'show_admin_column' => true,
            'query_var'         => true,
            'show_in_rest'      => true,
            'rewrite'           => ['slug' => 'product-category'],
        ]);

        // Product Tags (non-hierarchical like tags)
        $tag_labels = [
            'name'                       => _x('Product Tags', 'taxonomy general name', 'plugin-name'),
            'singular_name'              => _x('Product Tag', 'taxonomy singular name', 'plugin-name'),
            'search_items'               => __('Search Product Tags', 'plugin-name'),
            'popular_items'              => __('Popular Product Tags', 'plugin-name'),
            'all_items'                  => __('All Product Tags', 'plugin-name'),
            'edit_item'                  => __('Edit Product Tag', 'plugin-name'),
            'update_item'                => __('Update Product Tag', 'plugin-name'),
            'add_new_item'               => __('Add New Product Tag', 'plugin-name'),
            'new_item_name'              => __('New Product Tag Name', 'plugin-name'),
            'separate_items_with_commas' => __('Separate tags with commas', 'plugin-name'),
            'add_or_remove_items'        => __('Add or remove tags', 'plugin-name'),
            'choose_from_most_used'      => __('Choose from the most used tags', 'plugin-name'),
            'not_found'                  => __('No tags found.', 'plugin-name'),
            'menu_name'                  => __('Tags', 'plugin-name'),
        ];

        register_taxonomy('product_tag', ['product'], [
            'hierarchical'      => false,
            'labels'            => $tag_labels,
            'show_ui'           => true,
            'show_admin_column' => true,
            'query_var'         => true,
            'show_in_rest'      => true,
            'rewrite'           => ['slug' => 'product-tag'],
        ]);
    }
}
```

---

## Plugin Updates

### Self-Hosted Update Checker

```php
<?php
declare(strict_types=1);

namespace PluginName;

/**
 * Handle plugin updates from custom server
 */
class UpdateChecker {

    private string $plugin_slug;
    private string $update_url;
    private string $plugin_file;

    public function __construct() {
        $this->plugin_slug = 'plugin-name';
        $this->plugin_file = PLUGIN_NAME_BASENAME;
        $this->update_url = 'https://example.com/api/plugin-updates/';
    }

    /**
     * Initialize update checker
     */
    public function init(): void {
        add_filter('pre_set_site_transient_update_plugins', [$this, 'check_for_update']);
        add_filter('plugins_api', [$this, 'plugin_info'], 20, 3);
        add_action('in_plugin_update_message-' . $this->plugin_file, [$this, 'update_message'], 10, 2);
    }

    /**
     * Check for plugin updates
     */
    public function check_for_update(object $transient): object {
        if (empty($transient->checked)) {
            return $transient;
        }

        $remote = $this->get_remote_info();

        if (
            $remote &&
            version_compare(PLUGIN_NAME_VERSION, $remote->version, '<') &&
            version_compare($remote->requires, get_bloginfo('version'), '<=') &&
            version_compare($remote->requires_php, PHP_VERSION, '<=')
        ) {
            $transient->response[$this->plugin_file] = (object) [
                'slug'        => $this->plugin_slug,
                'plugin'      => $this->plugin_file,
                'new_version' => $remote->version,
                'url'         => $remote->url,
                'package'     => $remote->package,
                'icons'       => (array) ($remote->icons ?? []),
                'banners'     => (array) ($remote->banners ?? []),
                'tested'      => $remote->tested ?? '',
                'requires'    => $remote->requires ?? '',
            ];
        }

        return $transient;
    }

    /**
     * Plugin information for update screen
     */
    public function plugin_info(mixed $result, string $action, object $args): mixed {
        if ($action !== 'plugin_information' || $args->slug !== $this->plugin_slug) {
            return $result;
        }

        $remote = $this->get_remote_info();

        if (!$remote) {
            return $result;
        }

        return (object) [
            'name'            => $remote->name,
            'slug'            => $this->plugin_slug,
            'version'         => $remote->version,
            'author'          => $remote->author,
            'author_profile'  => $remote->author_profile ?? '',
            'requires'        => $remote->requires,
            'tested'          => $remote->tested,
            'requires_php'    => $remote->requires_php,
            'sections'        => (array) $remote->sections,
            'download_link'   => $remote->package,
            'banners'         => (array) ($remote->banners ?? []),
            'icons'           => (array) ($remote->icons ?? []),
            'last_updated'    => $remote->last_updated ?? '',
            'homepage'        => $remote->url ?? '',
        ];
    }

    /**
     * Custom update message
     */
    public function update_message(array $plugin_data, object $response): void {
        if (!empty($response->upgrade_notice)) {
            printf(
                '<br /><strong>%s</strong>: %s',
                esc_html__('Upgrade Notice', 'plugin-name'),
                esc_html($response->upgrade_notice)
            );
        }
    }

    /**
     * Get remote plugin information
     */
    private function get_remote_info(): ?object {
        $transient_key = 'plugin_name_update_info';
        $remote = get_transient($transient_key);

        if ($remote !== false) {
            return $remote === 'error' ? null : $remote;
        }

        $response = wp_remote_get($this->update_url . 'info.json', [
            'timeout' => 10,
            'headers' => [
                'Accept' => 'application/json',
            ],
        ]);

        if (
            is_wp_error($response) ||
            wp_remote_retrieve_response_code($response) !== 200 ||
            empty(wp_remote_retrieve_body($response))
        ) {
            set_transient($transient_key, 'error', HOUR_IN_SECONDS);
            return null;
        }

        $remote = json_decode(wp_remote_retrieve_body($response));
        set_transient($transient_key, $remote, 12 * HOUR_IN_SECONDS);

        return $remote;
    }
}
```

---

## Best Practices

### Do

- Use namespaces to avoid function/class name collisions
- Follow WordPress Coding Standards (WPCS)
- Include proper plugin headers with all required fields
- Implement proper activation/deactivation/uninstall hooks
- Use the Settings API for options pages
- Register CPTs with `show_in_rest` for Gutenberg support
- Cache remote API responses with transients
- Provide translation support with text domains
- Include a proper uninstall.php for cleanup

### Do Not

- Access the database directly without proper preparation
- Store options without sanitization
- Skip capability checks in admin functions
- Leave orphaned data after uninstall
- Hardcode plugin paths (use constants)
- Register hooks in constructors (use init methods)
- Modify core WordPress tables
- Include heavy operations in activation hooks
