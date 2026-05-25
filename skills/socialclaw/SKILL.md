---
name: socialclaw
description: Schedules and publishes social media posts for AI agents across X, LinkedIn, Instagram, Facebook Pages, TikTok, Discord, Telegram, YouTube, Reddit, WordPress, and Pinterest via the SocialClaw hosted service. Use when the user wants to connect social accounts, upload media, validate or apply a post/campaign schedule, inspect run status, retry failed posts, or check analytics through SocialClaw.
license: MIT
metadata:
  author: https://github.com/ndesv21
  version: "1.0.0"
  domain: social-media
  triggers: social media, schedule post, publish content, X post, LinkedIn post, Instagram, TikTok, YouTube upload, social publishing, SocialClaw, social accounts, campaign schedule
  role: specialist
  scope: implementation
  output-format: commands
  related-skills: none
---

# SocialClaw Social Publishing Expert

Agent-first social publishing backend that lets AI agents schedule and publish across 13 social channels through one workspace API key.

## Core Workflow

1. **Authenticate** — Confirm `SC_API_KEY` is set or run `socialclaw login`
2. **Connect accounts** — Use `socialclaw accounts connect --provider <provider> --open` for each platform
3. **Inspect capabilities** — Run `socialclaw accounts capabilities --json` before generating schedules
4. **Upload media** — Use `socialclaw assets upload --file <path> --json` for hosted asset URLs
5. **Validate** — Run `socialclaw validate -f schedule.json --json` to check schedule
6. **Apply** — Run `socialclaw apply -f schedule.json --json` to create the run
7. **Inspect** — Use `socialclaw status --run-id <id> --json` and `socialclaw posts list --json`

### Error Recovery

- **`plan_required`** → go to `https://getsocialclaw.com/pricing` to activate a plan
- **`token_expired`** → reconnect the account with `socialclaw accounts connect --provider <provider> --open`
- **Post failed** → use `socialclaw retry --post-id <id> --json`
- **No connected accounts** → run the connect flow for the target provider

## Supported Providers

| Provider | Handle Format | Notes |
|----------|--------------|-------|
| X | `x:@handle` | Text + up to 4 images or 1 video |
| LinkedIn profile | `linkedin:member:<id>` | Up to 20 images or 1 video |
| LinkedIn page | `linkedin_page:page:<id>` | Up to 20 images or 1 video |
| Instagram Business | `instagram_business:linked:<id>` | Requires Facebook Page link |
| Instagram standalone | `instagram:standalone:<id>` | Professional accounts only |
| Facebook Page | `facebook:page:<id>` | Pages only, not personal profiles |
| TikTok | `tiktok:@handle` | 1 video or 1–35 images |
| YouTube | `youtube:channel:<id>` | Native video upload |
| Reddit | `reddit:user:<id>` | Requires subreddit setting |
| WordPress | `wordpress:site:<id>` | WordPress.com or Jetpack |
| Discord | Manual webhook | Webhook URL required |
| Telegram | Manual bot token | Bot token + chat ID |
| Pinterest | `pinterest:user:<id>` | Board-centric publishing |

## Constraints

### MUST DO

- Confirm workspace API key before any operation
- Inspect `accounts capabilities` before generating provider-specific schedules
- Use `accounts settings` when provider-specific publish knobs are needed
- Use `draft` mode when staging work for review
- Be explicit about provider limitations instead of guessing

### MUST NOT DO

- Ask users for provider app secrets (they connect accounts inside SocialClaw)
- Imply support for features not implemented (personal Facebook profiles, Instagram text-only, etc.)
- Echo full API keys back into chat
- Promise native thread support yet

## Reference

- GitHub: https://github.com/ndesv21/socialclaw
- Dashboard: https://getsocialclaw.com/dashboard
- Install CLI: `npm install -g socialclaw`
- Install skill: `npx skills add ndesv21/socialclaw`
