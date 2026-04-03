# Agent Handoff

This repository is intentionally prepared for both Codex and Claude Code.

## Codex

Codex reads `AGENTS.md` before working. This repository uses `AGENTS.md` as the main shared instructions file.

Recommended starting sequence for Codex:

1. read `AGENTS.md`
2. read `code_review.md`
3. read `docs/architecture.md`
4. read `docs/implementation-roadmap.md`
5. if the task is large, create an ExecPlan using `.agent/PLANS.md`

Useful prompt entry point:

- `prompts/codex-first-prompt.md`

## Claude Code

Claude Code reads `CLAUDE.md`, not `AGENTS.md`, so this repository uses a small `CLAUDE.md` that imports `AGENTS.md` and adds Claude-specific guidance.

Claude also supports `.claude/rules/` for modular, path-scoped instructions.

Recommended starting sequence for Claude Code:

1. load `CLAUDE.md`
2. read only the docs needed for the task
3. respect `.claude/rules/` when touching matching files
4. use plan mode for significant changes

Useful prompt entry point:

- `prompts/claude-first-prompt.md`

## Human operator workflow

A good human workflow is:

1. decide the next vertical slice
2. point the agent at the relevant docs
3. require tests and doc updates
4. review against `code_review.md`
5. keep the repo understandable without the prior chat history

## What makes handoff work here

The handoff strategy is based on:

- a small root instruction file
- deeper reference docs under `docs/`
- explicit review criteria
- an execution-plan file for larger work
- a working starter slice, not only a design memo

## Keep this true over time

If the repo evolves, preserve these properties:

- root instructions stay concise
- architecture docs stay current
- rules stay documented
- tests remain fast enough for agent iteration
- implementation order stays milestone-driven
