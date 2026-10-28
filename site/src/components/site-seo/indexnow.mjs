// IndexNow for Jeff's sites: one key, served by the hub at the domain root, so it covers every
// site on jeffallan.github.io. The key is public by design (search engines fetch it).
// No dependencies.

export const INDEXNOW_KEY = '17c975f34bbe97c32cf68c4f58503478';
const HOST = 'jeffallan.github.io';
export const KEY_LOCATION = `https://${HOST}/${INDEXNOW_KEY}.txt`;

/**
 * astro-seo-graph's seoGraph({ indexNow }) option for the site at siteUrl (with its base path),
 * or undefined unless INDEXNOW_SUBMIT is '1'. Only the deploy build sets it, so pull request
 * and other builds never submit. Incremental: only pages changed since the live site's
 * indexnow-manifest.json are submitted.
 */
export function indexNowOptions(siteUrl, env = process.env) {
  if (env.INDEXNOW_SUBMIT !== '1') return undefined;
  return {
    key: INDEXNOW_KEY,
    host: HOST,
    siteUrl: siteUrl.replace(/\/+$/, ''),
    keyLocation: KEY_LOCATION,
    incremental: true,
  };
}
