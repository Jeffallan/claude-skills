---
title: Privacy Policy
description: How the Fullstack Dev Skills Plugin and its documentation site handle information
---

**Effective:** October 26, 2026

This privacy policy describes how the **Fullstack Dev Skills Plugin** (`claude-skills`) and its companion documentation site at `https://jeffallan.github.io/claude-skills/` handle information.

The plugin and documentation site are maintained by [@jeffallan](https://github.com/jeffallan) as an individual open-source project. This is a personal project and is not a product or service of Synergetic Solutions or any other entity.

## 1. The Plugin

The plugin distributes static content: markdown skill files, slash command templates, and Python validation scripts. When you install the plugin in Claude Code, Claude Cowork, or another compatible host, the plugin:

- **Does not collect, transmit, or store any personal information.**
- **Does not make network requests on your behalf.**
- **Does not include telemetry, analytics, or usage tracking of any kind.**
- **Runs entirely within your local Claude environment.** All file reads, prompts, and tool calls happen within your existing Claude host process.

Any data your Claude host sends to Anthropic during a session (prompts, tool results, etc.) is governed by Anthropic's privacy policy, not this one. The plugin itself adds no additional data collection.

## 2. MCP Server Integrations

Some workflow commands in this plugin integrate with external services through [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) servers that you configure separately in your Claude host. The project workflow commands, for instance, require an **Atlassian MCP server** to interact with Jira and Confluence, as described in the [Atlassian MCP Setup Guide](https://github.com/jeffallan/claude-skills/blob/main/docs/ATLASSIAN_MCP_SETUP.md).

The plugin does not bundle, run, or proxy any MCP server. When you use a command that invokes an MCP server:

- The MCP server runs in your local environment under your configuration and credentials.
- Any data sent to the MCP server, and any data the MCP server forwards to a third-party vendor, is governed by **that vendor's privacy policy**, not this one.
- This project has no visibility into, and assumes no responsibility for, the data flow between your MCP server and the underlying service.

Before configuring an MCP server, review the privacy policy of the vendor whose service it accesses. The Atlassian integration is covered by [Atlassian's privacy policy](https://www.atlassian.com/legal/privacy-policy).

## 3. The Documentation Site

The documentation site at `https://jeffallan.github.io/claude-skills/` uses the following third-party services:

| Service                             | Purpose                                                                                   | Data involved                                                                                                                                                                       |
| ----------------------------------- | ----------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| GitHub Pages                        | Static site hosting                                                                       | IP addresses logged in standard server access logs, governed by [GitHub's privacy policy](https://docs.github.com/en/site-policy/privacy-policies/github-general-privacy-statement) |
| Google Analytics 4 (`G-QVMEHEZBXE`) | Aggregate page-view and session metrics                                                   | Cookies, page URL, referrer, approximate geolocation derived from IP, browser/device info; governed by [Google's privacy policy](https://policies.google.com/privacy)               |
| jsDelivr CDN                        | Loads the Mermaid diagram library on pages that render diagrams                           | IP address logged in CDN access logs; governed by [jsDelivr's privacy policy](https://www.jsdelivr.com/terms/privacy-policy-jsdelivr-net)                                           |
| Formspree                           | Delivers messages sent with the contact form (the Contact button at the end of each page) | The name, email address, topic and message you enter, and the site and page you sent it from; governed by [Formspree's privacy policy](https://formspree.io/legal/privacy-policy/)  |

To opt out of Google Analytics, you can use the [Google Analytics opt-out browser add-on](https://tools.google.com/dlpage/gaoptout), enable browser privacy features such as Do Not Track, or use any standard ad/tracker blocker. The site functions normally with these enabled.

## 4. GitHub Repository Interactions

If you file an issue, open a pull request, post in discussions, or otherwise interact with the project's [GitHub repository](https://github.com/jeffallan/claude-skills), GitHub processes that interaction under [GitHub's privacy policy](https://docs.github.com/en/site-policy/privacy-policies/github-general-privacy-statement). Information you post publicly on GitHub remains public.

## 5. Contact

All privacy questions, sensitive disclosures, data subject requests, and other inquiries related to this project should be sent through the contact form on the maintainer's personal site:

[https://jeffallan.github.io/#ContactMe](https://jeffallan.github.io/#ContactMe)

Form submissions are processed by [Formspree](https://formspree.io/legal/privacy-policy/), a third-party form-handling service. Their privacy policy applies to the form-submission step.

## 6. Sale of Personal Information

This project does not sell, rent, or trade personal information. No personal information is collected by the plugin itself, and the documentation site's third-party services are used solely for hosting, aggregate site analytics, and delivering contact-form messages, as described in section 3.

## 7. Children

This project is not directed at children under 13 (or the equivalent minimum age in your jurisdiction). No information is intentionally collected from children.

## 8. Changes to This Policy

If this policy changes materially, the updated version will be published at this URL with a new effective date. Material changes will also be noted in the project's [CHANGELOG.md](https://github.com/jeffallan/claude-skills/blob/main/CHANGELOG.md).
