# spec:complete docs eval

Scores the two docs duties of one `spec:complete` run on a fixture spec with a known effect on the system (`plugin/commands/spec/complete.md`, Step 2): item 6, which proposes the system description changes the spec causes, applies the approved ones and adds a `## Change history` row; and item 8, docs:verify, which checks the project docs' claims against the spec's diff and flags the ones the diff made stale. The workflow eval (`../workflow/EVAL.md`) scores the tickets and commits; this one scores what the run did to the docs.

## What it checks

| Check | Passes when | Reads |
|-------|-------------|-------|
| `sd-changed` | Every section the gold set says must change matches none of its `stale` regexes and every `expect` regex after the run. An `optional` section is reported, changed or not, and never fails the check | `docs/system-description.md` at the completion commit |
| `sd-unchanged` | Every section the gold set says must not change is the same before and after, whitespace aside | The description before the run and at the completion commit |
| `change-history` | The Change history table has a row for the spec whose Sections changed cell matches every `sections_include` regex | The description at the completion commit |
| `verify-recall` | Every required stale claim matches a flagged row on the same doc whose Claim matches. A claim with `"required": false` is reported, found or not, and never fails the check | The docs:verify table |
| `verify-false-flags` | No flagged row matches a `not_stale` claim | The docs:verify table |

The docs:verify table is `review/docs-verify.md`: `| Doc | Claim | Verdict | Evidence |`, Doc the path and section, Verdict `holds`, `stale` or `unknown`, and a stale row later marked `fixed` or `declined` once the owner answers. A row whose Verdict says `stale`, `fixed` or `declined` is a flag; `holds` and `unknown` are not. When nothing in the docs names what the diff changed, the file holds an empty table and the line "No doc names what this diff changed.", which flags nothing. Flags on a doc under `excluded_docs` are ignored. A section is found by its heading regex, else by its number.

## Gold set

A JSON file, kept with the fixture in a private eval directory (`../README.md`):

```json
{
  "spec": "<spec>",
  "fixture_start": "<sha>",
  "system_description": {
    "sections": [
      {"section": "2", "heading": "<regex on the ## line>", "must_change": true,
       "stale": ["<regex the section matches before and must not match after>"],
       "expect": ["<regex the section must match after>"]}
    ],
    "change_history_row": {"spec": "<spec>", "sections_include": ["<regex>"]}
  },
  "docs_verify": {
    "stale_claims": [{"id": "S1", "doc": "<path>", "match": "<regex on the Claim cell>", "required": true}],
    "not_stale": [{"id": "N1", "doc": "<path>", "match": "<regex on the Claim cell>", "why": "<why it still holds>"}],
    "excluded_docs": ["<path prefix whose flags are ignored>"]
  }
}
```

`must_change` is `true`, `false`, `"optional"` (reported only) or `"neutral"` (not read). Paths compare after a leading `./` is stripped; a Doc cell matches a gold doc when it starts with the gold path, so `docs/a.md, Setup` matches `docs/a.md`.

## Running it

```bash
make eval-spec-complete-docs EVAL=<eval directory> RUN=<run name>
make eval-spec-complete-docs BEFORE=<description before> AFTER=<description after> VERIFY=<docs-verify.md> GOLD=<gold.json>
```

`eval.json` names the gold file and, per run, `before` and `after` (the description at the start and at the completion commit, saved with `git show <sha>:docs/system-description.md`) and `verify`. It prints one JSON result with `score`, `total` and each check. Exit 0 means every check passed, 1 means one failed, 2 means bad input.

`scripts/test-eval-loop.sh` (part of `make test`) checks the scorer on a synthetic run that matches its gold set, one that misses every check, and an empty docs:verify table.

## Limits

- `spec:complete` is attended: the owner approves each section change and each stale-claim fix. A scored run scripts those answers, and the gold set must match them.
- The new sections are scored by stale sentences gone and keywords present, not by reading them; whether they say the right thing is the owner's read.
- Item 7 (`docs-affected`, the docs index) isn't scored here.
