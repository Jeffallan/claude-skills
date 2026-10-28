// JSON-LD graphs for Jeff's sites (D-009). The hub declares the one Person; every other site
// carries a stub with the same @id and points at it. No dependencies.

/** The Person's @id. Permanent, even if a site moves domain (D-026). */
export const PERSON_ID = 'https://jeffallan.github.io/#person';

const HUB_URL = new URL(PERSON_ID).origin + '/';
const ref = (id) => ({ '@id': id });
const person = ref(PERSON_ID);
const orgId = (org) => `${org.url.replace(/\/+$/, '')}/#organization`;
const graphOf = (nodes) => ({ '@context': 'https://schema.org', '@graph': nodes });

/**
 * A docs site page. site: { url (with base path, trailing slash), name, description?, repo };
 * without a site description, the repo node takes the home page's.
 * page: { url, title, description, isHome }; profile: site-footer/profile.json.
 */
export function docsPageGraph({ site, page, profile }) {
  const websiteId = `${site.url}#website`;
  const nodes = [
    { '@type': 'Person', '@id': PERSON_ID, name: profile.name, url: HUB_URL },
    {
      '@type': 'WebSite',
      '@id': websiteId,
      url: site.url,
      name: site.name,
      description: site.description,
      publisher: person,
      inLanguage: 'en',
    },
  ];
  if (page.isHome) {
    const codeId = `${site.url}#code`;
    nodes.push(
      {
        '@type': 'SoftwareSourceCode',
        '@id': codeId,
        name: site.name,
        description: site.description ?? page.description,
        url: site.url,
        codeRepository: site.repo,
        author: person,
      },
      {
        '@type': 'WebPage',
        '@id': `${page.url}#webpage`,
        url: page.url,
        name: page.title,
        description: page.description,
        isPartOf: ref(websiteId),
        about: ref(codeId),
        inLanguage: 'en',
      },
    );
  } else {
    nodes.push({
      '@type': 'TechArticle',
      '@id': `${page.url}#article`,
      url: page.url,
      headline: page.title,
      description: page.description,
      author: person,
      publisher: person,
      isPartOf: ref(websiteId),
      inLanguage: 'en',
    });
  }
  return graphOf(nodes);
}

// The title is the quoted part of an IEEE-style citation
function citationTitle(citation) {
  return citation.match(/"([^"]+?),?"/)?.[1] ?? citation;
}

function works(career) {
  const org = ref(orgId(career.organization));
  const p = career.person;
  return [
    ...p.vulnerabilities.map((v) => ({
      '@type': 'CreativeWork',
      '@id': v.url,
      name: v.id,
      description: v.summary,
      url: v.url,
      author: person,
    })),
    ...p.publications.map((pub) => ({
      '@type': 'ScholarlyArticle',
      '@id': pub.url,
      headline: citationTitle(pub.citation),
      url: pub.url,
      author: person,
    })),
    ...p.open_source.map((o) => ({
      '@type': 'SoftwareSourceCode',
      '@id': o.url,
      name: o.name,
      description: o.text,
      url: o.url,
      ...(o.url.startsWith('https://github.com/') && { codeRepository: o.url }),
      author: person,
    })),
    ...career.products.map((prod) => ({
      '@type': 'CreativeWork',
      '@id': prod.url,
      name: prod.name,
      description: prod.description,
      url: prod.url,
      creator: person,
      publisher: org,
    })),
  ];
}

/**
 * A hub page. career: site-career/career.json; profile: site-footer/profile.json;
 * knowsAbout: topics for the Person; page: { url, title, description, isHome }.
 * The home page is the Person's ProfilePage and lists the works.
 */
export function hubGraph({ career, profile, knowsAbout, page }) {
  const websiteId = `${HUB_URL}#website`;
  const org = career.organization;
  const nodes = [
    {
      '@type': 'Person',
      '@id': PERSON_ID,
      name: career.person.name,
      alternateName: career.person.alternate_name,
      url: HUB_URL,
      jobTitle: profile.role,
      description: career.person.bios.one_liner,
      sameAs: profile.profiles.map((x) => x.url),
      knowsAbout,
      affiliation: ref(orgId(org)),
    },
    { '@type': 'Organization', '@id': orgId(org), name: org.name, url: org.url },
    {
      '@type': 'WebSite',
      '@id': websiteId,
      url: HUB_URL,
      name: career.person.name,
      publisher: person,
      inLanguage: 'en',
    },
    {
      '@type': page.isHome ? 'ProfilePage' : 'WebPage',
      '@id': `${page.url}#webpage`,
      url: page.url,
      name: page.title,
      description: page.description,
      isPartOf: ref(websiteId),
      ...(page.isHome && { mainEntity: person }),
      inLanguage: 'en',
    },
  ];
  if (page.isHome) nodes.push(...works(career));
  return graphOf(nodes);
}

/** The graph as text for a <script type="application/ld+json">; `<` is escaped. */
export function jsonLdScript(graph) {
  return JSON.stringify(graph).replace(/</g, '\\u003c');
}
