# FAQ

## General

### What is slopcheck?
A deterministic static analysis scanner that catches AI-generated code failures. It runs 72 regex-based rules against Python, JS/TS, Go, C/C++, SQL, and Markdown files.

### Does it use AI/LLM?
No. All rules are deterministic regex or heuristic patterns. No LLM calls, no network requests, no backend. Tree-sitter (optional) provides AST-level context but is still fully deterministic.

### How is it different from ESLint/ruff/golangci-lint?
slopcheck focuses on **AI-specific code failures** that general linters don't catch: stub functions, AI instruction comments, conversational bleed, hallucinated placeholders, cross-language idiom leakage. It also adds security rules (hardcoded secrets, SQL injection) and API contract detection.

### What precision does it achieve?
~91% on enabled-by-default rules across 12 production repos (17,671 files). Higher with baselines and confidence filtering.

## Rules

### How many rules are there?
72 rules across 8 categories. About 50 are enabled by default; 22 are opt-in (configurable).

### How do I disable a rule?
In `.slopcheck/config.yaml`:
```yaml
rules:
  js_loose_equality:
    enabled: false
```

### How do I suppress a single finding?
```python
x = value  # slopcheck: ignore[rule_id]
```

### A rule is too noisy. What do I do?
1. Check if the rule has config options (e.g., `min_consecutive_lines`, `max_methods`)
2. Use `--min-confidence medium` to filter low-confidence findings
3. Create a baseline: `slopcheck create-baseline findings.json`
4. Disable the rule in config if it doesn't fit your codebase

### Can I add custom rules?
Yes. See [docs/rule-authoring.md](../docs/rule-authoring.md). Create a rule class, config class, register it, add tests.

## CI/CD

### How fast is it?
2-12 seconds for a typical 1,000-5,000 file repo. Threaded scanning with `--jobs` helps on multi-core CI runners.

### Can I scan only changed files?
Yes: `slopcheck scan . --changed-files git` scans only files changed since HEAD~1.

### How do I integrate with GitHub Security tab?
```bash
slopcheck sarif findings.json > results.sarif
# Upload with github/codeql-action/upload-sarif
```

### How do I adopt on an existing codebase?
Use baselines. First scan creates a baseline of existing findings. CI only fails on NEW findings going forward.

## Tree-sitter

### Do I need tree-sitter?
No. It's optional. Without it, rules use a lightweight regex-based context filter. With it, rules that check string/comment context are more precise (~5% precision improvement).

### How do I install it?
```bash
pip install tree-sitter-python tree-sitter-javascript tree-sitter-go tree-sitter-typescript
```

### Which rules use tree-sitter?
`ai_identity_refusal`, `hallucinated_placeholder`, `cross_language_idiom`, `hardcoded_secret`, `dead_code_comment`. All fall back gracefully without it.
