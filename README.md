# Banana Skill Interior

This repository has the [`banana-claude`](https://github.com/AgriciDaniel/banana-claude) Claude Code skill installed as a project-scoped skill at `.claude/skills/banana/`. Claude Code automatically discovers project skills in this location for anyone working in this repo — no manual plugin install step required.

## What the skill does

`banana` turns Claude into a Creative Director for AI image generation, powered by Google's Gemini Nano Banana models. It interprets intent, selects a domain mode (Cinema, Product, Portrait, Editorial, UI, Logo, Landscape, Infographic, Abstract), constructs prompts with Google's 5-component formula, and orchestrates Gemini generation/editing via MCP.

## Setup

1. Get a free API key at [Google AI Studio](https://aistudio.google.com/apikey).
2. In Claude Code, run `/banana setup` to configure the MCP server with your key.
3. Try it: `/banana generate "a hero image for a coffee shop website"`

See `.claude/skills/banana/SKILL.md` for the full skill definition and `references/` for prompt engineering, model, and cost-tracking docs.

## Source & license

Vendored from [AgriciDaniel/banana-claude](https://github.com/AgriciDaniel/banana-claude), MIT licensed (see `.claude/skills/banana/LICENSE`).
