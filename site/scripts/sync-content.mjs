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

const GITHUB_BLOB = 'https://github.com/jeffallan/claude-skills/blob/main';

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

// ─── Role → sidebar badge ───────────────────────────────────────────
const ROLE_BADGES = {
  specialist: { text: 'Specialist', variant: 'default' },
  expert: { text: 'Expert', variant: 'success' },
  architect: { text: 'Architect', variant: 'caution' },
  engineer: { text: 'Engineer', variant: 'note' },
};

// ─── Core docs mapping (source relative to ROOT → dest relative to DOCS_DIR)
const CORE_DOCS = [
  { src: 'QUICKSTART.md', dest: 'getting-started.md', title: 'Getting Started' },
  { src: 'SKILLS_GUIDE.md', dest: 'skills-guide.md', title: 'Skills Guide' },
  { src: 'CONTRIBUTING.md', dest: 'contributing.md', title: 'Contributing' },
  { src: 'CHANGELOG.md', dest: 'changelog.md', title: 'Changelog' },
  { src: 'ROADMAP.md', dest: 'roadmap.md', title: 'Roadmap' },
];

// ─── Guide docs mapping ─────────────────────────────────────────────
const GUIDE_DOCS = [
  { src: 'docs/WORKFLOW_COMMANDS.md', dest: 'guides/workflow-commands.md', title: 'Workflow Commands' },
  { src: 'docs/COMMON_GROUND.md', dest: 'guides/common-ground.md', title: 'Common Ground' },
  { src: 'docs/ATLASSIAN_MCP_SETUP.md', dest: 'guides/atlassian-mcp-setup.md', title: 'Atlassian MCP Setup' },
  { src: 'docs/local_skill_development.md', dest: 'guides/local-development.md', title: 'Local Development' },
];

// ─── Link rewrite map (built during sync) ───────────────────────────
const linkMap = new Map();

function buildLinkMap() {
  // Core docs
  for (const { src, dest } of CORE_DOCS) {
    const slug = dest.replace(/\.md$/, '');
    addLinkVariants(src, `/${slug}/`);
  }
  // Guide docs
  for (const { src, dest } of GUIDE_DOCS) {
    const slug = dest.replace(/\.md$/, '');
    addLinkVariants(src, `/${slug}/`);
  }
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
    const resolved = linkMap.get(urlPath) || linkMap.get(urlPath.replace(/^\.\//, ''));
    if (resolved) {
      const suffix = anchor ? `#${anchor}` : '';
      return `[${text}](${resolved}${suffix})`;
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
  for (const { src, dest, title } of CORE_DOCS) {
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

    const fm = starlightFrontmatter({ title });
    const destPath = path.join(DOCS_DIR, dest);
    ensureDir(path.dirname(destPath));
    fs.writeFileSync(destPath, fm + '\n' + body.trim() + '\n');
    console.log(`  ${src} → ${dest}`);
  }
}

// ─── Sync guide docs ────────────────────────────────────────────────

function syncGuideDocs() {
  for (const { src, dest, title } of GUIDE_DOCS) {
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

    const fm = starlightFrontmatter({ title });
    const destPath = path.join(DOCS_DIR, dest);
    ensureDir(path.dirname(destPath));
    fs.writeFileSync(destPath, fm + '\n' + body.trim() + '\n');
    console.log(`  ${src} → ${dest}`);
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
    const fm = starlightFrontmatter({ title });
    const destPath = path.join(DOCS_DIR, 'workflows', file);
    ensureDir(path.dirname(destPath));
    fs.writeFileSync(destPath, fm + '\n' + body.trim() + '\n');
    console.log(`  docs/workflow/${file} → workflows/${file}`);
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
          return `[${info.title}](/skills/${info.domain}/${name}/)`;
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

    // Build sidebar badge
    const badge = ROLE_BADGES[role] || ROLE_BADGES.specialist;

    // Assemble frontmatter
    const fm = starlightFrontmatter({
      title,
      description,
      sidebar: { badge },
    });

    // Assemble page
    const page = fm + '\n' + metaBlock + triggersBlock + relatedBlock + body.trim() + '\n';

    const destPath = path.join(DOCS_DIR, 'skills', domain, `${dir}.md`);
    ensureDir(path.dirname(destPath));
    fs.writeFileSync(destPath, page);
    count++;
  }

  console.log(`  ${count} skill pages synced`);
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

  console.log('sync-content: done.');
}

main();
