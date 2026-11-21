# Ground File Management

> Reference for: Common Ground
> Load when: Storage operations, file format

---

## Where the files live

The ground file lives in the repository next to the system description, so it is versioned and shared with everyone who works on the project:

```
<docsRoot>/                               # docsRoot from .claude/workflow-config.json, default docs
├── system-description.md                 # what is true now (spec:current)
├── current-state.json                    # compiled from it (guard current-state)
├── COMMON-GROUND.md                      # human-readable assumptions
└── ground.index.json                     # machine-readable index
```

The repository identifies the project, so there is no project id and no global registry. Older versions kept the file under `~/.claude/common-ground/<project>/`; when one exists for this repository and `<docsRoot>/COMMON-GROUND.md` doesn't, offer to move its assumptions in.

---

## Ground File (COMMON-GROUND.md)

Located at: `<docsRoot>/COMMON-GROUND.md`

### Template

```markdown
# Project Common Ground

**Project:** {project_name}
**Created:** {created_timestamp}
**Last Updated:** {updated_timestamp}

---

## ESTABLISHED

High confidence assumptions. Treat as premises.

### {id}: {title}

- **Type:** {stated|inferred|assumed}
- **Assumption:** {description}
- **Source:** {evidence or citation}
- **Validated:** {date}
- **Context:** {when this applies}

---

## WORKING

Medium confidence. Use but flag if contradicted.

### {id}: {title}

- **Type:** {stated|inferred|assumed}
- **Assumption:** {description}
- **Source:** {evidence or citation}
- **Validated:** {date}
- **Context:** {when this applies}

---

## OPEN

Low confidence. Ask before assuming.

### {id}: {title}

- **Type:** {stated|inferred|assumed|uncertain}
- **Assumption:** {description}
- **Source:** {evidence or citation}
- **Validated:** {date}
- **Context:** {when this applies}

---

## History

| Date | Action | ID | Details |
|------|--------|------|---------|
| {date} | {Created/Promoted/Demoted/Archived} | {id} | {details} |

---

*Managed by /common-ground command*
```

### Assumption ID Format

Format: `A{number}` (e.g., A001, A002, A003)

- Sequential within project
- Never reused (even after archival)
- Track highest ID in index.json

---

## Machine Index (ground.index.json)

Located at: `<docsRoot>/ground.index.json`

### Schema

```json
{
  "version": "1.0",
  "project_name": "{human_readable_name}",
  "created": "{ISO_timestamp}",
  "last_updated": "{ISO_timestamp}",
  "next_id": 4,
  "assumptions": [
    {
      "id": "A001",
      "title": "{short_title}",
      "type": "stated|inferred|assumed|uncertain",
      "tier": "ESTABLISHED|WORKING|OPEN",
      "assumption": "{full_description}",
      "source": "{evidence}",
      "validated": "{ISO_date}",
      "context": "{when_applies}",
      "created": "{ISO_timestamp}",
      "history": [
        {
          "date": "{ISO_timestamp}",
          "action": "created|promoted|demoted",
          "from_tier": null,
          "to_tier": "WORKING",
          "reason": "{optional}"
        }
      ]
    }
  ],
  "archived": []
}
```

### Field Definitions

| Field | Type | Description |
|-------|------|-------------|
| `version` | string | Schema version for migrations |
| `project_name` | string | Human-readable project name |
| `next_id` | number | Next assumption ID to assign |
| `assumptions` | array | Active assumptions |
| `archived` | array | Archived assumptions (future) |

---

## File Operations

### Create New Ground File

1. Write `<docsRoot>/COMMON-GROUND.md` from template
2. Write `<docsRoot>/ground.index.json` with empty assumptions
3. Commit both: `docs(common-ground): start the ground file`

### Update Existing Ground File

1. Read `ground.index.json`
2. Apply changes (add/promote/demote)
3. Update `last_updated` timestamp
4. Regenerate `COMMON-GROUND.md` from index.json
5. Commit both: `docs(common-ground): <what changed>`

### Read Ground File

1. Check if `<docsRoot>/ground.index.json` exists
2. If exists, parse JSON and return
3. If not exists, return null (trigger fresh start)

---

## Writing Best Practices

### Human-Readable (COMMON-GROUND.md)

- Use consistent markdown formatting
- Include horizontal rules between tiers
- Keep assumptions readable without JSON
- Include history table for audit trail

### Machine-Readable (ground.index.json)

- Always valid JSON
- Include all fields (no omissions)
- Use ISO 8601 timestamps
- Preserve history array for audit

### Sync Rules

- `ground.index.json` is source of truth
- `COMMON-GROUND.md` is generated from index.json
- Always update both on any change
- Never manually edit COMMON-GROUND.md (regenerate instead)

---

## Error Handling

| Scenario | Action |
|----------|--------|
| Corrupted index.json | Backup and regenerate from COMMON-GROUND.md |
| Missing ground file | Create fresh on next run |
| Permission denied | Report error with path |
