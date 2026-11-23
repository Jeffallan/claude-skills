---
title: Privacy Policy
description: How the Fullstack Dev Skills Plugin and its documentation site handle information
---

**Effective:** November 23, 2026

This privacy policy describes how the **Fullstack Dev Skills Plugin** (`claude-skills`) and its companion documentation site at `https://jeffallan.github.io/claude-skills/` handle information.

The plugin and documentation site are maintained by [@jeffallan](https://github.com/jeffallan) as an individual open-source project. This is a personal project and is not a product or service of Synergetic Solutions or any other entity.

## 1. The Plugin

The plugin distributes markdown skill files and reference documents, slash command templates with their YAML definitions, agent definitions, hooks and a small local runtime (`runtime/guard.pyz`) that the workflow commands and hooks run. When you install the plugin in Claude Code, Claude Cowork, or another compatible host, the plugin:

- Does not collect or transmit any personal information. The runtime keeps its working state in your repository: under `.git/ticket-guard/` (the active ticket, run evidence with command output and file paths, owner decisions and the Claude session id that made them), and in review files under your spec folder, which you may commit.
- Sends nothing to this project or anyone else. The runtime runs locally through [uv](https://docs.astral.sh/uv/), which may download a Python interpreter the first time if a suitable one isn't installed. A few runtime commands start other tools that use the network under your own credentials: `guard spec-status` (used by `/spec:status`, `/spec:diff` and `/common-ground`) asks the GitHub CLI for pull request status when your code host is GitHub, and `guard run-batches`, which you start yourself, runs headless Claude sessions. The workflow commands may also ask Claude to run tools such as `gh`, `git push`, `npx` or `uvx`, which your host asks you to approve.
- Does not include telemetry, analytics, or usage tracking of any kind.
- Runs on your machine. Skills, commands and agents run inside your Claude host; hooks and the runtime run as local processes the host starts.

Any data your Claude host sends to Anthropic during a session (prompts, tool results, etc.) is governed by Anthropic's privacy policy, not this one. The plugin itself adds no data collection.

## 2. Ticket Trackers and MCP Servers

The workflow commands reach your ticket tracker and code host through tools you set up yourself: `gh` and `git` for GitHub, and for Jira or Linear a [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) server you configure separately in your Claude host (see the [Atlassian MCP Setup Guide](https://github.com/jeffallan/claude-skills/blob/main/docs/ATLASSIAN_MCP_SETUP.md)). When no MCP server is connected, or it lacks a call the command needs, the commands use the tracker's own API with an API token you keep in an environment variable. With the text tracker, tickets are files in your repository, and the plugin sends ticket data to no tracker service. Those files go wherever you push the repository. With a GitHub code host, `spec:complete` pushes the spec branch with its ticket edits and lists each ticket's ID and title in the pull request.

The plugin does not bundle, run, or proxy any MCP server, and it stores no tracker credentials: tokens stay with `gh`, your MCP server's sign-in, or your environment variables. When you use a command that calls `gh`, `git`, a tracker API, or an MCP server:

- The tool runs under your configuration and credentials. `gh`, `git` and a self-hosted MCP server (such as the Docker setup in the guide) run on your machine. A remote MCP server, such as Atlassian's Rovo MCP Server or a connector added to your Claude account, runs on its provider's infrastructure.
- Any data sent to the tool, and any data it forwards to a third-party vendor, is governed by that vendor's privacy policy, not this one.
- This project has no visibility into, and assumes no responsibility for, the data flow between that tool and the underlying service.

Before connecting a tracker, review the privacy policy of the vendor whose service it accesses: [GitHub](https://docs.github.com/en/site-policy/privacy-policies/github-general-privacy-statement), [Atlassian](https://www.atlassian.com/legal/privacy-policy) or [Linear](https://linear.app/privacy).

## 3. The Documentation Site

The documentation site at `https://jeffallan.github.io/claude-skills/` uses the following third-party services:

| Service                             | Purpose                                                                                   | Data involved                                                                                                                                                                                                                |
| ----------------------------------- | ----------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| GitHub Pages                        | Static site hosting                                                                       | IP addresses logged in standard server access logs, governed by [GitHub's privacy policy](https://docs.github.com/en/site-policy/privacy-policies/github-general-privacy-statement)                                          |
| Google Analytics 4 (`G-QVMEHEZBXE`) | Aggregate page-view and session metrics                                                   | Cookies, page URL, referrer, approximate geolocation derived from IP, browser/device info; governed by [Google's privacy policy](https://policies.google.com/privacy)                                                        |
| jsDelivr CDN                        | Loads the Mermaid diagram library on every page                                           | IP address logged in CDN access logs; governed by [jsDelivr's privacy policy](https://www.jsdelivr.com/terms/privacy-policy)                                                                                                 |
| GitHub API                          | Shows the repository's star count in the page header                                      | Your browser requests it on every page, so GitHub receives your IP address and browser info; governed by [GitHub's privacy policy](https://docs.github.com/en/site-policy/privacy-policies/github-general-privacy-statement) |
| Formspree                           | Delivers messages sent with the contact form (the Contact button at the end of each page) | The name, email address, topic and message you enter, and the site and page you sent it from; governed by [Formspree's privacy policy](https://formspree.io/legal/privacy-policy/)                                           |

To opt out of Google Analytics, use the [Google Analytics opt-out browser add-on](https://tools.google.com/dlpage/gaoptout) or a standard ad or tracker blocker. Google Analytics does not honor Do Not Track. The site works normally with either in place.

## 4. GitHub Repository Interactions

If you file an issue, open a pull request, post in discussions, or otherwise interact with the project's [GitHub repository](https://github.com/jeffallan/claude-skills), GitHub processes that interaction under [GitHub's privacy policy](https://docs.github.com/en/site-policy/privacy-policies/github-general-privacy-statement). Information you post publicly on GitHub remains public.

## 5. Contact

All privacy questions, sensitive disclosures, data subject requests, and other inquiries related to this project should be sent through the contact form on the maintainer's personal site:

[https://jeffallan.github.io/#ContactMe](https://jeffallan.github.io/#ContactMe)

Form submissions are processed by [Formspree](https://formspree.io/legal/privacy-policy/), a third-party form-handling service. Their privacy policy applies to the form-submission step.

## 6. Sale of Personal Information

This project does not sell, rent, or trade personal information. No personal information is collected by the plugin itself, and the documentation site's third-party services are used solely for hosting, loading the diagram library, showing the repository's star count, aggregate site analytics, and delivering contact-form messages, as described in section 3.

## 7. Children

This project is not directed at children under 13 (or the equivalent minimum age in your jurisdiction). No information is intentionally collected from children.

## 8. Changes to This Policy

If this policy changes materially, the updated version will be published at this URL with a new effective date. Material changes will also be noted in the project's [CHANGELOG.md](https://github.com/jeffallan/claude-skills/blob/main/CHANGELOG.md).
