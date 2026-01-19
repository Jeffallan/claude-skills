# Gutenberg Blocks

> Reference for: WordPress Pro
> Load when: Block dev, patterns, FSE, dynamic blocks, block editor, custom blocks

---

## Block Development Overview

WordPress 6.4+ uses the Block Editor (Gutenberg) as the primary editing experience. Blocks are the fundamental building units.

### Block Types

| Type | Description | Use Case |
|------|-------------|----------|
| Static | Fixed HTML output | Simple content, images |
| Dynamic | Server-rendered | Posts list, dynamic data |
| Interactive | Client-side JS | Accordions, tabs, carousels |

---

## Project Setup

### Using @wordpress/create-block

```bash
# Create a new block plugin
npx @wordpress/create-block my-block --namespace my-plugin

# Create with specific template
npx @wordpress/create-block my-block --template @wordpress/create-block-interactive-template

# Create dynamic block
npx @wordpress/create-block my-block --variant dynamic
```

### Generated Structure

```
my-block/
├── my-block.php           # Plugin file
├── package.json           # NPM dependencies
├── src/
│   ├── block.json         # Block metadata
│   ├── edit.js            # Editor component
│   ├── save.js            # Frontend save
│   ├── index.js           # Block registration
│   ├── editor.scss        # Editor styles
│   └── style.scss         # Frontend styles
├── build/                 # Compiled assets
└── readme.txt
```

### package.json Scripts

```json
{
    "name": "my-block",
    "version": "1.0.0",
    "scripts": {
        "build": "wp-scripts build",
        "start": "wp-scripts start",
        "format": "wp-scripts format",
        "lint:js": "wp-scripts lint-js",
        "lint:css": "wp-scripts lint-style",
        "packages-update": "wp-scripts packages-update"
    },
    "devDependencies": {
        "@wordpress/scripts": "^27.0.0"
    }
}
```

---

## Block Registration

### block.json (WordPress 6.4+)

```json
{
    "$schema": "https://schemas.wp.org/trunk/block.json",
    "apiVersion": 3,
    "name": "my-plugin/my-block",
    "version": "1.0.0",
    "title": "My Block",
    "category": "widgets",
    "icon": "smiley",
    "description": "A custom block for displaying content.",
    "keywords": ["custom", "content", "block"],
    "supports": {
        "html": false,
        "align": ["wide", "full"],
        "anchor": true,
        "color": {
            "background": true,
            "text": true,
            "link": true,
            "gradients": true
        },
        "spacing": {
            "margin": true,
            "padding": true,
            "blockGap": true
        },
        "typography": {
            "fontSize": true,
            "lineHeight": true
        },
        "__experimentalBorder": {
            "color": true,
            "radius": true,
            "style": true,
            "width": true
        }
    },
    "attributes": {
        "content": {
            "type": "string",
            "source": "html",
            "selector": "p"
        },
        "alignment": {
            "type": "string",
            "default": "left"
        },
        "showBorder": {
            "type": "boolean",
            "default": false
        },
        "items": {
            "type": "array",
            "default": []
        },
        "selectedPostId": {
            "type": "number"
        }
    },
    "example": {
        "attributes": {
            "content": "Example content for the block preview."
        }
    },
    "textdomain": "my-plugin",
    "editorScript": "file:./index.js",
    "editorStyle": "file:./index.css",
    "style": "file:./style-index.css",
    "viewScript": "file:./view.js",
    "render": "file:./render.php"
}
```

### PHP Registration

```php
<?php
declare(strict_types=1);

/**
 * Register all blocks
 */
function my_plugin_register_blocks(): void {
    // Auto-register from block.json
    register_block_type(__DIR__ . '/build/my-block');

    // Or with additional arguments
    register_block_type(__DIR__ . '/build/another-block', [
        'render_callback' => 'my_plugin_render_another_block',
    ]);
}
add_action('init', 'my_plugin_register_blocks');

/**
 * Register block category
 */
function my_plugin_block_categories(array $categories): array {
    return array_merge(
        [
            [
                'slug'  => 'my-plugin-blocks',
                'title' => __('My Plugin Blocks', 'my-plugin'),
                'icon'  => 'wordpress',
            ],
        ],
        $categories
    );
}
add_filter('block_categories_all', 'my_plugin_block_categories');
```

