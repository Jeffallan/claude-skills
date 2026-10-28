// og:image cards for every docs page, at /claude-skills/og/<page>.png (site-seo).
import { getCollection } from 'astro:content';
import { docsPages, ogRoute } from '../../components/site-seo/og.mjs';

export const { getStaticPaths, GET } = await ogRoute({
  name: 'Claude Skills',
  pages: docsPages(await getCollection('docs')),
});
