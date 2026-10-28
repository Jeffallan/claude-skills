// site-sync: copies a skill repo's skills, docs and workflow docs into its Starlight site, and
// writes the Markdown copies, llms-full.txt and the page list that llms.mjs turns into llms.txt.
// Each docs site calls syncSite() from its scripts/sync-content.mjs before astro dev and build.
//
// Shared facts come from [tool.skill-linter] in the repo's pyproject.toml (D-032): skills_dir,
// domains, docs_url and credit. Everything else is the site's config.
import fs from 'node:fs';
import path from 'node:path';
import * as yaml from 'js-yaml';
import { parse as parseToml } from 'smol-toml';

import { findH1, removeH1, firstSentences, stripTrailingLines } from './markdown.mjs';
import { PAGES_FILE } from './llms.mjs';

const WORKFLOW_DESCRIPTION_MAX = 160;

/**
 * config:
 *   repoRoot, siteDir     absolute paths
 *   base                  the site's base path, e.g. '/claude-skills'
 *   githubBlob            e.g. 'https://github.com/Jeffallan/claude-skills/blob/main'
 *   pageTitle             skill page <title> template, e.g. 'Writing With Agents | {title}'
 *   docs                  [{ src, dest, title, description, category }] copied as they are
 *   workflowsDir          repo-relative folder of workflow docs, or null
 *   linkMap               extra { sourceLink: siteUrl } entries
 *   llmsOrder             llms.txt and llms-full.txt sections: [{ category, name }], where the
 *                         category 'skills' stands for one section per domain
 *   indexMirror(version)  Markdown for the home page's copy, given version.json
 */
export function syncSite(config) {
  const linter = readLinterConfig(config.repoRoot);
  const ctx = {
    ...config,
    linter,
    docsDir: path.join(config.siteDir, 'src', 'content', 'docs'),
    publicDir: path.join(config.siteDir, 'public'),
    pages: [],
    links: new Map(),
  };

  console.log('site-sync: starting...');
  buildLinkMap(ctx);
  cleanSyncedContent(ctx);
  syncDocs(ctx);
  syncWorkflowDocs(ctx);
  syncSkillPages(ctx, buildSkillIndex(ctx));
  cleanPublic(ctx);
  writeMarkdownCopies(ctx);
  writeIndexCopy(ctx);
  const order = expandOrder(ctx);
  writeLlmsFullTxt(ctx, order);
  writePagesFile(ctx, order);
  console.log('site-sync: done.');
}

// ─── Config ─────────────────────────────────────────────────────────

function readLinterConfig(repoRoot) {
  const file = path.join(repoRoot, 'pyproject.toml');
  const table = parseToml(fs.readFileSync(file, 'utf-8')).tool?.['skill-linter'];
  if (!table) throw new Error(`site-sync: no [tool.skill-linter] table in ${file}`);
  for (const key of ['skills_dir', 'domains', 'docs_url']) {
    if (!table[key]) throw new Error(`site-sync: [tool.skill-linter] in ${file} has no ${key}`);
  }
  return {
    skillsDir: table.skills_dir,
    domains: table.domains,
    docsUrl: table.docs_url,
    credit: table.credit?.text ?? null,
  };
}

function expandOrder(ctx) {
  return ctx.llmsOrder.flatMap(({ category, name }) =>
    category === 'skills'
      ? ctx.linter.domains.map((d) => ({ category: `skills:${d.id}`, name: `Skills: ${d.label}` }))
      : [{ category, name }],
  );
}

// ─── Links ──────────────────────────────────────────────────────────

function slugOf(dest) {
  return dest.replace(/\.md$/, '');
}

