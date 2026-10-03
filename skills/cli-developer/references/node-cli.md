# Node.js CLI Development

## Commander.js (Recommended)

Modern, elegant CLI framework with TypeScript support.

```javascript
#!/usr/bin/env node
import { Command } from 'commander';
import { version } from './package.json';

const program = new Command();

program
  .name('mycli')
  .description('My awesome CLI tool')
  .version(version);

// Simple command
program
  .command('init')
  .description('Initialize a new project')
  .option('-t, --template <type>', 'Project template', 'default')
  .option('-f, --force', 'Overwrite existing files')
  .action(async (options) => {
    console.log(`Initializing with template: ${options.template}`);
  });

// Command with arguments
program
  .command('deploy <environment>')
  .description('Deploy to environment')
  .option('--dry-run', 'Preview without executing')
  .action(async (environment, options) => {
    if (options.dryRun) {
      console.log(`Would deploy to: ${environment}`);
    } else {
      await deploy(environment);
    }
  });

// Nested subcommands
const config = program.command('config').description('Manage configuration');

config
  .command('get <key>')
  .description('Get config value')
  .action((key) => console.log(getConfig(key)));

config
  .command('set <key> <value>')
  .description('Set config value')
  .action((key, value) => setConfig(key, value));

program.parse();
```

## Yargs (Alternative)

Powerful argument parsing with middleware support.

```javascript
#!/usr/bin/env node
import yargs from 'yargs';
import { hideBin } from 'yargs/helpers';

yargs(hideBin(process.argv))
  .command(
    'deploy <env>',
    'Deploy to environment',
    (yargs) => {
      return yargs
        .positional('env', {
          describe: 'Environment name',
          choices: ['dev', 'staging', 'prod'],
        })
        .option('force', {
          alias: 'f',
          type: 'boolean',
          description: 'Force deployment',
        });
    },
    async (argv) => {
      await deploy(argv.env, { force: argv.force });
    }
  )
  .middleware([(argv) => {
    // Validate before all commands
    if (!isConfigValid()) {
      throw new Error('Invalid config');
    }
  }])
  .demandCommand()
  .help()
  .parse();
```

## Interactive Prompts (Inquirer)

Beautiful interactive prompts for user input.

```javascript
import inquirer from 'inquirer';

// Text input
const { name } = await inquirer.prompt([
  {
    type: 'input',
    name: 'name',
    message: 'Project name:',
    default: 'my-project',
    validate: (input) => input.length > 0 || 'Name required',
  },
]);

// Select from list
const { environment } = await inquirer.prompt([
  {
    type: 'list',
    name: 'environment',
    message: 'Select environment:',
    choices: ['development', 'staging', 'production'],
    default: 'development',
  },
]);

// Checkbox (multi-select)
const { features } = await inquirer.prompt([
  {
    type: 'checkbox',
    name: 'features',
    message: 'Select features:',
    choices: [
      { name: 'TypeScript', checked: true },
      { name: 'ESLint', checked: true },
      { name: 'Prettier', checked: true },
      { name: 'Jest', checked: false },
    ],
  },
]);

// Confirmation
const { confirmed } = await inquirer.prompt([
  {
    type: 'confirm',
    name: 'confirmed',
    message: 'Deploy to production?',
    default: false,
  },
]);

// Password
const { password } = await inquirer.prompt([
  {
    type: 'password',
    name: 'password',
    message: 'Enter password:',
    mask: '*',
  },
]);
```

## Terminal Output (Chalk)

Colorful terminal output with proper TTY detection.

```javascript
import chalk from 'chalk';

// Basic colors
console.log(chalk.blue('Info: ') + 'Starting deployment...');
console.log(chalk.green('Success: ') + 'Deployment complete');
console.log(chalk.yellow('Warning: ') + 'Deprecated flag used');
console.log(chalk.red('Error: ') + 'Deployment failed');

// Styles
console.log(chalk.bold.underline('Important'));
console.log(chalk.dim('Less important'));

// Templates
const success = chalk.green.bold;
const error = chalk.red.bold;
console.log(success('✓') + ' Build successful');
console.log(error('✗') + ' Build failed');

// Disable colors for CI
const log = {
  info: (msg) => console.log(chalk.blue('ℹ'), msg),
  success: (msg) => console.log(chalk.green('✔'), msg),
  warn: (msg) => console.log(chalk.yellow('⚠'), msg),
  error: (msg) => console.log(chalk.red('✖'), msg),
};

// Auto-detects TTY and CI environments
```

