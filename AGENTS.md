# AGENTS.md

## Mission

Build `slopcheck` into a deterministic, GitHub-first pull request scanner for AI-style code failures.

The product must remain understandable by a human maintainer who joins cold. Do not build a clever system that only works if an agent keeps re-deriving the intent.

## Hard constraints

- Do **not** add LLM calls to the product path.
- Do **not** add a backend, database, queue, or web service for v1.
- Keep the first production integration target as GitHub pull requests.
- Prefer simple typed Python over framework-heavy abstractions.
- Add new dependencies only when they clearly unlock a rule or a workflow.
- Treat false-positive control as a core feature, not a cleanup task.

## Product shape

The intended runtime model is:

1. GitHub Action checks out code.
2. The CLI scans files and produces a `findings.json`.
3. The workflow emits annotations and optionally a summary.
4. The CLI exit code decides pass or fail.

Longer-term optional flows may add:

- diff-only scanning
- baseline and suppressions
- SARIF export
- a separate privileged commenter workflow

## What counts as success

A successful change does one or more of these:

- adds a new deterministic rule with tests
- improves the findings contract or config model
- reduces false positives without hiding real problems
- moves the GitHub integration forward safely
- improves performance while keeping the code obvious
- improves documentation so the next agent can continue without guesswork

## What to avoid

- speculative framework layers
- plugin systems before there are enough real plugins
- generic “AI quality” scoring
- invisible magic
- tightly coupling a rule to GitHub-specific runtime state unless the rule truly needs it
- burying decisions in code without documenting them

## Required reading before major changes

Read these files before changing architecture, workflows, or rule contracts:

1. `README.md`
2. `code_review.md`
3. `docs/architecture.md`
4. `docs/implementation-roadmap.md`
5. `docs/security-model.md`
6. `docs/github-integration.md`
7. `docs/rule-authoring.md`

## Execution plans

When writing a significant feature or refactor, use an ExecPlan as defined in `.agent/PLANS.md`.

Use an ExecPlan when the change involves any of the following:

- new workflow topology
- baseline and suppression design
- Tree-sitter integration
- rule engine contract changes
- large refactors across multiple modules
- anything likely to touch more than three files or introduce uncertainty

Keep the ExecPlan current while implementing. It is a living document, not a throwaway note.

## Working style

- Implement in vertical slices.
- Keep each slice runnable.
- Update docs in the same change when behavior or architecture changes.
- Prefer adding one real rule over inventing a rule DSL.
- Every new rule must have tests and a documentation entry.
- If a rule is noisy, fix the rule before adding more rules like it.

## Coding standards

- Use Python 3.12+ syntax and type hints.
- Keep functions small and side effects explicit.
- Use datamodels for external contracts.
- Make exit conditions and failure behavior obvious.
- Keep file paths relative to `repo_root` once inside the engine.
- Prefer pure functions for rendering output and computing fingerprints.

## Testing standards

Run these before you consider a change complete:

```bash
pytest
ruff check .
```

When adding a rule, add or update:

- unit tests
- fixture files if needed
- docs in `docs/rule-authoring.md` or a more specific doc
- example config if the rule introduces new config

## Review standards

Follow `code_review.md` for all review and self-review work.

## GitHub workflow safety

Default to the safer model:

- untrusted code runs on `pull_request`
- no secrets in the scan job
- write privileges only in trusted follow-up workflows if needed
- do not execute PR code on `pull_request_target`

## Where to put things

- generic rule code: `slopcheck/rules/generic/`
- repo-specific example rules: `slopcheck/rules/repo/`
- output renderers: `slopcheck/output/`
- GitHub integration helpers: `slopcheck/github/`
- architecture and product reasoning: `docs/`
- agent prompts: `prompts/`

## When in doubt

Choose the option that makes the next human maintainer say:

> “I can see exactly how this works, why it exists, and how to extend it.”
