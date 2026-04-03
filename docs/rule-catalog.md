# Rule Catalog

Complete catalog of all 72 rules. For configuration details, see [docs/configuration-guide.md](configuration-guide.md). For suppression and baseline usage, see [docs/user-guide.md](user-guide.md).

## Categories

- [AI Detection — Tier 1](#ai-detection--tier-1)
- [AI Smoking Guns — Tier 2](#ai-smoking-guns--tier-2)
- [Quality / Supplementary — Tier 3](#quality--supplementary--tier-3)
- [Security](#security)
- [JavaScript / Node](#javascript--node)
- [Go](#go)
- [Python](#python)
- [Cross-language / Structural](#cross-language--structural)
- [Repo-specific](#repo-specific)
- [Meta](#meta)

---

## AI Detection — Tier 1

Highest-signal AI failure patterns. All enabled by default.

---

### stub_function_body

| | |
|---|---|
| **ID** | `stub_function_body` |
| **Languages** | Python (`.py`) |
| **Default** | On |
| **Severity** | `warning` |
| **Confidence** | `high` (functions starting with `get_`, `fetch_`, `load_`, `compute_`, `calculate_`, `process_`) / `medium` (others) |

Detects Python functions whose entire body is a single stub statement: `pass`, `...`, `return None`, `return []`, `return {}`, or similar trivial return values.

These are characteristic of LLM output truncation where the model omits actual implementation.

**Triggers:**
```python
def get_user(user_id: int):
    return None  # flagged

def calculate_total(items):
    pass  # flagged
```

**Does not trigger:**
```python
@abstractmethod
def get_user(self, user_id: int):
    ...  # abstract methods are skipped

def __init__(self):
    pass  # __init__ is in excluded list by default
```

**Config:** `stub_function_body.excluded_function_patterns` — list of exact function names to skip (default: `__init__`, `setUp`, `tearDown`, `setUpClass`, `tearDownClass`).

**False-positive notes:** Intentional no-op functions in testing infrastructure. Add the function name to `excluded_function_patterns` or use inline suppression.

---

### stub_function_body_js

| | |
|---|---|
| **ID** | `stub_function_body_js` |
| **Languages** | JavaScript/TypeScript (`.js`, `.jsx`, `.ts`, `.tsx`) |
| **Default** | On |
| **Severity** | `warning` |
| **Confidence** | `low` |

Detects JS/TS functions with stub bodies: empty `{}`, one-liner returning `null`/`undefined`/`false`/`[]`, or `throw new Error("not implemented")`.

Skips test/spec files. Skips functions whose names start with `empty`, `noop`, `mock`, `fake`, `stub`, `dummy`.

**Triggers:**
```typescript
async function fetchUser(id: string): Promise<User> {
    return null;  // flagged
}

const processOrder = (order: Order) => {};  // flagged
```

**Config:** Shares `stub_function_body.enabled` — controlled by the same flag as the Python variant.

---

### stub_function_body_go

| | |
|---|---|
| **ID** | `stub_function_body_go` |
| **Languages** | Go (`.go`) |
| **Default** | On |
| **Severity** | `warning` |
| **Confidence** | `low` |

Detects Go functions with stub bodies: single `return nil`, `return ""`, `return 0`, `return false`, empty struct/map, or empty body.

**Triggers:**
```go
func GetUser(id string) (*User, error) {
    return nil, nil  // flagged
}
```

**Config:** Shares `stub_function_body.enabled`.

---

### ai_instruction_comment

| | |
|---|---|
| **ID** | `ai_instruction_comment` |
| **Languages** | All file types |
| **Default** | On |
| **Severity** | `warning` |
| **Confidence** | `high` |

Detects AI instruction-style comments that indicate incomplete implementation. Two patterns:

- Instruction phrases: "implement this logic", "fill in the implementation", "write the remaining code"
- Code omission markers: "existing code", "omitted for brevity", "rest of the code", "unchanged code", "code goes here"

**Triggers:**
```python
# TODO: implement the remaining logic here
def process():
    pass

# ... existing code ...
```

**Config:** `ai_instruction_comment.enabled`

---

### bare_except_pass

| | |
|---|---|
| **ID** | `bare_except_pass` |
| **Languages** | Python (`.py`) |
| **Default** | On |
| **Severity** | `warning` |
| **Confidence** | `high` (bare `except:`) / `medium` (`except Exception:`) |

Detects Python exception handlers that silently swallow errors: `except:` or `except Exception:` with an empty body, only `pass`, or only `...`.

**Triggers:**
```python
try:
    risky_call()
except:
    pass  # flagged
```

**Config:** `bare_except_pass.enabled`

---

### bare_except_pass_js

| | |
|---|---|
| **ID** | `bare_except_pass_js` |
| **Languages** | `.js`, `.jsx`, `.ts`, `.tsx` |
| **Default** | On |
| **Severity** | `warning` |
| **Confidence** | `medium` |

Detects empty `catch` blocks in JS/TS.

**Config:** `bare_except_pass.enabled`

---

### bare_except_pass_go

| | |
|---|---|
| **ID** | `bare_except_pass_go` |
| **Languages** | Go (`.go`) |
| **Default** | On |
| **Severity** | `warning` |
| **Confidence** | `medium` |

Detects Go error checks that silently return a zero value: `if err != nil { return nil }` or similar single-line silent returns.

**Config:** `bare_except_pass.enabled`

---

## AI Smoking Guns — Tier 2

Near-certain AI artifacts. Enabled by default.

---

### ai_conversational_bleed

| | |
|---|---|
| **ID** | `ai_conversational_bleed` |
| **Languages** | Source code files (`.py`, `.js`, `.jsx`, `.ts`, `.tsx`, `.go`, `.rs`, `.java`, `.kt`, `.cs`, `.c`, `.cc`, `.cpp`, `.h`, `.hpp`) |
| **Default** | On |
| **Severity** | `error` |
| **Confidence** | `high` |

Detects AI conversational text copy-pasted into source files:

- Chat preamble phrases: "Certainly!", "Sure, here's the code", "As requested,", "I've created", "Let me help you", "I'll implement"
- Markdown code fences in source files

Skips files with path segments: `prompt`, `template`, `example`, `fixture`, `test`, `generator`, `dataset`, `sample`.

**Config:** `ai_conversational_bleed.enabled`

---

### ai_identity_refusal

| | |
|---|---|
| **ID** | `ai_identity_refusal` |
| **Languages** | All file types |
| **Default** | On |
| **Severity** | `error` |
| **Confidence** | `high` |

Detects AI self-identification and refusal text: "As an AI language model", "I'm an AI", "I cannot fulfill", "I apologize, but I cannot", "I don't have access to", "I'm not able to".

Skips comment-only lines. Uses tree-sitter to skip matches inside strings when available.

**Config:** `ai_identity_refusal.enabled`

---

### hallucinated_placeholder

| | |
|---|---|
| **ID** | `hallucinated_placeholder` |
| **Languages** | All file types |
| **Default** | On |
| **Severity** | `warning` |
| **Confidence** | `medium` |

Detects four categories of hallucinated placeholder values:

- Placeholder credentials: `"your_api_key"`, `"my-token-here"`
- Replacement markers: `REPLACE_ME`, `<INSERT_VALUE>`, `YOUR_API_KEY_HERE`, `sk-xxxx`
- Fake URLs: `https://api.example.com`, `https://your.service.com`
- Fake paths: `path/to/your/config`, `/path/to/file`

Skips test, fixture, mock, stub, example files. Allowed domains configurable.

**Config:**
- `hallucinated_placeholder.allowed_domains` — domains to allow in URLs
- `hallucinated_placeholder.extra_patterns` — additional patterns

---

## Quality / Supplementary — Tier 3

---

### placeholder_tokens

| | |
|---|---|
| **ID** | `placeholder_tokens` |
| **Languages** | `.py`, `.js`, `.jsx`, `.ts`, `.tsx`, `.go`, `.rs`, `.java`, `.kt`, `.cs`, `.c`, `.cc`, `.cpp`, `.h`, `.hpp` |
| **Default** | On |
| **Severity** | `warning` |
| **Confidence** | `high` |

Detects banned placeholder tokens as word-boundary matches. Default tokens: `TODO`, `FIXME`, `HACK`, `TEMPORARY`.

**Config:** `placeholder_tokens.banned_tokens` — list of tokens to flag.

---

### dead_code_comment

| | |
|---|---|
| **ID** | `dead_code_comment` |
| **Languages** | `.py`, `.js`, `.jsx`, `.ts`, `.tsx`, `.go`, `.rs`, `.java`, `.kt`, `.cs`, `.c`, `.cc`, `.cpp`, `.h`, `.hpp` |
| **Default** | On |
| **Severity** | `note` |
| **Confidence** | `medium` |

Detects blocks of 4+ consecutive commented-out code lines. Uses code-pattern matching and prose filtering via English stopwords.

**Config:**
- `dead_code_comment.min_consecutive_lines` — threshold (default: 4)
- `dead_code_comment.excluded_paths` — path patterns to skip

---

### incomplete_error_message

| | |
|---|---|
| **ID** | `incomplete_error_message` |
| **Languages** | `.py`, `.js`, `.jsx`, `.ts`, `.tsx`, `.go`, `.java`, `.kt`, `.cs`, `.rs` |
| **Default** | On |
| **Severity** | `note` |
| **Confidence** | `medium` |

Detects generic error messages in `raise`/`throw` statements: "An error occurred", "Something went wrong", "Failed to process", "Invalid input", "Unexpected error", "Operation failed", "Internal error", "Not implemented".

Skips lines with string interpolation (`{`, `%s`, `f"`) since those typically add context.

---

### missing_default_branch

| | |
|---|---|
| **ID** | `missing_default_branch` |
| **Languages** | Python (`.py`) |
| **Default** | **Off (opt-in)** |
| **Severity** | `note` (if/elif) / `warning` (match) |
| **Confidence** | `low` (if/elif) / `medium` (match) |

Detects `if/elif` chains with 2+ `elif` branches but no `else`, and `match` statements with 2+ cases but no `case _:`.

Off by default (~60% precision on guard-clause patterns).

**Config:**
- `missing_default_branch.enabled` — must set to `true` to use
- `missing_default_branch.min_elif_count` — default `2`
- `missing_default_branch.check_match` — default `true`

---

### ai_hardcoded_mocks

| | |
|---|---|
| **ID** | `ai_hardcoded_mocks` |
| **Languages** | All file types |
| **Default** | **Off (opt-in)** |
| **Severity** | `warning` |
| **Confidence** | `low` |

Detects AI-generated mock data in non-test source files:

- Person names: "John Doe", "Jane Doe", "John Smith", "Bob Smith", "Alice Johnson"
- Company names: "Acme Corp", "Foo Bar", "Example Corp", "Widget Co"
- Email addresses with suspicious prefixes not on allowed domains
- Phone numbers: 555/123 prefix patterns

Off by default (~50% precision without per-project tuning).

**Config:**
- `ai_hardcoded_mocks.enabled` — must set to `true` to use
- `ai_hardcoded_mocks.additional_excluded_paths` — extra path patterns to skip

---

## Security

---

### hardcoded_secret

| | |
|---|---|
| **ID** | `hardcoded_secret` |
| **Languages** | All file types |
| **Default** | On |
| **Severity** | `error` |
| **Confidence** | `high` (Shannon entropy > 3.5) / `medium` (lower entropy) |

Detects passwords, API keys, tokens, and secrets assigned to recognizable variable names. Uses Shannon entropy to distinguish real secrets from placeholder strings. Skips test, fixture, mock, stub, example, spec, seed, sample, generated, vendor files.

---

### sql_string_concat

| | |
|---|---|
| **ID** | `sql_string_concat` |
| **Languages** | `.py`, `.js`, `.jsx`, `.ts`, `.tsx`, `.go` |
| **Default** | On |
| **Severity** | `error` |
| **Confidence** | `medium` |

Detects SQL queries built by string concatenation, f-strings, or `.format()` — a SQL injection risk.

**Triggers:**
```python
query = "SELECT * FROM users WHERE name = '" + name + "'"  # flagged
query = f"DELETE FROM sessions WHERE user_id = {user_id}"  # flagged
```

---

### insecure_default

| | |
|---|---|
| **ID** | `insecure_default` |
| **Languages** | `.py`, `.js`, `.jsx`, `.ts`, `.tsx`, `.go` |
| **Default** | On |
| **Severity** | `warning` |
| **Confidence** | `high` |

Detects: `verify=False`, `ssl._create_unverified_context()`, subprocess with `shell=True` and variable arg, `DEBUG=True`, wildcard CORS origins (`*`).

---

### weak_hash

| | |
|---|---|
| **ID** | `weak_hash` |
| **Languages** | `.py`, `.js`, `.ts`, `.go`, `.java` |
| **Default** | On |
| **Severity** | `warning` |
| **Confidence** | `high` |

Detects MD5 and SHA-1 hash algorithm usage.

---

### undeclared_import

| | |
|---|---|
| **ID** | `undeclared_import` |
| **Languages** | `.py`, `.js`, `.jsx`, `.ts`, `.tsx`, `.go` |
| **Default** | **Off (opt-in)** |
| **Severity** | `error` |
| **Confidence** | `high` |

Detects imports not declared in the project manifest (requirements.txt / package.json / go.mod). Skips stdlib and Node.js built-ins.

Off by default — noisy without a properly maintained manifest.

**Config:**
- `undeclared_import.enabled` — must set to `true` to use
- `undeclared_import.additional_allowed` — extra allowed package names

---

## JavaScript / Node

---

### js_await_in_loop

| | |
|---|---|
| **ID** | `js_await_in_loop` |
| **Languages** | `.js`, `.jsx`, `.ts`, `.tsx` |
| **Default** | On |
| **Severity** | `warning` |
| **Confidence** | `medium` |

Detects `await` inside `for`/`while` loop bodies. Sequential awaits serialize async work.

**Fix:** Use `Promise.all(items.map(item => doAsync(item)))`.

---

### js_json_parse_unguarded

| | |
|---|---|
| **ID** | `js_json_parse_unguarded` |
| **Languages** | `.js`, `.jsx`, `.ts`, `.tsx` |
| **Default** | On |
| **Severity** | `warning` |
| **Confidence** | `medium` |

Detects `JSON.parse()` calls without a try/catch within 3 lines.

---

### js_unhandled_promise

| | |
|---|---|
| **ID** | `js_unhandled_promise` |
| **Languages** | `.js`, `.jsx`, `.ts`, `.tsx` |
| **Default** | On |
| **Severity** | `warning` |
| **Confidence** | `medium` |

Detects `.then(...)` without `.catch(...)` within 3 lines.

---

### js_timer_no_cleanup

| | |
|---|---|
| **ID** | `js_timer_no_cleanup` |
| **Languages** | `.jsx`, `.tsx` (React component files) |
| **Default** | On |
| **Severity** | `note` |
| **Confidence** | `medium` |

Detects `setTimeout`/`setInterval` without a corresponding `clearTimeout`/`clearInterval` anywhere in the file.

---

### js_loose_equality

| | |
|---|---|
| **ID** | `js_loose_equality` |
| **Languages** | `.js`, `.jsx`, `.ts`, `.tsx` |
| **Default** | On |
| **Severity** | `note` |
| **Confidence** | `high` |

Detects `==` and `!=` operators (type-coercing). Use `===` and `!==` instead.

---

### js_dangerously_set_html

| | |
|---|---|
| **ID** | `js_dangerously_set_html` |
| **Languages** | `.jsx`, `.tsx` |
| **Default** | On |
| **Severity** | `error` |
| **Confidence** | `high` |

Detects the `dangerouslySetInnerHTML` React prop — a potential XSS risk. Sanitize HTML with a library such as DOMPurify before using this prop.

---

### console_log_in_production

| | |
|---|---|
| **ID** | `console_log_in_production` |
| **Languages** | `.js`, `.jsx`, `.ts`, `.tsx` |
| **Default** | On |
| **Severity** | `note` |
| **Confidence** | `medium` |

Detects `console.log`, `console.debug`, `console.info`, `console.warn` in non-test JS/TS. `console.error` is allowed by default.

**Config:** `console_log_in_production.allowed_methods` — list of allowed methods.

---

### typescript_any_abuse

| | |
|---|---|
| **ID** | `typescript_any_abuse` |
| **Languages** | `.ts`, `.tsx` |
| **Default** | On |
| **Severity** | `warning` |
| **Confidence** | `medium` |

Detects TypeScript type-safety bypasses: `as any`, `@ts-ignore`, and `@ts-expect-error` without an explanation.

---

### react_index_key

| | |
|---|---|
| **ID** | `react_index_key` |
| **Languages** | `.jsx`, `.tsx` |
| **Default** | On |
| **Severity** | `warning` |
| **Confidence** | `high` |

Detects array index used as React `key` prop: `key={index}`, `key={i}`, `key={idx}`.

---

### react_async_useeffect

| | |
|---|---|
| **ID** | `react_async_useeffect` |
| **Languages** | `.js`, `.jsx`, `.ts`, `.tsx` |
| **Default** | On |
| **Severity** | `error` |
| **Confidence** | `high` |

Detects `useEffect(async` — passing an async function directly to `useEffect`. React ignores the returned Promise.

---

### regex_dos

| | |
|---|---|
| **ID** | `regex_dos` |
| **Languages** | `.py`, `.js`, `.jsx`, `.ts`, `.tsx`, `.go` |
| **Default** | On |
| **Severity** | `warning` |
| **Confidence** | `medium` |

Detects regex patterns with nested quantifiers inside string literals: `(a+)+`, `(?:a*)+`, etc.

---

## Go

---

### go_ignored_error

| | |
|---|---|
| **ID** | `go_ignored_error` |
| **Languages** | Go (`.go`) |
| **Default** | On |
| **Severity** | `warning` |
| **Confidence** | `medium` |

Detects `_ = pkg.Func(...)` silently discarding error returns. Comprehensive allowlist for conventional patterns (fmt.Print*, io.Copy, etc.).

**Config:** `go_ignored_error.extra_allowed_patterns` — additional allowed function patterns.

---

### go_missing_defer

| | |
|---|---|
| **ID** | `go_missing_defer` |
| **Languages** | Go (`.go`) |
| **Default** | On |
| **Severity** | `warning` |
| **Confidence** | `medium` |

Detects `http.Get`, `os.Open`, `os.Create` without `defer X.Close()` within 5 lines.

---

### go_error_wrap_missing_w

| | |
|---|---|
| **ID** | `go_error_wrap_missing_w` |
| **Languages** | Go (`.go`) |
| **Default** | On |
| **Severity** | `warning` |
| **Confidence** | `high` |

Detects `fmt.Errorf("...: %v", err)` where `%w` should be used to preserve the error chain.

---

## Python

---

### python_mutable_default

| | |
|---|---|
| **ID** | `python_mutable_default` |
| **Languages** | Python (`.py`) |
| **Default** | On |
| **Severity** | `warning` |
| **Confidence** | `high` |

Detects mutable default arguments: `def f(x=[])`, `def f(data={})`, `def f(s=set())`.

---

## Cross-language / Structural

---

### cross_language_idiom

| | |
|---|---|
| **ID** | `cross_language_idiom` |
| **Languages** | `.py`, `.js`, `.jsx`, `.ts`, `.tsx`, `.go` |
| **Default** | On |
| **Severity** | `error` |
| **Confidence** | `high` |

Detects language-wrong idioms per file type:

| File type | Flagged constructs |
|-----------|-------------------|
| `.py` | `null`, `.push()`, `console.log(` |
| `.js`/`.ts`/`.jsx`/`.tsx` | `nil`, `def `, `elif`, `:=` |
| `.go` | `None`, `self.`, `this.`, `console.log(` |

Uses tree-sitter (when available) for accurate string/comment detection.

---

### select_star_sql

| | |
|---|---|
| **ID** | `select_star_sql` |
| **Languages** | `.py`, `.js`, `.jsx`, `.ts`, `.tsx`, `.go` |
| **Default** | On |
| **Severity** | `note` |
| **Confidence** | `medium` |

Detects `SELECT * FROM` in application code. Skips test/spec directories.

---

### deep_nesting

| | |
|---|---|
| **ID** | `deep_nesting` |
| **Languages** | `.py`, `.js`, `.jsx`, `.ts`, `.tsx`, `.go` |
| **Default** | **Off (opt-in)** |
| **Severity** | `note` |
| **Confidence** | `medium` |

Detects code nested beyond `max_depth` levels (default: 6). Off by default (~243K findings at depth=4 on benchmark set).

**Config:** `deep_nesting.max_depth` — default `6`.

---

### large_function

| | |
|---|---|
| **ID** | `large_function` |
| **Languages** | `.py`, `.js`, `.jsx`, `.ts`, `.tsx`, `.go` |
| **Default** | **Off (opt-in)** |
| **Severity** | `note` |
| **Confidence** | `low` |

Detects functions exceeding `max_lines` lines (default: 100). Off by default (~16K findings at 60 lines).

**Config:** `large_function.max_lines` — default `100`.

---

### obvious_perf_drain

| | |
|---|---|
| **ID** | `obvious_perf_drain` |
| **Languages** | `.py`, `.js`, `.jsx`, `.ts`, `.tsx`, `.go` |
| **Default** | **Off (opt-in)** |
| **Severity** | `note` |
| **Confidence** | `low` |

Detects nested loops suggesting O(n²) complexity. Off by default (~37K findings without scope analysis).

**Config:** `obvious_perf_drain.enabled` — must set to `true` to use.

---

## Repo-specific

---

### forbidden_import_edges

| | |
|---|---|
| **ID** | `forbidden_import_edges` |
| **Languages** | Python (`.py`) |
| **Default** | On (no-op without config) |
| **Severity** | `error` |
| **Confidence** | `high` |

Enforces Python import boundary rules. Requires `boundaries` configuration. Handles both absolute and relative imports.

**Config:**
```yaml
rules:
  forbidden_import_edges:
    boundaries:
      - source_glob: "src/api/*.py"
        forbidden_prefixes:
          - src.db
        message: "API must not import DB directly."
```

---

## Meta

---

### unused_suppression

| | |
|---|---|
| **ID** | `unused_suppression` |
| **Languages** | All file types |
| **Default** | On (currently a no-op) |

Intended to flag `slopcheck: ignore` directives that matched no findings (like ruff's RUF100). Registered but not yet implemented — requires post-scan suppression tracking. Currently returns empty results.
