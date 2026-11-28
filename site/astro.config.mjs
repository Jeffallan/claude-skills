import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';
import starlightLinksValidator from 'starlight-links-validator';
import seoGraph from '@jdevalk/astro-seo-graph/integration';
import { llmsSectionsFromSync } from './src/components/site-sync/llms.mjs';
import { indexNowOptions } from './src/components/site-seo/indexnow.mjs';

const SITE_URL = 'https://jeffallan.github.io/claude-skills';
const DESCRIPTION =
  '72 specialized skills for Claude Code — progressive disclosure, context engineering, and full-stack coverage.';

export default defineConfig({
  site: 'https://jeffallan.github.io',
  base: '/claude-skills',
  integrations: [
    starlight({
      title: 'Claude Skills',
      description: DESCRIPTION,
      routeMiddleware: './src/routeData.ts',
      plugins: [starlightLinksValidator()],
      customCss: [
        '@fontsource-variable/outfit',
        '@fontsource-variable/source-sans-3',
        './src/components/site-style/tokens.css',
        './src/components/site-style/starlight.css',
        './src/styles/custom.css',
      ],
      head: [
        {
          tag: 'meta',
          attrs: {
            name: 'google-site-verification',
            content: 'F01KE0U-EHMrEHtYf5nOpt5tlbWeoMoil6Wkp0x5ONQ',
          },
        },
        {
          tag: 'script',
          attrs: {
            async: true,
            src: 'https://www.googletagmanager.com/gtag/js?id=G-QVMEHEZBXE',
          },
        },
        {
          tag: 'script',
          content: `
            window.dataLayer = window.dataLayer || [];
            function gtag(){dataLayer.push(arguments);}
            gtag('js', new Date());
            gtag('config', 'G-QVMEHEZBXE');
          `,
        },
        {
          tag: 'link',
          attrs: {
            rel: 'alternate',
            type: 'text/plain',
            href: '/claude-skills/llms.txt',
            title: 'LLM-friendly content',
          },
        },
        {
          tag: 'script',
          attrs: {
            type: 'module',
          },
          content: `
            import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs';
            mermaid.initialize({ startOnLoad: false, theme: 'dark' });

            function renderMermaid() {
              document.querySelectorAll('pre[data-language="mermaid"]').forEach((pre, i) => {
                const lines = pre.querySelectorAll('.ec-line');
                const code = Array.from(lines).map(line => line.textContent).join('\\n');
                const div = document.createElement('div');
                div.className = 'mermaid';
                div.id = 'mermaid-' + i;
                div.textContent = code;
                const block = pre.closest('.expressive-code');
                // Expressive Code puts its one stylesheet and script inside the first
                // code block on the page. Keep them when that block is a diagram.
                block.querySelectorAll('link, script').forEach((el) => document.head.append(el));
                block.replaceWith(div);
              });
              mermaid.run();
            }

            renderMermaid();
            document.addEventListener('astro:page-load', renderMermaid);
          `,
        },
      ],
      components: {
        SocialIcons: './src/components/SocialIcons.astro',
        Header: './src/components/Header.astro',
        Footer: './src/components/Footer.astro',
        Hero: './src/components/Hero.astro',
      },
      social: [
        {
          icon: 'github',
          label: 'GitHub',
          href: 'https://github.com/jeffallan/claude-skills',
        },
      ],
      sidebar: [
        { label: 'Home', link: '/' },
        { label: 'Getting Started', link: '/getting-started/' },
        { label: 'Skills Guide', link: '/skills-guide/' },
        {
          label: 'Guides',
          items: [
            { label: 'Workflow Commands', link: '/guides/workflow-commands/' },
            { label: 'Intake', link: '/guides/intake/' },
            { label: 'Tracker Setup', link: '/guides/tracker-setup/' },
            { label: 'Goal Runs', link: '/guides/goal-runs/' },
            { label: 'Tracker Setup', link: '/guides/tracker-setup/' },
            { label: 'Intake', link: '/guides/intake/' },
            { label: 'Goal Runs', link: '/guides/goal-runs/' },
            { label: 'Common Ground', link: '/guides/common-ground/' },
            {
              label: 'Atlassian MCP Setup',
              link: '/guides/atlassian-mcp-setup/',
            },
            {
              label: 'Local Development',
              link: '/guides/local-development/',
            },
            {
              label: 'Supported Agents',
              link: '/guides/supported-agents/',
            },
          ],
        },
        {
          label: 'Workflows',
          collapsed: true,
          items: [
            {
              label: 'Intake Phase',
              collapsed: true,
              items: [
                { label: 'Overview', link: '/workflows/intake-phase/' },
                { label: 'intake:existing-docs', link: '/workflows/intake-existing-docs/' },
                { label: 'intake:document-codebase', link: '/workflows/intake-document-codebase/' },
                {
                  label: 'intake:document-data-model',
                  link: '/workflows/intake-document-data-model/',
                },
                {
                  label: 'intake:document-file-tree',
                  link: '/workflows/intake-document-file-tree/',
                },
                {
                  label: 'intake:document-integrations',
                  link: '/workflows/intake-document-integrations/',
                },
                { label: 'intake:document-api', link: '/workflows/intake-document-api/' },
                {
                  label: 'intake:document-user-model',
                  link: '/workflows/intake-document-user-model/',
                },
                { label: 'intake:document-features', link: '/workflows/intake-document-features/' },
                { label: 'intake:document-glossary', link: '/workflows/intake-document-glossary/' },
                { label: 'intake:document-security', link: '/workflows/intake-document-security/' },
                {
                  label: 'intake:document-authorization',
                  link: '/workflows/intake-document-authorization/',
                },
                {
                  label: 'intake:document-user-flow',
                  link: '/workflows/intake-document-user-flow/',
                },
                { label: 'intake:document-config', link: '/workflows/intake-document-config/' },
                {
                  label: 'intake:document-analytics',
                  link: '/workflows/intake-document-analytics/',
                },
                { label: 'intake:create-onboarding', link: '/workflows/intake-create-onboarding/' },
                { label: 'Capture behavior', link: '/workflows/intake-capture-behavior/' },
                { label: 'intake:testing-setup', link: '/workflows/intake-testing-setup/' },
                { label: 'intake:testing-features', link: '/workflows/intake-testing-features/' },
                {
                  label: 'intake:testing-authorization',
                  link: '/workflows/intake-testing-authorization/',
                },
                { label: 'intake:testing-owasp', link: '/workflows/intake-testing-owasp/' },
                {
                  label: 'intake:testing-user-flows',
                  link: '/workflows/intake-testing-user-flows/',
                },
                {
                  label: 'intake:create-system-description',
                  link: '/workflows/intake-create-system-description/',
                },
              ],
            },
            {
              label: 'Discovery Phase',
              collapsed: true,
              items: [
                { label: 'Overview', link: '/workflows/discovery-phase/' },
                { label: 'discovery:create', link: '/workflows/discovery-create/' },
                { label: 'discovery:approve', link: '/workflows/discovery-approve/' },
              ],
            },
            {
              label: 'Spec Phase',
              collapsed: true,
              items: [
                { label: 'Overview', link: '/workflows/spec-phase/' },
                { label: 'spec:triage', link: '/workflows/spec-triage/' },
                { label: 'spec:create', link: '/workflows/spec-create/' },
                { label: 'spec:review', link: '/workflows/spec-review/' },
                { label: 'spec:complete', link: '/workflows/spec-complete/' },
                { label: 'spec:status', link: '/workflows/spec-status/' },
                { label: 'spec:current', link: '/workflows/spec-current/' },
                { label: 'spec:diff', link: '/workflows/spec-diff/' },
              ],
            },
            {
              label: 'Ticket Phase',
              collapsed: true,
              items: [
                { label: 'Overview', link: '/workflows/ticket-phase/' },
                { label: 'ticket:execute', link: '/workflows/ticket-execute/' },
                { label: 'ticket:complete', link: '/workflows/ticket-complete/' },
              ],
            },
            { label: 'common-ground', link: '/workflows/common-ground/' },
            { label: 'Workflow Definition Schema', link: '/workflows/workflow-definition-schema/' },
          ],
        },
        {
          label: 'Language',
          collapsed: true,
          items: [{ autogenerate: { directory: 'skills/language' } }],
        },
        {
          label: 'Backend Frameworks',
          collapsed: true,
          items: [{ autogenerate: { directory: 'skills/backend' } }],
        },
        {
          label: 'Frontend & Mobile',
          collapsed: true,
          items: [{ autogenerate: { directory: 'skills/frontend' } }],
        },
        {
          label: 'Infrastructure & Cloud',
          collapsed: true,
          items: [{ autogenerate: { directory: 'skills/infrastructure' } }],
        },
        {
          label: 'API & Architecture',
          collapsed: true,
          items: [{ autogenerate: { directory: 'skills/api-architecture' } }],
        },
        {
          label: 'Quality & Testing',
          collapsed: true,
          items: [{ autogenerate: { directory: 'skills/quality' } }],
        },
        {
          label: 'DevOps & Operations',
          collapsed: true,
          items: [{ autogenerate: { directory: 'skills/devops' } }],
        },
        {
          label: 'Security',
          collapsed: true,
          items: [{ autogenerate: { directory: 'skills/security' } }],
        },
        {
          label: 'Data & ML',
          collapsed: true,
          items: [{ autogenerate: { directory: 'skills/data-ml' } }],
        },
        {
          label: 'Platform',
          collapsed: true,
          items: [{ autogenerate: { directory: 'skills/platform' } }],
        },
        {
          label: 'Specialized',
          collapsed: true,
          items: [{ autogenerate: { directory: 'skills/specialized' } }],
        },
        {
          label: 'Workflow Skills',
          collapsed: true,
          items: [{ autogenerate: { directory: 'skills/workflow' } }],
        },
        {
          label: 'Project',
          items: [
            { label: 'README', link: '/readme/' },
            { label: 'Contributing', link: '/contributing/' },
            { label: 'Changelog', link: '/changelog/' },
            { label: 'Roadmap', link: '/roadmap/' },
          ],
        },
      ],
    }),
    // llms.txt from site-sync's page list (D-028); site-sync writes llms-full.txt
    seoGraph({
      // Its link check reads links from the domain root and misses the base path, so it
      // reports every internal link as a 404. starlight-links-validator checks them instead
      validateInternalLinks: false,
      // Submits changed pages to IndexNow, from the deploy build only (site-seo)
      indexNow: indexNowOptions(SITE_URL),
      llmsTxt: {
        title: 'Claude Skills',
        siteUrl: SITE_URL,
        summary: DESCRIPTION,
        sections: llmsSectionsFromSync(import.meta.dirname, SITE_URL),
      },
    }),
  ],
});
