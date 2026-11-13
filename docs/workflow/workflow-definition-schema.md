# Workflow Definition Schema

Machine-readable YAML definitions for workflow commands and the workflow manifest.

---

## Per-Command YAML Schema

Each command has a co-located `.yaml` file describing its interface.

### Annotated Example

```yaml
# Unique command identifier: {phase}:{action}
command: "discovery:create"

# Workflow phase this command belongs to
phase: discovery

# Relative path to the command's .md implementation file
path: commands/discovery/create.md

# Relative path to the human-readable overview in docs/workflow/
description: docs/workflow/discovery-create.md

# Ordered list of inputs the command accepts
inputs:
  - name: topic-input
    type: string
    required: true
    description: Feature sets, business requirements, a build request, or an existing ticket ID

# Ordered list of outputs the command produces
outputs:
  - name: discovery-document
    type: file
    path: "{specsRoot}/todo/discovery/{topic}/discovery.md"
    description: Feature list, open questions, proposed tickets and status

# Backend capabilities this command depends on
# Valid values: ticketing, or an empty list
requires:
  - ticketing

# Command lifecycle status (default: existing)
status: existing

# CLI syntax hint shown in help text
argument-hint: "<topic-or-ticket>"

# Whether this command is invoked several times per spec (default: false)
repeat: false

# Whether the command runs under unattended rules inside a goal run
unattended: false

# Tracker and code-host operations the command uses
adapter-operations:
  - read
```

### Field Reference

| Field | Type | Required | Default | Constraints |
|-------|------|----------|---------|-------------|
| `command` | string | yes | — | Format `{phase}:{action}` or bare name for utilities. Unique across all definitions. |
| `phase` | string | yes | — | One of: `intake`, `discovery`, `spec`, `ticket`. Required for phase commands. Omit for utility commands. |
| `path` | string | yes | — | Relative path from repo root to the `.md` command file. Must resolve to an existing file when `status: existing`. When `status: planned`, the path is not required to resolve to an existing file. |
| `description` | string | yes | — | Relative path from repo root to the overview `.md` in `docs/workflow/`. Must resolve to an existing file. |
| `inputs` | list | yes | — | Ordered list of input objects. May be empty (`[]`). |
| `inputs[].name` | string | yes | — | Kebab-case identifier. |
| `inputs[].type` | string | yes | — | One of: `string`, `url`, `list[url]`, `list[string]`, `flag`. |
| `inputs[].required` | boolean | yes | — | Whether the input must be provided. |
| `inputs[].description` | string | yes | — | Human-readable description of the input. |
| `outputs` | list | yes | — | Ordered list of output objects. May be empty (`[]`). |
| `outputs[].name` | string | yes | — | Kebab-case identifier. |
| `outputs[].type` | string | yes | — | One of: `url`, `document`, `tickets`, `report`, `file`. |
| `outputs[].path` | string | no | — | Template path for the output location. Supports `{input-name}` interpolation. |
| `outputs[].description` | string | no | — | Human-readable description of the output. |
| `requires` | list | yes | — | Backend capabilities needed. Valid value: `ticketing`. Empty list (`[]`) if no backend is needed. |
| `status` | string | no | `existing` | One of: `existing`, `planned`, `deprecated`. |
| `argument-hint` | string | no | — | CLI syntax hint (e.g., `<spec-name>`). |
| `repeat` | boolean | no | `false` | `true` if the command is invoked several times per spec (e.g., per-ticket commands). |
| `unattended` | boolean | no | — | `true` for a command that runs under unattended rules in a goal run (`ticket:execute`, `ticket:complete`); `false` for an attended-only command. skill-linter's WF-02 rejects write operations on an unattended command. |
| `adapter-operations` | list | no | — | Tracker and code-host operations the command uses: `create`, `read`, `list-spec-tickets`, `link`, `update`, `comment`, `close`, `reopen`, `ensure-group`, `link-groups`, `list-ungrouped`, `open-pr`, `read-pr-feedback`, `reply-resolve`, `check-pr`, `merge-pr`. See `references/adapters/operations.md`. |

### Input Types

| Type | Description | Example |
|------|-------------|---------|
| `string` | Single string value | `CC-60` |
| `url` | Single URL | `https://example.com/notes` |
| `list[url]` | Space-separated URLs | `url1 url2 url3` |
| `list[string]` | Space-separated strings | `--decision=D1:B --decision=D2:Y` |
| `flag` | Boolean flag | `--list`, `--check`, `--graph` |

