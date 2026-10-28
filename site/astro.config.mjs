import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';
import starlightLinksValidator from 'starlight-links-validator';
import seoGraph from '@jdevalk/astro-seo-graph/integration';
import { llmsSectionsFromSync } from './src/components/site-sync/llms.mjs';
import { indexNowOptions } from './src/components/site-seo/indexnow.mjs';

const SITE_URL = 'https://jeffallan.github.io/claude-skills';
const DESCRIPTION =
  '67 specialized skills for Claude Code — progressive disclosure, context engineering, and full-stack coverage.';

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
                { label: 'intake:document-codebase', link: '/workflows/intake-document-codebase/' },
                { label: 'intake:capture-behavior', link: '/workflows/intake-capture-behavior/' },
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
                { label: 'discovery:synthesize', link: '/workflows/discovery-synthesize/' },
                { label: 'discovery:approve', link: '/workflows/discovery-approve/' },
              ],
            },
            {
              label: 'Planning Phase',
              collapsed: true,
              items: [
                { label: 'Overview', link: '/workflows/planning-phase/' },
                { label: 'planning:epic-plan', link: '/workflows/planning-epic-plan/' },
                { label: 'planning:impl-plan', link: '/workflows/planning-impl-plan/' },
              ],
            },
            {
              label: 'Execution Phase',
              collapsed: true,
              items: [
                { label: 'Overview', link: '/workflows/execution-phase/' },
                { label: 'execution:execute-ticket', link: '/workflows/execution-execute-ticket/' },
                {
                  label: 'execution:complete-ticket',
                  link: '/workflows/execution-complete-ticket/',
                },
              ],
            },
            {
              label: 'Retrospective Phase',
              collapsed: true,
              items: [
                { label: 'Overview', link: '/workflows/retrospective-phase/' },
                {
                  label: 'retrospectives:complete-epic',
                  link: '/workflows/retrospective-complete-epic/',
                },
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
