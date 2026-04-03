# Architecture

See [docs/architecture.md](../docs/architecture.md) for the full architecture documentation with Mermaid diagrams, data model, threading model, and rule catalog tables.

## Overview

```
GitHub Actions → slopcheck scan → findings.json → annotations/SARIF/summary
                      ↓
              ThreadPoolExecutor (up to 8 workers)
                      ↓
              Per-file: read → suppress → run applicable rules → collect findings
                      ↓
              Sort → filter (baseline, confidence) → output
```

## Key Design Decisions

1. **No LLM** — deterministic regex + optional tree-sitter (ADR-0002)
2. **No backend** — CLI + file-based state only (ADR-0001)
3. **Tree-sitter optional** — graceful fallback to regex (ADR-0003)
4. **Per-file scanning** — each file is independent, enables threading
5. **Extension pre-filtering** — Go rules never run on .py files
