# Performance & Security

> Reference for: WordPress Pro
> Load when: Caching, optimization, hardening, backups, security audit

---

## Performance Optimization

### Database Query Optimization

```php
<?php
declare(strict_types=1);

/**
 * Efficient database queries
 */

// BAD: Query inside loop
foreach ($post_ids as $post_id) {
    $meta = get_post_meta($post_id, 'my_key', true); // N+1 queries!
}

// GOOD: Batch query with caching
function get_posts_with_meta(array $post_ids): array {
    global $wpdb;

    $ids = implode(',', array_map('intval', $post_ids));

    // Single query for all meta
    $results = $wpdb->get_results($wpdb->prepare("
        SELECT post_id, meta_value
        FROM {$wpdb->postmeta}
        WHERE post_id IN ({$ids})
        AND meta_key = %s
    ", 'my_key'));

    $meta_map = [];
    foreach ($results as $row) {
        $meta_map[$row->post_id] = $row->meta_value;
    }

    return $meta_map;
}

/**
 * Use proper $wpdb methods with prepared statements
 */
function get_custom_data(int $user_id, string $status): array {
    global $wpdb;

    $table = $wpdb->prefix . 'custom_table';

    // GOOD: Prepared statement prevents SQL injection
    return $wpdb->get_results($wpdb->prepare("
        SELECT id, title, created_at
        FROM {$table}
        WHERE user_id = %d
        AND status = %s
        ORDER BY created_at DESC
        LIMIT 100
    ", $user_id, $status));
}

/**
 * Optimize WP_Query
 */
$optimized_query = new WP_Query([
    'post_type'              => 'product',
    'posts_per_page'         => 10,
    'no_found_rows'          => true,  // Skip SQL_CALC_FOUND_ROWS for pagination
    'update_post_meta_cache' => false, // Skip meta cache if not needed
    'update_post_term_cache' => false, // Skip term cache if not needed
    'fields'                 => 'ids', // Only get IDs if that's all you need
]);

/**
 * Use transients for expensive queries
 */
function get_popular_posts(): array {
    $cache_key = 'popular_posts_week';
    $posts = get_transient($cache_key);

    if ($posts === false) {
        $posts = get_posts([
            'post_type'      => 'post',
            'posts_per_page' => 10,
            'meta_key'       => 'views_count',
            'orderby'        => 'meta_value_num',
            'order'          => 'DESC',
            'date_query'     => [
                ['after' => '1 week ago'],
            ],
        ]);

        set_transient($cache_key, $posts, HOUR_IN_SECONDS);
    }

    return $posts;
}

/**
 * Invalidate cache when data changes
 */
add_action('save_post', function(int $post_id): void {
    delete_transient('popular_posts_week');
    delete_transient('featured_posts');
});
```

### Object Caching

```php
<?php
/**
 * WordPress object cache (works with Redis, Memcached)
 */

// Set cache
wp_cache_set('my_data', $data, 'my_plugin', 3600);

// Get cache
$data = wp_cache_get('my_data', 'my_plugin');
if ($data === false) {
    // Cache miss - fetch and set
    $data = expensive_operation();
    wp_cache_set('my_data', $data, 'my_plugin', 3600);
}

// Delete cache
wp_cache_delete('my_data', 'my_plugin');

// Cache with automatic handling
function get_expensive_data(int $id): mixed {
    $cache_key = 'expensive_data_' . $id;
    $cache_group = 'my_plugin';

    $data = wp_cache_get($cache_key, $cache_group);

    if ($data === false) {
        $data = perform_expensive_operation($id);
        wp_cache_set($cache_key, $data, $cache_group, HOUR_IN_SECONDS);
    }

    return $data;
}

/**
 * Fragment caching for expensive HTML
 */
function render_sidebar_widget(): void {
    $cache_key = 'sidebar_widget_html';
    $html = get_transient($cache_key);

    if ($html === false) {
        ob_start();
        // Expensive rendering
        include plugin_dir_path(__FILE__) . 'templates/widget.php';
        $html = ob_get_clean();

        set_transient($cache_key, $html, 15 * MINUTE_IN_SECONDS);
    }

    echo $html; // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped
}
```

