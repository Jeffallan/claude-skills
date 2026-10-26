import { defineMiddleware } from 'astro:middleware';

import { ctaText, isSkillPage } from './components/cta-text';
import { ctaBlock, insertBeforeFirstH2 } from './components/site-contact/cta-html.mjs';

// Skill pages are Markdown, where a component can't go: put the call to
// action into the built HTML, before the page's first heading.
export const onRequest = defineMiddleware(async (context, next) => {
  const response = await next();
  if (!isSkillPage(context.url.pathname)) return response;
  const html = await response.text();
  const block = ctaBlock({ text: ctaText, cta: 'page-intro' });
  return new Response(insertBeforeFirstH2(html, block), response);
});
