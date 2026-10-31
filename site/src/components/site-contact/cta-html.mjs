// Helpers for putting the call to action inside Markdown pages, where an
// Astro component can't go. A site's src/middleware.ts uses them on the
// built HTML of the pages it chooses. Comes from the handbook's
// personal-sites/site-contact; change it there, not in the project.
//
// The block matches ContactCTA.astro, and its button opens the page's one
// ContactDialog (rendered by SiteFooter).

const escape = (text) =>
  text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');

/** HTML for a call to action: a line of text and a button that opens the dialog. */
export function ctaBlock({ text, cta = 'page-intro', label = 'Contact' }) {
  return (
    `<aside class="site-cta" aria-label="Contact">` +
    `<p class="site-cta-text">${escape(text)}</p>` +
    `<button type="button" class="site-cta-button" data-site-cta-open data-cta="${escape(cta)}">${escape(label)}</button>` +
    `</aside>`
  );
}

/**
 * Inserts `block` before the first h2 inside Starlight's content area
 * (.sl-markdown-content), skipping headings elsewhere such as "On this page".
 * Returns the page unchanged when there is no content area or no h2 in it.
 */
export function insertBeforeFirstH2(html, block) {
  const content = html.indexOf('<div class="sl-markdown-content');
  if (content === -1) return html;
  const rest = html.slice(content);
  const match = rest.match(/<div class="sl-heading-wrapper level-h2|<h2[\s>]/);
  if (!match || match.index === undefined) return html;
  const at = content + match.index;
  return html.slice(0, at) + block + html.slice(at);
}
