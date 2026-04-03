# Rule Authoring

This project lives or dies by rule quality.

A rule is only good if it is accurate enough that engineers keep it enabled.

## What makes a rule AI-specific?

A rule is "AI-specific" if it detects patterns caused by LLM text generation, not
general coding mistakes. The taxonomy:

- **Laziness** — LLMs truncate output to save tokens (stub bodies, omission comments)
- **Amnesia** — LLMs forget context (hallucinated placeholders, wrong variable names)
- **Conversational bleed** — chat artifacts copy-pasted into source files
- **Alignment artifacts** — AI refusal text committed as code

If a human would naturally write it while problem-solving, it belongs in a linter like
ruff. If it is an artifact of an LLM's text-generation process, it belongs in slopcheck.

## Rule categories

There are currently **42 rules** across 8 categories.

### AI detection (Tier 1)

The highest-signal AI failure patterns. All enabled by default.

- `stub_function_body` / `stub_function_body_js` / `stub_function_body_go` — functions with only `return None`/`pass`/`...`/empty body
- `ai_instruction_comment` — "implement this", "omitted for brevity", "add error handling here"
- `bare_except_pass` / `bare_except_pass_js` / `bare_except_pass_go` — silently swallowed exceptions

### AI smoking guns (Tier 2)

Near-certain AI artifacts. Enabled by default.

- `ai_conversational_bleed` — "Certainly!", "Of course!", markdown code fences (`\`\`\``) in source
- `ai_identity_refusal` — "As an AI language model", "I cannot assist with"
- `hallucinated_placeholder` — YOUR_API_KEY_HERE, example.com in non-allowed domains

### Quality / supplementary (Tier 3)

- `placeholder_tokens` — TODO/FIXME/HACK/TEMPORARY (configurable token list)
- `dead_code_comment` — 4+ consecutive commented-out lines (`min_consecutive_lines` configurable)
- `incomplete_error_message` — generic "An error occurred", "Something went wrong"
- `missing_default_branch` — opt-in (60% precision); if/elif without else, match without `case _`
- `ai_hardcoded_mocks` — opt-in (50% precision); "John Doe", "Acme Corp" in non-test code

### Security

- `hardcoded_secret` — API keys, tokens, passwords embedded in source
- `sql_string_concat` — SQL built by string concatenation (SQLi risk)
- `insecure_default` — `verify=False`, `DEBUG=True`, `ssl=False` hardcoded
- `weak_hash` — MD5 or SHA1 used for security-relevant purposes
- `undeclared_import` — opt-in; imports not found in requirements manifest

### JavaScript / Node

- `js_await_in_loop` — sequential `await` inside a `for`/`while` loop (use `Promise.all`)
- `js_json_parse_unguarded` — `JSON.parse` without try/catch
- `js_unhandled_promise` — `.then(...)` without `.catch(...)`
- `js_timer_no_cleanup` — `setInterval`/`setTimeout` without storing the return value
- `js_loose_equality` — `==` / `!=` instead of `===` / `!==`
- `js_dangerously_set_html` — unsafe raw HTML injection via React prop
- `console_log_in_production` — `console.log/debug/info/warn` outside test files
- `typescript_any_abuse` — excessive use of `any` type
- `react_index_key` — array index used as React list key
- `react_async_useeffect` — async function passed directly to `useEffect`
- `regex_dos` — ReDoS-vulnerable patterns (nested quantifiers, catastrophic backtracking)

### Go

- `go_ignored_error` — `_` assigned to an error return value
- `go_missing_defer` — `Lock()` called without `defer Unlock()`
- `go_error_wrap_missing_w` — `fmt.Errorf("...: %v", err)` without `%w` (loses stack)

### Python

- `python_mutable_default` — mutable default argument `def f(x=[])` or `def f(x={})`

### Cross-language / structural

- `cross_language_idiom` — language-wrong idioms (Python writing `null`/`undefined`, JS writing `None`/`True`)
- `select_star_sql` — `SELECT *` in application code
- `deep_nesting` — opt-in; nesting depth > 6 (243K findings at depth=4 on the benchmark set)
- `large_function` — opt-in; functions > 100 lines (16K findings at 60 lines)
- `obvious_perf_drain` — opt-in; hot-path issues (37K findings without scope analysis)

