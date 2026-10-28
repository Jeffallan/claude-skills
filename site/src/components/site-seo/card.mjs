// The og:image card: its style (the dark theme of site-style/tokens.css), its text, and the
// <meta> tags that point at it. No dependencies; og.mjs renders the card with astro-og-canvas.

export const CARD = {
  width: 1200,
  height: 630,
  background: [
    [15, 26, 30], // --site-bg (dark)
    [22, 38, 43], // --site-surface (dark)
  ],
  border: [32, 197, 220], // --site-accent (dark)
  text: [230, 241, 243], // --site-text (dark)
  text2: [169, 191, 197], // --site-text-2 (dark)
  logoHeight: 72,
  descriptionMax: 260,
};

// Static Fontsource files: astro-og-canvas renders the variable ones at their default weight
const FONTS = [
  'node_modules/@fontsource/outfit/files/outfit-latin-600-normal.woff2',
  'node_modules/@fontsource/outfit/files/outfit-latin-ext-600-normal.woff2',
  'node_modules/@fontsource/source-sans-3/files/source-sans-3-latin-400-normal.woff2',
  'node_modules/@fontsource/source-sans-3/files/source-sans-3-latin-ext-400-normal.woff2',
];
export const LOCKUP_FONT = FONTS[0];

/**
 * As many whole sentences as fit in 260 characters, so the text stays clear of the bottom
 * border (astro-og-canvas does not truncate). A first sentence longer than that is cut at a
 * word and ends with an ellipsis. The sentence rule matches site-sync's workflow
 * descriptions; this piece does not depend on site-sync.
 */
export function cardDescription(text) {
  if (!text) return '';
  const flat = text.replace(/\s*\n\s*/g, ' ').trim();
  const ends = [...flat.matchAll(/[.!?](?=\s+[A-Z]|$)/g)].map((m) => m.index + 1);
  const fit = ends.filter((e) => e <= CARD.descriptionMax);
  if (fit.length) return flat.slice(0, fit.at(-1));
  if (flat.length <= CARD.descriptionMax) return flat;
  // A first sentence too long for the card is cut at the last whole word that fits
  const cut = flat.slice(0, CARD.descriptionMax);
  return `${cut.slice(0, cut.lastIndexOf(' ')).replace(/[\s,;:—-]+$/, '')}…`;
}

/** astro-og-canvas options for one card. logo: path to the site's lockup PNG. */
export function cardOptions({ title, description, logo }) {
  return {
    title,
    description: cardDescription(description),
    logo: { path: logo, size: [undefined, CARD.logoHeight] },
    bgGradient: CARD.background,
    border: { color: CARD.border, width: 14, side: 'block-end' },
    padding: 80,
    font: {
      // The Fontsource files name their families after the variable font's default instance
      title: {
        families: ['Outfit Thin SemiBold', 'Outfit Thin', 'Outfit'],
        weight: 'SemiBold',
        size: 72,
        color: CARD.text,
        lineHeight: 1.1,
      },
      description: {
        families: ['Source Sans 3 ExtraLight', 'Source Sans 3'],
        size: 36,
        color: CARD.text2,
        lineHeight: 1.35,
      },
    },
    fonts: FONTS,
  };
}

/** The card's path for a page path, e.g. /claude-skills/readme/ → /claude-skills/og/readme.png. */
export function ogImagePath(pathname, base) {
  const prefix = base.replace(/\/+$/, '');
  const rest = pathname.slice(prefix.length).replace(/^\/+|\/+$/g, '');
  return `${prefix}/og/${rest || 'index'}.png`;
}

/** Starlight head entries for the card at `url` (absolute). */
export function ogImageTags({ url, alt }) {
  const meta = (property, content) => ({ tag: 'meta', attrs: { property, content } });
  return [
    meta('og:image', url),
    meta('og:image:width', String(CARD.width)),
    meta('og:image:height', String(CARD.height)),
    meta('og:image:alt', alt),
  ];
}