### Asset Optimization

```php
<?php
/**
 * Efficient script and style loading
 */

// Conditional loading
add_action('wp_enqueue_scripts', function(): void {
    // Only load on specific pages
    if (!is_page('contact')) {
        return;
    }

    wp_enqueue_script('contact-form', ...);
});

// Defer non-critical scripts
add_filter('script_loader_tag', function(string $tag, string $handle): string {
    $defer_scripts = ['analytics', 'social-share', 'comments'];

    if (in_array($handle, $defer_scripts, true)) {
        return str_replace(' src', ' defer src', $tag);
    }

    return $tag;
}, 10, 2);

// Async scripts
add_filter('script_loader_tag', function(string $tag, string $handle): string {
    if ($handle === 'my-async-script') {
        return str_replace(' src', ' async src', $tag);
    }
    return $tag;
}, 10, 2);

// Preload critical assets
add_action('wp_head', function(): void {
    $font_url = get_template_directory_uri() . '/assets/fonts/inter.woff2';
    echo '<link rel="preload" href="' . esc_url($font_url) . '" as="font" type="font/woff2" crossorigin>';
}, 1);

// Remove unused scripts/styles
add_action('wp_enqueue_scripts', function(): void {
    // Remove block library CSS if not using blocks
    if (!is_singular()) {
        wp_dequeue_style('wp-block-library');
        wp_dequeue_style('wp-block-library-theme');
        wp_dequeue_style('global-styles');
    }

    // Remove emoji scripts
    remove_action('wp_head', 'print_emoji_detection_script', 7);
    remove_action('wp_print_styles', 'print_emoji_styles');
}, 100);

/**
 * Combine/minify inline styles
 */
add_action('wp_footer', function(): void {
    // Add critical CSS inline
    $critical_css = file_get_contents(get_template_directory() . '/assets/css/critical.css');
    if ($critical_css) {
        echo '<style id="critical-css">' . $critical_css . '</style>'; // phpcs:ignore
    }
}, 1);
```

### Image Optimization

```php
<?php
/**
 * Image optimization techniques
 */

// Add custom image sizes
add_action('after_setup_theme', function(): void {
    add_image_size('card-thumbnail', 400, 300, true);
    add_image_size('hero-image', 1600, 900, true);
});

// Lazy load images
add_filter('wp_get_attachment_image_attributes', function(array $attr): array {
    $attr['loading'] = 'lazy';
    $attr['decoding'] = 'async';
    return $attr;
});

// Add srcset for responsive images
add_filter('wp_calculate_image_srcset_meta', function(array $image_meta): array {
    // Ensure srcset is calculated
    return $image_meta;
});

// WebP support (requires server-side conversion)
add_filter('wp_generate_attachment_metadata', function(array $metadata, int $attachment_id): array {
    $file = get_attached_file($attachment_id);
    $mime = mime_content_type($file);

    if (in_array($mime, ['image/jpeg', 'image/png'], true)) {
        // Convert to WebP (requires Imagick or GD)
        my_plugin_create_webp_version($file);
    }

    return $metadata;
}, 10, 2);

// Serve WebP with fallback
function get_webp_image_url(string $url): string {
    $webp_url = preg_replace('/\.(jpe?g|png)$/i', '.webp', $url);
    $webp_path = str_replace(
        wp_upload_dir()['baseurl'],
        wp_upload_dir()['basedir'],
        $webp_url
    );

    if (file_exists($webp_path)) {
        return $webp_url;
    }

    return $url;
}
```

### Database Cleanup

