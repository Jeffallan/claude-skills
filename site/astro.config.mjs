import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';

export default defineConfig({
  site: 'https://jeffallan.github.io',
  base: '/claude-skills',
  integrations: [
    starlight({
      title: 'Claude Skills',
      description:
        '65 specialized skills for Claude Code — progressive disclosure, context engineering, and full-stack coverage.',
      customCss: ['./src/styles/custom.css'],
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
                pre.closest('.expressive-code').replaceWith(div);
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
                { label: 'intake:create-system-description', link: '/workflows/intake-create-system-description/' },
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
                { label: 'execution:complete-ticket', link: '/workflows/execution-complete-ticket/' },
              ],
            },
            {
              label: 'Retrospective Phase',
              collapsed: true,
              items: [
                { label: 'Overview', link: '/workflows/retrospective-phase/' },
                { label: 'retrospectives:complete-epic', link: '/workflows/retrospective-complete-epic/' },
              ],
            },
            { label: 'common-ground', link: '/workflows/common-ground/' },
            { label: 'Workflow Definition Schema', link: '/workflows/workflow-definition-schema/' },
          ],
        },
        {
          label: 'Language',
          collapsed: true,
          autogenerate: { directory: 'skills/language' },
        },
        {
          label: 'Backend Frameworks',
          collapsed: true,
          autogenerate: { directory: 'skills/backend' },
        },
        {
          label: 'Frontend & Mobile',
          collapsed: true,
          autogenerate: { directory: 'skills/frontend' },
        },
        {
          label: 'Infrastructure & Cloud',
          collapsed: true,
          autogenerate: { directory: 'skills/infrastructure' },
        },
        {
          label: 'API & Architecture',
          collapsed: true,
          autogenerate: { directory: 'skills/api-architecture' },
        },
        {
          label: 'Quality & Testing',
          collapsed: true,
          autogenerate: { directory: 'skills/quality' },
        },
        {
          label: 'DevOps & Operations',
          collapsed: true,
          autogenerate: { directory: 'skills/devops' },
        },
        {
          label: 'Security',
          collapsed: true,
          autogenerate: { directory: 'skills/security' },
        },
        {
          label: 'Data & ML',
          collapsed: true,
          autogenerate: { directory: 'skills/data-ml' },
        },
        {
          label: 'Platform',
          collapsed: true,
          autogenerate: { directory: 'skills/platform' },
        },
        {
          label: 'Specialized',
          collapsed: true,
          autogenerate: { directory: 'skills/specialized' },
        },
        {
          label: 'Workflow Skills',
          collapsed: true,
          autogenerate: { directory: 'skills/workflow' },
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
  ],
});
