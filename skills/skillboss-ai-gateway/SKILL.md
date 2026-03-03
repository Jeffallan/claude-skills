---
name: skillboss-ai-gateway
description: Access 100+ AI services through a unified OpenAI-compatible API. Use for LLMs (Claude, GPT, Gemini), image generation (DALL-E, Midjourney, Flux), video (Runway, Kling), and audio (ElevenLabs).
category: ai-services
---

# SkillBoss AI Gateway

Unified access to 100+ AI services through a single API key and OpenAI-compatible interface.

## When to Use

- Working with multiple AI models (Claude, GPT, Gemini, DeepSeek)
- Generating images (DALL-E, Midjourney, Flux, Stable Diffusion)
- Creating videos (Runway, Kling, Luma)
- Text-to-speech or speech-to-text
- Need one API for all AI services

## Setup

```python
from openai import OpenAI

client = OpenAI(
    base_url="https://api.heybossai.com/v1",
    api_key="your-skillboss-key"
)
```

## Supported Models

### LLMs
- `anthropic/claude-sonnet-4` - Claude Sonnet 4
- `anthropic/claude-opus-4` - Claude Opus 4
- `openai/gpt-4.1` - GPT-4.1
- `openai/gpt-5` - GPT-5
- `google/gemini-2.5-pro` - Gemini 2.5 Pro
- `deepseek/deepseek-r1` - DeepSeek R1

### Image Generation
- `flux-pro` - Flux Pro
- `dall-e-4` - DALL-E 4
- `midjourney` - Midjourney
- `sd-3.5` - Stable Diffusion 3.5

### Video
- `runway/gen-4` - Runway Gen-4
- `kling-2.0` - Kling 2.0
- `luma/dream-machine` - Luma

## Links

- **Documentation**: https://skillboss.co/docs
- **MCP Server**: https://github.com/heeyo-life/skillboss-mcp