```php
<?php
/**
 * Database maintenance
 */

// Clean up revisions (run via WP-CLI or cron)
function cleanup_post_revisions(int $keep = 5): int {
    global $wpdb;

    $deleted = 0;

    $posts = $wpdb->get_col("
        SELECT ID FROM {$wpdb->posts}
        WHERE post_type = 'revision'
        AND post_parent IN (
            SELECT ID FROM {$wpdb->posts} WHERE post_type IN ('post', 'page')
        )
    ");

    // Group by parent
    $by_parent = [];
    foreach ($posts as $revision_id) {
        $parent = wp_get_post_parent_id($revision_id);
        $by_parent[$parent][] = $revision_id;
    }

    foreach ($by_parent as $parent_id => $revisions) {
        // Keep most recent $keep revisions
        $to_delete = array_slice($revisions, $keep);
        foreach ($to_delete as $revision_id) {
            wp_delete_post_revision($revision_id);
            $deleted++;
        }
    }

    return $deleted;
}

// Clean up orphaned meta
function cleanup_orphaned_postmeta(): int {
    global $wpdb;

    return $wpdb->query("
        DELETE pm FROM {$wpdb->postmeta} pm
        LEFT JOIN {$wpdb->posts} p ON pm.post_id = p.ID
        WHERE p.ID IS NULL
    ");
}

// Clean up transients
function cleanup_expired_transients(): int {
    global $wpdb;

    $time = time();

    return $wpdb->query($wpdb->prepare("
        DELETE a, b FROM {$wpdb->options} a
        INNER JOIN {$wpdb->options} b ON b.option_name = CONCAT('_transient_timeout_', SUBSTRING(a.option_name, 12))
        WHERE a.option_name LIKE %s
        AND b.option_value < %d
    ", '_transient_%', $time));
}

// Schedule cleanup
add_action('init', function(): void {
    if (!wp_next_scheduled('my_plugin_db_cleanup')) {
        wp_schedule_event(time(), 'weekly', 'my_plugin_db_cleanup');
    }
});

add_action('my_plugin_db_cleanup', function(): void {
    cleanup_post_revisions(3);
    cleanup_orphaned_postmeta();
    cleanup_expired_transients();
});
```

---

## Security Hardening

### Input Sanitization

```php
<?php
declare(strict_types=1);

/**
 * Always sanitize user input
 */

// Text fields
$title = sanitize_text_field($_POST['title'] ?? '');
$email = sanitize_email($_POST['email'] ?? '');
$url = esc_url_raw($_POST['url'] ?? '');

// Textarea (allows line breaks)
$content = sanitize_textarea_field($_POST['content'] ?? '');

// HTML content (with allowed tags)
$html = wp_kses_post($_POST['html_content'] ?? '');

// Custom allowed HTML
$allowed_html = [
    'a'      => ['href' => [], 'title' => [], 'target' => []],
    'strong' => [],
    'em'     => [],
    'p'      => ['class' => []],
];
$safe_html = wp_kses($_POST['custom_html'] ?? '', $allowed_html);

// File names
$filename = sanitize_file_name($_POST['filename'] ?? '');

// Keys (alphanumeric, dashes, underscores)
$key = sanitize_key($_POST['key'] ?? '');

// Arrays
$ids = array_map('absint', (array) ($_POST['ids'] ?? []));
$tags = array_map('sanitize_text_field', (array) ($_POST['tags'] ?? []));

// Numbers
$id = absint($_POST['id'] ?? 0);
$price = (float) filter_var($_POST['price'] ?? 0, FILTER_SANITIZE_NUMBER_FLOAT, FILTER_FLAG_ALLOW_FRACTION);

/**
 * Database-safe queries
 */
global $wpdb;

// ALWAYS use prepared statements
$results = $wpdb->get_results($wpdb->prepare("
    SELECT * FROM {$wpdb->prefix}custom_table
    WHERE user_id = %d
    AND status = %s
    AND created_at > %s
", $user_id, $status, $date));

// Insert with proper escaping
$wpdb->insert(
    $wpdb->prefix . 'custom_table',
    [
        'user_id' => $user_id,
        'title'   => $title,
        'content' => $content,
    ],
    ['%d', '%s', '%s']
);

// Update with proper escaping
$wpdb->update(
    $wpdb->prefix . 'custom_table',
    ['title' => $new_title],
    ['id' => $id],
    ['%s'],
    ['%d']
);
```

