// Starlight route middleware that adds the page's JSON-LD graph and its og:image card to
// Starlight's own head (Starlight keeps writing the title, description, canonical and the
// other Open Graph tags). The cards come from og.mjs at <base>/og/<page>.png.
// A docs site's src/routeData.ts:
//
//   import profile from './components/site-footer/profile.json';
//   import { docsSeo } from './components/site-seo/starlight.mjs';
//   export const onRequest = docsSeo({ name, repo, base: '/claude-skills', profile });
//
// and astro.config.mjs: starlight({ routeMiddleware: './src/routeData.ts' }).
import { ogImagePath, ogImageTags } from './card.mjs';
import { docsPageGraph, jsonLdScript } from './graph.mjs';

/** name, repo, base and profile, plus an optional site description. */
export function docsSeo({ name, description, repo, base, profile }) {
  return async (context, next) => {
    const route = context.locals.starlightRoute;
    const data = route.entry.data;
    const siteUrl = new URL(`${base.replace(/\/+$/, '')}/`, context.site).href;
    const pageUrl = new URL(context.url.pathname, context.site).href;
    // Skill pages carry a brand prefix in title; their sidebar label is the bare name
    const title = data.sidebar?.label ?? data.title;
    const graph = docsPageGraph({
      site: { url: siteUrl, name, description, repo },
      profile,
      page: {
        url: pageUrl,
        title,
        description: data.description,
        isHome: pageUrl === siteUrl,
      },
    });
    route.head.push({
      tag: 'script',
      attrs: { type: 'application/ld+json' },
      content: jsonLdScript(graph),
    });
    // Starlight's 404 page is not in the docs collection, so it has no card
    if (route.id !== '404') {
      const image = new URL(ogImagePath(context.url.pathname, base), context.site).href;
      route.head.push(...ogImageTags({ url: image, alt: title }));
    }
    await next();
  };
}
