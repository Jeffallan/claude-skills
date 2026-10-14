# Feature: Sidecar — product-decision and issue-tracker side agents

## Overview

A Claude Code mod (a hooks-module plugin) that runs two side agents alongside the main conversation, in the spirit of Anthropic's "by the way" plugin: things the main agent notices mid-turn but has no good place to put.

- **Decisions** — surfaces product decisions the main agent is making or papering over mid-turn, and lets the person answer in free text or escalate to a proper `AskUserQuestion` dialog.
- **Issues** — collects bug-shaped findings (failing output, "this doesn't work," TODOs the agent walked past) and lets the person tick the ones worth filing, then files them into the project's ticketing backend.

Both live in **one docked pane** on the right of a fullscreen terminal, with two tabs (`d` Decisions, `i` Issues). One mod, one pane: the engine's dock shows a single pane at a time with tabs when several are open, so stacking two panes is not available; a tab row inside one pane is the equivalent.

Filing goes through the v0.5.0 backend adapter (`.claude/workflow-config.json` → `ticketing: local | jira | github-issues`), so the mod inherits whatever backend the project already uses.

Written against the Claude Code function-hooks API as declared in this build's `claude-code.d.ts` (early access; the declaration file is the authority).

## Functional Requirements

### FR-001: Plugin shape

The mod shall be a function-hooks plugin:

```
mods/sidecar/
  .claude-plugin/plugin.json      # name, version, description, userConfig, types
  hooks/hooks.json                # { "modules": ["./register.tsx"] }
  hooks/register.tsx              # export const register: Register
  hooks/decisions.ts              # detector + handlers for the Decisions tab
  hooks/issues.ts                 # detector + handlers for the Issues tab
  hooks/filing.ts                 # ticketing backend adapters
  hooks/*.test.ts                 # claude plugin test
  types/index.d.ts                # PluginState contract
  README.md
```

The module runs in the plugin environment (no DOM, no Node); everything outside it is reached through `$`. Files the module imports use `import` declarations only (no dynamic `import()`).

### FR-002: One pane, two tabs

The mod shall own one pane, `id: "sidecar"`, opened with `$.ui.open({ id: "sidecar", title, columns })` and drawn by a `ui.render` hook on `{ component: "Pane", requestId: "sidecar" }`.

The tree shall be:

```
[ d: Decisions (2) ]  [ i: Issues (5) ]        ← tab row: two plain Buttons with hotkeys
───────────────────────────────────────────
<active tab body>
```

- Tab labels carry the count of open items on that tab so activity on the hidden tab is visible.
- Hotkeys are one lowercase letter each (`d`, `i`); the engine refuses anything else, so no space-bar binding.
- The active tab is `$.state` (`sidecar.activeTab`), not a module variable, so a hot reload keeps it.
- When a new item lands on the hidden tab, the pane switches to that tab and a toast says what arrived.
- The tree is sized to `e.props.bodyColumns`, never the viewport.

### FR-003: Pane placement and fallback

- The pane is opened unasked (from a detector, not a keypress), so the engine places it only at ≥144 terminal columns (≥110 once the person has opened `sidecar` by hand in any session and not closed it). Below that it waits undrawn and `$.ui.open` resolves `{ isPlaced: false }`.
- When `isPlaced` is false the mod shall fall back to `$.ui.toast` with the item's one-line summary and the hint `/sidecar` to open the pane.
- A `/sidecar` slash command (registered in `session.start`) opens the pane with `focus: true`. Because that open answers the person's input it is placed at any width — inline above the prompt on a narrow terminal.
- The pane shall not set `holdToasts` (it stays open; that flag is for dialogs).

### FR-004: Decisions — detection

On each model request of a turn the mod shall look for product decisions the main agent is making implicitly.