### Output Escaping

```php
<?php
/**
 * Always escape output
 */

// HTML context
echo '<h1>' . esc_html($title) . '</h1>';
echo '<p>' . esc_html__('Welcome', 'my-plugin') . '</p>';

// Attributes
echo '<input type="text" value="' . esc_attr($value) . '" />';
echo '<div class="' . esc_attr($class) . '">';
echo '<div data-config="' . esc_attr(wp_json_encode($config)) . '">';

// URLs
echo '<a href="' . esc_url($url) . '">' . esc_html($text) . '</a>';
echo '<img src="' . esc_url($image_url) . '" alt="' . esc_attr($alt) . '" />';

// JavaScript
echo '<script>var config = ' . wp_json_encode($config) . ';</script>';

// Textarea content
echo '<textarea>' . esc_textarea($content) . '</textarea>';

// Allow specific HTML
echo wp_kses_post($html_content);

// Translation with escaping
printf(
    /* translators: %s: user name */
    esc_html__('Hello, %s!', 'my-plugin'),
    esc_html($user_name)
);

/**
 * When outputting large blocks of HTML
 */
?>
<div class="card">
    <h2><?php echo esc_html($card_title); ?></h2>
    <p><?php echo wp_kses_post($card_content); ?></p>
    <a href="<?php echo esc_url($card_link); ?>" class="<?php echo esc_attr($card_class); ?>">
        <?php echo esc_html($card_cta); ?>
    </a>
</div>
<?php
```

### Nonce Verification

```php
<?php
/**
 * Nonces prevent CSRF attacks
 */

// In form
function render_settings_form(): void {
    ?>
    <form method="post" action="<?php echo esc_url(admin_url('admin-post.php')); ?>">
        <?php wp_nonce_field('my_plugin_save_settings', 'my_plugin_nonce'); ?>
        <input type="hidden" name="action" value="my_plugin_save_settings" />

        <!-- Form fields -->

        <?php submit_button(__('Save Settings', 'my-plugin')); ?>
    </form>
    <?php
}

// Verify nonce on submission
add_action('admin_post_my_plugin_save_settings', function(): void {
    // Verify nonce
    if (!wp_verify_nonce($_POST['my_plugin_nonce'] ?? '', 'my_plugin_save_settings')) {
        wp_die(
            esc_html__('Security check failed.', 'my-plugin'),
            esc_html__('Error', 'my-plugin'),
            ['response' => 403]
        );
    }

    // Verify capability
    if (!current_user_can('manage_options')) {
        wp_die(
            esc_html__('You do not have permission to perform this action.', 'my-plugin'),
            esc_html__('Error', 'my-plugin'),
            ['response' => 403]
        );
    }

    // Process form
    $settings = [
        'option_1' => sanitize_text_field($_POST['option_1'] ?? ''),
        'option_2' => absint($_POST['option_2'] ?? 0),
    ];

    update_option('my_plugin_settings', $settings);

    wp_safe_redirect(add_query_arg('updated', 'true', wp_get_referer()));
    exit;
});

/**
 * AJAX with nonce
 */

// Localize script with nonce
wp_localize_script('my-script', 'myPluginData', [
    'ajaxUrl' => admin_url('admin-ajax.php'),
    'nonce'   => wp_create_nonce('my_plugin_ajax'),
]);

// JavaScript
// fetch(myPluginData.ajaxUrl, {
//     method: 'POST',
//     headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
//     body: new URLSearchParams({
//         action: 'my_plugin_action',
//         nonce: myPluginData.nonce,
//         data: 'value'
//     })
// });

// Handle AJAX
add_action('wp_ajax_my_plugin_action', function(): void {
    check_ajax_referer('my_plugin_ajax', 'nonce');

    if (!current_user_can('edit_posts')) {
        wp_send_json_error(['message' => 'Unauthorized'], 403);
    }

    $data = sanitize_text_field($_POST['data'] ?? '');

    // Process request
    $result = process_data($data);

    wp_send_json_success(['result' => $result]);
});
```

