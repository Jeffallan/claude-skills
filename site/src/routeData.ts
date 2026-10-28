// Adds the page's JSON-LD graph and og:image card (site-seo) to Starlight's head.
import profile from './components/site-footer/profile.json';
import { docsSeo } from './components/site-seo/starlight.mjs';

export const onRequest = docsSeo({
  name: 'Claude Skills',
  repo: 'https://github.com/Jeffallan/claude-skills',
  base: '/claude-skills',
  profile,
});
