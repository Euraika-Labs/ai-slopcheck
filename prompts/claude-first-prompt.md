Load `CLAUDE.md`, then read `code_review.md`, `docs/architecture.md`, `docs/implementation-roadmap.md`, and `docs/security-model.md`.

Then do the following:

1. Explain the current state of the repository.
2. Choose the next best vertical slice.
3. Use plan mode if the slice is large or uncertain.
4. Implement the slice fully, not partially.
5. Add or update tests.
6. Update the relevant Markdown docs.
7. Run `pytest` and `ruff check .`.
8. Summarize what changed, what risks remain, and what the next slice should be.

Stay inside the product constraints:

- deterministic rules only
- no backend
- GitHub-first
- simple Python package and CLI
- prefer precision over noisy heuristics
