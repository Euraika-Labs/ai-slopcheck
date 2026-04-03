# Contributing to slopcheck

Thank you for considering contributing to slopcheck.

## Getting Started

```bash
git clone https://git.euraika.net/euraika/slopcheck.git
cd slopcheck
pip install -e .[dev]
pytest
ruff check .
```

## Development Workflow

We follow **Git Flow** with conventional commits.

| Branch | Purpose |
|--------|---------|
| `main` | Production-ready, tagged with SemVer |
| `develop` | Integration branch for next release |
| `feature/<name>` | New features — branch from `develop` |
| `fix/<name>` | Bug fixes — branch from `develop` |

### Steps

1. Branch from `develop`: `git checkout -b feature/my-rule develop`
2. Implement your change
3. Run: `pytest && ruff check .`
4. Commit: `feat:`, `fix:`, `docs:`, `test:`, `refactor:`
5. Push and open a merge request to `develop`

## Adding a New Rule

See [docs/rule-authoring.md](docs/rule-authoring.md) for the full guide.

### Quick checklist

1. Create rule in `ai_slopcheck/rules/generic/your_rule.py`
2. Add config class in `ai_slopcheck/config.py`
3. Register in `ai_slopcheck/rules/registry.py`
4. Write tests in `tests/test_your_rule.py` (6+ tests)
5. Run `pytest && ruff check .`

### Design principles

- **Precision > recall** — target >80% precision
- **Deterministic** — no LLM, no network, no randomness
- **Configurable** — users can tune or disable any rule
- **Tested** — positive AND negative test cases required

### When to make a rule opt-in (`enabled: False`)

- Precision below ~70%
- Style opinion (not a bug/security issue)
- Generates >1,000 findings on a typical repo

## Code Style

- Python 3.12+, type hints everywhere
- Ruff: line-length 100, double quotes
- Pydantic v2 with `ConfigDict(extra="forbid")`

## Testing

```bash
pytest                              # all tests
pytest tests/test_your_rule.py      # single file
pytest -k test_detects_something    # single test
```

## Tree-sitter (Optional)

```bash
pip install tree-sitter-python tree-sitter-javascript tree-sitter-go tree-sitter-typescript
```

Rules using tree-sitter must fall back gracefully when it's not installed.

## Documentation

Update when behavior changes:
- `docs/rule-catalog.md` — new rules
- `docs/configuration-guide.md` — new config options
- `docs/cli-reference.md` — new CLI flags
- `CHANGELOG.md` — add entry

## License

Contributions are licensed under the MIT License.
