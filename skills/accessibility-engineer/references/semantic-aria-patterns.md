# Semantic HTML and ARIA Patterns

Use this reference while building or reviewing the accessibility tree and interaction contract of a web interface.

## Semantics First

Choose the element whose built-in behavior matches the user action.

| Need | Prefer | Avoid |
|------|--------|-------|
| Trigger an action | `<button type="button">` | Clickable `<div>` or `<span>` |
| Navigate to a resource | `<a href="...">` | Button with `location.href` |
| Choose one option | Radio inputs or native `<select>` | Unstructured clickable list |
| Toggle a boolean | Checkbox or button with `aria-pressed` | Visual switch with no state |
| Enter a labeled value | `<label>` associated with an input | Placeholder-only labeling |
| Group page navigation | `<nav aria-label="...">` | Generic container with links |
| Present tabular relationships | `<table>` with headers | CSS grid of generic elements |

Native controls provide focusability, activation keys, form behavior, states, and platform mappings. Add ARIA only when the semantic HTML vocabulary cannot express the required widget.

## Accessible Names

Every interactive element needs a stable name that describes its purpose. Prefer visible labels because they help sighted and screen-reader users share the same vocabulary.

```html
<label for="email">Work email</label>
<input id="email" name="email" type="email" autocomplete="email" />

<button type="button" aria-label="Close settings">
  <svg aria-hidden="true" focusable="false"><!-- icon --></svg>
</button>
```

Check these failure modes:

- The name is missing, duplicated, or changes unexpectedly between renders.
- `aria-label` replaces useful visible text with a different phrase.
- `aria-labelledby` references a missing or hidden-away label.
- An SVG title leaks into a parent control and creates a repeated name.
- Voice-control users cannot say the visible label because the accessible name differs.

Use `aria-describedby` for supplementary instructions or errors, not as a replacement for the label.

## Roles, States, and Properties

Expose state at the element that owns the interaction:

```html
<button
  type="button"
  aria-expanded="false"
  aria-controls="account-menu"
>
  Account
</button>
<ul id="account-menu" hidden>
  <li><a href="/profile">Profile</a></li>
</ul>
```

Update `aria-expanded` and `hidden` from the same source of truth. Do not announce a state that disagrees with the rendered interface.

Common state contracts:

| Widget | State or relationship |
|--------|-----------------------|
| Disclosure/menu trigger | `aria-expanded`, optionally `aria-controls` |
| Toggle button | `aria-pressed` |
| Current navigation item | `aria-current="page"` |
| Invalid field | `aria-invalid="true"` plus associated error text |
| Busy result region | `aria-busy="true"` while updating |
| Selected option/tab | `aria-selected` on the owned item |

Do not add redundant roles such as `role="button"` to `<button>`. Avoid `role="presentation"` or `aria-hidden="true"` on focusable content.

## Keyboard Interaction

Match native and APG conventions rather than inventing shortcuts.

| Pattern | Expected keys |
|---------|---------------|
| Button | `Enter`, `Space` activate |
| Link | `Enter` follows link |
| Dialog | Focus enters, `Tab` stays inside, `Escape` closes when allowed, focus returns |
| Tabs | Arrow keys move among tabs; activation follows the chosen model |
| Menu | Arrow keys navigate, `Enter`/`Space` activate, `Escape` closes |
| Listbox | Arrow keys move active option; selection behavior stays consistent |

Use roving `tabindex` or `aria-activedescendant` only for composite widgets that require one tab stop. Positive `tabindex` values create a second focus order and should not be used.

## Focus Management

Move focus only when the user's context changes and the new location is predictable:

- On dialog open, focus the least destructive meaningful control or dialog heading.
- On dialog close, return focus to the opener if it still exists.
- After client-side navigation, move focus to the main heading or main region when the framework does not do so.
- After deleting the focused item, move focus to the next logical item or a stable container.
- On validation failure, focus the error summary or first invalid field according to the form design.

Never repeatedly steal focus during typing, asynchronous refreshes, or background notifications.

## Dialog Example

```html
<button id="open-preferences" type="button">Preferences</button>

<dialog id="preferences" aria-labelledby="preferences-title">
  <h2 id="preferences-title">Preferences</h2>
  <form method="dialog">
    <label><input type="checkbox" name="compact" /> Compact layout</label>
    <button value="cancel">Cancel</button>
    <button value="save">Save</button>
  </form>
</dialog>
```

Use the native `<dialog>` API where support requirements permit, then verify initial focus, focus containment, `Escape`, backdrop behavior, and focus restoration. A role alone does not implement any of those behaviors.

## Forms and Errors

Group related controls with `<fieldset>` and `<legend>`. Mark required fields in text as well as programmatically. Keep instructions available after the user begins typing.

```html
<label for="password">Password</label>
<p id="password-help">At least 12 characters</p>
<input
  id="password"
  name="password"
  type="password"
  aria-describedby="password-help password-error"
  aria-invalid="true"
/>
<p id="password-error">Enter at least 12 characters.</p>
```

Errors must identify the field and explain how to recover. Do not rely on red borders, transient toasts, or a generic “invalid input” message.

## Dynamic Content

Use live regions sparingly. Prefer status semantics for polite, non-blocking updates and alert semantics only for urgent information.

```html
<p role="status" aria-live="polite">3 results loaded</p>
```

Insert or update text inside an existing live region. Avoid announcing entire containers, rapidly changing counters, or duplicated visual and live-region messages.

## Authoritative References

- WCAG 2.2: <https://www.w3.org/TR/WCAG22/>
- WAI-ARIA 1.2: <https://www.w3.org/TR/wai-aria-1.2/>
- ARIA Authoring Practices Guide: <https://www.w3.org/WAI/ARIA/apg/>
- Accessible Name and Description Computation: <https://www.w3.org/TR/accname-1.2/>
- HTML Accessibility API Mappings: <https://www.w3.org/TR/html-aam-1.0/>