### Repo-specific

- `forbidden_import_edges` — cross-module import boundary violations (configured per-repo)

### Meta

- `unused_suppression` — `slopcheck: ignore` comments that matched no findings

## Rule contract

A rule should answer:

- what files it applies to (`supported_extensions`)
- what evidence it looks for
- what finding it emits
- how the finding should be fingerprinted
- how false positives are controlled

## Rule interface

```python
class MyRule(Rule):
    rule_id = "my_rule"
    title = "Descriptive title"
    supported_extensions = {".py"}  # or None for all code files

    def scan_file(
        self,
        *,
        repo_root: Path,
        relative_path: str,
        content: str,
        config: AppConfig,
    ) -> list[Finding]:
        ...
        return [
            self.build_finding(
                relative_path=relative_path,
                line=lineno,
                message="What the user sees",
                severity=Severity.WARNING,
                confidence=Confidence.HIGH,
                evidence=matched_text,
                suggestion="How to fix it",
            )
        ]
```

`build_finding()` automatically computes the fingerprint from `rule_id + path + line + evidence`.

## Fingerprints

A fingerprint should be stable enough that a later baseline file can suppress the same finding again.

Good fingerprint inputs:

- rule id
- relative file path
- line number or stable span
- stable evidence string

Avoid including volatile text such as timestamps or line counts that change on refactor.

## Severity versus confidence

Keep them separate.

- severity = impact if true
- confidence = how certain the scanner is

Use `HIGH` confidence sparingly. It should mean the rule has strong evidence and low ambiguity.

## False-positive control

Rules should bias toward precision first.

Ways to keep precision high:

- require strong evidence
- scope by file type (`supported_extensions`)
- scope by path pattern
- allow repo config to declare boundaries
- add allowlists where the pattern has legitimate uses
- keep the finding message concrete
- default opt-out rules to `enabled: false` when precision is below ~70%

## Inline suppression

Users can suppress individual findings without disabling the rule:

```python
x = get_secret()  # slopcheck: ignore[hardcoded_secret]
```

```go
// slopcheck: ignore-next[go_ignored_error]
val, _ = riskyCall()
```

The scanner tracks suppressed findings in `ScanStats.suppressed`. The `unused_suppression` rule fires if a directive never matched anything.

## Context filtering

Two tools are available to avoid false positives from matches inside strings or comments:

**`context_filter.py`** (no dependencies): single-pass scanner that detects whether a match position is inside a string literal, comment, or regex. Returns `bool`. Works for Python, JS, Go.

**`treesitter.py`** (optional dependency): wraps tree-sitter for accurate AST-level context detection. Returns `True`/`False` if tree-sitter is installed, `None` otherwise. Rules should fall back to `context_filter.py` when `None` is returned.

## When regex is enough

Regex is fine when:

- the syntax pattern is simple
- the false-positive surface is small
- the rule does not need structural awareness

## When tree-sitter is worth it

Tree-sitter becomes worthwhile when:

- syntax matters (e.g., distinguishing a function call from a string containing the same text)
- whitespace and comments must not confuse the rule
- imports or calls need AST precision
- the regex version is noticeably noisy

Do not add tree-sitter to "look more advanced." Add it because a concrete rule benefits.

## Suggested rule development flow

1. write the problem statement
2. add one fixture that should fail
3. add one fixture that should pass
4. implement the simplest working detector
5. review the finding message
6. add edge-case tests
7. register in `registry.py`
8. add typed config in `config.py`
9. document the rule here or in a more specific doc

## Required tests for a new rule

At minimum:

- one positive case (should fire)
- one negative case (should not fire)
- one config-driven case if the rule is configurable
- path-specific tests if the rule is path-sensitive

## Documentation requirement

Every new rule must update at least one of:

- `docs/rule-authoring.md`
- a more specific doc under `docs/`
- example config
- README if the new rule changes the value proposition

## Rule placement guide

- starts broad and reusable → `generic/`
- depends on repo architecture → `repo/`
- not yet clear → start in `repo/`, generalize later if it proves reusable
