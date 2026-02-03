#!/usr/bin/env node

/**
 * sync-content.mjs
 *
 * Pre-build script that transforms repo-root content into Starlight-compatible
 * pages under site/src/content/docs/. Run via `npm run sync`.
 */

import fs from 'node:fs';
import path from 'node:path';
import yaml from 'js-yaml';

const ROOT = path.resolve(import.meta.dirname, '..', '..');
const DOCS_DIR = path.resolve(import.meta.dirname, '..', 'src', 'content', 'docs');
const PUBLIC_DIR = path.resolve(import.meta.dirname, '..', 'public');

const GITHUB_BLOB = 'https://github.com/jeffallan/claude-skills/blob/main';
const BASE_PATH = '/claude-skills';

const pageManifest = []; // { siteUrl, title, description, category, contentFile }

// ─── Domain label mapping ───────────────────────────────────────────
const DOMAIN_LABELS = {
  language: 'Language',
  backend: 'Backend Frameworks',
  frontend: 'Frontend & Mobile',
  infrastructure: 'Infrastructure & Cloud',
  'api-architecture': 'API & Architecture',
  quality: 'Quality & Testing',
  devops: 'DevOps & Operations',
  security: 'Security',
  'data-ml': 'Data & ML',
  platform: 'Platform',
  specialized: 'Specialized',
  workflow: 'Workflow Skills',
};

// ─── Core docs mapping (source relative to ROOT → dest relative to DOCS_DIR)
const CORE_DOCS = [
  { src: 'QUICKSTART.md', dest: 'getting-started.md', title: 'Getting Started', description: 'Installation and first steps', category: 'docs' },
  { src: 'SKILLS_GUIDE.md', dest: 'skills-guide.md', title: 'Skills Guide', description: 'Decision trees and skill combinations for choosing the right skill', category: 'docs' },
  { src: 'README.md', dest: 'readme.md', title: 'README', description: 'Project overview, architecture, and usage patterns', category: 'project' },
  { src: 'CONTRIBUTING.md', dest: 'contributing.md', title: 'Contributing', description: 'How to contribute new skills and improve existing ones', category: 'project' },
  { src: 'CHANGELOG.md', dest: 'changelog.md', title: 'Changelog', description: 'Version history and release notes', category: 'project' },
  { src: 'ROADMAP.md', dest: 'roadmap.md', title: 'Roadmap', description: 'Planned features and future direction', category: 'project' },
];

// ─── Guide docs mapping ─────────────────────────────────────────────
const GUIDE_DOCS = [
  { src: 'docs/WORKFLOW_COMMANDS.md', dest: 'guides/workflow-commands.md', title: 'Workflow Commands', description: 'Project workflow commands for managing development lifecycle' },
  { src: 'docs/COMMON_GROUND.md', dest: 'guides/common-ground.md', title: 'Common Ground', description: 'Surface and validate hidden assumptions about projects' },
  { src: 'docs/ATLASSIAN_MCP_SETUP.md', dest: 'guides/atlassian-mcp-setup.md', title: 'Atlassian MCP Setup', description: 'Configure Jira and Confluence MCP integration' },
  { src: 'docs/local_skill_development.md', dest: 'guides/local-development.md', title: 'Local Development', description: 'Develop and test skills locally' },
  { src: 'docs/SUPPORTED_AGENTS.md', dest: 'guides/supported-agents.md', title: 'Supported Agents', description: 'Agents and frameworks compatible with the Agent Skills specification' },
];

// ─── Link rewrite map (built during sync) ───────────────────────────
const linkMap = new Map();