function buildLinkMap(ctx) {
  const { base, links } = ctx;
  for (const { src, dest } of ctx.docs) {
    const url = `${base}/${slugOf(dest)}/`;
    for (const v of [src, `./${src}`, path.basename(src)]) links.set(v, url);
    links.set(`/${slugOf(dest)}/`, url);
  }
  if (ctx.workflowsDir) {
    for (const file of markdownFiles(path.join(ctx.repoRoot, ctx.workflowsDir))) {
      const url = `${base}/workflows/${slugOf(file)}/`;
      links.set(file, url);
      links.set(`workflow/${file}`, url);
      links.set(`/workflows/${slugOf(file)}/`, url);
    }
  }
  for (const [from, to] of Object.entries(ctx.linkMap ?? {})) links.set(from, to);

  // Site-absolute links that need the base path: every first path segment the site has
  const sections = new Set([
    'skills',
    'workflows',
    ...ctx.docs.map((d) => slugOf(d.dest).split('/')[0]),
  ]);
  ctx.internalPath = new RegExp(`^/(${[...sections].join('|')})/`);
}

function rewriteLinks(ctx, body) {
  return body.replace(/\[([^\]]*)\]\(([^)]+)\)/g, (match, text, url) => {
    if (url.startsWith('http') || url.startsWith('#')) return match;
    const [urlPath, anchor] = url.split('#');
    const suffix = anchor ? `#${anchor}` : '';
    const resolved = ctx.links.get(urlPath) || ctx.links.get(urlPath.replace(/^\.\//, ''));
    if (resolved) return `[${text}](${resolved}${suffix})`;
    if (
      urlPath.startsWith('/') &&
      !urlPath.startsWith(ctx.base) &&
      ctx.internalPath.test(urlPath)
    ) {
      return `[${text}](${ctx.base}${urlPath}${suffix})`;
    }
    return match;
  });
}

// ─── Helpers ────────────────────────────────────────────────────────

function markdownFiles(dir) {
  return fs.existsSync(dir)
    ? fs
        .readdirSync(dir)
        .filter((f) => f.endsWith('.md'))
        .sort()
    : [];
}

function splitFrontmatter(content) {
  const match = content.match(/^---\n([\s\S]*?)\n---\n([\s\S]*)$/);
  return match ? { frontmatter: match[1], body: match[2] } : { frontmatter: null, body: content };
}

