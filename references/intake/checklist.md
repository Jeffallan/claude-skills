# Intake Checklist

The whole intake phase on one page: four phases, run in order, one command per item. Copy the template below into the project as `docs/intake-checklist.md` and work it top to bottom, attended or as a goal run (`references/intake/goal-prompt.md`). The checklist file is the run's memory: a checked box, its completion note and any `BLOCKED:` note are all the next session knows.

The operating rule for every item: **characterize, don't fix** (`references/intake/findings.md`). Docs and tests record what the code does today. Every bug goes in `docs/intake-findings.md`, never into a fix.

## Template

```markdown
# Intake Checklist

Started <YYYY-MM-DD> on branch <intake-branch> at <start-sha>. One item per command; check an item only
after its verification ran in the same session, and add an indented note with the date, the commit and
the evidence on the lines right below the item.

## Phase 1: Document

- [ ] Start the findings tracker: `docs/intake-findings.md` with the shape in `references/intake/findings.md`
- [ ] `intake:existing-docs`: `docs/intake-existing-docs.md`, every doc the project already has, mapped to the intake docs and checked against the code
- [ ] `intake:document-codebase`: docstrings across the code; tests pass before and after, no executable line changed
- [ ] `intake:document-file-tree`
- [ ] `intake:document-data-model`
- [ ] `intake:document-integrations`
- [ ] `intake:document-api`
- [ ] `intake:document-user-model`
- [ ] `intake:document-features`
- [ ] `intake:document-glossary`
- [ ] `intake:document-security`
- [ ] `intake:document-authorization`
- [ ] `intake:document-user-flow`
- [ ] `intake:document-config`
- [ ] `intake:document-analytics`
- [ ] `intake:create-onboarding`: `docs/README.md` linking every doc above, ending with its `## Accuracy audit`
- [ ] Link `docs/README.md` from the project's `CLAUDE.md` so agents find the docs

## Phase 2: Harness

- [ ] `intake:testing-setup`: unit, integration and e2e layers with a smoke test each before any real test, the `test:unit`, `test:integration`, `test:e2e` and `test:all` scripts, and the command's Test paths line in the note

## Phase 3: Test

- [ ] `intake:testing-features`
- [ ] `intake:testing-authorization`
- [ ] `intake:testing-owasp`
- [ ] `intake:testing-user-flows`
- [ ] `intake:create-system-description`: the baseline spec and `docs/system-description.md`

## Phase 4: Gate

- [ ] Wire the PR gate: unit and cheap integration layers on every PR, heavy layers on a schedule
- [ ] Note the gate's environment needs and scope around known pre-existing failures
- [ ] Close out the findings tracker: every finding ticketed, accepted as a risk, fixed or invalid
```

## Rules for working it

| Rule | Why |
|------|-----|
| `<start-sha>` in the header is the commit the intake branch was cut from, and the tracker header names the same one | The eval compares the two; a header copied from an older run names the wrong base |
| One item per command, in order | Later items read earlier output: the testing commands read the docs, the system description reads everything |
| Prove the harness with a smoke test before any real test | A test suite that never ran is worse than none: it reads as coverage |
| Verify before checking a box, in the same session | A checked box is the only memory the next session has; a false one is unrecoverable |
| Never reorder, reword or delete items | The eval and the next session match items by their text |
| Keep each item on one line; notes go on indented lines right below it | A note inside a wrapped item splits its text, and the next session can't tell item from note |
| One commit per item, checklist edit included | `git log` then traces each item to its evidence |
| A stuck item gets an indented `BLOCKED: <what is needed>` note and stays unchecked | The run moves on to the next item that doesn't depend on it |

Items that don't apply (a project with no analytics, no UI for e2e) are still worked: the command records "not present" and the item is checked with that note. Skipping one silently looks like a missed item.

## Phase 4 is attended

The gate touches CI configuration and the close-out records owner decisions on findings, so a goal run stops before Phase 4. The owner works it attended, after reading the findings tracker.

When the branch isn't pushed, the gate can't be seen running on CI. Check it locally (a workflow linter such as `actionlint`, then the workflow's steps in a fresh clone) and say in the item's note that it hasn't run on CI yet.

## When not to use it

- A codebase that already has current reference docs and a test suite: run `intake:existing-docs` first, then only the commands for the gaps it finds.
- A brand-new project with no code yet: there is nothing to characterize. Start at discovery.