### Capability Checks

```php
<?php
/**
 * Always verify user capabilities
 */

// Check before displaying admin page
function render_admin_page(): void {
    if (!current_user_can('manage_options')) {
        wp_die(__('You do not have permission to access this page.', 'my-plugin'));
    }

    // Render page
}

// Check before performing action
function delete_item(int $item_id): bool {
    if (!current_user_can('delete_posts')) {
        return false;
    }

    // Delete item
    return true;
}

// Meta capability check for specific post
function edit_custom_post(int $post_id): bool {
    if (!current_user_can('edit_post', $post_id)) {
        return false;
    }

    // Edit post
    return true;
}

/**
 * Custom capabilities
 */

// Add custom capabilities on activation
function add_custom_capabilities(): void {
    $admin = get_role('administrator');
    $editor = get_role('editor');

    if ($admin) {
        $admin->add_cap('manage_my_plugin');
        $admin->add_cap('edit_my_plugin_items');
        $admin->add_cap('delete_my_plugin_items');
    }

    if ($editor) {
        $editor->add_cap('edit_my_plugin_items');
    }
}

// Use custom capability
if (current_user_can('manage_my_plugin')) {
    // Show management interface
}

// Map meta capabilities
add_filter('map_meta_cap', function(array $caps, string $cap, int $user_id, array $args): array {
    if ($cap === 'edit_my_plugin_item') {
        $item_id = $args[0] ?? 0;
        $item = get_my_plugin_item($item_id);

        if ($item && $item->author_id === $user_id) {
            $caps = ['edit_my_plugin_items'];
        } else {
            $caps = ['manage_my_plugin'];
        }
    }

    return $caps;
}, 10, 4);
```

### File Upload Security

```php
<?php
/**
 * Secure file upload handling
 */

function handle_file_upload(): array|WP_Error {
    // Verify nonce and capability
    if (!wp_verify_nonce($_POST['nonce'] ?? '', 'my_plugin_upload')) {
        return new WP_Error('security', __('Security check failed.', 'my-plugin'));
    }

    if (!current_user_can('upload_files')) {
        return new WP_Error('permission', __('You cannot upload files.', 'my-plugin'));
    }

    // Check file exists
    if (empty($_FILES['my_file']['tmp_name'])) {
        return new WP_Error('no_file', __('No file uploaded.', 'my-plugin'));
    }

    $file = $_FILES['my_file'];

    // Validate file type
    $allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'application/pdf'];
    $file_type = wp_check_filetype_and_ext($file['tmp_name'], $file['name']);

    if (!in_array($file_type['type'], $allowed_types, true)) {
        return new WP_Error('invalid_type', __('File type not allowed.', 'my-plugin'));
    }

    // Validate file size (5MB max)
    $max_size = 5 * 1024 * 1024;
    if ($file['size'] > $max_size) {
        return new WP_Error('too_large', __('File is too large.', 'my-plugin'));
    }

    // Sanitize filename
    $filename = sanitize_file_name($file['name']);

    // Use WordPress upload handling
    require_once ABSPATH . 'wp-admin/includes/file.php';
    require_once ABSPATH . 'wp-admin/includes/media.php';
    require_once ABSPATH . 'wp-admin/includes/image.php';

    // Handle upload
    $upload = wp_handle_upload($file, [
        'test_form' => false,
        'mimes'     => [
            'jpg|jpeg' => 'image/jpeg',
            'png'      => 'image/png',
            'gif'      => 'image/gif',
            'pdf'      => 'application/pdf',
        ],
    ]);

    if (isset($upload['error'])) {
        return new WP_Error('upload_error', $upload['error']);
    }

    // Create attachment
    $attachment_id = wp_insert_attachment([
        'post_mime_type' => $upload['type'],
        'post_title'     => preg_replace('/\.[^.]+$/', '', $filename),
        'post_content'   => '',
        'post_status'    => 'inherit',
    ], $upload['file']);

    // Generate metadata
    $metadata = wp_generate_attachment_metadata($attachment_id, $upload['file']);
    wp_update_attachment_metadata($attachment_id, $metadata);

    return [
        'id'  => $attachment_id,
        'url' => $upload['url'],
    ];
}
```