- Hook: `turn.step` (async generator; `yield* next(e)` forwards the stream and evaluates to the step's result). Run detection on the result's assistant text after the stream settles; never block the stream.
- Gate: `$.model.classify(text, ["product-decision", "none"])`. Only on `"product-decision"` proceed.
- Extract: `$.model.fork({ prompt })` — one tool-less question over the session's own transcript as last sent, served from the prompt cache, so the extractor sees full context at near-zero cost. The prompt asks for a JSON list of `{ question, context, options?, default? }` where `default` is what the agent is about to assume.
- Dedupe: fingerprint = normalized `question`; a fingerprint already in `sidecar.decisions` (open or answered) is dropped. Fingerprints of answered decisions also persist in `$.store` keyed by project root so the same question is not re-raised next session.
- Threshold: a `userConfig` field `decisionSensitivity: "low" | "medium" | "high"` maps to how aggressive the classify prompt is. Default `medium`.
- Mute: `sidecar.muted.decisions` boolean in `$.state`, toggled from the pane; while muted, detection does not run.

### FR-005: Decisions — UI and answers

Each open decision is a card:

```
Which auth provider for the YMCA tenant?            ← question
Agent is assuming: Firebase, matching Coach Command ← default, dim
[ Input: type an answer… ]            (Enter: send)
[ a: Ask me properly ]  [ k: Keep default ]  [ x: Dismiss ]
```

- **Free-text answer** — `Input` with `onSubmit`. The answer is written into the conversation with `$.session.append({ message: { type: "user", content: [{ type: "text", text }] } })`: a meta user row the model reads on its next step without starting a turn. If the session is idle, the mod instead calls `$.prompt.submit` so the answer starts a turn. The card moves to the answered list.
- **Ask me properly** — `$.tool.call({ tool: "AskUserQuestion", questions: [...] })` with the extracted `options` (and "Other" is always offered by the tool). The tool's dialog and permission flow run as if the model had called it; the resolved answer is appended as above.
- **Keep default** — appends "Proceed with <default>" so the assumption becomes explicit in the transcript.
- **Dismiss** — removes the card and records the fingerprint so it is not raised again this session.
- Hotkeys on the card buttons are scoped to the focused card (the ring walks cards with Tab/arrows); only the focused card's hotkeys are drawn.
- Mobile has no `Input`; there the card shows "Ask me properly" and "Keep default" only.

### FR-006: Issues — capture

The mod shall collect issue-shaped findings from three sources:

1. **Tool results** — hook `tool.call`, `await next(e)`, inspect `result.text` for failure signatures (non-zero exit, stack traces, `FAIL`, `error:`, test-runner summaries). Cheap regex gate first, then `$.model.classify` on hits to reject noise (an expected failure the agent is working on is not an issue).
2. **Model text** — the same `turn.step` pass as FR-004, with labels `["bug-observation", "none"]`: the agent saying "this looks broken but it's out of scope," a TODO it noticed, a mismatch between docs and behaviour.
3. **Deliberate** — a model-callable tool `$.tool.register({ name: "log_issue", inputSchema: { title, body, severity?, files? } })`, served by a `tool.call` hook on `mcp__sidecar__log_issue`, so the main agent (or a skill) can log one on purpose. Registered with `isDeferred: false` so it is in the tool list from the start.

Each finding is `{ id, title, body, severity, files[], source, fingerprint, status: "open" | "ticked" | "filed" | "skipped", ticketRef? }` in `sidecar.issues`. Fingerprint = normalized title + first file; duplicates merge (count bumps, body appends).

### FR-007: Issues — UI and filing

```
[ ] 1  Cancelled games still RSVP-able      games/calendar.tsx
[x] 2  Team Chat hidden for program director nav/sidebar.tsx
[ ] 3  Forgot-password email not sent        auth/reset.ts
                                              [ f: File ticked (1) ]  [ s: Skip rest ]
```

- Each row is one plain `Button` with hotkey `1`–`9` toggling `open ↔ ticked`; rows beyond nine paginate (`n`/`p`). Enter on the focused row toggles too.
- A row's address is its `key` (the finding id), never its text.
- **File ticked** (`f`) files every ticked finding through FR-008, in order, marking each `filed` with its `ticketRef` and drawing the ref on the row. Failures leave the row ticked with the error dim beneath it.
- **Skip rest** (`s`) marks all open findings `skipped`; skipped fingerprints persist in `$.store` per project root so they are not re-raised.
- Filed refs are appended to the conversation as a meta user row (`Filed: #57 Cancelled games still RSVP-able`) so the main agent knows.
- A `userConfig` field `autoTick: boolean` (default false) pre-ticks findings of severity `high`.

### FR-008: Ticketing backend adapters

Filing shall resolve the backend from `.claude/workflow-config.json` in `$.session.root()`, read with `$.fs.read`, defaulting to `local`:

| backend | how | ref |
|---|---|---|
| `local` | append a Markdown issue to `docs/issues/{slug}.md` (the v0.5.0 local ticketing layout) via `$.fs.write` | file path |
| `github-issues` | `$.process.run({ argv: ["gh", "issue", "create", "--title", t, "--body", b, "--label", ...] })` in the repo root; repo from `$.session.repo()` | `#N` + URL |
| `jira` | `$.tool.call({ tool: "mcp__Jira__createJiraIssue", ... })` when the Jira MCP tools are connected; otherwise fall back to `local` with a toast | issue key |

`userConfig` adds `labels: string` (comma-separated defaults), `milestone: string`, and `jiraProject: string`. The adapter interface is `file(finding) → Promise<{ ref, url? } | { error }>`, one module per backend, so a fourth backend is one file.

### FR-009: Slash command and status

- `/sidecar` — open the pane (focused). `/sidecar mute decisions|issues` toggles a tab's detector. `/sidecar clear` empties both lists.
- `$.ui.status` shows a compact `◆ 2d 5i` while anything is open; cleared when both lists are empty.

### FR-010: State contract

`types/index.d.ts` declares, under `PluginState.sidecar`:

```ts
activeTab: "decisions" | "issues"
decisions: Decision[]
issues: Finding[]
muted: { decisions: boolean; issues: boolean }
```

All values are `$.state` (session, survives hot reload). `$.store` holds, per project root: answered decision fingerprints, skipped finding fingerprints, and the filed-ref map.

## Non-Functional Requirements

### Cost
- One `classify` per `turn.step` result, per tab, when not muted; `fork` only on a classify hit. Expected overhead well under 5% of the turn's tokens on a typical coding session.
- Detection never blocks the stream: `turn.step` hooks forward with `yield* next(e)` and do their work after the result settles, bounded by the dispatch budget; anything longer moves to `$.clock.after` from the result.

### Surfaces
- Terminal and desktop draw the same tree; `vscode` too. `mobile` lacks `Input` and `Select`; the Decisions card degrades per FR-005.
- Every tree is built from `$.ui.resolve(e)` for the event's surface; the tests loop over `['terminal', 'desktop'] as const`.

### Robustness
- Every hook that could refuse (`tool.call` for `log_issue`) carries a `.catch` that answers in its place.
- A `ui.render` tree that fails validation is replaced by the engine's own and logged; the pane must never leave the session stuck. Keep trees small; long bodies are truncated in the row and shown whole only on the focused card.
- Hot reload: `register` runs again, module variables reset; nothing the person sees lives in a module variable.

### Privacy
- Nothing leaves the session except through the configured ticketing backend, and only the findings the person ticked.

## Acceptance Criteria

### AC-001: Pane and tabs
- `/sidecar` opens one pane; two tabs; `d` and `i` switch; counts in labels match state.
- At <144 columns an unasked open yields a toast with the summary and `/sidecar` hint.

### AC-002: Decisions round-trip
- A turn in which the agent writes "I'll assume Firebase for auth" produces one Decisions card within the same turn.
- Typing an answer and pressing Enter appends a user-role meta row the next model step reads; the card moves to answered.
- "Ask me properly" raises the real `AskUserQuestion` dialog and the resolved answer is appended.
- The same question is not raised twice in a session, nor in the next session after being answered.

### AC-003: Issues round-trip
- A `Bash` tool result with a failing test summary produces one Issues row; a second identical failure merges into it.
- `mcp__sidecar__log_issue` called by the model produces a row with `source: "model"`.
- Ticking rows with `1`/`2` and pressing `f` files them through the configured backend; rows show the returned ref; a meta row names the refs.
- With `ticketing: "github-issues"` the issue exists on the repo with the configured labels and milestone.

### AC-004: Validation and tests
- `claude plugin validate mods/sidecar` reports no refusals; `tsc -p mods/sidecar` passes against the laid types.
- `claude plugin test mods/sidecar` passes: tab switching, card answer append, row tick + file against a mocked `local` backend, placement fallback toast — each on terminal and desktop.

## Error Handling

- `$.model.classify` / `fork` returning `isAnswered: false` → skip this step silently; log once per reason per session to the debug log.
- Backend adapter error → row stays ticked, error drawn dim under it, toast with the first line; never retry automatically.
- `AskUserQuestion` unavailable (headless, `-p`) → the "Ask me properly" button is not drawn; free text and keep-default remain.
- Missing or malformed `.claude/workflow-config.json` → `local` backend with a one-time toast.
- `$.session.append` refused (no running loop to append to, or a policy plugin denied) → fall back to `$.prompt.submit`.

## Implementation TODO

### Phase 1: Skeleton and pane
- [ ] `plugin.json`, `hooks.json`, `register.tsx` with the pane, tab row, `/sidecar`, status line, state contract
- [ ] Placement fallback toast
- [ ] Tests: tabs, status, fallback

### Phase 2: Issues tab
- [ ] `issues.ts`: tool-result regex gate + classify, `log_issue` tool, fingerprint merge
- [ ] Rows, tick hotkeys, pagination, skip-rest
- [ ] `filing.ts`: `local` adapter first, then `github-issues`, then `jira`
- [ ] Tests: capture from a mocked tool result, tick + file against `local`

### Phase 3: Decisions tab
- [ ] `decisions.ts`: `turn.step` classify + fork extractor, dedupe, store-backed memory
- [ ] Cards: Input answer, Ask-me-properly via `$.tool.call("AskUserQuestion")`, keep default, dismiss
- [ ] Tests: card from a mocked step result, answer append, ask-me-properly round-trip

### Phase 4: Ship
- [ ] README with `/plugin install sidecar --marketplace Jeffallan/claude-skills`
- [ ] `.claude-plugin/marketplace.json` entry; `scripts/build-plugin-dist.sh` ships `mods/`
- [ ] CHANGELOG under Unreleased; docs page under `docs/`

## Out of Scope

- Stacking two panes vertically (engine dock shows one pane with tabs).
- Space-bar toggling (hotkeys are a digit or lowercase letter only).
- Semantic dedupe of decisions beyond normalized-question fingerprints.
- Editing a finding's title/body in the pane before filing (file, then edit in the tracker).
- Auto-filing without a tick.

## Resolved Decisions

- **One mod, one pane, two tabs** (2026-10-13). Two sections stacked was the ask; the dock cannot stack, and a tab row inside one pane is the closest equivalent. Splitting into a dock mod plus two agent mods is deferred until the discovery mechanism (#250) can suggest them independently.
- **Filing goes through the v0.5.0 backend adapter config**, not a mod-specific setting, so projects configure ticketing once.
- **Detection uses `classify` as the gate and `fork` as the extractor.** `fork` rides the session's prompt cache and sees the full transcript; a fresh `complete` would need the context re-sent.
- **Answers enter the conversation as meta user rows via `session.append`**, with `prompt.submit` only when the session is idle, so an answer during a running turn does not start a second one.

## Open Questions

- [ ] Should answered decisions be written to the project's docs (a decisions log under `docs/`) in addition to the transcript? Fits the local-first workflow; adds a write the person did not ask for.
- [ ] Severity: let the classifier assign it, or require `log_issue` callers to set it and default captured findings to `medium`?
- [ ] Does the pane deserve a third tab later (e.g. "Assumptions" from common-ground #108/#111), or does that fold into Decisions?
- [ ] Which milestone: #250 is under V0.5.0, but the roadmap places selective skill activation in v0.6.0 and the #64 discovery Discussion in v0.7.0; the mod itself can ship independently of either.