function buildLinkMap() {
  // Core docs
  for (const { src, dest } of CORE_DOCS) {
    const slug = dest.replace(/\.md$/, '');
    addLinkVariants(src, `${BASE_PATH}/${slug}/`);
  }
  // Guide docs
  for (const { src, dest } of GUIDE_DOCS) {
    const slug = dest.replace(/\.md$/, '');
    addLinkVariants(src, `${BASE_PATH}/${slug}/`);
    // Also map the dest path for cross-references between guides
    const destSlug = dest.replace(/\.md$/, '').replace('guides/', '');
    linkMap.set(`/guides/${destSlug}/`, `${BASE_PATH}/guides/${destSlug}/`);
  }
  // README is now synced via CORE_DOCS, but add extra variant without path prefix
  linkMap.set('README.md', `${BASE_PATH}/readme/`);
  linkMap.set('./README.md', `${BASE_PATH}/readme/`);
  // Workflow cross-links (relative .md references between workflow files)
  const workflowDir = path.join(ROOT, 'docs', 'workflow');
  if (fs.existsSync(workflowDir)) {
    for (const file of fs.readdirSync(workflowDir).filter((f) => f.endsWith('.md'))) {
      const slug = file.replace(/\.md$/, '');
      linkMap.set(file, `${BASE_PATH}/workflows/${slug}/`);
      linkMap.set(`workflow/${file}`, `${BASE_PATH}/workflows/${slug}/`);
      linkMap.set(`/workflows/${slug}/`, `${BASE_PATH}/workflows/${slug}/`);
    }
  }
  // Map common internal paths that may appear without base path
  const coreSlugs = ['getting-started', 'skills-guide', 'readme', 'contributing', 'changelog', 'roadmap'];
  for (const slug of coreSlugs) {
    linkMap.set(`/${slug}/`, `${BASE_PATH}/${slug}/`);
  }
  // Map command source files to their doc site equivalents
  linkMap.set('../commands/common-ground/COMMAND.md', `${BASE_PATH}/guides/common-ground/`);
  linkMap.set('commands/common-ground/COMMAND.md', `${BASE_PATH}/guides/common-ground/`);
  // Map source-only files to GitHub
  linkMap.set('LICENSE', `${GITHUB_BLOB}/LICENSE`);
  linkMap.set('docs/v0.5.0-plan.md', `${GITHUB_BLOB}/docs/v0.5.0-plan.md`);
}

function addLinkVariants(srcPath, siteUrl) {
  const variants = [
    srcPath,
    `./${srcPath}`,
    path.basename(srcPath),
  ];
  for (const v of variants) {
    linkMap.set(v, siteUrl);
  }
}

// ─── Helpers ─────────────────────────────────────────────────────────

function ensureDir(dirPath) {
  fs.mkdirSync(dirPath, { recursive: true });
}

function stripFrontmatter(content) {
  const match = content.match(/^---\n([\s\S]*?)\n---\n([\s\S]*)$/);
  if (match) return { frontmatter: match[1], body: match[2] };
  return { frontmatter: null, body: content };
}

function parseFrontmatter(content) {
  const { frontmatter, body } = stripFrontmatter(content);
  const data = frontmatter ? yaml.load(frontmatter) : {};
  return { data, body };
}