---

## Static Block Development

### index.js (Entry Point)

```javascript
/**
 * WordPress dependencies
 */
import { registerBlockType } from '@wordpress/blocks';

/**
 * Internal dependencies
 */
import Edit from './edit';
import save from './save';
import metadata from './block.json';
import './style.scss';

/**
 * Register block
 */
registerBlockType(metadata.name, {
    edit: Edit,
    save,
});
```

### edit.js (Editor Component)

```javascript
/**
 * WordPress dependencies
 */
import { __ } from '@wordpress/i18n';
import {
    useBlockProps,
    RichText,
    InspectorControls,
    BlockControls,
    AlignmentToolbar,
    MediaUpload,
    MediaUploadCheck,
} from '@wordpress/block-editor';
import {
    PanelBody,
    ToggleControl,
    TextControl,
    SelectControl,
    RangeControl,
    Button,
} from '@wordpress/components';
import './editor.scss';

/**
 * Edit component
 *
 * @param {Object} props               Block props
 * @param {Object} props.attributes    Block attributes
 * @param {Function} props.setAttributes Function to update attributes
 * @return {JSX.Element} Block edit component
 */
export default function Edit({ attributes, setAttributes }) {
    const { content, alignment, showBorder, imageId, imageUrl, columns } = attributes;

    const blockProps = useBlockProps({
        className: `align-${alignment}${showBorder ? ' has-border' : ''}`,
    });

    const onSelectImage = (media) => {
        setAttributes({
            imageId: media.id,
            imageUrl: media.url,
        });
    };

    const onRemoveImage = () => {
        setAttributes({
            imageId: undefined,
            imageUrl: undefined,
        });
    };

    return (
        <>
            <BlockControls>
                <AlignmentToolbar
                    value={alignment}
                    onChange={(newAlignment) =>
                        setAttributes({ alignment: newAlignment })
                    }
                />
            </BlockControls>

            <InspectorControls>
                <PanelBody title={__('Settings', 'my-plugin')} initialOpen={true}>
                    <ToggleControl
                        label={__('Show Border', 'my-plugin')}
                        checked={showBorder}
                        onChange={(value) => setAttributes({ showBorder: value })}
                    />

                    <RangeControl
                        label={__('Columns', 'my-plugin')}
                        value={columns}
                        onChange={(value) => setAttributes({ columns: value })}
                        min={1}
                        max={6}
                    />

                    <SelectControl
                        label={__('Layout', 'my-plugin')}
                        value={attributes.layout}
                        options={[
                            { label: __('Default', 'my-plugin'), value: 'default' },
                            { label: __('Card', 'my-plugin'), value: 'card' },
                            { label: __('Minimal', 'my-plugin'), value: 'minimal' },
                        ]}
                        onChange={(value) => setAttributes({ layout: value })}
                    />
                </PanelBody>

                <PanelBody title={__('Image', 'my-plugin')} initialOpen={false}>
                    <MediaUploadCheck>
                        <MediaUpload
                            onSelect={onSelectImage}
                            allowedTypes={['image']}
                            value={imageId}
                            render={({ open }) => (
                                <div className="editor-post-featured-image">
                                    {imageUrl ? (
                                        <>
                                            <img src={imageUrl} alt="" />
                                            <Button
                                                onClick={onRemoveImage}
                                                isDestructive
                                            >
                                                {__('Remove Image', 'my-plugin')}
                                            </Button>
                                        </>
                                    ) : (
                                        <Button onClick={open} variant="secondary">
                                            {__('Select Image', 'my-plugin')}
                                        </Button>
                                    )}
                                </div>
                            )}
                        />
                    </MediaUploadCheck>
                </PanelBody>
            </InspectorControls>

            <div {...blockProps}>
                {imageUrl && (
                    <img src={imageUrl} alt="" className="block-image" />
                )}
                <RichText
                    tagName="p"
                    value={content}
                    onChange={(value) => setAttributes({ content: value })}
                    placeholder={__('Enter content...', 'my-plugin')}
                    allowedFormats={['core/bold', 'core/italic', 'core/link']}
                />
            </div>
        </>
    );
}
```