## Progress Indicators (Ora)

Elegant terminal spinners and progress indicators.

```javascript
import ora from 'ora';

// Simple spinner
const spinner = ora('Loading...').start();
await doWork();
spinner.succeed('Done!');

// Update text
const spinner = ora('Starting...').start();
spinner.text = 'Processing...';
await process();
spinner.text = 'Finalizing...';
await finalize();
spinner.succeed('Complete!');

// Different states
spinner.start('Installing dependencies...');
// ... work
spinner.succeed('Dependencies installed');
// or
spinner.fail('Installation failed');
// or
spinner.warn('Some packages skipped');
// or
spinner.info('Using cached packages');

// Multiple spinners
const spinners = {
  api: ora('Deploying API...').start(),
  web: ora('Deploying web app...').start(),
  db: ora('Running migrations...').start(),
};

await Promise.all([
  deployApi().then(() => spinners.api.succeed()),
  deployWeb().then(() => spinners.web.succeed()),
  runMigrations().then(() => spinners.db.succeed()),
]);
```

## Progress Bars (cli-progress)

```javascript
import cliProgress from 'cli-progress';

// Single progress bar
const bar = new cliProgress.SingleBar({}, cliProgress.Presets.shades_classic);
bar.start(100, 0);

for (let i = 0; i <= 100; i++) {
  await processItem(i);
  bar.update(i);
}

bar.stop();

// Multi-progress
const multibar = new cliProgress.MultiBar({
  clearOnComplete: false,
  hideCursor: true,
});

const bar1 = multibar.create(100, 0, { task: 'API' });
const bar2 = multibar.create(100, 0, { task: 'Web' });

await Promise.all([
  processApi(bar1),
  processWeb(bar2),
]);

multibar.stop();
```

## File System Helpers

```javascript
import fs from 'fs-extra';
import { globby } from 'globby';
import path from 'path';

// Copy with template
await fs.copy('templates/app', targetDir, {
  filter: (src) => !src.includes('node_modules'),
});

// Read/write JSON
const config = await fs.readJson('config.json');
await fs.writeJson('output.json', data, { spaces: 2 });

// Ensure directory exists
await fs.ensureDir('dist/assets');

// Find files
const files = await globby(['src/**/*.ts', '!src/**/*.test.ts']);
```

## Error Handling

```javascript
import { Command } from 'commander';

program
  .command('deploy')
  .action(async () => {
    try {
      await deploy();
    } catch (error) {
      if (error.code === 'EACCES') {
        console.error(chalk.red('Permission denied'));
        console.error('Try running with sudo or check file permissions');
        process.exit(77);
      } else if (error.code === 'ENOENT') {
        console.error(chalk.red('File not found:'), error.path);
        process.exit(127);
      } else {
        console.error(chalk.red('Deployment failed:'), error.message);
        if (process.env.DEBUG) {
          console.error(error.stack);
        }
        process.exit(1);
      }
    }
  });

// Handle SIGINT (Ctrl+C)
process.on('SIGINT', () => {
  console.log('\nOperation cancelled');
  process.exit(130);
});
```

## Package.json Setup

```json
{
  "name": "mycli",
  "version": "1.0.0",
  "type": "module",
  "bin": {
    "mycli": "./bin/cli.js"
  },
  "files": [
    "bin/",
    "lib/",
    "templates/"
  ],
  "engines": {
    "node": ">=18.0.0"
  },
  "dependencies": {
    "commander": "^11.0.0",
    "inquirer": "^9.0.0",
    "chalk": "^5.0.0",
    "ora": "^7.0.0"
  }
}
```

## Testing CLIs

```javascript
import { execaCommand } from 'execa';
import { describe, it, expect } from 'vitest';

describe('mycli', () => {
  it('shows version', async () => {
    const { stdout } = await execaCommand('node bin/cli.js --version');
    expect(stdout).toMatch(/\d+\.\d+\.\d+/);
  });

  it('shows help', async () => {
    const { stdout } = await execaCommand('node bin/cli.js --help');
    expect(stdout).toContain('Usage:');
  });

  it('handles invalid command', async () => {
    await expect(
      execaCommand('node bin/cli.js invalid')
    ).rejects.toThrow();
  });
});
```