### Security Headers

```php
<?php
/**
 * Add security headers
 */

add_action('send_headers', function(): void {
    // Only on frontend, not admin or REST
    if (is_admin() || defined('REST_REQUEST')) {
        return;
    }

    // Prevent clickjacking
    header('X-Frame-Options: SAMEORIGIN');

    // Prevent MIME sniffing
    header('X-Content-Type-Options: nosniff');

    // XSS Protection
    header('X-XSS-Protection: 1; mode=block');

    // Referrer Policy
    header('Referrer-Policy: strict-origin-when-cross-origin');

    // Content Security Policy (customize as needed)
    $csp = "default-src 'self'; " .
           "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://www.google-analytics.com; " .
           "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; " .
           "font-src 'self' https://fonts.gstatic.com; " .
           "img-src 'self' data: https:; " .
           "connect-src 'self' https://www.google-analytics.com;";

    header("Content-Security-Policy: {$csp}");

    // Permissions Policy
    header("Permissions-Policy: geolocation=(), microphone=(), camera=()");
});
```

### Login Security

```php
<?php
/**
 * Login security enhancements
 */

// Limit login attempts
add_filter('authenticate', function(?WP_User $user, string $username, string $password): WP_User|WP_Error|null {
    if (empty($username) || empty($password)) {
        return $user;
    }

    $ip = $_SERVER['REMOTE_ADDR'];
    $lockout_key = 'login_attempts_' . md5($ip);
    $attempts = (int) get_transient($lockout_key);

    if ($attempts >= 5) {
        return new WP_Error(
            'too_many_attempts',
            sprintf(
                __('Too many failed login attempts. Please try again in %d minutes.', 'my-plugin'),
                15
            )
        );
    }

    return $user;
}, 20, 3);

// Track failed attempts
add_action('wp_login_failed', function(string $username): void {
    $ip = $_SERVER['REMOTE_ADDR'];
    $lockout_key = 'login_attempts_' . md5($ip);
    $attempts = (int) get_transient($lockout_key);

    set_transient($lockout_key, $attempts + 1, 15 * MINUTE_IN_SECONDS);
});

// Clear on successful login
add_action('wp_login', function(string $username): void {
    $ip = $_SERVER['REMOTE_ADDR'];
    $lockout_key = 'login_attempts_' . md5($ip);
    delete_transient($lockout_key);
});

// Disable XML-RPC if not needed
add_filter('xmlrpc_enabled', '__return_false');

// Hide login errors (don't reveal if username exists)
add_filter('login_errors', function(): string {
    return __('Invalid login credentials.', 'my-plugin');
});

// Force strong passwords
add_action('user_profile_update_errors', function(WP_Error $errors, bool $update, object $user): void {
    $password = $_POST['pass1'] ?? '';

    if (!empty($password)) {
        // Require minimum 12 characters
        if (strlen($password) < 12) {
            $errors->add('weak_password', __('Password must be at least 12 characters.', 'my-plugin'));
        }

        // Require mixed case, numbers, special chars
        if (!preg_match('/[A-Z]/', $password) ||
            !preg_match('/[a-z]/', $password) ||
            !preg_match('/[0-9]/', $password) ||
            !preg_match('/[^A-Za-z0-9]/', $password)) {
            $errors->add('weak_password', __('Password must contain uppercase, lowercase, numbers, and special characters.', 'my-plugin'));
        }
    }
}, 10, 3);
```

