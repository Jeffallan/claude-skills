# Discovery run eval

Scores one discovery topic, from `discovery:create` through `discovery:approve`, against a gold set: did each item take the right route, did the run raise the blocking decisions a careful reader would, and did the tickets that should exist get created. Feature Forge interviews need an owner, so a scored run scripts the owner's answers in advance and keeps them with the gold set.

## What it checks

| Check | Passes when | Reads |
|-------|-------------|-------|
| `routing` | Every gold item (a regex on the Item cell of the `## Features` table) has the gold route: `Clear`, `Feature Forge` or `Research` | `discovery.md` |
| `blocking-decisions` | Every gold decision (a regex) matches a row of a `## Blocking decisions` table | `discovery.md`, `synthesis.md` |
| `approved-tickets` | Every gold ticket (a regex) matches the title of a proposed ticket the topic records as created: `discovery:approve` writes "Created as <ID>" next to the ticket, in its table row, on a line that names it, or under its `### P<n>:` heading | `discovery.md`, `synthesis.md` |

## Gold set

A JSON file, kept in a private eval directory (`../README.md`) with the seeded input and the scripted owner answers:

```json
{
  "topic": "<topic>",
  "routes": {"<item regex>": "Clear | Feature Forge | Research"},
  "decisions": ["<decision regex>"],
  "tickets": ["<ticket title regex>"]
}
```

## Running it

```bash
make eval-discovery EVAL=<eval directory> RUN=<run name>
make eval-discovery REPO=<repo> TOPIC=<topic> GOLD=<gold.json>
```

`eval.json` names the gold file and, per run, the `repo` and the `topic`. It prints one JSON result with `score`, `total` and each check. Exit 0 means every check passed, 1 means one failed, 2 means bad input.

`scripts/test-eval-loop.sh` (part of `make test`) checks the scorer on a synthetic topic that matches its gold set and one that doesn't.