### Output Types

| Type | Description |
|------|-------------|
| `url` | A URL to a published document or page |
| `document` | A generated local markdown document |
| `tickets` | Jira tickets created in the ticketing system |
| `report` | A generated report (completion report, retrospective) |
| `file` | A local file produced on disk |

---

## Workflow Manifest Schema

The manifest at `commands/workflow-manifest.yaml` defines the phase DAG and command ordering.

### Annotated Example

```yaml
# Manifest schema version
version: "1.0"

# Ordered phases forming the workflow DAG
phases:
  intake:
    # Relative path to the phase overview markdown
    description: docs/workflow/intake-phase.md

    # Phase dependencies (empty = entry point)
    depends_on: []

    # Whether this phase runs once per project (vs. once per spec)
    run_once: true

    # Ordered list of commands in this phase
    commands:
      - command: "intake:document-codebase"
        definition: commands/intake/document-codebase.yaml
      - command: "intake:capture-behavior"
        definition: commands/intake/capture-behavior.yaml
      - command: "intake:create-system-description"
        definition: commands/intake/create-system-description.yaml

  discovery:
    description: docs/workflow/discovery-phase.md
    depends_on:
      - phase: intake
        strength: recommended  # Not strictly required, but recommended
    optional: true             # Phase can be skipped entirely
    external_skills:
      - skill: feature-forge
        role: prerequisite     # Feature-forge identifies unknowns that trigger discovery
    commands:
      - command: "discovery:create"
        definition: commands/discovery/create.yaml
      - command: "discovery:synthesize"
        definition: commands/discovery/synthesize.yaml
      - command: "discovery:approve"
        definition: commands/discovery/approve.yaml

# Utility commands not tied to a specific phase
utilities:
  - command: common-ground
    definition: commands/common-ground.yaml
    invocation: on-demand      # Can be invoked at any point
```

### Manifest Field Reference

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `version` | string | yes | Manifest schema version. Currently `"1.0"`. |
| `phases` | map | yes | Ordered map of phase name → phase definition. |
| `phases.<name>.description` | string | yes | Path to the phase overview markdown. |
| `phases.<name>.depends_on` | list | yes | Phase dependencies. Empty list for entry points. |
| `phases.<name>.depends_on[].phase` | string | yes | Name of the dependency phase. |
| `phases.<name>.depends_on[].strength` | string | yes | `required` or `recommended`. |
| `phases.<name>.run_once` | boolean | no | `true` if the phase runs once per project. Default `false`. |
| `phases.<name>.optional` | boolean | no | `true` if the phase can be skipped. Default `false`. |
| `phases.<name>.external_skills` | list | no | Skills from outside the workflow that feed into this phase. |
| `phases.<name>.external_skills[].skill` | string | yes | Skill name. |
| `phases.<name>.external_skills[].role` | string | yes | Relationship: `prerequisite`, `companion`, `output-consumer`. |
| `phases.<name>.commands` | list | yes | Ordered list of commands in this phase. |
| `phases.<name>.commands[].command` | string | yes | Command identifier matching the YAML definition's `command` field. |
| `phases.<name>.commands[].definition` | string | yes | Relative path to the command's `.yaml` definition file. |
| `utilities` | list | no | Commands not tied to a phase. |
| `utilities[].command` | string | yes | Command identifier. |
| `utilities[].definition` | string | yes | Path to the command's `.yaml` definition file. |
| `utilities[].invocation` | string | yes | Invocation pattern: `on-demand`, `scheduled`, `triggered`. |

### Validation Rules

1. **No cycles:** The `depends_on` graph must be a DAG. A phase cannot transitively depend on itself.
2. **Command uniqueness:** Every `command` value across all phases and utilities must be unique.
3. **Path resolution:** All `definition` and `description` paths must resolve to existing files.
4. **Phase reference validity:** Every `depends_on[].phase` must reference a phase defined in the manifest.
5. **Definition consistency:** Each `commands[].command` must match the `command` field inside the referenced YAML definition file.
6. **Status gating:** Commands with `status: planned` should be flagged as unavailable when the manifest is consumed at runtime.
