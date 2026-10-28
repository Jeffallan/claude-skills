// Adds the page's JSON-LD graph (site-seo) to Starlight's head.
import profile from './components/site-footer/profile.json';
import { docsJsonLd } from './components/site-seo/starlight.mjs';

export const onRequest = docsJsonLd({
  name: 'Claude Skills',
  repo: 'https://github.com/Jeffallan/claude-skills',
  base: '/claude-skills',
  profile,
});