### save.js (Frontend Output)

```javascript
/**
 * WordPress dependencies
 */
import { useBlockProps, RichText } from '@wordpress/block-editor';

/**
 * Save component
 *
 * @param {Object} props            Block props
 * @param {Object} props.attributes Block attributes
 * @return {JSX.Element} Block save component
 */
export default function save({ attributes }) {
    const { content, alignment, showBorder, imageUrl } = attributes;

    const blockProps = useBlockProps.save({
        className: `align-${alignment}${showBorder ? ' has-border' : ''}`,
    });

    return (
        <div {...blockProps}>
            {imageUrl && (
                <img src={imageUrl} alt="" className="block-image" />
            )}
            <RichText.Content tagName="p" value={content} />
        </div>
    );
}
```

---

## Dynamic Block Development

Dynamic blocks render on the server, useful for content that changes or requires PHP logic.

### block.json for Dynamic Block

```json
{
    "$schema": "https://schemas.wp.org/trunk/block.json",
    "apiVersion": 3,
    "name": "my-plugin/recent-posts",
    "title": "Recent Posts",
    "category": "widgets",
    "icon": "list-view",
    "description": "Display recent posts with customizable options.",
    "supports": {
        "html": false,
        "align": ["wide", "full"]
    },
    "attributes": {
        "numberOfPosts": {
            "type": "number",
            "default": 5
        },
        "postType": {
            "type": "string",
            "default": "post"
        },
        "showExcerpt": {
            "type": "boolean",
            "default": true
        },
        "showFeaturedImage": {
            "type": "boolean",
            "default": true
        },
        "categories": {
            "type": "array",
            "default": []
        }
    },
    "textdomain": "my-plugin",
    "editorScript": "file:./index.js",
    "style": "file:./style-index.css",
    "render": "file:./render.php"
}
```

### edit.js for Dynamic Block

```javascript
/**
 * WordPress dependencies
 */
import { __ } from '@wordpress/i18n';
import { useBlockProps, InspectorControls } from '@wordpress/block-editor';
import {
    PanelBody,
    RangeControl,
    ToggleControl,
    SelectControl,
    Spinner,
} from '@wordpress/components';
import { useSelect } from '@wordpress/data';
import { store as coreStore } from '@wordpress/core-data';
import ServerSideRender from '@wordpress/server-side-render';

/**
 * Edit component for dynamic block
 */
export default function Edit({ attributes, setAttributes }) {
    const { numberOfPosts, postType, showExcerpt, showFeaturedImage } = attributes;

    const blockProps = useBlockProps();

    // Fetch post types for select
    const postTypes = useSelect((select) => {
        const { getPostTypes } = select(coreStore);
        const types = getPostTypes({ per_page: -1 });
        return types?.filter((type) => type.viewable && type.rest_base) || [];
    }, []);

    // Fetch categories
    const categories = useSelect((select) => {
        const { getEntityRecords } = select(coreStore);
        return getEntityRecords('taxonomy', 'category', { per_page: -1 }) || [];
    }, []);

    const postTypeOptions = postTypes.map((type) => ({
        label: type.labels.singular_name,
        value: type.slug,
    }));

    return (
        <>
            <InspectorControls>
                <PanelBody title={__('Settings', 'my-plugin')}>
                    <RangeControl
                        label={__('Number of Posts', 'my-plugin')}
                        value={numberOfPosts}
                        onChange={(value) => setAttributes({ numberOfPosts: value })}
                        min={1}
                        max={20}
                    />

                    {postTypeOptions.length > 0 && (
                        <SelectControl
                            label={__('Post Type', 'my-plugin')}
                            value={postType}
                            options={postTypeOptions}
                            onChange={(value) => setAttributes({ postType: value })}
                        />
                    )}

                    <ToggleControl
                        label={__('Show Excerpt', 'my-plugin')}
                        checked={showExcerpt}
                        onChange={(value) => setAttributes({ showExcerpt: value })}
                    />

                    <ToggleControl
                        label={__('Show Featured Image', 'my-plugin')}
                        checked={showFeaturedImage}
                        onChange={(value) => setAttributes({ showFeaturedImage: value })}
                    />
                </PanelBody>
            </InspectorControls>

            <div {...blockProps}>
                <ServerSideRender
                    block="my-plugin/recent-posts"
                    attributes={attributes}
                    LoadingResponsePlaceholder={() => (
                        <div className="loading-placeholder">
                            <Spinner />
                            <p>{__('Loading...', 'my-plugin')}</p>
                        </div>
                    )}
                    EmptyResponsePlaceholder={() => (
                        <p>{__('No posts found.', 'my-plugin')}</p>
                    )}
                />
            </div>
        </>
    );
}
```

