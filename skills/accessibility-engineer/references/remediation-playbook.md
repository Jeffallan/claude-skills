# Accessibility Remediation Playbook

Use this reference to turn an accessibility finding into a prioritized, verifiable engineering change.

## Write an Actionable Finding

Each finding should answer six questions:

1. Which user journey and UI state is affected?
2. Which users or assistive technologies encounter the barrier?
3. What exact steps reproduce it?
4. What happens, and what should happen instead?
5. Which WCAG 2.2 success criterion or product requirement applies?
6. What evidence will prove the remediation works?

Example:

> **High - Shipping dialog traps screen-reader context outside the modal**
>
> On checkout, activate “Change shipping address” and navigate with VoiceOver. Background checkout controls remain in the virtual cursor order even though the dialog visually obscures them. Keyboard focus is contained, but the rest of the document is not made inert. This blocks reliable dialog navigation and conflicts with WCAG 2.2 SC 1.3.2 and 2.4.3. Apply native `<dialog>` behavior or make the background inert, then verify dialog name, reading order, `Escape`, and focus restoration in Safari/VoiceOver and Chrome/NVDA.

## Prioritize by User Impact

Use severity to communicate task impact, not implementation effort.

| Severity | User impact | Examples |
|----------|-------------|----------|
| Critical | Core task cannot be completed and no reasonable workaround exists | Keyboard trap, inaccessible authentication, destructive action without confirmation |
| High | Core task is substantially blocked or error-prone | Unlabeled required controls, unusable dialog, errors never announced |
| Medium | Task remains possible with significant friction or a workaround | Illogical focus order, insufficient non-text contrast, missing table headers |
| Low | Localized friction with limited task impact | Redundant announcement, minor heading inconsistency |

Also record reach, frequency, affected journey importance, and whether the barrier compounds with others. Do not downgrade a severe barrier because few users reported it.

## Fix Root Causes

Prefer changes at the shared component or design-system layer when the defect repeats. Common transformations:

| Symptom | Root-cause remediation |
|---------|------------------------|
| Clickable generic element | Replace with native button or link |
| Missing or unstable name | Add persistent visible label; use ARIA only when necessary |
| Focus disappears after render | Preserve node identity or explicitly restore focus after state transition |
| Custom widget keys differ by page | Centralize the APG interaction contract in one component |
| Error shown only by color | Add text, programmatic invalid state, and error association |
| Toast is never announced | Use an existing status region and concise message |
| Motion cannot be disabled | Add reduced-motion behavior that preserves state and meaning |
| Contrast varies by theme | Correct design tokens and test every component state |

Avoid patches that satisfy a scanner but leave the interaction broken, such as adding `role="button"` without keyboard activation or adding an empty `aria-label`.

## Safe Remediation Sequence

1. Add a focused automated regression test when the behavior is deterministic.
2. Reproduce the barrier with the original manual or assistive-technology steps.
3. Implement the smallest semantic or interaction change at the owning layer.
4. Run component tests and the affected end-to-end journey.
5. Repeat the original keyboard, screen-reader, zoom, or visual verification.
6. Scan nearby states for regressions introduced by the change.
7. Update the finding with evidence, environment, and remaining limitations.

Automation-first is not appropriate when the defect can only be judged through comprehension or assistive-technology output. In that case, document the manual regression procedure alongside the code change.

## Framework Considerations

### React and Component Frameworks

- Keep focusable element identity stable across state changes; avoid changing a button into an unrelated element after activation.
- Forward refs only when a parent truly owns focus movement.
- Generate deterministic IDs for label/control and description relationships.
- Put keyboard behavior in the reusable component, not in each consumer.
- Announce route and asynchronous state changes deliberately; rendering text does not guarantee announcement.

### Client-Side Routing

After navigation, update the document title and establish a predictable focus destination. Preserve user focus for inline state changes that do not create a new page context. Test browser back/forward navigation and deep links separately.

### Server Rendering and Hydration

Ensure IDs, accessible names, and landmark structure do not change during hydration. A transient duplicate ID or missing label can produce confusing accessibility-tree updates even if the final DOM looks correct.

## Exceptions and Third-Party Barriers

When a barrier cannot be fixed immediately:

- Record the inaccessible behavior and affected journey.
- Identify the owning dependency or vendor and version.
- Provide an accessible alternative or mitigation when possible.
- Set an owner and review date instead of an indefinite waiver.
- Define the exact condition that will trigger retesting.
- Keep the exception visible in release risk and procurement decisions.

Do not suppress automated rules globally for one third-party component. Scope exclusions to the smallest known node and retain manual coverage for the affected journey.

## Verification Checklist

Before closing a finding, confirm:

- The original reproduction no longer fails.
- The fix works with the input and assistive technology that exposed the barrier.
- Name, role, value, state, and relationships remain accurate.
- Focus order and reading order remain logical before, during, and after the interaction.
- Error, loading, empty, success, and disabled states were checked where relevant.
- Zoom, contrast, target size, motion, and responsive behavior were not regressed.
- Automated coverage asserts user-observable semantics rather than implementation details.
- The report names any browser/assistive-technology combinations not tested.

## Report Structure

Use a report that supports both triage and engineering:

```markdown
## Finding title

- Severity:
- Journey and state:
- Affected users:
- WCAG 2.2 criterion:
- Environment:
- Steps to reproduce:
- Expected behavior:
- Actual behavior:
- Evidence:
- Recommended remediation:
- Regression coverage:
- Retest result:
- Remaining risk:
```

Avoid vague conclusions such as “screen-reader friendly” or “passes accessibility.” Report the combinations and criteria actually evaluated.

## Definition of Done

A remediation is done when the user-observable barrier is removed, the original evidence is retested, relevant adjacent states are checked, and repeatable coverage exists at the appropriate automated or manual layer. A code merge or zero-violation scan alone is not completion.

## Authoritative References

- WCAG 2.2 quick reference: <https://www.w3.org/WAI/WCAG22/quickref/>
- Understanding WCAG 2.2: <https://www.w3.org/WAI/WCAG22/Understanding/>
- WAI planning and managing accessibility: <https://www.w3.org/WAI/planning-and-managing/>
