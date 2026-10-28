// Starlight route middleware that adds the page's JSON-LD graph to Starlight's own head
// (Starlight keeps writing the title, description, canonical and Open Graph tags).
// A docs site's src/routeData.ts:
//
//   import profile from './components/site-footer/profile.json';
//   import { docsJsonLd } from './components/site-seo/starlight.mjs';
//   export const onRequest = docsJsonLd({ name, repo, base: '/claude-skills', profile });
//
// and astro.config.mjs: starlight({ routeMiddleware: './src/routeData.ts' }).
import { docsPageGraph, jsonLdScript } from './graph.mjs';

/** name, repo, base and profile, plus an optional site description. */
export function docsJsonLd({ name, description, repo, base, profile }) {
  return async (context, next) => {
    const route = context.locals.starlightRoute;
    const data = route.entry.data;
    const siteUrl = new URL(`${base.replace(/\/+$/, '')}/`, context.site).href;
    const pageUrl = new URL(context.url.pathname, context.site).href;
    const graph = docsPageGraph({
      site: { url: siteUrl, name, description, repo },
      profile,
      page: {
        url: pageUrl,
        // Skill pages carry a brand prefix in title; their sidebar label is the bare name
        title: data.sidebar?.label ?? data.title,
        description: data.description,
        isHome: pageUrl === siteUrl,
      },
    });
    route.head.push({
      tag: 'script',
      attrs: { type: 'application/ld+json' },
      content: jsonLdScript(graph),
    });
    await next();
  };
}