### render.php (Server-Side Render)

```php
<?php
/**
 * Server-side rendering for Recent Posts block
 *
 * @var array    $attributes Block attributes
 * @var string   $content    Block content
 * @var WP_Block $block      Block instance
 */

declare(strict_types=1);

defined('ABSPATH') || exit;

$number_of_posts = absint($attributes['numberOfPosts'] ?? 5);
$post_type = sanitize_key($attributes['postType'] ?? 'post');
$show_excerpt = (bool) ($attributes['showExcerpt'] ?? true);
$show_featured_image = (bool) ($attributes['showFeaturedImage'] ?? true);
$categories = array_map('absint', $attributes['categories'] ?? []);

$query_args = [
    'post_type'      => $post_type,
    'posts_per_page' => $number_of_posts,
    'post_status'    => 'publish',
    'orderby'        => 'date',
    'order'          => 'DESC',
];

if (!empty($categories) && $post_type === 'post') {
    $query_args['category__in'] = $categories;
}

$posts_query = new WP_Query($query_args);

$wrapper_attributes = get_block_wrapper_attributes([
    'class' => 'recent-posts-block',
]);
?>

<div <?php echo $wrapper_attributes; ?>>
    <?php if ($posts_query->have_posts()) : ?>
        <ul class="recent-posts-list">
            <?php while ($posts_query->have_posts()) : $posts_query->the_post(); ?>
                <li class="recent-posts-item">
                    <?php if ($show_featured_image && has_post_thumbnail()) : ?>
                        <div class="post-thumbnail">
                            <a href="<?php the_permalink(); ?>">
                                <?php the_post_thumbnail('thumbnail'); ?>
                            </a>
                        </div>
                    <?php endif; ?>

                    <div class="post-content">
                        <h3 class="post-title">
                            <a href="<?php the_permalink(); ?>">
                                <?php the_title(); ?>
                            </a>
                        </h3>

                        <time class="post-date" datetime="<?php echo esc_attr(get_the_date('c')); ?>">
                            <?php echo esc_html(get_the_date()); ?>
                        </time>

                        <?php if ($show_excerpt) : ?>
                            <div class="post-excerpt">
                                <?php the_excerpt(); ?>
                            </div>
                        <?php endif; ?>
                    </div>
                </li>
            <?php endwhile; ?>
        </ul>
    <?php else : ?>
        <p class="no-posts"><?php esc_html_e('No posts found.', 'my-plugin'); ?></p>
    <?php endif; ?>

    <?php wp_reset_postdata(); ?>
</div>
```

---

## Block Patterns

### Registering Patterns in PHP

