# Trim Recording Reference

Trims raw Playwright codegen output to a marker URL entry point, removing pre-feature navigation noise (login, dashboard clicks, etc.).

## Why Trim?

`npx playwright codegen` captures everything from the moment the browser opens — login flows, sidebar navigation, page loads that precede the actual feature under test. Running these raw recordings as tests creates:
- **Fragile tests** that break when unrelated UI changes
- **Slow tests** that repeat auth flows already handled by fixtures
- **Noisy tests** that obscure the actual feature coverage

Trimming isolates the feature-specific actions starting from the marker URL.

## Marker URL Convention

A marker URL is the route where the feature under test begins. Examples:
- `/invoices/export` — the export feature page
- `/settings/billing` — billing settings
- `/api/v2/docs` — API documentation page

Choose the most specific URL that marks the start of the user flow you want to test.

## Script Usage

```bash
npx ts-node scripts/trim-recording.ts <input> <marker-url> <output> [fixture-name]
```

**Arguments:**
- `input` — Path to raw codegen recording (`.spec.ts`)
- `marker-url` — URL path to trim to (e.g. `/invoices/export`)
- `output` — Path for trimmed output file
- `fixture-name` — Auth fixture name (default: `authenticatedPage`)

**Example:**
```bash
npx ts-node scripts/trim-recording.ts \
  recordings/raw-session-20240315.spec.ts \
  /invoices/export \
  e2e/invoice-export.spec.ts \
  authenticatedPage
```

## `trim-recording.ts` Script

```typescript
#!/usr/bin/env ts-node
/**
 * trim-recording.ts
 * Trims a raw Playwright codegen recording to a marker URL entry point.
 *
 * Usage:
 *   ts-node trim-recording.ts <input-file> <marker-url> <output-file> [fixture-name]
 *
 * Example:
 *   ts-node trim-recording.ts recordings/raw.spec.ts /invoices/export e2e/invoice-export.spec.ts authenticatedPage
 */
import * as fs from 'fs';
import * as path from 'path';

const [inputFile, markerUrl, outputFile, fixtureName = 'authenticatedPage'] = process.argv.slice(2);

if (!inputFile || !markerUrl || !outputFile) {
  console.error('Usage: ts-node trim-recording.ts <input> <markerUrl> <output> [fixtureName]');
  console.error('');
  console.error('  input       Path to raw codegen recording (.spec.ts)');
  console.error('  markerUrl   URL path to trim to, e.g. /invoices/export');
  console.error('  output      Path for trimmed output file');
  console.error('  fixtureName Auth fixture name (default: authenticatedPage)');
  process.exit(1);
}

if (!fs.existsSync(inputFile)) {
  console.error(`Input file not found: ${inputFile}`);
  process.exit(1);
}

const raw = fs.readFileSync(inputFile, 'utf-8');
const lines = raw.split('\n');

// Find the line where the marker URL first appears in a goto() call
const markerIndex = lines.findIndex(line =>
  line.includes('page.goto(') && line.includes(markerUrl)
);

if (markerIndex === -1) {
  console.error(`Marker URL "${markerUrl}" not found in any page.goto() call.`);
  console.error('');
  console.error('URLs found in recording:');
  lines
    .filter(l => l.includes('page.goto('))
    .forEach(l => console.error(' ', l.trim()));
  process.exit(1);
}

// Extract imports from top of file
const imports = lines.filter(line =>
  line.startsWith('import') || line.startsWith('const {')
);

// Everything from the marker line down becomes the test body
const body = lines.slice(markerIndex);

// Derive a test name from the output filename
const testName = path.basename(outputFile, '.spec.ts')
  .replace(/-/g, ' ')
  .replace(/\b\w/g, c => c.toUpperCase());

// Build output
const output = [
  imports.join('\n'),
  '',
  `test('${testName}', async ({ ${fixtureName}: page }) => {`,
  body.join('\n'),
].join('\n').trimEnd();

// Ensure output directory exists
const outputDir = path.dirname(outputFile);
if (!fs.existsSync(outputDir)) {
  fs.mkdirSync(outputDir, { recursive: true });
}

fs.writeFileSync(outputFile, output + '\n');

const linesRemoved = markerIndex;
const linesKept = body.length;

console.log('');
console.log('Recording trimmed successfully');
console.log(`  Input:         ${inputFile}`);
console.log(`  Output:        ${outputFile}`);
console.log(`  Marker URL:    ${markerUrl} (line ${markerIndex + 1})`);
console.log(`  Auth fixture:  ${fixtureName}`);
console.log(`  Lines removed: ${linesRemoved} (pre-feature activity)`);
console.log(`  Lines kept:    ${linesKept}`);
console.log('');
console.log('Next steps:');
console.log('  1. Review output -- add assertions at key checkpoints');
console.log('  2. Harden any positional or CSS locators');
console.log('  3. Parameterize hardcoded dynamic values');
console.log('  4. Tag: @happy-path or @bug-repro');
```

## Example: Before and After

**Raw recording (input):**
```typescript
import { test, expect } from '@playwright/test';

test('test', async ({ page }) => {
  await page.goto('https://app.example.com/login');
  await page.getByLabel('Email').fill('user@example.com');
  await page.getByLabel('Password').fill('password123');
  await page.getByRole('button', { name: 'Sign in' }).click();
  await page.getByRole('link', { name: 'Invoices' }).click();
  await page.goto('https://app.example.com/invoices/export');
  await page.getByLabel('Date Range').fill('last-30-days');
  await page.getByRole('button', { name: 'Download' }).click();
});
```

**Trimmed output:**
```typescript
import { test, expect } from '@playwright/test';

test('Invoice Export', async ({ authenticatedPage: page }) => {
  await page.goto('https://app.example.com/invoices/export');
  await page.getByLabel('Date Range').fill('last-30-days');
  await page.getByRole('button', { name: 'Download' }).click();
});
```

Lines 3–8 (login + navigation) are removed. The auth fixture handles session setup.