function titleCase(name) {
  return name.replace(/-/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
}

function starlightFrontmatter(fields) {
  return `---\n${yaml.dump(fields, { lineWidth: -1, quotingType: '"' })}---\n`;
}

// Remove <!-- SKILL_COUNT -->65<!-- /SKILL_COUNT --> style tags, keep the inner text
function stripCountMarkers(body) {
  return body.replace(/<!--\s*\w+\s*-->([^<]+?)<!--\s*\/\w+\s*-->/g, '$1');
}

function writePage(ctx, dest, frontmatter, body) {
  const file = path.join(ctx.docsDir, dest);
  fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.writeFileSync(file, frontmatter + '\n' + body.trim() + '\n');
}

// ─── Synced pages ───────────────────────────────────────────────────

function cleanSyncedContent(ctx) {
  const dirs = new Set(['skills', 'workflows']);
  for (const { dest } of ctx.docs) {
    if (dest.includes('/')) dirs.add(dest.split('/')[0]);
    else fs.rmSync(path.join(ctx.docsDir, dest), { force: true });
  }
  for (const dir of dirs) fs.rmSync(path.join(ctx.docsDir, dir), { recursive: true, force: true });
}

function syncDocs(ctx) {
  for (const { src, dest, title, description, category } of ctx.docs) {
    const file = path.join(ctx.repoRoot, src);
    if (!fs.existsSync(file)) {
      console.warn(`  SKIP ${src} (not found)`);
      continue;
    }
    let body = removeH1(splitFrontmatter(fs.readFileSync(file, 'utf-8')).body);
    body = rewriteLinks(ctx, stripCountMarkers(body));
    // GitHub-only HTML (badges, centered images)
    body = body.replace(/<p align="center">[\s\S]*?<\/p>/g, '');
    // A rule left at the very top would sit right under the frontmatter, and Astro 7
    // reads the text up to the next rule as a second frontmatter block
    body = body.trim().replace(/^---[ \t]*\n/, '');
    writePage(ctx, dest, starlightFrontmatter({ title, description }), body);
    ctx.pages.push({
      siteUrl: `/${slugOf(dest)}/`,
      title,
      description,
      category,
      contentFile: dest,
    });
  }
}

function syncWorkflowDocs(ctx) {
  if (!ctx.workflowsDir) return;
  const dir = path.join(ctx.repoRoot, ctx.workflowsDir);
  for (const file of markdownFiles(dir)) {
    const raw = splitFrontmatter(fs.readFileSync(path.join(dir, file), 'utf-8')).body;
    const title = findH1(raw) || titleCase(slugOf(file));
    const body = rewriteLinks(ctx, stripCountMarkers(removeH1(raw)));
    const firstParagraph = body
      .split('\n\n')
      .find((p) => p.trim() && !p.startsWith('#') && !p.startsWith('|') && !p.startsWith('-'));
    const description = firstParagraph
      ? firstSentences(firstParagraph, WORKFLOW_DESCRIPTION_MAX)
      : '';
    const dest = `workflows/${file}`;
    writePage(ctx, dest, starlightFrontmatter({ title, description }), body);
    ctx.pages.push({
      siteUrl: `/workflows/${slugOf(file)}/`,
      title,
      description,
      category: 'workflows',
      contentFile: dest,
    });
  }
}

function readSkills(ctx) {
  const dir = path.join(ctx.repoRoot, ctx.linter.skillsDir);
  const known = new Set(ctx.linter.domains.map((d) => d.id));
  return fs
    .readdirSync(dir)
    .sort()
    .filter((name) => fs.existsSync(path.join(dir, name, 'SKILL.md')))
    .map((name) => {
      const file = path.join(dir, name, 'SKILL.md');
      const { frontmatter, body } = splitFrontmatter(fs.readFileSync(file, 'utf-8'));
      const data = frontmatter ? yaml.load(frontmatter) : {};
      const domain = data.metadata?.domain;
      if (!known.has(domain)) {
        throw new Error(
          `site-sync: ${file} has domain "${domain}", not one of [tool.skill-linter] domains`,
        );
      }
      return { name, data, body, domain, title: findH1(body) || titleCase(name) };
    });
}

function buildSkillIndex(ctx) {
  ctx.skills = readSkills(ctx);
  return new Map(ctx.skills.map((s) => [s.name, s]));
}

function syncSkillPages(ctx, index) {
  const labels = Object.fromEntries(ctx.linter.domains.map((d) => [d.id, d.label]));
  for (const { name, data, body: raw, domain, title } of ctx.skills) {
    const meta = data.metadata ?? {};
    const description = data.description || '';

    const rows = [
      ['Domain', labels[domain]],
      ['Role', meta.role || 'specialist'],
      ['Scope', meta.scope],
      ['Output', meta['output-format']],
    ].filter(([, v]) => v);
    const metaBlock = `| | |\n|---|---|\n${rows.map(([k, v]) => `| **${k}** | ${v} |`).join('\n')}\n\n`;
    const triggersBlock = meta.triggers ? `**Triggers:** ${meta.triggers}\n\n` : '';
    let relatedBlock = '';
    if (meta['related-skills']) {
      const links = meta['related-skills']
        .split(',')
        .map((s) => s.trim())
        .filter(Boolean)
        .map((n) => {
          const info = index.get(n);
          return info ? `[${info.title}](${ctx.base}/skills/${info.domain}/${n}/)` : n;
        });
      relatedBlock = `> **Related Skills:** ${links.join(' · ')}\n\n`;
    }

    let body = removeH1(raw);
    body = body.replace(
      /`references\/([^`]+)`/g,
      (_m, ref) =>
        `[references/${ref}](${ctx.githubBlob}/${ctx.linter.skillsDir}/${name}/references/${ref})`,
    );
    // The documentation backlink and the maintainer credit are in SKILL.md for aggregators
    // (skills.sh and the like). On the docs site the backlink points at the page itself and
    // the footer already carries the credit.
    const backlink = `[Documentation](${ctx.linter.docsUrl.replace('{domain}', domain).replace('{name}', name)})`;
    body = stripTrailingLines(body, [backlink, ctx.linter.credit]);
    body = rewriteLinks(ctx, body);

    // D-028: the meta description is the skill description as written
    const frontmatter = starlightFrontmatter({
      title: ctx.pageTitle.replace('{title}', title),
      description,
      sidebar: { label: title },
    });
    const dest = `skills/${domain}/${name}.md`;
    writePage(ctx, dest, frontmatter, metaBlock + triggersBlock + relatedBlock + body.trim());
    ctx.pages.push({
      siteUrl: `/skills/${domain}/${name}/`,
      title,
      description,
      category: `skills:${domain}`,
      contentFile: dest,
    });
  }
  console.log(`  ${ctx.skills.length} skill pages synced`);
}

// ─── Generated files under public/ ──────────────────────────────────

function cleanPublic(ctx) {
  if (!fs.existsSync(ctx.publicDir)) return;
  for (const file of ['llms.txt', 'llms-full.txt'])
    fs.rmSync(path.join(ctx.publicDir, file), { force: true });
  // Every index.html.md under public/ is a copy this script wrote; drop folders left empty
  const sweep = (dir) => {
    for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
      const full = path.join(dir, entry.name);
      if (entry.isDirectory()) {
        sweep(full);
        if (!fs.readdirSync(full).length) fs.rmdirSync(full);
      } else if (entry.name === 'index.html.md') {
        fs.unlinkSync(full);
      }
    }
  };
  sweep(ctx.publicDir);
}

function pageBody(ctx, contentFile) {
  return splitFrontmatter(
    fs.readFileSync(path.join(ctx.docsDir, contentFile), 'utf-8'),
  ).body.trim();
}

function writeMarkdownCopies(ctx) {
  for (const { siteUrl, title, contentFile } of ctx.pages) {
    const file = path.join(ctx.publicDir, siteUrl, 'index.html.md');
    fs.mkdirSync(path.dirname(file), { recursive: true });
    fs.writeFileSync(file, `# ${title}\n\n${pageBody(ctx, contentFile)}\n`);
  }
  console.log(`  ${ctx.pages.length} Markdown copies written`);
}

function writeIndexCopy(ctx) {
  const version = JSON.parse(fs.readFileSync(path.join(ctx.repoRoot, 'version.json'), 'utf-8'));
  fs.mkdirSync(ctx.publicDir, { recursive: true });
  fs.writeFileSync(path.join(ctx.publicDir, 'index.html.md'), ctx.indexMirror(version));
}

function writeLlmsFullTxt(ctx, order) {
  const sections = order.flatMap(({ category }) =>
    ctx.pages
      .filter((p) => p.category === category)
      .map(({ title, contentFile }) => `# ${title}\n\n${pageBody(ctx, contentFile)}`),
  );
  fs.writeFileSync(path.join(ctx.publicDir, 'llms-full.txt'), sections.join('\n\n---\n\n') + '\n');
  console.log('  llms-full.txt written');
}

function writePagesFile(ctx, order) {
  const file = path.join(ctx.siteDir, PAGES_FILE);
  fs.mkdirSync(path.dirname(file), { recursive: true });
  const pages = ctx.pages.map(({ siteUrl, title, description, category }) => ({
    siteUrl,
    title,
    description,
    category,
  }));
  fs.writeFileSync(file, JSON.stringify({ pages, order }, null, 2) + '\n');
}
