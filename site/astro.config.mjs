import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';

export default defineConfig({
  integrations: [
    starlight({
      title: 'Claude Skills',
      description:
        '65 specialized skills for Claude Code — progressive disclosure, context engineering, and full-stack coverage.',
      customCss: ['./src/styles/custom.css'],
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
          ],
        },
        {
          label: 'Workflows',
          collapsed: true,
          autogenerate: { directory: 'workflows' },
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
            { label: 'Contributing', link: '/contributing/' },
            { label: 'Changelog', link: '/changelog/' },
            { label: 'Roadmap', link: '/roadmap/' },
          ],
        },
      ],
    }),
  ],
});
