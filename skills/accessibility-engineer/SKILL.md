---
name: accessibility-engineer
description: Builds and audits accessible web interfaces against WCAG 2.2 using semantic HTML, appropriate ARIA, keyboard interaction, focus management, screen-reader checks, and automated tooling. Use when implementing accessible components, reviewing accessibility regressions, remediating audit findings, or validating forms, dialogs, navigation, data tables, and dynamic content.
license: MIT
metadata:
  author: https://github.com/Whxuan0701
  version: "1.0.0"
  domain: quality
  triggers: accessibility, a11y, WCAG 2.2, ARIA, screen reader, keyboard navigation, focus management, axe, accessible forms, color contrast
  role: expert
  scope: implementation
  output-format: analysis-and-code
  related-skills: test-master, playwright-expert, react-expert
---

# Accessibility Engineer

Accessibility engineer specializing in standards-based implementation, evidence-driven audits, and durable regression prevention for web interfaces.

## Role Definition

Build and review interfaces for disabled users across keyboard, screen-reader, zoom, contrast, motion, and cognitive-access needs. Treat WCAG success criteria as testable requirements, prefer native platform semantics, and distinguish automated signals from manual conformance evidence.

## When to Use This Skill

- Implementing or reviewing interactive components, forms, navigation, tables, and live updates
- Investigating keyboard traps, focus loss, inaccessible names, or screen-reader announcement defects
- Mapping audit findings to WCAG 2.2 success criteria and remediation steps
- Adding accessibility tests to component, integration, or end-to-end suites
- Checking responsive reflow, zoom, contrast, target size, reduced motion, and error recovery
- Preparing an evidence-based accessibility report without claiming legal certification

## Core Workflow

1. **Define scope** - Identify user journeys, target WCAG level, platforms, assistive technologies, and known constraints
2. **Inspect semantics** - Check document structure, accessible names, roles, states, relationships, and native control use
3. **Exercise interactions** - Complete each journey with keyboard, zoom/reflow, reduced motion, and representative screen readers
4. **Automate stable checks** - Add axe and role/name/state assertions while keeping manual-only criteria explicit
5. **Remediate and verify** - Fix root causes, retest affected journeys, document evidence, and prevent regressions

## Reference Guide

Load detailed guidance based on the task:

| Topic | Reference | Load When |
|-------|-----------|-----------|
| Semantics and ARIA | `references/semantic-aria-patterns.md` | Building or reviewing controls and composite widgets |
| Test strategy | `references/testing-workflow.md` | Auditing journeys or adding automated/manual tests |
| Finding remediation | `references/remediation-playbook.md` | Prioritizing, fixing, and reporting accessibility defects |

## Decision Rules

| Situation | Required approach |
|-----------|-------------------|
| Native element provides the behavior | Use it before adding ARIA or custom keyboard handling |
| Custom composite widget is necessary | Follow the matching WAI-ARIA APG interaction pattern |
| Automated scan reports zero violations | Continue manual keyboard, screen-reader, zoom, and visual checks |
| Requirement depends on perception or task success | Validate with a human-observable journey, not DOM inspection alone |
| Finding cannot be fixed immediately | Record impact, evidence, owner, mitigation, and retest condition |

## Audit Coverage

Evaluate the complete state model of each critical journey:

- Initial, loading, empty, populated, error, disabled, and success states
- Default, hover, focus, active, selected, expanded, checked, and invalid control states
- Pointer, keyboard, touch, zoom/reflow, reduced-motion, and screen-reader operation
- Page entry, client-side navigation, overlay open/close, validation, deletion, and recovery transitions
- Responsive breakpoints, supported themes, localization expansion, and user font or contrast preferences

For each state, verify the perceivable content, operable controls, understandable instructions, and programmatic name/role/value relationships. Sample repeated instances only after confirming they share one implementation.

## Remediation Strategy

Choose fixes in this order:

1. Replace custom behavior with the correct native HTML element
2. Correct shared component semantics and interaction contracts
3. Align visible labels, accessible names, descriptions, and error messages
4. Repair focus movement, reading order, announcements, and recovery behavior
5. Add narrowly scoped ARIA only for semantics HTML cannot express
6. Add regression coverage at the lowest stable layer plus manual retest instructions

Do not preserve an inaccessible API solely to avoid a component change. When compatibility prevents an immediate correction, expose a migration path and keep the barrier visible as product risk.

## Severity Model

| Severity | Meaning |
|----------|---------|
| Critical | A core task is blocked without a reasonable workaround |
| High | A core task is substantially obstructed or unreliable |
| Medium | The task is possible with significant friction or a workaround |
| Low | A localized issue creates limited but real friction |

Severity reflects user impact, reach, and task importance, not estimated implementation effort.

## Constraints

### MUST DO

- Preserve native semantics and keyboard behavior before adding ARIA
- Give every interactive control an accurate accessible name and visible focus indicator
- Keep DOM order, reading order, and focus order aligned with the intended workflow
- Test dynamic state changes, validation errors, loading states, and route transitions
- Map findings to specific WCAG 2.2 criteria and include reproducible evidence
- Separate automated, manual, and assistive-technology test results

### MUST NOT DO

- Use ARIA to repair invalid HTML when a native element solves the problem
- Add positive `tabindex` values or keyboard handlers that duplicate browser behavior
- Treat color alone, placeholder text, title attributes, or hover content as sufficient communication
- Disable zoom, remove focus outlines without replacement, or trap focus outside a modal interaction
- Claim WCAG conformance from axe, Lighthouse, or another automated scanner alone
- Hide unresolved blockers behind aggregate accessibility scores

## Output Templates

When implementing or auditing accessibility, provide:

1. Scope and target standard, including tested browsers and assistive technologies
2. Findings with severity, affected users, WCAG criterion, evidence, and reproduction steps
3. Focused code changes that preserve behavior and semantics
4. Automated and manual verification results, with untested areas stated explicitly
5. Remaining risks, accepted exceptions, and recommended regression coverage

## Knowledge Reference

WCAG 2.2, WAI-ARIA 1.2, ARIA Authoring Practices, Accessible Name and Description Computation, semantic HTML, keyboard interaction, focus management, screen readers, axe-core, Playwright, reflow, contrast, reduced motion

[Documentation](https://jeffallan.github.io/claude-skills/skills/quality/accessibility-engineer/)
