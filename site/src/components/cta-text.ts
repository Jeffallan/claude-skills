// Where this site's call to action goes, and what it says, per page.
// Used by the hero (Hero.astro), Markdown pages (middleware.ts) and the end
// of other pages (Footer.astro).

export const ctaText = 'Need help putting these skills to work on your team?';

type Placement = { where: 'intro' | 'end' | 'none'; text: string };

// Reference pages carry no call to action; the footer's Contact link still
// reaches the form.
const REFERENCE = ['readme', 'changelog', 'contributing', 'roadmap', 'privacy'];

/** Placement for a page, from its path under the site's base. */
export function ctaFor(pathname: string): Placement {
  const base = import.meta.env.BASE_URL.replace(/\/?$/, '/');
  const path = '/' + pathname.slice(base.length).replace(/^\/?/, '');
  const top = path.split('/')[1] ?? '';

  if (REFERENCE.includes(top)) return { where: 'none', text: ctaText };
  if (top === 'workflows') {
    return { where: 'intro', text: 'Want help running these workflows with your team?' };
  }
  if (top === 'getting-started') {
    return { where: 'intro', text: 'Setting this up for a team? I can help.' };
  }
  if (/^\/skills\/[^/]+\/[^/]+\/$/.test(path) || top === 'skills-guide' || top === 'guides') {
    return { where: 'intro', text: ctaText };
  }
  return { where: 'end', text: ctaText };
}
