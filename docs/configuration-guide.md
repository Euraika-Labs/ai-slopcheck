# Configuration Guide

## Config file locations

slopcheck looks for a config file in this order:

1. `--config PATH` flag (explicit override)
2. `{repo-root}/.slopcheck/config.yaml`
3. `{repo-root}/.slopcheck.yaml`
4. `{repo-root}/.slopcheck.yml`

If no file is found, all defaults apply and all opt-in rules remain disabled.

Config files must be valid YAML. Schema errors produce a fatal exit with a description of the validation failure.

---

## Config file structure

```yaml
# .slopcheck/config.yaml

# Glob patterns for paths to exclude from scanning entirely.
ignored_paths:
  - .git/**
  - .venv/**
  - node_modules/**
  - dist/**

# Per-rule configuration.
rules:
  placeholder_tokens:
    enabled: true
    banned_tokens:
      - TODO
      - FIXME
      - HACK
      - TEMPORARY

  forbidden_import_edges:
    enabled: true
    boundaries:
      - source_glob: "slopcheck/output/*.py"
        forbidden_prefixes:
          - slopcheck.engine
        message: "Output modules must not import from the engine directly."

  # ... all other rules
```

All keys are optional. Omitting a key uses the documented default.

Extra keys that are not recognized by any config model cause a validation error. This is intentional — it catches typos in rule names.

---

## ignored_paths

A list of glob patterns applied to relative file paths. Files matching any pattern are excluded from scanning entirely.

Default ignored patterns:

```yaml
ignored_paths:
  - .git/**
  - .venv/**
  - "**/.venv/**"
  - dist/**
  - "**/dist/**"
  - build/**
  - "**/build/**"
  - .next/**
  - "**/.next/**"
  - node_modules/**
  - "**/node_modules/**"
  - vendor/**
  - "**/vendor/**"
  - "**/generated/**"
  - "**/.claude/**"
  - "**/worktrees/**"
  - "**/swarm/runs/**"
  - "**/agents/swarm/**"
```

Patterns use `fnmatch` semantics. `**` matches any number of path segments.

To add exclusions without replacing the defaults, include the defaults and append your additions.

---

## Enabling and disabling rules

Every rule has an `enabled` field. Set it to `false` to disable the rule.

```yaml
rules:
  placeholder_tokens:
    enabled: false   # turn off entirely

  deep_nesting:
    enabled: true    # turn on this opt-in rule
```

Rules that are **off by default** (opt-in) are marked in the [rule catalog](rule-catalog.md). These rules were disabled because their precision is below ~70% on real-world codebases without additional tuning.

---

## Per-rule configuration reference

### placeholder_tokens

Detects TODO/FIXME/HACK/TEMPORARY and similar tokens.

```yaml
rules:
  placeholder_tokens:
    enabled: true
    banned_tokens:
      - TODO
      - FIXME
      - HACK
      - TEMPORARY
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `enabled` | bool | `true` | Enable/disable the rule. |
| `banned_tokens` | list[str] | `["TODO", "FIXME", "HACK", "TEMPORARY"]` | Tokens to flag as word boundaries. Case-sensitive. |

---

### forbidden_import_edges

Enforces Python import boundary rules. Requires configuration — does nothing without `boundaries`.

```yaml
rules:
  forbidden_import_edges:
    enabled: true
    boundaries:
      - source_glob: "slopcheck/output/*.py"
        forbidden_prefixes:
          - slopcheck.engine
          - slopcheck.rules
        message: "Output modules must not import engine internals."
      - source_glob: "myapp/api/*.py"
        forbidden_prefixes:
          - myapp.db
        message: "API layer must not import DB layer directly."
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `enabled` | bool | `true` | Enable/disable the rule. |
| `boundaries` | list[BoundaryConfig] | `[]` | Import boundary definitions. |

Each boundary:

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `source_glob` | str | _(required)_ | Glob pattern matching files this boundary applies to. |
| `forbidden_prefixes` | list[str] | `[]` | Module prefixes that must not be imported from files matching the glob. |
| `message` | str | `"Forbidden import edge."` | The finding message shown to the developer. |

---

### stub_function_body

Detects Python functions whose body is only `pass`, `...`, or a trivial return value.

```yaml
rules:
  stub_function_body:
    enabled: true
    excluded_function_patterns:
      - __init__
      - setUp
      - tearDown
      - setUpClass
      - tearDownClass
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `enabled` | bool | `true` | Enable/disable the rule. Also controls `stub_function_body_js` and `stub_function_body_go`. |
| `excluded_function_patterns` | list[str] | `["__init__", "setUp", "tearDown", "setUpClass", "tearDownClass"]` | Exact function names to skip. |

---

### ai_instruction_comment

Detects comments like "implement this", "omitted for brevity", "add error handling here".

```yaml
rules:
  ai_instruction_comment:
    enabled: true