---

## Backup Strategy

```php
<?php
/**
 * Backup implementation
 */

class Database_Backup {

    private string $backup_dir;

    public function __construct() {
        $upload_dir = wp_upload_dir();
        $this->backup_dir = $upload_dir['basedir'] . '/backups/';

        if (!file_exists($this->backup_dir)) {
            wp_mkdir_p($this->backup_dir);

            // Protect directory
            file_put_contents($this->backup_dir . '.htaccess', 'deny from all');
            file_put_contents($this->backup_dir . 'index.php', '<?php // Silence is golden');
        }
    }

    /**
     * Create database backup
     */
    public function create_backup(): string|WP_Error {
        global $wpdb;

        $filename = 'db-backup-' . date('Y-m-d-His') . '.sql';
        $filepath = $this->backup_dir . $filename;

        $tables = $wpdb->get_col('SHOW TABLES');
        $output = "-- WordPress Database Backup\n";
        $output .= "-- Generated: " . date('Y-m-d H:i:s') . "\n\n";

        foreach ($tables as $table) {
            // Skip non-WordPress tables
            if (strpos($table, $wpdb->prefix) !== 0) {
                continue;
            }

            $output .= "DROP TABLE IF EXISTS `{$table}`;\n";

            $create = $wpdb->get_row("SHOW CREATE TABLE `{$table}`", ARRAY_N);
            $output .= $create[1] . ";\n\n";

            $rows = $wpdb->get_results("SELECT * FROM `{$table}`", ARRAY_A);

            foreach ($rows as $row) {
                $values = array_map(function($value) use ($wpdb) {
                    return $value === null ? 'NULL' : "'" . $wpdb->_real_escape($value) . "'";
                }, $row);

                $output .= "INSERT INTO `{$table}` VALUES (" . implode(',', $values) . ");\n";
            }

            $output .= "\n";
        }

        if (file_put_contents($filepath, $output) === false) {
            return new WP_Error('backup_failed', __('Failed to write backup file.', 'my-plugin'));
        }

        // Compress
        if (function_exists('gzencode')) {
            $compressed = gzencode($output, 9);
            file_put_contents($filepath . '.gz', $compressed);
            unlink($filepath);
            $filepath .= '.gz';
        }

        return $filepath;
    }

    /**
     * Clean old backups
     */
    public function cleanup_old_backups(int $keep_days = 30): int {
        $deleted = 0;
        $files = glob($this->backup_dir . '*.sql*');
        $cutoff = time() - ($keep_days * DAY_IN_SECONDS);

        foreach ($files as $file) {
            if (filemtime($file) < $cutoff) {
                unlink($file);
                $deleted++;
            }
        }

        return $deleted;
    }
}

// Schedule automatic backups
add_action('init', function(): void {
    if (!wp_next_scheduled('my_plugin_daily_backup')) {
        wp_schedule_event(time(), 'daily', 'my_plugin_daily_backup');
    }
});

add_action('my_plugin_daily_backup', function(): void {
    $backup = new Database_Backup();
    $result = $backup->create_backup();

    if (!is_wp_error($result)) {
        $backup->cleanup_old_backups(7);
    }
});
```

---

## Best Practices Summary

### Performance

- Use object caching (Redis/Memcached)
- Implement transients for expensive operations
- Optimize database queries with proper indexes
- Lazy load images and defer non-critical scripts
- Use `no_found_rows` when pagination not needed
- Clean up revisions and transients regularly

### Security

- Sanitize ALL user input
- Escape ALL output
- Use nonces for all form submissions and AJAX
- Verify capabilities before any action
- Use prepared statements for database queries
- Validate file uploads thoroughly
- Implement rate limiting for login
- Add security headers
- Keep WordPress and plugins updated
