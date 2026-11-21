# intake:document-codebase

Add accurate, agent-readable docstrings and module comments across an existing codebase without changing a single executable line.

**Step:** docstrings (intake phase, first) · **Procedure file:** `references/intake/procedures/document-codebase.md` · **Run:** `intake document-codebase`

---

## Inputs

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `directory` | string | no | Root directory to document. Defaults to the project root. |

## Outputs

| Name | Type | Description |
|------|------|-------------|
| `docstrings` | directory | Docstrings and module comments across the code, with no executable line changed |
| `documentation-report` | report | Coverage before and after, the test runs, the executable-line check and the findings raised |

## How it runs

The procedure records the start commit and runs the project's tests, detects the language, the framework and the docstring style already in use, and lists what lacks a docstring with public APIs first. After the checkpoint it writes docstrings that say what each unit does, takes, returns, raises and changes, from reading the code and its callers.

It proves the pass changed nothing that runs in two ways: the test suite gives the same result before and after, and a diff check confirms every changed hunk is a comment or docstring (an AST comparison for Python, a comment-stripped comparison for JavaScript and TypeScript, a comment-line check elsewhere). Any hunk that touches code is reverted.

Code that contradicts its own name or type gets a docstring describing what it does and a finding in `docs/intake-findings.md`. The bug is never fixed here.

## Next steps

Run the `document-*` procedures next; see the [intake phase](intake-phase.md).
