// Builds the `sections` that astro-seo-graph's seoGraph({ llmsTxt }) renders into llms.txt (D-028).
// No dependencies: astro.config.mjs imports it.
import fs from 'node:fs';
import path from 'node:path';

/** Where site-sync writes the page list, relative to the site folder. */
export const PAGES_FILE = path.join('node_modules', '.cache', 'site-sync', 'pages.json');

const FULL_TEXT = {
  title: 'Full text',
  file: 'llms-full.txt',
  description: 'Every page on this site in one Markdown file',
};

/**
 * pages: [{ siteUrl, title, description, category }] as site-sync writes them.
 * order: [{ category, name }], the sections in the order llms.txt lists them.
 * siteUrl: the site's absolute URL including its base path.
 * The Optional section (added when the order has none) ends with a link to llms-full.txt.
 */
export function llmsSections({ pages, order, siteUrl }) {
  const root = siteUrl.replace(/\/+$/, '');
  const sections = order.map(({ category, name }) => ({
    name,
    links: pages
      .filter((p) => p.category === category)
      .map((p) => ({
        title: p.title,
        url: `${root}${p.siteUrl}index.html.md`,
        description: p.description,
      })),
  }));
  let optional = sections.find((s) => s.name === 'Optional');
  if (!optional) sections.push((optional = { name: 'Optional', links: [] }));
  optional.links.push({
    title: FULL_TEXT.title,
    url: `${root}/${FULL_TEXT.file}`,
    description: FULL_TEXT.description,
  });
  return sections.filter((s) => s.links.length);
}

/** llmsSections, reading the page list that site-sync wrote under `siteDir`. */
export function llmsSectionsFromSync(siteDir, siteUrl) {
  const file = path.join(siteDir, PAGES_FILE);
  if (!fs.existsSync(file)) throw new Error(`site-sync: ${file} not found; run npm run sync first`);
  const { pages, order } = JSON.parse(fs.readFileSync(file, 'utf-8'));
  return llmsSections({ pages, order, siteUrl });
}