```

No additional fields.

---

### bare_except_pass

Detects Python `except:` or `except Exception:` with only `pass`/`...` as body.

```yaml
rules:
  bare_except_pass:
    enabled: true
```

No additional fields. Also controls `bare_except_pass_js` and `bare_except_pass_go`.

---

### ai_conversational_bleed

Detects AI chat phrases ("Certainly!", "Here's the updated code") and markdown code fences in source files.

```yaml
rules:
  ai_conversational_bleed:
    enabled: true
```

No additional fields.

---

### ai_identity_refusal

Detects AI self-identification and refusal text ("As an AI language model", "I cannot assist").

```yaml
rules:
  ai_identity_refusal:
    enabled: true
```

No additional fields.

---

### hallucinated_placeholder

Detects placeholder credentials, fake URLs, and replacement markers in non-test files.

```yaml
rules:
  hallucinated_placeholder:
    enabled: true
    extra_patterns: []
    allowed_domains:
      - example.com
      - example.org
      - example.net
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `enabled` | bool | `true` | Enable/disable the rule. |
| `extra_patterns` | list[str] | `[]` | Additional regex patterns to flag as placeholders. |
| `allowed_domains` | list[str] | `["example.com", "example.org", "example.net"]` | Domains allowed in URLs (RFC 2606 reserved names for documentation). |

---

### dead_code_comment

Detects blocks of 4+ consecutive commented-out code lines.

```yaml
rules:
  dead_code_comment:
    enabled: true
    min_consecutive_lines: 4
    excluded_paths:
      - docs/**
      - examples/**
      - "*.md"
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `enabled` | bool | `true` | Enable/disable the rule. |
| `min_consecutive_lines` | int | `4` | Minimum number of consecutive commented-out code lines required to fire. |
| `excluded_paths` | list[str] | `["docs/**", "examples/**", "*.md"]` | Glob patterns for paths to skip. |

---

### incomplete_error_message

Detects generic error messages like `raise ValueError("An error occurred")`.

```yaml
rules:
  incomplete_error_message:
    enabled: true
```

No additional fields.

---

### missing_default_branch

**Off by default (opt-in).** Detects `if/elif` chains without `else` and `match` statements without `case _:`.

```yaml
rules:
  missing_default_branch:
    enabled: false   # set to true to enable
    min_elif_count: 2
    check_match: true
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `enabled` | bool | `false` | Enable/disable the rule. Off by default (~60% precision). |
| `min_elif_count` | int | `2` | Minimum number of `elif` branches required before flagging. |
| `check_match` | bool | `true` | Also check `match` statements for missing `case _:`. |

---

### ai_hardcoded_mocks

**Off by default (opt-in).** Detects AI-generated mock data like "John Doe", "Acme Corp" in non-test files.

```yaml
rules:
  ai_hardcoded_mocks:
    enabled: false   # set to true to enable
    additional_excluded_paths:
      - "**/seed*"
      - "**/conftest*"
      - "**/factory*"
      - "**/fake*"
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `enabled` | bool | `false` | Enable/disable the rule. Off by default (~50% precision). |
| `additional_excluded_paths` | list[str] | `["**/seed*", "**/conftest*", "**/factory*", "**/fake*"]` | Additional path patterns to skip. |

---

### undeclared_import

**Off by default (opt-in).** Detects imports not declared in the project manifest (requirements.txt / package.json / go.mod).

```yaml
rules:
  undeclared_import:
    enabled: false   # set to true to enable
    additional_allowed:
      - typing
      - typing_extensions
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `enabled` | bool | `false` | Enable/disable the rule. Off by default (noisy without per-project manifest config). |
| `additional_allowed` | list[str] | `["typing", "typing_extensions"]` | Additional package names to treat as allowed (e.g., dev-only tools). |

---

### sql_string_concat

Detects SQL queries built by string concatenation, f-strings, or `.format()`.

```yaml
rules:
  sql_string_concat:
    enabled: true
```

No additional fields.

---

### insecure_default

Detects insecure configuration defaults: `verify=False`, `DEBUG=True`, `ssl._create_unverified_context`, subprocess with `shell=True` and a variable argument, and wildcard CORS origins.

```yaml
rules:
  insecure_default:
    enabled: true
```

No additional fields.

---

### hardcoded_secret

Detects passwords, API keys, tokens, and other secrets assigned to recognizable variable names. Uses Shannon entropy to distinguish real secrets from low-entropy enum values.

```yaml
rules:
  hardcoded_secret:
    enabled: true
```

No additional fields.

---

### typescript_any_abuse

Detects `as any` casts, `@ts-ignore`, and `@ts-expect-error` without an explanation in TypeScript files.

```yaml
rules:
  typescript_any_abuse:
    enabled: true
```

No additional fields.

---

### react_index_key

Detects `key={index}`, `key={i}`, `key={idx}` in JSX/TSX files.

```yaml
rules:
  react_index_key:
    enabled: true
```

No additional fields.

---

### react_async_useeffect

