# Rule Catalog

See [docs/rule-catalog.md](../docs/rule-catalog.md) for the full catalog with examples, false-positive notes, and config options for all 72 rules.

## Quick Reference

| Category | Count | Key Rules |
|----------|-------|-----------|
| AI Detection (Tier 1) | 7 | stub_function_body, ai_instruction_comment, bare_except_pass |
| AI Smoking Guns (Tier 2) | 3 | ai_conversational_bleed, ai_identity_refusal, hallucinated_placeholder |
| Quality (Tier 3) | 5 | placeholder_tokens, dead_code_comment, incomplete_error_message |
| Security | 7 | hardcoded_secret, sql_string_concat, insecure_default, weak_hash |
| JS/Node | 11 | js_await_in_loop, js_json_parse_unguarded, react_index_key |
| Go | 3 | go_ignored_error, go_missing_defer, go_error_wrap_missing_w |
| Python | 1 | python_mutable_default |
| Cross-Language | 17 | cross_language_idiom, debug_code_left, unreachable_code_after_return |
| Data-Flow | 4 | contradictory_null_check, lock_without_release, idor_risk |
| Quality (opt-in) | 9 | deep_nesting, large_function, within_file_duplication |
| API Contract | 1 | api_contract_breaking |
| Repo-Specific | 1 | forbidden_import_edges |
| Meta | 1 | unused_suppression |
| **Total** | **72** | |