function extractH1(body) {
  const match = body.match(/^#\s+(.+)$/m);
  return match ? match[1].trim() : null;
}

function removeH1(body) {
  return body.replace(/^#\s+.+\n*/m, '');
}

function starlightFrontmatter(fields) {
  const fm = yaml.dump(fields, { lineWidth: -1, quotingType: '"' });
  return `---\n${fm}---\n`;
}

function rewriteLinks(body) {
  // Rewrite markdown links [text](url) using linkMap
  return body.replace(/\[([^\]]*)\]\(([^)]+)\)/g, (_match, text, url) => {
    // Skip external URLs and anchors
    if (url.startsWith('http') || url.startsWith('#')) return _match;

    // Strip anchor from URL for lookup, preserve anchor
    const [urlPath, anchor] = url.split('#');
    const suffix = anchor ? `#${anchor}` : '';

    // Check linkMap first
    const resolved = linkMap.get(urlPath) || linkMap.get(urlPath.replace(/^\.\//, ''));
    if (resolved) {
      return `[${text}](${resolved}${suffix})`;
    }

    // Handle absolute paths that need base path prefix
    if (urlPath.startsWith('/') && !urlPath.startsWith(BASE_PATH)) {
      // Check if it's an internal site path (skills, guides, workflows, etc.)
      if (urlPath.match(/^\/(skills|guides|workflows|getting-started|skills-guide|readme|contributing|changelog|roadmap)\//)) {
        return `[${text}](${BASE_PATH}${urlPath}${suffix})`;
      }
    }

    return _match;
  });
}

function stripHtmlCommentTags(body) {
  // Remove <!-- SKILL_COUNT -->65<!-- /SKILL_COUNT --> style tags, keep inner text
  return body.replace(/<!--\s*\w+\s*-->(\w+)<!--\s*\/\w+\s*-->/g, '$1');
}

// ─── Clean synced content ────────────────────────────────────────────

function cleanSyncedContent() {
  const syncedDirs = ['skills', 'guides', 'workflows'];
  for (const dir of syncedDirs) {
    const full = path.join(DOCS_DIR, dir);
    if (fs.existsSync(full)) {
      fs.rmSync(full, { recursive: true });
    }
  }

  const syncedFiles = CORE_DOCS.map((d) => d.dest);
  for (const file of syncedFiles) {
    const full = path.join(DOCS_DIR, file);
    if (fs.existsSync(full)) {
      fs.unlinkSync(full);
    }
  }
}

// ─── Sync core docs ─────────────────────────────────────────────────

function syncCoreDocs() {
  for (const { src, dest, title, description, category } of CORE_DOCS) {
    const srcPath = path.join(ROOT, src);
    if (!fs.existsSync(srcPath)) {
      console.warn(`  SKIP ${src} (not found)`);
      continue;
    }

    let content = fs.readFileSync(srcPath, 'utf-8');
    const { body: rawBody } = stripFrontmatter(content);
    let body = removeH1(rawBody);
    body = stripHtmlCommentTags(body);
    body = rewriteLinks(body);

    // Remove GitHub-specific HTML (badges, images, typing SVGs)
    body = body.replace(/<p align="center">[\s\S]*?<\/p>/g, '');

    const fm = starlightFrontmatter({ title, description });
    const destPath = path.join(DOCS_DIR, dest);
    ensureDir(path.dirname(destPath));
    fs.writeFileSync(destPath, fm + '\n' + body.trim() + '\n');
    console.log(`  ${src} → ${dest}`);

    const slug = dest.replace(/\.md$/, '');
    pageManifest.push({ siteUrl: `/${slug}/`, title, description, category, contentFile: dest });
  }
}

// ─── Sync guide docs ────────────────────────────────────────────────

function syncGuideDocs() {
  for (const { src, dest, title, description } of GUIDE_DOCS) {
    const srcPath = path.join(ROOT, src);
    if (!fs.existsSync(srcPath)) {
      console.warn(`  SKIP ${src} (not found)`);
      continue;
    }

    let content = fs.readFileSync(srcPath, 'utf-8');
    const { body: rawBody } = stripFrontmatter(content);
    let body = removeH1(rawBody);
    body = stripHtmlCommentTags(body);
    body = rewriteLinks(body);

    const fm = starlightFrontmatter({ title, description });
    const destPath = path.join(DOCS_DIR, dest);
    ensureDir(path.dirname(destPath));
    fs.writeFileSync(destPath, fm + '\n' + body.trim() + '\n');
    console.log(`  ${src} → ${dest}`);

    const slug = dest.replace(/\.md$/, '');
    pageManifest.push({ siteUrl: `/${slug}/`, title, description, category: 'guides', contentFile: dest });
  }
}

// ─── Sync workflow docs ─────────────────────────────────────────────

function syncWorkflowDocs() {
  const workflowDir = path.join(ROOT, 'docs', 'workflow');
  if (!fs.existsSync(workflowDir)) {
    console.warn('  SKIP docs/workflow/ (not found)');
    return;
  }

  const files = fs.readdirSync(workflowDir).filter((f) => f.endsWith('.md'));
  for (const file of files) {
    const srcPath = path.join(workflowDir, file);
    let content = fs.readFileSync(srcPath, 'utf-8');
    const { body: rawBody } = stripFrontmatter(content);
    const h1 = extractH1(rawBody);
    let body = removeH1(rawBody);
    body = stripHtmlCommentTags(body);
    body = rewriteLinks(body);

    const title = h1 || file.replace(/\.md$/, '').replace(/-/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
    const firstPara = body.split('\n\n').find((p) => p.trim() && !p.startsWith('#') && !p.startsWith('|') && !p.startsWith('-'));
    const description = firstPara ? firstPara.trim().replace(/\n/g, ' ').slice(0, 160) : '';

    const fm = starlightFrontmatter({ title, description });
    const destPath = path.join(DOCS_DIR, 'workflows', file);
    ensureDir(path.dirname(destPath));
    fs.writeFileSync(destPath, fm + '\n' + body.trim() + '\n');
    console.log(`  docs/workflow/${file} → workflows/${file}`);

    const slug = file.replace(/\.md$/, '');
    pageManifest.push({ siteUrl: `/workflows/${slug}/`, title, description, category: 'workflows', contentFile: `workflows/${file}` });
  }
}

// ─── Build skill domain index (for related-skills linking) ──────────

function buildSkillIndex() {
  const index = new Map(); // name → { domain, title }
  const skillsDir = path.join(ROOT, 'skills');
  const dirs = fs.readdirSync(skillsDir).filter((d) =>
    fs.statSync(path.join(skillsDir, d)).isDirectory()
  );

  for (const dir of dirs) {
    const skillPath = path.join(skillsDir, dir, 'SKILL.md');
    if (!fs.existsSync(skillPath)) continue;

    const content = fs.readFileSync(skillPath, 'utf-8');
    const { data, body } = parseFrontmatter(content);
    const domain = data.metadata?.domain || 'specialized';
    const title = extractH1(body) || dir.replace(/-/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
    index.set(dir, { domain, title });
  }

  return index;
}

// ─── Sync skill pages ───────────────────────────────────────────────

function syncSkillPages(skillIndex) {
  const skillsDir = path.join(ROOT, 'skills');
  const dirs = fs.readdirSync(skillsDir).filter((d) =>
    fs.statSync(path.join(skillsDir, d)).isDirectory()
  );

  let count = 0;
  for (const dir of dirs) {
    const skillPath = path.join(skillsDir, dir, 'SKILL.md');
    if (!fs.existsSync(skillPath)) continue;

    const content = fs.readFileSync(skillPath, 'utf-8');
    const { data, body: rawBody } = parseFrontmatter(content);

    const domain = data.metadata?.domain || 'specialized';
    const role = data.metadata?.role || 'specialist';
    const scope = data.metadata?.scope || '';
    const outputFormat = data.metadata?.['output-format'] || '';
    const triggers = data.metadata?.triggers || '';
    const relatedSkills = data.metadata?.['related-skills'] || '';
    const description = data.description || '';

    const h1 = extractH1(rawBody);
    const title = h1 || dir.replace(/-/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
    let body = removeH1(rawBody);

    // Build metadata table
    const metaRows = [];
    if (domain) metaRows.push(`| **Domain** | ${DOMAIN_LABELS[domain] || domain} |`);
    if (role) metaRows.push(`| **Role** | ${role} |`);
    if (scope) metaRows.push(`| **Scope** | ${scope} |`);
    if (outputFormat) metaRows.push(`| **Output** | ${outputFormat} |`);

    let metaBlock = '';
    if (metaRows.length) {
      metaBlock = `| | |\n|---|---|\n${metaRows.join('\n')}\n\n`;
    }

    // Triggers
    let triggersBlock = '';
    if (triggers) {
      triggersBlock = `**Triggers:** ${triggers}\n\n`;
    }

    // Related skills with links
    let relatedBlock = '';
    if (relatedSkills) {
      const names = relatedSkills.split(',').map((s) => s.trim()).filter(Boolean);
      const links = names.map((name) => {
        const info = skillIndex.get(name);
        if (info) {
          return `[${info.title}](${BASE_PATH}/skills/${info.domain}/${name}/)`;
        }
        return name;
      });
      relatedBlock = `> **Related Skills:** ${links.join(' · ')}\n\n`;
    }

    // Rewrite reference table links to GitHub blob URLs
    body = body.replace(
      /`references\/([^`]+)`/g,
      (_match, refPath) =>
        `[references/${refPath}](${GITHUB_BLOB}/skills/${dir}/references/${refPath})`
    );

    body = rewriteLinks(body);

    // Assemble frontmatter (branded title + description for SEO, skills only)
    const metaTitle = `Agent Skills for Claude Code | ${title}`;
    const metaDescription = description
      ? `Claude Skills | ${title} | ${description}`
      : '';
    const fm = starlightFrontmatter({
      title: metaTitle,
      description: metaDescription,
      sidebar: { label: title },
    });

    // Assemble page
    const page = fm + '\n' + metaBlock + triggersBlock + relatedBlock + body.trim() + '\n';

    const destPath = path.join(DOCS_DIR, 'skills', domain, `${dir}.md`);
    ensureDir(path.dirname(destPath));
    fs.writeFileSync(destPath, page);
    count++;

    pageManifest.push({ siteUrl: `/skills/${domain}/${dir}/`, title, description, category: `skills:${domain}`, contentFile: `skills/${domain}/${dir}.md` });
  }

  console.log(`  ${count} skill pages synced`);
}

// ─── Clean generated public content ──────────────────────────────────

function cleanGeneratedPublicContent() {
  if (!fs.existsSync(PUBLIC_DIR)) return;

  for (const file of ['llms.txt', 'llms-full.txt', 'index.html.md']) {
    const full = path.join(PUBLIC_DIR, file);
    if (fs.existsSync(full)) fs.unlinkSync(full);
  }

  function cleanDir(dir) {
    if (!fs.existsSync(dir)) return;
    for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
      const full = path.join(dir, entry.name);
      if (entry.isDirectory()) {
        cleanDir(full);
        try { fs.rmdirSync(full); } catch { /* not empty, skip */ }
      } else if (entry.name === 'index.html.md') {
        fs.unlinkSync(full);
      }
    }
  }

  for (const dir of ['getting-started', 'skills-guide', 'skills', 'guides', 'workflows', 'contributing', 'changelog', 'roadmap']) {
    cleanDir(path.join(PUBLIC_DIR, dir));
    const full = path.join(PUBLIC_DIR, dir);
    if (fs.existsSync(full)) {
      try { fs.rmdirSync(full); } catch { /* not empty, skip */ }
    }
  }
}

// ─── Generate markdown mirrors ──────────────────────────────────────

function generateMarkdownMirrors() {
  let count = 0;
  for (const { siteUrl, title, contentFile } of pageManifest) {
    const srcPath = path.join(DOCS_DIR, contentFile);
    if (!fs.existsSync(srcPath)) {
      console.warn(`  SKIP mirror for ${siteUrl} (${contentFile} not found)`);
      continue;
    }

    const content = fs.readFileSync(srcPath, 'utf-8');
    const { body } = stripFrontmatter(content);
    const markdown = `# ${title}\n\n${body.trim()}\n`;

    const destPath = path.join(PUBLIC_DIR, siteUrl, 'index.html.md');
    ensureDir(path.dirname(destPath));
    fs.writeFileSync(destPath, markdown);
    count++;
  }
  console.log(`  ${count} markdown mirrors generated`);
}

// ─── Generate index mirror (landing page) ───────────────────────────

function generateIndexMirror() {
  const versionData = JSON.parse(fs.readFileSync(path.join(ROOT, 'version.json'), 'utf-8'));

  const markdown = `# Claude Skills

> ${versionData.skillCount} specialized skills for Claude Code — progressive disclosure, context engineering, and full-stack coverage.

Transform Claude Code into your expert pair programmer across the entire development stack.

## Quick Install

\`\`\`bash
/plugin marketplace add jeffallan/claude-skills
\`\`\`

\`\`\`bash
/plugin install fullstack-dev-skills@jeffallan
\`\`\`

## Stats

- **${versionData.skillCount}** specialized skills across 12 domains
- **${versionData.workflowCount}** project workflow commands
- **${versionData.referenceFileCount}** deep-dive reference files

See the [Getting Started guide](/getting-started/) for all installation methods and first steps.
`;

  const destPath = path.join(PUBLIC_DIR, 'index.html.md');
  ensureDir(PUBLIC_DIR);
  fs.writeFileSync(destPath, markdown);
  console.log('  index.html.md generated');
}

// ─── Generate llms.txt ──────────────────────────────────────────────

function generateLlmsTxt() {
  const versionData = JSON.parse(fs.readFileSync(path.join(ROOT, 'version.json'), 'utf-8'));

  const lines = [];
  lines.push('# Claude Skills');
  lines.push(`> ${versionData.skillCount} specialized skills for Claude Code — progressive disclosure, context engineering, and full-stack coverage.`);
  lines.push('');

  // Group manifest entries by category
  const groups = {};
  for (const entry of pageManifest) {
    if (!groups[entry.category]) groups[entry.category] = [];
    groups[entry.category].push(entry);
  }

  // Docs
  if (groups['docs']?.length) {
    lines.push('## Docs');
    for (const { siteUrl, title, description } of groups['docs']) {
      lines.push(`- [${title}](${siteUrl}index.html.md): ${description}`);
    }
    lines.push('');
  }

  // Guides
  if (groups['guides']?.length) {
    lines.push('## Guides');
    for (const { siteUrl, title, description } of groups['guides']) {
      lines.push(`- [${title}](${siteUrl}index.html.md): ${description}`);
    }
    lines.push('');
  }

  // Skills by domain (same order as DOMAIN_LABELS)
  for (const [domain, label] of Object.entries(DOMAIN_LABELS)) {
    const key = `skills:${domain}`;
    if (groups[key]?.length) {
      lines.push(`## Skills: ${label}`);
      for (const { siteUrl, title, description } of groups[key]) {
        lines.push(`- [${title}](${siteUrl}index.html.md): ${description}`);
      }
      lines.push('');
    }
  }

  // Workflows
  if (groups['workflows']?.length) {
    lines.push('## Workflows');
    for (const { siteUrl, title, description } of groups['workflows']) {
      lines.push(`- [${title}](${siteUrl}index.html.md): ${description}`);
    }
    lines.push('');
  }

  // Optional (project pages)
  if (groups['project']?.length) {
    lines.push('## Optional');
    for (const { siteUrl, title, description } of groups['project']) {
      lines.push(`- [${title}](${siteUrl}index.html.md): ${description}`);
    }
    lines.push('');
  }

  const destPath = path.join(PUBLIC_DIR, 'llms.txt');
  ensureDir(PUBLIC_DIR);
  fs.writeFileSync(destPath, lines.join('\n'));
  console.log('  llms.txt generated');
}

// ─── Generate llms-full.txt ─────────────────────────────────────────

function generateLlmsFullTxt() {
  const sections = [];

  // Order: docs → guides → skills (by domain) → workflows → project
  const orderedCategories = [
    'docs',
    'guides',
    ...Object.keys(DOMAIN_LABELS).map((d) => `skills:${d}`),
    'workflows',
    'project',
  ];

  const groups = {};
  for (const entry of pageManifest) {
    if (!groups[entry.category]) groups[entry.category] = [];
    groups[entry.category].push(entry);
  }

  for (const cat of orderedCategories) {
    if (!groups[cat]?.length) continue;
    for (const { title, contentFile } of groups[cat]) {
      const srcPath = path.join(DOCS_DIR, contentFile);
      if (!fs.existsSync(srcPath)) continue;

      const content = fs.readFileSync(srcPath, 'utf-8');
      const { body } = stripFrontmatter(content);
      sections.push(`# ${title}\n\n${body.trim()}`);
    }
  }

  const destPath = path.join(PUBLIC_DIR, 'llms-full.txt');
  ensureDir(PUBLIC_DIR);
  fs.writeFileSync(destPath, sections.join('\n\n---\n\n') + '\n');
  console.log('  llms-full.txt generated');
}

// ─── Main ────────────────────────────────────────────────────────────

function main() {
  console.log('sync-content: starting...');

  buildLinkMap();

  console.log('Cleaning synced content...');
  cleanSyncedContent();

  console.log('Syncing core docs...');
  syncCoreDocs();

  console.log('Syncing guide docs...');
  syncGuideDocs();

  console.log('Syncing workflow docs...');
  syncWorkflowDocs();

  console.log('Building skill index...');
  const skillIndex = buildSkillIndex();

  console.log('Syncing skill pages...');
  syncSkillPages(skillIndex);

  console.log('Generating LLM content...');
  cleanGeneratedPublicContent();
  generateMarkdownMirrors();
  generateIndexMirror();
  generateLlmsTxt();
  generateLlmsFullTxt();

  console.log('sync-content: done.');
}

main();
