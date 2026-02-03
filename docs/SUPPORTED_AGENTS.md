# Supported Agents

This plugin follows the [Agent Skills specification](https://agentskills.io/specification), an open standard for packaging reusable AI agent capabilities. Skills are portable across any agent that implements the spec.

## Compatible Agents

| Agent | Developer | Type | Skills Documentation |
|-------|-----------|------|---------------------|
| [Claude Code](https://claude.ai/claude-code) | Anthropic | CLI | Native support |
| [GitHub Copilot](https://github.com/features/copilot) | Microsoft/GitHub | VS Code, CLI | [Agent Skills in VS Code](https://code.visualstudio.com/docs/copilot/customization/agent-skills) |
| [Codex CLI](https://github.com/openai/codex) | OpenAI | CLI | [Codex Skills](https://developers.openai.com/codex/skills/) |
| [Cursor](https://cursor.com) | Cursor | IDE | [Cursor Skills](https://cursor.com/docs/context/skills) |
| [Gemini CLI](https://github.com/google-gemini/gemini-cli) | Google | CLI | [Gemini Skills](https://geminicli.com/docs/cli/skills/) |
| [Goose](https://github.com/block/goose) | Block | CLI, Desktop | [Goose Docs](https://block.github.io/goose/) |
| [Letta](https://github.com/letta-ai/letta) | Letta AI | CLI | [Letta Skills](https://docs.letta.com/letta-code/skills/) |
| [Roo Code](https://github.com/RooCodeInc/Roo-Code) | Roo Code Inc | VS Code | [Roo Skills](https://docs.roocode.com/features/skills) |
| [Amp](https://ampcode.com) | Sourcegraph | CLI, VS Code | [Amp Skills](https://ampcode.com/news/agent-skills) |
| [OpenCode](https://github.com/opencode-ai/opencode) | OpenCode AI | CLI | [OpenCode Skills](https://opencode.ai/docs/skills) |

## Submit a New Agent

To add an agent to this list, open a pull request with the following:

1. **Verify compatibility** — The agent must implement the [Agent Skills specification](https://agentskills.io/specification)
2. **Add to Compatible Agents table** — Include agent name (with link), developer, type, and skills documentation link
3. **Add to Skills Directory Locations table** — Document where the agent looks for project and user skills
4. **Provide evidence** — Link to the agent's skills documentation or announcement

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

- [Agent Skills Specification](https://agentskills.io/specification) — Format definition
