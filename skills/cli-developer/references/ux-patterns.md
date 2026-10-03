# CLI UX Patterns

## Progress Indicators

### When to Use What

```
Determinate (known total):
  [████████████░░░░░░░░] 60% (3/5 files)
  Use: File operations, downloads, batch processing

Indeterminate (unknown duration):
  ⠋ Loading...
  Use: API calls, database queries, waiting for external services

Multi-step:
  ✓ Dependencies installed
  ⠋ Building application...
  ⏳ Running tests...
  Use: Multi-phase operations (build, deploy, etc.)
```

### Progress Bar Best Practices

```
Good:
[████████████░░░░░░░░] 60% | 120/200 MB | 2.4 MB/s | ETA: 33s
↑ Visual     ↑ Percent  ↑ Progress  ↑ Rate     ↑ Time

Components:
- Visual bar (20-40 chars)
- Percentage (when known)
- Current/total (with units)
- Speed/rate (when applicable)
- ETA (estimated time remaining)

Bad:
Processing... (no feedback)
60% (no context)
[████████████████████████████████████████] (too wide)
```

### Spinner Styles

```
⠋ ⠙ ⠹ ⠸ ⠼ ⠴ ⠦ ⠧ ⠇ ⠏   Dots (elegant, low-key)
⣾ ⣽ ⣻ ⢿ ⡿ ⣟ ⣯ ⣷        Blocks (bold, attention)
◐ ◓ ◑ ◒                  Circle (classic)
▖ ▘ ▝ ▗                  Corners (minimal)
⠁ ⠂ ⠄ ⡀ ⢀ ⠠ ⠐ ⠈        Line (subtle)

Choose based on:
- Terminal compatibility (stick to ASCII for Windows)
- Branding (match your tool's personality)
- Context (subtle for background, bold for main task)
```

## Color Usage

### Semantic Colors

```
Red:     Errors, failures, destructive actions
Yellow:  Warnings, deprecations, non-critical issues
Green:   Success, completion, positive feedback
Blue:    Information, hints, neutral messages
Cyan:    Commands, code, technical details
Magenta: Highlights, special items
Gray:    Less important, metadata, timestamps

Examples:
✓ Success: Deployment complete
✗ Error: File not found
⚠ Warning: Deprecated flag --old-flag
ℹ Info: Using cache from ~/.mycli/cache
```

### When to Disable Colors

```javascript
// Detect non-TTY output (piped to file, etc.)
const noColor = !process.stdout.isTTY ||
                process.env.NO_COLOR ||
                process.env.CI === 'true';

if (noColor) {
  // Disable colors
}

// Support NO_COLOR standard
// https://no-color.org/
```

### Color Accessibility

```
- Don't rely on color alone (use symbols too)
- Provide high contrast (test with various terminals)
- Support color blindness (red/green alternatives)

Good:
✓ Build successful (green)
✗ Build failed (red)
↑ Symbols work without color

Bad:
Success (only color, no symbol)
Failed (only color, no symbol)
```

## Help Text Design

### Command Help Structure

```
USAGE
  mycli <command> [options]

COMMANDS
  init         Initialize a new project
  deploy       Deploy to environment
  config       Manage configuration
  plugins      Manage plugins

OPTIONS
  -h, --help     Show help
  -v, --version  Show version
  --config FILE  Config file path

Run 'mycli <command> --help' for more information on a command.

EXAMPLES
  # Initialize a new project
  mycli init my-app

  # Deploy to production
  mycli deploy production --dry-run

Learn more: https://docs.mycli.dev
```

### Subcommand Help

```
USAGE
  mycli deploy <environment> [options]

ARGUMENTS
  environment    Target environment (required)
                 Values: development, staging, production

OPTIONS
  -c, --config <file>    Config file path
                         Default: ./mycli.config.yml

  -f, --force            Skip confirmation prompts
                         Use with caution in production

  -d, --dry-run          Preview changes without executing
                         Shows what would happen

  -v, --verbose          Show detailed output
                         Includes debug information

EXAMPLES
  # Deploy to production (with confirmation)
  mycli deploy production

  # Preview staging deployment
  mycli deploy staging --dry-run

  # Use custom config
  mycli deploy production --config ./prod.yml

  # Force deploy without prompts
  mycli deploy production --force

For more information, visit https://docs.mycli.dev/deploy
```

## Error Messages

### Good Error Messages

```
Pattern: [Context] → [Problem] → [Solution]

Example 1: File not found
✗ Error: Config file not found

Searched locations:
  • ./mycli.config.yml
  • ~/.config/mycli/config.yml
  • /etc/mycli/config.yml

Solutions:
  • Run 'mycli init' to create a config file
  • Use --config to specify a different location
  • Check file permissions

Example 2: Validation error
✗ Error: Invalid environment 'prod'

Expected one of:
  • development
  • staging
  • production

Did you mean 'production'?

Example 3: Permission error
✗ Error: Permission denied writing to /etc/mycli/config.yml

This operation requires elevated permissions.

Try:
  • Run with sudo: sudo mycli config set key value
  • Use user config: mycli config set --user key value
  • Check file permissions: ls -la /etc/mycli/config.yml
```

