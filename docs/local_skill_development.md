# Local Skill Development Workflow

How to develop and test Claude Code marketplace plugins (skills) without releasing new versions.

---

## How Plugin Loading Works

Claude Code loads plugins from a **cache** directory, not from your source code. Understanding this is key to the development workflow.

| Directory | Purpose |
|-----------|---------|
| `~/.claude/plugins/marketplaces/<plugin>/` | Git clone managed by Claude Code (plugin source) |
| `~/.claude/plugins/cache/<plugin>/<name>/<version>/` | Installed snapshot (what the CLI actually loads) |
| Your working copy (e.g. `~/projects/<plugin>/`) | Where you develop (separate git clone) |

When you install a plugin, Claude Code clones the repo into `marketplaces/` and copies a clean snapshot into `cache/`. The CLI reads from `cache/` at session start. Edits to your working copy or the marketplace clone have **no effect** until the cache is updated.

---

## Symlink Development Setup

Symlink the cache directory to your working copy so edits are immediately available on CLI restart.

### Step 1: Identify Your Paths

Find your plugin's cache path:

```bash
cat ~/.claude/plugins/installed_plugins.json | grep installPath
```

This returns something like:

```
"installPath": "/home/<user>/.claude/plugins/cache/<plugin>/<name>/<version>"
```

Note the full path — you'll symlink this directory.

### Step 2: Back Up the Cached Version

```bash
mv ~/.claude/plugins/cache/<plugin>/<name>/<version> \
   ~/.claude/plugins/cache/<plugin>/<name>/<version>.bak
```

### Step 3: Create Symlink to Working Copy

Point the cache path to your local development clone:

```bash
ln -s /path/to/your/working/copy \
   ~/.claude/plugins/cache/<plugin>/<name>/<version>
```

**Important:** Symlink to the directory where you actually edit code, not the marketplace clone that Claude Code manages.

### Step 4: Verify

```bash
ls -la ~/.claude/plugins/cache/<plugin>/<name>/
# Should show: <version> -> /path/to/your/working/copy
```

---

## Development Workflow

Once the symlink is in place:

1. **Edit skills, commands, or references** in your working copy
2. **Restart Claude Code** — exit the current session and start a new one. Plugins load at session start; changes are not hot-reloaded.
3. **Test your changes** — invoke the skill or command as a user would
4. **Iterate** — repeat steps 1-3

No commits, pushes, or version bumps needed during development.

---

## Reverting to the Released Version

```bash
# Remove the symlink
rm ~/.claude/plugins/cache/<plugin>/<name>/<version>

# Restore the backup
mv ~/.claude/plugins/cache/<plugin>/<name>/<version>.bak \
   ~/.claude/plugins/cache/<plugin>/<name>/<version>
```

---

## Caveats

### Plugin auto-updates may break the symlink

Claude Code periodically checks for plugin updates. An auto-update could:
- Replace the symlink with a fresh cache copy
- Write updated files into the symlinked directory (i.e. into your working copy)

If your symlink stops working after you didn't touch it, check whether an auto-update ran and re-create the symlink.

### Working copy differs from a clean cache

The cache is normally a clean snapshot — no `.git/`, no IDE files, no uncommitted work. Your symlinked working copy includes all of that. This is generally harmless — the plugin loader reads markdown files and ignores unknown entries — but be aware:

- New files that reference structures you haven't created yet may cause confusing behavior
- `.git/`, `.DS_Store`, `node_modules/`, and similar directories are exposed but ignored

### Restart is required

Claude Code loads plugins at session start. There is no hot-reload. After every change, exit and restart the CLI.

---

## Testing a Specific Version or Branch

```bash
cd /path/to/your/working/copy
git checkout <branch-or-tag>

# Restart Claude Code — the symlink still points here,
# so it will load whatever is checked out
```

To compare against the released version, temporarily revert the symlink (see above) and restart.

---

## Quick Reference

```bash
# Setup (one-time)
CACHE=~/.claude/plugins/cache/<plugin>/<name>/<version>
WORKDIR=/path/to/your/working/copy

mv "$CACHE" "${CACHE}.bak"
ln -s "$WORKDIR" "$CACHE"

# Develop (repeat)
# 1. Edit files in $WORKDIR
# 2. Restart Claude Code
# 3. Test

# Teardown (when done)
rm "$CACHE"
mv "${CACHE}.bak" "$CACHE"
```