```php
<?php
/**
 * Register block patterns
 */
function my_plugin_register_patterns(): void {
    // Register pattern category
    register_block_pattern_category('my-plugin-patterns', [
        'label' => __('My Plugin Patterns', 'my-plugin'),
    ]);

    // Register pattern
    register_block_pattern('my-plugin/hero-section', [
        'title'       => __('Hero Section', 'my-plugin'),
        'description' => __('A full-width hero section with heading and CTA.', 'my-plugin'),
        'categories'  => ['my-plugin-patterns', 'featured'],
        'keywords'    => ['hero', 'banner', 'cta'],
        'blockTypes'  => ['core/template-part/header'],
        'content'     => '<!-- wp:cover {"dimRatio":60,"overlayColor":"black","align":"full"} -->
            <div class="wp-block-cover alignfull">
                <span class="wp-block-cover__background has-black-background-color has-background-dim-60"></span>
                <div class="wp-block-cover__inner-container">
                    <!-- wp:heading {"textAlign":"center","level":1} -->
                    <h1 class="wp-block-heading has-text-align-center">' . esc_html__('Welcome', 'my-plugin') . '</h1>
                    <!-- /wp:heading -->
                    <!-- wp:buttons {"layout":{"type":"flex","justifyContent":"center"}} -->
                    <div class="wp-block-buttons">
                        <!-- wp:button -->
                        <div class="wp-block-button"><a class="wp-block-button__link wp-element-button">' . esc_html__('Get Started', 'my-plugin') . '</a></div>
                        <!-- /wp:button -->
                    </div>
                    <!-- /wp:buttons -->
                </div>
            </div>
            <!-- /wp:cover -->',
    ]);
}
add_action('init', 'my_plugin_register_patterns');
```

### Pattern File (patterns/feature-grid.php)

```php
<?php
/**
 * Title: Feature Grid
 * Slug: my-plugin/feature-grid
 * Categories: my-plugin-patterns
 * Keywords: features, grid, cards
 * Block Types: core/group
 * Viewport Width: 1200
 */

declare(strict_types=1);

defined('ABSPATH') || exit;
?>

<!-- wp:group {"align":"wide","layout":{"type":"constrained"}} -->
<div class="wp-block-group alignwide">
    <!-- wp:heading {"textAlign":"center"} -->
    <h2 class="wp-block-heading has-text-align-center"><?php esc_html_e('Our Features', 'my-plugin'); ?></h2>
    <!-- /wp:heading -->

    <!-- wp:columns {"align":"wide"} -->
    <div class="wp-block-columns alignwide">
        <!-- wp:column -->
        <div class="wp-block-column">
            <!-- wp:group {"style":{"spacing":{"padding":{"top":"var:preset|spacing|m","right":"var:preset|spacing|m","bottom":"var:preset|spacing|m","left":"var:preset|spacing|m"}},"border":{"radius":"8px"}},"backgroundColor":"base-alt"} -->
            <div class="wp-block-group has-base-alt-background-color has-background">
                <!-- wp:image {"width":"64px","sizeSlug":"full"} -->
                <figure class="wp-block-image size-full is-resized" style="width:64px"><img src="<?php echo esc_url(get_template_directory_uri()); ?>/assets/images/icon-feature-1.svg" alt="" /></figure>
                <!-- /wp:image -->
                <!-- wp:heading {"level":3} -->
                <h3 class="wp-block-heading"><?php esc_html_e('Feature One', 'my-plugin'); ?></h3>
                <!-- /wp:heading -->
                <!-- wp:paragraph -->
                <p><?php esc_html_e('Description of the first feature goes here.', 'my-plugin'); ?></p>
                <!-- /wp:paragraph -->
            </div>
            <!-- /wp:group -->
        </div>
        <!-- /wp:column -->

        <!-- wp:column -->
        <div class="wp-block-column">
            <!-- wp:group {"style":{"spacing":{"padding":{"top":"var:preset|spacing|m","right":"var:preset|spacing|m","bottom":"var:preset|spacing|m","left":"var:preset|spacing|m"}},"border":{"radius":"8px"}},"backgroundColor":"base-alt"} -->
            <div class="wp-block-group has-base-alt-background-color has-background">
                <!-- wp:image {"width":"64px","sizeSlug":"full"} -->
                <figure class="wp-block-image size-full is-resized" style="width:64px"><img src="<?php echo esc_url(get_template_directory_uri()); ?>/assets/images/icon-feature-2.svg" alt="" /></figure>
                <!-- /wp:image -->
                <!-- wp:heading {"level":3} -->
                <h3 class="wp-block-heading"><?php esc_html_e('Feature Two', 'my-plugin'); ?></h3>
                <!-- /wp:heading -->
                <!-- wp:paragraph -->
                <p><?php esc_html_e('Description of the second feature goes here.', 'my-plugin'); ?></p>
                <!-- /wp:paragraph -->
            </div>
            <!-- /wp:group -->
        </div>
        <!-- /wp:column -->

        <!-- wp:column -->
        <div class="wp-block-column">
            <!-- wp:group {"style":{"spacing":{"padding":{"top":"var:preset|spacing|m","right":"var:preset|spacing|m","bottom":"var:preset|spacing|m","left":"var:preset|spacing|m"}},"border":{"radius":"8px"}},"backgroundColor":"base-alt"} -->
            <div class="wp-block-group has-base-alt-background-color has-background">
                <!-- wp:image {"width":"64px","sizeSlug":"full"} -->
                <figure class="wp-block-image size-full is-resized" style="width:64px"><img src="<?php echo esc_url(get_template_directory_uri()); ?>/assets/images/icon-feature-3.svg" alt="" /></figure>
                <!-- /wp:image -->
                <!-- wp:heading {"level":3} -->
                <h3 class="wp-block-heading"><?php esc_html_e('Feature Three', 'my-plugin'); ?></h3>
                <!-- /wp:heading -->
                <!-- wp:paragraph -->
                <p><?php esc_html_e('Description of the third feature goes here.', 'my-plugin'); ?></p>
                <!-- /wp:paragraph -->
            </div>
            <!-- /wp:group -->
        </div>
        <!-- /wp:column -->
    </div>
    <!-- /wp:columns -->
</div>
<!-- /wp:group -->
```