### Error Message Guidelines

```
DO:
✓ Be specific ("Port 3000 already in use" not "Port unavailable")
✓ Show context ("in file config.yml, line 42")
✓ Suggest solutions ("Try running 'mycli fix'")
✓ Use plain language ("File not found" not "ENOENT")

DON'T:
✗ Show stack traces to users (save for --debug)
✗ Use jargon ("EACCES: permission denied")
✗ Leave users stuck ("Invalid input" with no explanation)
✗ Be vague ("Something went wrong")
```

## Interactive Prompts

### Prompt Types

```
Text Input:
  Project name: my-awesome-app
  ↑ Clear label

Select (Single Choice):
  ? Select environment: (Use arrow keys)
  ❯ development
    staging
    production

Checkbox (Multiple Choice):
  ? Select features: (Press space to select, enter to confirm)
  ◉ TypeScript
  ◯ ESLint
  ◉ Prettier
  ◯ Jest

Confirmation:
  ? Deploy to production? (y/N)
  ↑ Default is No (safer)

Password:
  ? Enter password: ********
  ↑ Masked input
```

### Prompt Guidelines

```
DO:
✓ Show keyboard hints ("Use arrow keys", "Press space")
✓ Provide sensible defaults (pre-select common choices)
✓ Allow skipping with Ctrl+C
✓ Validate input immediately
✓ Show preview/summary before final action

DON'T:
✗ Require interaction in CI/CD environments
✗ Ask obvious questions (confirm every action)
✗ Hide what will happen next
✗ Make users repeat information
```

## Output Formatting

### Tables

```
Good:
┌─────────────┬──────────┬──────────┐
│ Environment │ Status   │ Updated  │
├─────────────┼──────────┼──────────┤
│ production  │ ✓ Active │ 2h ago   │
│ staging     │ ✓ Active │ 5m ago   │
│ development │ ✗ Down   │ 1d ago   │
└─────────────┴──────────┴──────────┘

Minimal (for scripting):
Environment  Status  Updated
production   Active  2h ago
staging      Active  5m ago
development  Down    1d ago

JSON (for programmatic use):
[
  {"env": "production", "status": "active", "updated": "2h ago"},
  {"env": "staging", "status": "active", "updated": "5m ago"}
]
```

### Lists

```
Bulleted:
Features:
  • TypeScript support
  • Hot reload
  • Auto-formatting

Numbered:
Steps to deploy:
  1. Build application
  2. Run tests
  3. Deploy to server
  4. Verify deployment

Tree:
my-app/
├── src/
│   ├── components/
│   └── utils/
├── tests/
└── package.json
```

## Status Messages

### Real-time Updates

```
Multi-step process:
✓ Dependencies installed (2.3s)
✓ Application built (8.1s)
⠋ Running tests... (current)
⏳ Deploying... (pending)
⏳ Verifying... (pending)

Updates:
⠋ Installing dependencies...
  → npm install
✓ Dependencies installed (2.3s)

⠋ Building application...
  → webpack build
✓ Application built (8.1s)
  → Output: dist/ (2.4 MB)
```

### Summary/Completion

```
✓ Deployment complete!

Summary:
  Environment:  production
  Version:      v1.2.3
  Duration:     2m 34s
  Deployed:     2023-12-14 10:30:45 UTC

Next steps:
  • View logs: mycli logs production
  • Monitor:   mycli status production
  • Rollback:  mycli rollback production

URL: https://app.example.com
```

## Debugging & Verbose Mode

```
Normal mode (default):
✓ Deployed to production (2m 34s)

Verbose mode (--verbose):
[10:30:12] Starting deployment...
[10:30:13] Loading config from ./mycli.config.yml
[10:30:14] Connecting to production server...
[10:30:15] Uploading files (124 files, 2.4 MB)...
[10:30:28] Running post-deploy hooks...
[10:32:46] ✓ Deployment complete

Debug mode (--debug):
[DEBUG] Config loaded: {env: 'production', ...}
[DEBUG] SSH connection established: user@host
[DEBUG] Executing: rsync -avz ./dist/ user@host:/var/www/
[DEBUG] Output: sending incremental file list...
[DEBUG] Exit code: 0
✓ Deployed to production (2m 34s)

Usage:
# Normal: concise output
mycli deploy production

# Verbose: detailed steps
mycli deploy production --verbose

# Debug: everything including internals
DEBUG=* mycli deploy production
```

## Man Page Format

```
NAME
    mycli-deploy - Deploy application to environment

SYNOPSIS
    mycli deploy <environment> [options]

DESCRIPTION
    Deploy your application to the specified environment.
    Supports development, staging, and production environments.

OPTIONS
    -c, --config <file>
        Path to configuration file
        Default: ./mycli.config.yml

    -f, --force
        Skip all confirmation prompts
        Use with caution in production

    -d, --dry-run
        Preview deployment without executing
        Shows what would be deployed

EXAMPLES
    Deploy to production:
        mycli deploy production

    Preview staging deployment:
        mycli deploy staging --dry-run

SEE ALSO
    mycli-init(1), mycli-config(1), mycli-rollback(1)
```
