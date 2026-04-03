# Codex (Technical Implementation Analyst) — Round 1

I reviewed `slopcheck/rules/base.py` plus the two current rules. These seven are the best next additions if the goal is high-signal AI-failure detection with the current line-oriented rule model. LOC estimates below assume rule code, config plumbing, tests, and a short docs entry.

1. `missing_local_import_target`
- What it catches: Hallucinated repo-local imports/includes such as `from .client_utils import ...`, `import x from "../service/foo"`, or `#include "llm_cache.h"` where the target file/module does not exist in the checkout.
- Detection: Regex-extract only literal local targets, then resolve them against the current file and check candidate files. Patterns: Python `^\s*from\s+(\.{1,3}[A-Za-z_][\w.]*)\s+import\b`; JS/TS `^\s*import\b.*\bfrom\s*["'](\.{1,2}/[^"']+)["']|require\(\s*["'](\.{1,2}/[^"']+)["']\s*\)`; C/C++ `^\s*#include\s+"([^"]+)"`. Resolve with extension and `index.*` fallbacks.
- False-positive risk and mitigation: Low if limited to relative/local imports only. Ignore package imports, alias paths, generated directories, and dynamic imports. Check common extensionless forms before flagging.
- Severity, confidence, applicable languages: `error`, `high`, `.py`, `.js`, `.jsx`, `.ts`, `.tsx`, `.c`, `.cc`, `.cpp`, `.h`, `.hpp`.
- Implementation complexity estimate: `~160-200 LOC`.

2. `ellipsis_concrete_body`
- What it catches: AI left a concrete Python function or method as `...` or `pass` instead of implementing it.
- Detection: Text heuristic over Python indentation blocks: find `def` / `async def`, inspect the first significant body line, and flag if the entire body is only `...` or `pass`. Exclude `.pyi`, `@abstractmethod`, `@overload`, and classes that obviously declare `Protocol` or `ABC`.
- False-positive risk and mitigation: Very low with the exclusions above. Also skip methods inside stub-like files and abstract declarations.
- Severity, confidence, applicable languages: `error`, `high`, `.py`.
- Implementation complexity estimate: `~80-120 LOC`.

3. `ai_meta_commentary`
- What it catches: Narrative AI comments in production code, for example “rest of implementation omitted for brevity”, “same as above”, “replace with actual logic”, or “implement as needed”.
- Detection: Scan comment-only lines and block-comment bodies for phrases such as `(?i)\b(rest of (the )?(implementation|code)|omitted for brevity|same as (above|before)|similar to (above|previous)|replace with (actual|real)|implement(ation)? (here|later|as needed)|your (existing|desired) logic|left as an exercise|as an ai)\b`.
- False-positive risk and mitigation: Low if restricted to comments, not string literals. Ignore docs/example directories if needed, but this should mostly be safe on source files alone.
- Severity, confidence, applicable languages: `warning`, `high`, all current source extensions with comment syntax support.
- Implementation complexity estimate: `~60-90 LOC`.

4. `placeholder_stub_return`
- What it catches: Stubbed functions that contain a placeholder cue and then return a hardcoded trivial value like `None`, `null`, `false`, `[]`, `{}`, `0`, or `""`.
- Detection: Function-block heuristic for small bodies: body has at most 8 significant lines, contains a cue like `placeholder|stub|dummy|sample response|implement later|for now|not implemented`, and exits via a trivial literal return. Works for indentation and brace-based languages.
- False-positive risk and mitigation: Low if both conditions are required together. Ignore `tests/**`, `fixtures/**`, `mocks/**`, and names like `_test`, `_spec`, because fake returns there can be intentional.
- Severity, confidence, applicable languages: `error`, `high`, `.py`, `.js`, `.jsx`, `.ts`, `.tsx`, `.go`, `.rs`, `.java`, `.kt`, `.cs`, `.c`, `.cc`, `.cpp`.
- Implementation complexity estimate: `~170-230 LOC`.

5. `silent_exception_swallow`
- What it catches: AI-generated `except` / `catch` blocks that silently discard failures with `pass`, empty comments, `return null`, `return false`, `continue`, or similarly empty behavior.
- Detection: Match handler starts, then inspect only very short bodies. Python example: `except ...:` followed by only `pass`, `continue`, `return None|False|[]|{}`. Brace languages: `catch (...) { ... }` with at most 2 significant statements and no `throw|raise|logger|log|warn|error|print`.
- False-positive risk and mitigation: Medium unless kept strict. Mitigate by flagging only handlers with no logging, no rethrow, no explanatory “best effort” comment, and no side effects beyond the silent fallback.
- Severity, confidence, applicable languages: `warning`, `medium`, `.py`, `.js`, `.jsx`, `.ts`, `.tsx`, `.java`, `.kt`, `.cs`, `.cc`, `.cpp`.
- Implementation complexity estimate: `~130-190 LOC`.

6. `duplicated_branch_body`
- What it catches: Copy-pasted `if` / `elif` / `case` branches where the condition changed but the body stayed identical, which is a common AI patch failure.
- Detection: Within one control structure, normalize each branch body by stripping whitespace/comments and compare normalized text. Flag when two separately written branches have identical non-trivial bodies of at least 2 statements or 30 non-whitespace characters.
- False-positive risk and mitigation: Medium. Ignore grouped labels that intentionally share one body, and ignore trivial bodies such as `break`, `continue`, `return`, or `pass`.
- Severity, confidence, applicable languages: `warning`, `medium`, `.py`, `.js`, `.jsx`, `.ts`, `.tsx`, `.go`, `.rs`, `.java`, `.kt`, `.cs`, `.c`, `.cc`, `.cpp`.
- Implementation complexity estimate: `~200-260 LOC`.

7. `partial_case_placeholder`
- What it catches: Incomplete `switch` / `match` / `if-elif` chains where one branch is still a placeholder or trivial sentinel while sibling branches contain real logic.
- Detection: Detect chains with at least 3 branches. Flag a branch when its body contains `TODO|FIXME|placeholder|implement later|not implemented|unsupported for now` or only returns a trivial sentinel, while at least one sibling branch contains real work such as assignments plus a call or multiple statements.
- False-positive risk and mitigation: Medium-low if you require structural asymmetry. Ignore `default` / `else` branches that explicitly `throw`, `raise`, or return a deliberate unsupported error.
- Severity, confidence, applicable languages: `error`, `medium`, `.py`, `.js`, `.jsx`, `.ts`, `.tsx`, `.go`, `.rs`, `.java`, `.kt`, `.cs`, `.c`, `.cc`, `.cpp`.
- Implementation complexity estimate: `~160-220 LOC`.

If I were sequencing implementation, I would build them in this order as written: the top four are the clearest AI-specific failures with the best expected precision.