---

## Interactivity API (WordPress 6.5+)

For client-side interactivity without custom JavaScript build processes.

### Interactive Block Example

```json
{
    "$schema": "https://schemas.wp.org/trunk/block.json",
    "apiVersion": 3,
    "name": "my-plugin/counter",
    "title": "Interactive Counter",
    "supports": {
        "interactivity": true
    },
    "textdomain": "my-plugin",
    "editorScript": "file:./index.js",
    "viewScriptModule": "file:./view.js",
    "render": "file:./render.php"
}
```

### render.php with Interactivity

```php
<?php
/**
 * Interactive counter block render
 */

declare(strict_types=1);

$initial_count = absint($attributes['initialCount'] ?? 0);

wp_interactivity_state('my-plugin/counter', [
    'count' => $initial_count,
]);
?>

<div
    <?php echo get_block_wrapper_attributes(); ?>
    data-wp-interactive="my-plugin/counter"
>
    <button
        data-wp-on--click="actions.decrement"
        data-wp-bind--disabled="!state.canDecrement"
    >
        -
    </button>

    <span data-wp-text="state.count"></span>

    <button data-wp-on--click="actions.increment">
        +
    </button>
</div>
```

### view.js (Interactivity Store)

```javascript
/**
 * WordPress dependencies
 */
import { store, getContext } from '@wordpress/interactivity';

store('my-plugin/counter', {
    state: {
        get canDecrement() {
            const { count } = store('my-plugin/counter').state;
            return count > 0;
        },
    },
    actions: {
        increment() {
            const state = store('my-plugin/counter').state;
            state.count++;
        },
        decrement() {
            const state = store('my-plugin/counter').state;
            if (state.count > 0) {
                state.count--;
            }
        },
    },
});
```

---

## Best Practices

### Do

- Use `block.json` for all block metadata (API version 3)
- Leverage `useBlockProps` for proper block wrapper handling
- Use `InspectorControls` for sidebar settings
- Implement `example` in block.json for previews
- Use `ServerSideRender` for dynamic block previews
- Follow WordPress Coding Standards for PHP render callbacks
- Use CSS custom properties from theme.json
- Test blocks in isolation and within posts
- Support align wide/full when appropriate
- Use the Interactivity API for simple client-side logic

### Do Not

- Skip the `$schema` property in block.json
- Use deprecated block API versions (use apiVersion 3)
- Forget to escape output in render.php
- Hardcode styles (use theme.json presets)
- Create unnecessary server requests in edit components
- Ignore block validation warnings
- Skip internationalization for text strings
- Bundle React/WordPress packages (use externals)
