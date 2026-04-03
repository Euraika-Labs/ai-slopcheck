Read `AGENTS.md`, `code_review.md`, `docs/architecture.md`, `docs/implementation-roadmap.md`, and `docs/security-model.md`.

Then do the following in order:

1. Summarize the current repository state in plain English.
2. Recommend the next best vertical slice to build.
3. If the slice is non-trivial, write an ExecPlan using `.agent/PLANS.md`.
4. Implement the slice end to end.
5. Add or update tests.
6. Update the relevant Markdown docs.
7. Run `pytest` and `ruff check .`.
8. Report what changed, what is still missing, and what should come next.

Stay within the repository constraints:

- deterministic checks only
- no backend
- GitHub-first
- simple Python CLI
- low false-positive tolerance
