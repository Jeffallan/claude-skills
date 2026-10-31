#!/usr/bin/env node

/**
 * sync-content.mjs
 *
 * Pre-build script that copies repo-root content into Starlight pages under
 * site/src/content/docs/. Run via `npm run sync`. The work is done by the
 * handbook's site-sync piece; this file holds what is particular to this site.
 * Skills folder, domains, docs URL and credit come from [tool.skill-linter]
 * in pyproject.toml.
 */

import path from 'node:path';
import { syncSite } from '../src/components/site-sync/sync.mjs';

const BASE_PATH = '/claude-skills';
const GITHUB_BLOB = 'https://github.com/jeffallan/claude-skills/blob/main';

syncSite({
  repoRoot: path.resolve(import.meta.dirname, '..', '..'),
  siteDir: path.resolve(import.meta.dirname, '..'),
  base: BASE_PATH,
  githubBlob: GITHUB_BLOB,
  pageTitle: '{title} Agent Skill for Claude Code',
  docs: [
    {
      src: 'QUICKSTART.md',
      dest: 'getting-started.md',
      title: 'Getting Started',
      description: 'Installation and first steps',
      category: 'docs',
    },
    {
      src: 'SKILLS_GUIDE.md',
      dest: 'skills-guide.md',
      title: 'Skills Guide',
      description: 'Decision trees and skill combinations for choosing the right skill',
      category: 'docs',
    },
    {
      src: 'README.md',
      dest: 'readme.md',
      title: 'README',
      description: 'Project overview, architecture, and usage patterns',
      category: 'project',
    },
    {
      src: 'CONTRIBUTING.md',
      dest: 'contributing.md',
      title: 'Contributing',
      description: 'How to contribute new skills and improve existing ones',
      category: 'project',
    },
    {
      src: 'CHANGELOG.md',
      dest: 'changelog.md',
      title: 'Changelog',
      description: 'Version history and release notes',
      category: 'project',
    },
    {
      src: 'ROADMAP.md',
      dest: 'roadmap.md',
      title: 'Roadmap',
      description: 'Planned features and future direction',
      category: 'project',
    },
    {
      src: 'docs/WORKFLOW_COMMANDS.md',
      dest: 'guides/workflow-commands.md',
      title: 'Workflow Commands',
      description: 'Project workflow commands for managing development lifecycle',
      category: 'guides',
    },
    {
      src: 'docs/COMMON_GROUND.md',
      dest: 'guides/common-ground.md',
      title: 'Common Ground',
      description: 'Surface and validate hidden assumptions about projects',
      category: 'guides',
    },
    {
      src: 'docs/ATLASSIAN_MCP_SETUP.md',
      dest: 'guides/atlassian-mcp-setup.md',
      title: 'Atlassian MCP in Claude Code: Jira and Confluence',
      description:
        'Set up the Atlassian MCP server in Claude Code so Claude can read and update Jira issues and Confluence pages from your terminal',
      category: 'guides',
    },
    {
      src: 'docs/local_skill_development.md',
      dest: 'guides/local-development.md',
      title: 'Local Development',
      description: 'Develop and test skills locally',
      category: 'guides',
    },
    {
      src: 'docs/SUPPORTED_AGENTS.md',
      dest: 'guides/supported-agents.md',
      title: 'Supported Agents',
      description: 'Agents and frameworks compatible with the Agent Skills specification',
      category: 'guides',
    },
  ],
  workflowsDir: 'docs/workflow',
  linkMap: {
    '../commands/common-ground.md': `${BASE_PATH}/guides/common-ground/`,
    'commands/common-ground.md': `${BASE_PATH}/guides/common-ground/`,
    LICENSE: `${GITHUB_BLOB}/LICENSE`,
    'docs/v0.5.0-plan.md': `${GITHUB_BLOB}/docs/v0.5.0-plan.md`,
  },
  llmsOrder: [
    { category: 'docs', name: 'Docs' },
    { category: 'guides', name: 'Guides' },
    { category: 'skills', name: 'Skills' },
    { category: 'workflows', name: 'Workflows' },
    { category: 'project', name: 'Optional' },
  ],
  indexMirror: (version) => `# Claude Skills

> ${version.skillCount} specialized skills for Claude Code — progressive disclosure, context engineering, and full-stack coverage.

Transform Claude Code into your expert pair programmer across the entire development stack.

## Quick Install

\`\`\`bash
/plugin marketplace add jeffallan/claude-skills
\`\`\`

\`\`\`bash
/plugin install fullstack-dev-skills@fullstack-dev-skills
\`\`\`

## Stats

- **${version.skillCount}** specialized skills across 12 domains
- **${version.workflowCount}** project workflow commands
- **${version.referenceFileCount}** deep-dive reference files

See the [Getting Started guide](${BASE_PATH}/getting-started/) for all installation methods and first steps.
`,
});
