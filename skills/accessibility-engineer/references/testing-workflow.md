# Accessibility Testing Workflow

Use this reference to combine fast automation with the manual checks needed to evaluate real user journeys.

## Define the Test Matrix

Start from critical journeys, not pages in isolation. For each journey, record:

- Entry point and successful outcome
- Controls, validation, dialogs, route changes, and asynchronous updates involved
- Target WCAG level and product-specific accessibility requirements
- Browser, operating system, viewport, zoom level, and assistive technology
- Authentication, test data, locale, and feature flags

A practical minimum matrix for a web application includes keyboard-only use, 200% and 400% zoom/reflow, forced or high-contrast modes where supported, reduced motion, and at least one representative desktop screen reader. Product audience and support policy determine additional combinations.

## Automated Checks

Automate deterministic failures early:

- Missing names, invalid ARIA, duplicate IDs, and some structural relationships
- Color contrast where computed foreground/background values are available
- Role, name, state, and visibility contracts for interactive controls
- Focus movement and keyboard activation in stable component behaviors
- Page title, language, landmarks, headings, and form associations

Automation cannot reliably judge whether alternative text is meaningful, focus order makes sense, instructions are understandable, announcements are useful, or a task is operable with a screen reader.

## Playwright and axe Example

```typescript
import AxeBuilder from '@axe-core/playwright';
import { expect, test } from '@playwright/test';

test('checkout has no automatically detectable WCAG A/AA violations', async ({ page }) => {
  await page.goto('/checkout');
  await page.getByLabel('Email').fill('buyer@example.com');

  const results = await new AxeBuilder({ page })
    .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa'])
    .analyze();

  expect(results.violations).toEqual([]);
});

test('validation summary receives focus and links to the invalid field', async ({ page }) => {
  await page.goto('/checkout');
  await page.getByRole('button', { name: 'Place order' }).click();

  const summary = page.getByRole('alert', { name: 'There is a problem' });
  await expect(summary).toBeFocused();
  await summary.getByRole('link', { name: 'Enter your email' }).click();
  await expect(page.getByLabel('Email')).toBeFocused();
});
```

Scope axe scans to stable UI states. Scan initial, expanded, error, modal, and completion states rather than only the first render. Do not disable rules merely to make CI green; document a verified false positive with the narrowest exclusion and an owner.

## Role-Based Assertions

Prefer user-perceived roles and names over CSS selectors:

```typescript
const trigger = page.getByRole('button', { name: 'Shipping options' });
await expect(trigger).toHaveAttribute('aria-expanded', 'false');
await trigger.click();
await expect(trigger).toHaveAttribute('aria-expanded', 'true');
await expect(page.getByRole('region', { name: 'Shipping options' })).toBeVisible();
```

These assertions catch broken accessible names and states while remaining aligned with assistive technology. They do not prove the complete screen-reader experience.

## Keyboard-Only Pass

For each journey:

1. Reload and put the pointer aside.
2. Press `Tab` from the browser chrome into the page.
3. Confirm every operable element receives focus in a meaningful order.
4. Confirm focus is always visible and not hidden behind sticky content.
5. Activate controls using their expected keys.
6. Check composite widgets with their APG arrow-key behavior.
7. Open and close overlays; verify containment and restoration.
8. Complete errors and recovery without pointer input.
9. Confirm no keyboard trap exists, including embedded editors and third-party widgets.

Record the exact key sequence for defects. “Keyboard inaccessible” is not a reproducible finding.

## Screen-Reader Pass

Use the screen reader's browse/read mode and focus/forms mode. Verify:

- Page title, language, landmarks, and heading hierarchy orient the user.
- Links and controls have unique, purpose-matching names in context.
- Form fields announce label, role, value, required/invalid state, help, and error.
- Tables expose captions or labels, headers, and cell relationships.
- Expanded, selected, pressed, checked, busy, and current states remain accurate.
- Dialog names and initial focus make sense; closing restores context.
- Status updates are announced once, at the right priority, without interrupting work.
- Reading order matches the visual and task order.

Do not infer output from DOM attributes. Listen to the actual announcement because browser and accessibility API mappings affect the result.

## Zoom, Reflow, and Visual Checks

At relevant widths and zoom levels, verify that content reflows without two-dimensional scrolling except where inherently necessary, text does not clip, controls do not overlap, and functionality remains available. Check:

- 200% text resizing and 400% browser zoom/reflow
- Focus indicators against adjacent colors
- Text and non-text contrast in default, hover, focus, disabled, and error states
- Target size and spacing for pointer inputs
- Content revealed on hover or focus can be dismissed, hovered, and persisted as required
- Animations respect `prefers-reduced-motion` without removing essential information
- Orientation is not unnecessarily locked

## Test Evidence

For every executed test, capture:

| Field | Example |
|-------|---------|
| Journey | Submit checkout with missing email |
| Environment | macOS, Safari, VoiceOver, 1440x900 |
| Method | Keyboard and screen reader |
| Expected | Error summary receives focus and identifies email error |
| Actual | Focus remains on submit button; new error is not announced |
| Criterion | WCAG 2.2 SC 3.3.1 and 4.1.3 |
| Artifact | Video, screenshot, trace, or exact announcement |

Pass results also need enough evidence to be repeatable. State untested combinations rather than treating them as passes.

## CI Strategy

Run component-level semantic tests close to the code and a small critical-journey axe suite in CI. Keep broader assistive-technology testing in a documented manual cadence unless the chosen platform supports reliable automation. Track scanner version and browser updates so rule changes are visible rather than mistaken for product regressions.

Avoid a single global accessibility score as a gate. Gate on actionable violations and critical task regressions, while reporting manual coverage separately.

## Authoritative and Tool References

- WCAG evaluation overview: <https://www.w3.org/WAI/test-evaluate/>
- Understanding conformance: <https://www.w3.org/WAI/WCAG22/Understanding/conformance>
- axe-core rules: <https://github.com/dequelabs/axe-core>
- Playwright accessibility testing: <https://playwright.dev/docs/accessibility-testing>
