# Supported Agents

This plugin follows the [Agent Skills specification](https://agentskills.io/specification), an open standard for packaging reusable AI agent capabilities. Skills are portable across any agent that implements the spec, and each agent reads them from its own skills folder. Pick your agent below.

## Quick install

In Claude Code:

```
/plugin marketplace add jeffallan/claude-skills
```

```
/plugin install fullstack-dev-skills@fullstack-dev-skills
```

Other agents can use the [Skills CLI](#skills-cli) with their agent id:

```bash
npx skills add jeffallan/claude-skills -a <agent-id> -s '*'
```

A copy of the skills in a project's `.agents/skills/` folder reaches every agent on this page except Claude Code and AdaL CLI. A project `.claude/skills/` copy also loads in GitHub Copilot, Cursor, Goose, Amp and OpenCode, so a Claude Code user often needs no second install for those.

Only the Claude Code commands have been run against this repo. The other commands on this page follow each vendor's or installer's documented syntax and are marked where that matters.

## Compatible Agents

| Agent | Developer | Type | Repo | Skills Documentation | Notes |
|-------|-----------|------|------|---------------------|-------|
| [Claude Code](https://code.claude.com/docs/en/overview) | Anthropic | CLI, IDE, desktop | [anthropics/claude-code](https://github.com/anthropics/claude-code) | [Skills](https://code.claude.com/docs/en/skills) | |
| [GitHub Copilot](https://github.com/features/copilot) | GitHub (Microsoft) | CLI, VS Code, JetBrains, Visual Studio | [github/copilot-cli](https://github.com/github/copilot-cli) | [About agent skills](https://docs.github.com/en/copilot/concepts/agents/about-agent-skills), [VS Code](https://code.visualstudio.com/docs/agent-customization/agent-skills) | |
| [Codex CLI](https://github.com/openai/codex) | OpenAI | CLI | [openai/codex](https://github.com/openai/codex) | [Build skills](https://learn.chatgpt.com/docs/build-skills) | |
| [Cursor](https://cursor.com) | Anysphere (not re-verified) | IDE, CLI | closed source | [Agent Skills](https://cursor.com/docs/skills) | Skills since 2.4 |
| [Gemini CLI](https://github.com/google-gemini/gemini-cli) | Google | CLI | [google-gemini/gemini-cli](https://github.com/google-gemini/gemini-cli) | [Agent Skills](https://geminicli.com/docs/cli/skills/) | Enterprise Code Assist only since 2026-06-18; other users moved to Antigravity CLI |
| [Goose](https://goose-docs.ai) | Agentic AI Foundation (Linux Foundation), created by Block | CLI, desktop | [aaif-goose/goose](https://github.com/aaif-goose/goose) | [Using Skills](https://goose-docs.ai/docs/guides/context-engineering/using-skills/) | Moved from Block in 2026-04 |
| [Letta Code](https://github.com/letta-ai/letta-code) | Letta | CLI | [letta-ai/letta-code](https://github.com/letta-ai/letta-code) | [Skills](https://docs.letta.com/configuration/skills) | |
| [Amp](https://ampcode.com) | Amp Frontier Corporation (spun out of Sourcegraph) | CLI, editor extensions | closed source | [Skills](https://ampcode.com/docs/customize/skills) | |
| [OpenCode](https://opencode.ai) | Anomaly, formerly the SST team (secondary sources only) | CLI | [anomalyco/opencode](https://github.com/anomalyco/opencode) | [Skills](https://opencode.ai/docs/skills/) | |
| [AdaL CLI](https://adalagent.ai) | SylphAI | CLI, desktop | [SylphAI-Inc/adal-cli](https://github.com/SylphAI-Inc/adal-cli) (community repo) | [Plugins and skills](https://docs.sylph.ai/customize/plugins-and-skills/) | Now marketed as a video agent |

Roo Code has moved to [Discontinued agents](#discontinued-agents).

## Skills Directory Locations

| Agent | Project skills | User skills | Notes |
|-------|----------------|-------------|-------|
| Claude Code | `.claude/skills/` (and parents up to the repo root) | `~/.claude/skills/` | Also plugin `skills/`, `--add-dir` targets and the managed settings folder. Plugin skills are namespaced `plugin:skill`. |
| GitHub Copilot | `.github/skills/`, `.agents/skills/`, `.claude/skills/` | `~/.copilot/skills/`, `~/.agents/skills/` | Also plugin `skills/` and `COPILOT_SKILLS_DIRS`; VS Code also reads `~/.claude/skills/`. First skill found wins, by `name`. |
| Codex CLI | `.agents/skills/` (cwd up to the repo root) | `~/.agents/skills/` | Also `/etc/codex/skills`. Same-name skills are not merged, so both may appear. |
| Cursor | `.agents/skills/`, `.cursor/skills/` | `~/.agents/skills/`, `~/.cursor/skills/` | Also `.claude/skills/`, `.codex/skills/` and their `~/` forms. Duplicate-name rule not documented. |
| Gemini CLI | `.agents/skills/`, `.gemini/skills/` | `~/.agents/skills/`, `~/.gemini/skills/` | Also extension skills. Workspace beats user; `.agents` beats `.gemini`. |
| Goose | `.agents/skills/` (recommended), `.goose/skills/`, `.claude/skills/` | `~/.agents/skills/`, `~/.config/goose/skills/`, `~/.claude/skills/`, `~/.config/agents/skills/` | Also `~/.agents/plugins/`. Project before global (read from source code, not docs). |
| Letta Code | `.agents/skills/`, legacy `.skills/` | `~/.letta/skills/` | Project beats agent memory, then global, then bundled (read from source code, not docs). |
| Amp | `.agents/skills/` (and parents), `.claude/skills/` | `~/.config/agents/skills/`, `~/.agents/skills/`, `~/.config/amp/skills/`, `~/.claude/skills/` | Also `~/.claude/plugins/cache/` and the `amp.skills.path` setting. First match by `name`. |
| OpenCode | `.opencode/skills/`, `.agents/skills/`, `.claude/skills/` (cwd up to the root) | `~/.config/opencode/skills/`, `~/.agents/skills/`, `~/.claude/skills/` | Also the `skills` array in `opencode.json`. |
| AdaL CLI | `.adal/skills/` | `~/.adal/skills/` | Also `~/.adal/plugin-cache/`. Its docs list neither `.claude/skills/` nor `.agents/skills/`. |

Paths are shown in POSIX form. None of these agents documents Windows paths. Goose's Windows user folder works out to `%APPDATA%\Block\goose\config\skills` from its source and config docs, though no doc page states it. Where `~` points on Windows is not documented for the others.

## Claude Code

```
/plugin marketplace add jeffallan/claude-skills
```

```
/plugin install fullstack-dev-skills@fullstack-dev-skills
```

Restart Claude Code when prompted. On Claude Code v2.1.292 or later you can do both steps from the shell:

```bash
claude plugin install fullstack-dev-skills --marketplace jeffallan/claude-skills
```

The plugin brings every skill plus the workflow commands (`/common-ground`, intake, spec and ticket) and their hooks. Every other route on this page installs skills only and leaves the workflow commands out. To install skills alone here, use `npx skills add jeffallan/claude-skills -a claude-code -s '*' -y` or copy into `~/.claude/skills/`. See [Claude Code: discover plugins](https://code.claude.com/docs/en/discover-plugins).

## GitHub Copilot

```bash
copilot plugin marketplace add jeffallan/claude-skills
copilot plugin install fullstack-dev-skills@fullstack-dev-skills
```

Copilot CLI looks for `.claude-plugin/marketplace.json` as one of its manifest locations, so these commands match its [documented syntax](https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-plugin-reference). They have not been run against this repo. The plugin also carries the workflow commands and hooks, which are Claude Code features and may not behave the same here. To install skills only, or to cover VS Code, which reads the same project folders:

```bash
npx skills add jeffallan/claude-skills -a github-copilot -s '*' -y
```

## Codex CLI

```bash
npx skills add jeffallan/claude-skills -a codex -s code-reviewer test-master debugging-wizard
```

Install only the skills you need. Codex limits its initial skills list to 2% of the context window, or 8,000 characters when the window is unknown, and past that it shortens descriptions and may omit skills with a warning ([OpenAI: Build skills](https://learn.chatgpt.com/docs/build-skills)). The names and descriptions of all the skills total about 33,400 characters (measured with 71 skills), roughly four times that fallback. Replace the names above with the skills you want. To install all of them anyway, use `-s '*'`, raise `skills.max_context_tokens` in your Codex config toward its 10,000-token maximum, and watch for the omission warning. Codex also accepts this repo's marketplace file through `codex plugin marketplace add jeffallan/claude-skills`, then installs from the `/plugins` browser in the TUI ([OpenAI: Build plugins](https://developers.openai.com/plugins/build/plugins)). That route is untested, brings every skill, and can show duplicates if you also installed by copy, since Codex does not merge same-name skills.

## Cursor

```bash
npx skills add jeffallan/claude-skills -a cursor -s '*' -y
```

Cursor imports GitHub repos only as plugins with a `.cursor-plugin/marketplace.json`, which this repo does not have, so there is no native route ([Cursor docs](https://cursor.com/docs/skills)). The installer writes to `.agents/skills/`, or `~/.cursor/skills/` with `-g`. Copying into either folder works too, and an existing `.claude/skills/` copy already loads.

## Gemini CLI

```bash
gemini skills install https://github.com/jeffallan/claude-skills.git --path plugin/skills --consent
```

This follows the [documented syntax](https://geminicli.com/docs/cli/skills/) and has not been run against this repo. It installs for your user by default; add `--scope workspace` for the project. Skills are on by default from v0.25.0 through the `skills.enabled` setting. Gemini CLI now targets Gemini Code Assist Standard and Enterprise licences, and free and Google AI Pro or Ultra users moved to Antigravity CLI on 2026-06-18 ([gemini-cli README](https://github.com/google-gemini/gemini-cli)). The fallback for Gemini CLI, and the route for Antigravity CLI:

```bash
npx skills add jeffallan/claude-skills -a gemini-cli -s '*' -y
npx skills add jeffallan/claude-skills -a antigravity-cli -s '*' -y
```

The `antigravity-cli` id writes to `.agents/skills/`, or `~/.gemini/config/skills/` with `-g`.

## Goose

```bash
npx skills add jeffallan/claude-skills -a goose -s '*' -y
```

Goose has no native route for this repo: `goose plugin install` recognises Open Plugins and Gemini extension manifests, which this repo lacks, and `goose skills` only lists ([goose plugins docs](https://github.com/aaif-goose/goose/blob/main/documentation/docs/guides/context-engineering/plugins.md)). The installer writes to `.goose/skills/`, or `~/.config/goose/skills/` with `-g`, while Goose's docs recommend `.agents/skills/`. Goose reads both folders according to its source code. Copying into `.agents/skills/` or `~/.agents/skills/` also works.

## Letta Code

```bash
git clone --depth 1 https://github.com/jeffallan/claude-skills
mkdir -p .agents/skills
cp -r claude-skills/plugin/skills/* .agents/skills/
```

Neither installer has a Letta id, so copy the skills into the project's `.agents/skills/` folder, or into `~/.letta/skills/` for your user. `npx skills add jeffallan/claude-skills -a universal -s '*' -y` writes to `.agents/skills/` too and works as a project-only shortcut. Letta's docs spell its own install command `letta install` and its README spells it `letta skills install`, so this page gives no native command until one has been run.

## Amp

```bash
npx skills add jeffallan/claude-skills -a amp -s '*' -y
```

If the Claude Code plugin is already installed, Amp needs nothing more: it reads `~/.claude/plugins/cache/`, the only agent here that does. The installer writes to `.agents/skills/`, or `~/.config/agents/skills/` with `-g`. Amp's own `amp skill add jeffallan/claude-skills` accepts a GitHub repo ([Amp manual](https://ampcode.com/docs/customize/skills)), though whether it finds skills nested under `plugin/skills/` is untested.

## OpenCode

```bash
npx skills add jeffallan/claude-skills -a opencode -s '*' -y
```

This is the opencode.ai agent from `anomalyco/opencode`. The older `opencode-ai/opencode` repo was archived and continued as Charm's Crush, which the Skills CLI targets as `-a crush`. OpenCode already loads an existing `~/.claude/skills/` or `.agents/skills/` copy, so a Claude Code skills-folder install covers it. The installer writes to `.agents/skills/`, or `~/.config/opencode/skills/` with `-g`.

## AdaL CLI

```
/plugin marketplace add jeffallan/claude-skills
```

```
/plugin install fullstack-dev-skills@fullstack-dev-skills
```

AdaL uses Claude-style plugin commands and reads the marketplace name from `marketplace.json` ([AdaL docs](https://docs.sylph.ai/customize/plugins-and-skills/)). These commands have not been run against this repo. The fallback is `npx skills add jeffallan/claude-skills -a adal -s '*' -y`, which writes to `.adal/skills/`. AdaL is now marketed as a video agent whose CLI still handles code ([adalagent.ai](https://adalagent.ai)). The old `npm install -g @sylphai/adal-cli` instruction is retired; install the CLI with `curl -fsSL https://adal.sylph.ai/install.sh | bash` ([install page](https://adalagent.ai/install)). Its docs claim Claude Code repo compatibility without listing `.claude/skills/` or `.agents/skills/`, so use `.adal/skills/` for a copy.

## Skills CLI

Two cross-agent installers can put the skills in any agent's folder:

```bash
npx skills add jeffallan/claude-skills -a <agent-id> -s '*'
npx agent-skills-cli@latest add jeffallan/claude-skills -a <agent-id>
```

[`npx skills`](https://github.com/vercel-labs/skills/blob/main/docs/commands.md) (Node 22.20 or later) picks the agent with `-a`, takes every skill with `-s '*'` or a few with `-s <name> <name>`, installs for your user with `-g`, skips prompts with `-y`, and copies with `--copy` instead of its default symlink. [`agent-skills-cli`](https://github.com/Karanjot786/agent-skills-cli) takes comma- or space-separated `-a` ids and adds `--dry-run` and `--skip-audit`. The two use different ids and folders:

| Agent | `npx skills` id | Writes to (project / user) | `agent-skills-cli` id | Writes to (project / user) |
|-------|-----------------|----------------------------|-----------------------|----------------------------|
| Claude Code | `claude-code` | `.claude/skills/` / `~/.claude/skills/` | `claude` | same |
| GitHub Copilot | `github-copilot` | `.agents/skills/` / `~/.copilot/skills/` | `copilot` | `.github/skills/` / `~/.github/skills/` |
| Codex CLI | `codex` | `.agents/skills/` / `~/.agents/skills/` | `codex` | `.codex/skills/` / `~/.codex/skills/` |
| Cursor | `cursor` | `.agents/skills/` / `~/.cursor/skills/` | `cursor` | `.cursor/skills/` / `~/.cursor/skills/` |
| Gemini CLI | `gemini-cli` | `.agents/skills/` / `~/.gemini/skills/` | `gemini-cli` | `.gemini/skills/` / `~/.gemini/skills/` |
| Goose | `goose` | `.goose/skills/` / `~/.config/goose/skills/` | `goose` | same |
| Letta Code | none | | none | |
| Amp | `amp` | `.agents/skills/` / `~/.config/agents/skills/` | `amp` | same |
| OpenCode | `opencode` | `.agents/skills/` / `~/.config/opencode/skills/` | `opencode` | `.opencode/skill/` / `~/.config/opencode/skill/` |
| AdaL CLI | `adal` | `.adal/skills/` / `~/.adal/skills/` | `adal` | same |

Sources: [skills docs/agents.md](https://github.com/vercel-labs/skills/blob/main/docs/agents.md) and the `agent-skills-cli` 1.2.0 package on [npm](https://www.npmjs.com/package/agent-skills-cli). Neither command has been run against this repo.

Caveats for `agent-skills-cli`:

- Its security scan blocks any skill with a critical finding. In a multi-skill install the blocked skill is skipped while the rest install, so the command can report success with fewer skills than the collection holds. Read the scan output, and re-run with `--skip-audit` only after reviewing it.
- Its Codex (`.codex/skills/`), OpenCode (`.opencode/skill/`, singular) and Copilot user (`~/.github/skills/`) folders do not appear in those agents' current docs. Use `npx skills add` for Codex CLI, OpenCode and GitHub Copilot.
- Its README says it installs to the agents detected on your machine, while its 1.2.0 source shows a prompt that preselects Cursor and Claude. Pass `-a` to choose.

`npx skills` symlinks each agent folder to one shared copy by default, so deleting that copy breaks every agent at once; `--copy` avoids that.

## Manual copy

```bash
git clone --depth 1 https://github.com/jeffallan/claude-skills
cp -r claude-skills/plugin/skills/* <target>/
```

Take `<target>` from the [Skills Directory Locations](#skills-directory-locations) table. A project `.agents/skills/` folder covers most agents at once; Claude Code needs `.claude/skills/` and AdaL CLI needs `.adal/skills/`. Copy whole skill folders. Each `SKILL.md` routes to files in its `references/` folder, so copying `SKILL.md` alone breaks every routing table.

## Uninstall

| Installed with | Command |
|----------------|---------|
| Claude Code plugin | `/plugin uninstall fullstack-dev-skills@fullstack-dev-skills` |
| Copilot CLI plugin | `copilot plugin uninstall fullstack-dev-skills@fullstack-dev-skills` (untested) |
| AdaL CLI plugin | `/plugin uninstall fullstack-dev-skills@fullstack-dev-skills` (untested) |
| Gemini CLI | `gemini skills uninstall <name> --scope workspace`, per skill |
| `npx skills` | `npx skills remove` with the same `-a` and `-g` flags as the install |
| Manual copy | `for d in claude-skills/plugin/skills/*/; do rm -r "<target>/$(basename "$d")"; done` |

## Discontinued agents

[Roo Code](https://github.com/RooCodeInc/Roo-Code) shut down on 2026-05-15 and its repo is archived; the final release is v3.54.0. Its folders (`.roo/skills/` and `.agents/skills/`, with `~/` forms for the user) and the `roo` installer id still work on that frozen release, which gets no fixes. Roo is the one agent that documented Windows paths: `%USERPROFILE%\.roo\skills` and `%USERPROFILE%\.agents\skills`. Its README points users to the ZooCode fork and to Cline. Whether ZooCode keeps the `.roo/skills/` folder has not been checked.

## Submit a New Agent

To add an agent to this list, open a pull request with the following:

1. **Verify compatibility**: the agent must implement the [Agent Skills specification](https://agentskills.io/specification)
2. **Add to Compatible Agents table**: include agent name (with link), developer, type, repo and skills documentation link
3. **Add to Skills Directory Locations table and add a section**: add a row with the project and user skills folders, and a `##` section for the agent with its recommended install command and any caveats
4. **Provide evidence**: link to the agent's skills documentation or announcement

### PR Template

```markdown
## Add [Agent Name] to Supported Agents

- **Agent:** [Name](https://link-to-agent)
- **Developer:** Company/Organization
- **Type:** CLI / IDE / VS Code / Desktop
- **Skills Docs:** [Documentation](https://link-to-docs)
- **Project Skills Directory:** `.agent/skills/`
- **User Skills Directory:** `~/.config/agent/skills/`

Evidence of Agent Skills support: [link to docs/announcement]
```

## Specification

- [Agent Skills Specification](https://agentskills.io/specification): the format definition
