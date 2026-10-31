import { defineMiddleware } from 'astro:middleware';

import { ctaFor } from './components/cta-text';
import { ctaBlock, insertBeforeFirstH2 } from './components/site-contact/cta-html.mjs';

// Docs pages are Markdown, where a component can't go: pages whose call to
// action goes near the top get it in the built HTML, before the first heading.
export const onRequest = defineMiddleware(async (context, next) => {
  const response = await next();
  const { where, text } = ctaFor(context.url.pathname);
  if (where !== 'intro') return response;
  const html = await response.text();
  return new Response(insertBeforeFirstH2(html, ctaBlock({ text, cta: 'page-intro' })), response);
});