Detects `useEffect(async` — passing an async function directly to `useEffect`.

```yaml
rules:
  react_async_useeffect:
    enabled: true
```

No additional fields.

---

### go_ignored_error

Detects `_ = pkg.Func(...)` assignments that silently discard error return values.

```yaml
rules:
  go_ignored_error:
    enabled: true
    extra_allowed_patterns: []
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `enabled` | bool | `true` | Enable/disable the rule. |
| `extra_allowed_patterns` | list[str] | `[]` | Additional regex patterns for function names where ignoring errors is acceptable. |

---

### python_mutable_default

Detects mutable default arguments in function definitions: `def f(x=[])`, `def f(data={})`.

```yaml
rules:
  python_mutable_default:
    enabled: true
```

No additional fields.

---

### go_missing_defer

Detects `http.Get`, `os.Open`, and `os.Create` calls without a matching `defer X.Close()` within the next 5 lines.

```yaml
rules:
  go_missing_defer:
    enabled: true
```

No additional fields.

---

### console_log_in_production

Detects `console.log`, `console.debug`, `console.info`, `console.warn` in non-test JS/TS files.

```yaml
rules:
  console_log_in_production:
    enabled: true
    allowed_methods:
      - error
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `enabled` | bool | `true` | Enable/disable the rule. |
| `allowed_methods` | list[str] | `["error"]` | Console methods that are allowed (not flagged). `console.error` is allowed by default. |

---

### go_error_wrap_missing_w

Detects `fmt.Errorf("...: %v", err)` where `%w` should be used for error wrapping.

```yaml
rules:
  go_error_wrap_missing_w:
    enabled: true
```

No additional fields.

---

### cross_language_idiom

Detects language-wrong idioms: `null` in Python, `nil` in JS/TS, `None` in Go, etc.

```yaml
rules:
  cross_language_idiom:
    enabled: true
```

No additional fields.

---

### js_await_in_loop

Detects `await` inside `for`/`while` loop bodies in JS/TS files.

```yaml
rules:
  js_await_in_loop:
    enabled: true
```

No additional fields.

---

### js_json_parse_unguarded

Detects `JSON.parse()` calls not surrounded by a try/catch within 3 lines.

```yaml
rules:
  js_json_parse_unguarded:
    enabled: true
```

No additional fields.

---

### js_unhandled_promise

Detects `.then(...)` without a `.catch(...)` handler within 3 lines.

```yaml
rules:
  js_unhandled_promise:
    enabled: true
```

No additional fields.

---

### js_timer_no_cleanup

Detects `setTimeout`/`setInterval` in React components (`.jsx`/`.tsx`) without a corresponding `clearTimeout`/`clearInterval` anywhere in the file.

```yaml
rules:
  js_timer_no_cleanup:
    enabled: true
```

No additional fields.

---

### js_loose_equality

Detects `==` and `!=` operators in JS/TS files (instead of `===`/`!==`).

```yaml
rules:
  js_loose_equality:
    enabled: true
```

No additional fields.

---

### js_dangerously_set_html

Detects use of the `dangerouslySetInnerHTML` React prop in JSX/TSX files.

```yaml
rules:
  js_dangerously_set_html:
    enabled: true
```

No additional fields.

---

### deep_nesting

**Off by default (opt-in).** Detects code nested beyond `max_depth` levels.

```yaml
rules:
  deep_nesting:
    enabled: false   # set to true to enable
    max_depth: 6
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `enabled` | bool | `false` | Enable/disable the rule. Off by default (produces ~243K findings at depth=4 on benchmark set). |
| `max_depth` | int | `6` | Maximum nesting depth before flagging. Python uses 4-space indent levels. JS/TS/Go use brace counting. |

---

### large_function

**Off by default (opt-in).** Detects functions exceeding `max_lines` lines.

```yaml
rules:
  large_function:
    enabled: false   # set to true to enable
    max_lines: 100
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `enabled` | bool | `false` | Enable/disable the rule. Off by default (~16K findings at 60 lines). |
| `max_lines` | int | `100` | Maximum function length in lines before flagging. |

---

### select_star_sql

Detects `SELECT * FROM` in application code (not in test/spec files).

```yaml
rules:
  select_star_sql:
    enabled: true
```

No additional fields.

---

### weak_hash

Detects MD5 and SHA-1 hash algorithm usage in `.py`, `.js`, `.ts`, `.go`, `.java` files.

```yaml
rules:
  weak_hash:
    enabled: true
```

No additional fields.

---

### regex_dos

Detects regex patterns with nested quantifiers like `(a+)+` inside string literals that can cause catastrophic backtracking.

```yaml
rules:
  regex_dos:
    enabled: true
```

No additional fields.

---

### obvious_perf_drain

**Off by default (opt-in).** Detects nested loops that suggest O(n²) complexity.

```yaml
rules:
  obvious_perf_drain:
    enabled: false   # set to true to enable
```

No additional fields. Off by default (~37K findings without scope analysis).

