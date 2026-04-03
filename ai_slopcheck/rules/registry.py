from __future__ import annotations

from ai_slopcheck.rules.base import Rule
from ai_slopcheck.rules.generic.ai_conversational_bleed import AiConversationalBleedRule
from ai_slopcheck.rules.generic.ai_hardcoded_mocks import AiHardcodedMocksRule
from ai_slopcheck.rules.generic.ai_identity_refusal import AiIdentityRefusalRule
from ai_slopcheck.rules.generic.ai_instruction_comment import AiInstructionCommentRule
from ai_slopcheck.rules.generic.api_contract_breaking import ApiContractBreakingRule
from ai_slopcheck.rules.generic.assignment_in_conditional import AssignmentInConditionalRule
from ai_slopcheck.rules.generic.bare_except_pass import BareExceptPassRule
from ai_slopcheck.rules.generic.bare_except_pass_go import BareExceptPassGoRule
from ai_slopcheck.rules.generic.bare_except_pass_js import BareExceptPassJsRule
from ai_slopcheck.rules.generic.break_in_nested_loop import BreakInNestedLoopRule
from ai_slopcheck.rules.generic.collection_modify_while_iterating import (
    CollectionModifyWhileIteratingRule,
)
from ai_slopcheck.rules.generic.console_log_in_production import ConsoleLogInProductionRule
from ai_slopcheck.rules.generic.contradictory_null_check import ContradictoryNullCheckRule
from ai_slopcheck.rules.generic.cross_language_idiom import CrossLanguageIdiomRule
from ai_slopcheck.rules.generic.dangerous_shell_in_markdown import DangerousShellInMarkdownRule
from ai_slopcheck.rules.generic.dead_code_comment import DeadCodeCommentRule
from ai_slopcheck.rules.generic.debug_code_left import DebugCodeLeftRule
from ai_slopcheck.rules.generic.deep_inheritance import DeepInheritanceRule
from ai_slopcheck.rules.generic.deep_nesting import DeepNestingRule
from ai_slopcheck.rules.generic.division_by_zero_risk import DivisionByZeroRiskRule
from ai_slopcheck.rules.generic.early_return_opportunity import EarlyReturnOpportunityRule
from ai_slopcheck.rules.generic.global_state_leak import GlobalStateLeakRule
from ai_slopcheck.rules.generic.go_error_wrap_missing_w import GoErrorWrapMissingWRule
from ai_slopcheck.rules.generic.go_ignored_error import GoIgnoredErrorRule
from ai_slopcheck.rules.generic.go_missing_defer import GoMissingDeferRule
from ai_slopcheck.rules.generic.goto_usage import GotoUsageRule
from ai_slopcheck.rules.generic.hallucinated_placeholder import HallucinatedPlaceholderRule
from ai_slopcheck.rules.generic.hardcoded_secret import HardcodedSecretRule
from ai_slopcheck.rules.generic.idor_risk import IdorRiskRule
from ai_slopcheck.rules.generic.incomplete_error_message import IncompleteErrorMessageRule
from ai_slopcheck.rules.generic.insecure_default import InsecureDefaultRule
from ai_slopcheck.rules.generic.js_await_in_loop import JsAwaitInLoopRule
from ai_slopcheck.rules.generic.js_dangerously_set_html import JsDangerouslySetHtmlRule
from ai_slopcheck.rules.generic.js_json_parse_unguarded import JsJsonParseUnguardedRule
from ai_slopcheck.rules.generic.js_loose_equality import JsLooseEqualityRule
from ai_slopcheck.rules.generic.js_timer_no_cleanup import JsTimerNoCleanupRule
from ai_slopcheck.rules.generic.js_unhandled_promise import JsUnhandledPromiseRule
from ai_slopcheck.rules.generic.large_anonymous_function import LargeAnonymousFunctionRule
from ai_slopcheck.rules.generic.large_file import LargeFileRule
from ai_slopcheck.rules.generic.large_function import LargeFunctionRule
from ai_slopcheck.rules.generic.lock_without_release import LockWithoutReleaseRule
from ai_slopcheck.rules.generic.many_positional_args import ManyPositionalArgsRule
from ai_slopcheck.rules.generic.missing_default_branch import MissingDefaultBranchRule
from ai_slopcheck.rules.generic.multiple_classes_per_file import MultipleClassesPerFileRule
from ai_slopcheck.rules.generic.obfuscated_code import ObfuscatedCodeRule
from ai_slopcheck.rules.generic.obvious_perf_drain import ObviousPerfDrainRule
from ai_slopcheck.rules.generic.oversized_class import OversizedClassRule
from ai_slopcheck.rules.generic.param_reassignment import ParamReassignmentRule
from ai_slopcheck.rules.generic.placeholder_tokens import PlaceholderTokensRule
from ai_slopcheck.rules.generic.python_mutable_default import PythonMutableDefaultRule
from ai_slopcheck.rules.generic.react_async_useeffect import ReactAsyncUseeffectRule
from ai_slopcheck.rules.generic.react_index_key import ReactIndexKeyRule
from ai_slopcheck.rules.generic.recursion_without_limit import RecursionWithoutLimitRule
from ai_slopcheck.rules.generic.redundant_sql_index import RedundantSqlIndexRule
from ai_slopcheck.rules.generic.regex_dos import RegexDosRule
from ai_slopcheck.rules.generic.select_star_sql import SelectStarSqlRule
from ai_slopcheck.rules.generic.short_variable_name import ShortVariableNameRule
from ai_slopcheck.rules.generic.sql_string_concat import SqlStringConcatRule
from ai_slopcheck.rules.generic.stale_comment import StaleCommentRule
from ai_slopcheck.rules.generic.stub_function_body import StubFunctionBodyRule
from ai_slopcheck.rules.generic.stub_function_body_go import StubFunctionBodyGoRule
from ai_slopcheck.rules.generic.stub_function_body_js import StubFunctionBodyJsRule
from ai_slopcheck.rules.generic.thread_unsafe_global import ThreadUnsafeGlobalRule
from ai_slopcheck.rules.generic.typescript_any_abuse import TypescriptAnyAbuseRule
from ai_slopcheck.rules.generic.undeclared_import import UndeclaredImportRule
from ai_slopcheck.rules.generic.unreachable_code_after_return import UnreachableCodeAfterReturnRule
from ai_slopcheck.rules.generic.unused_suppression import UnusedSuppressionRule
from ai_slopcheck.rules.generic.use_after_free import UseAfterFreeRule
from ai_slopcheck.rules.generic.weak_function_name import WeakFunctionNameRule
from ai_slopcheck.rules.generic.weak_hash import WeakHashRule
from ai_slopcheck.rules.generic.within_file_duplication import WithinFileDuplicationRule
from ai_slopcheck.rules.repo.forbidden_import_edges import ForbiddenImportEdgesRule


def build_rules() -> list[Rule]:
    return [
        # Original rules
        PlaceholderTokensRule(),
        ForbiddenImportEdgesRule(),
        # Tier 1: AI code failure detection
        StubFunctionBodyRule(),
        AiInstructionCommentRule(),
        BareExceptPassRule(),
        # Tier 2: Smoking guns
        AiConversationalBleedRule(),
        AiIdentityRefusalRule(),
        HallucinatedPlaceholderRule(),
        # Tier 3: Supplementary
        DeadCodeCommentRule(),
        IncompleteErrorMessageRule(),
        MissingDefaultBranchRule(),
        AiHardcodedMocksRule(),
        # Multi-language variants
        StubFunctionBodyJsRule(),
        StubFunctionBodyGoRule(),
        BareExceptPassJsRule(),
        BareExceptPassGoRule(),
        # Security rules (Phase 2)
        UndeclaredImportRule(),
        SqlStringConcatRule(),
        InsecureDefaultRule(),
        HardcodedSecretRule(),
        # Language-specific rules (Phase 3)
        TypescriptAnyAbuseRule(),
        ReactIndexKeyRule(),
        ReactAsyncUseeffectRule(),
        GoIgnoredErrorRule(),
        PythonMutableDefaultRule(),
        GoMissingDeferRule(),
        # Phase 4: Language-quality rules
        ConsoleLogInProductionRule(),
        GoErrorWrapMissingWRule(),
        CrossLanguageIdiomRule(),
        # Meta-rules
        UnusedSuppressionRule(),
        # Phase 5: JS/Node and cross-language rules
        JsAwaitInLoopRule(),
        JsJsonParseUnguardedRule(),
        JsUnhandledPromiseRule(),
        JsTimerNoCleanupRule(),
        JsLooseEqualityRule(),
        JsDangerouslySetHtmlRule(),
        DeepNestingRule(),
        LargeFunctionRule(),
        SelectStarSqlRule(),
        WeakHashRule(),
        RegexDosRule(),
        ObviousPerfDrainRule(),
        # Phase 6: Obfuscation, global state, iteration safety, numeric safety
        ObfuscatedCodeRule(),
        GlobalStateLeakRule(),
        CollectionModifyWhileIteratingRule(),
        DivisionByZeroRiskRule(),
        UnreachableCodeAfterReturnRule(),
        # Phase 7: Code quality and correctness
        ParamReassignmentRule(),
        LargeFileRule(),
        ShortVariableNameRule(),
        GotoUsageRule(),
        AssignmentInConditionalRule(),
        # Phase 8: Structure and design rules
        WithinFileDuplicationRule(),
        EarlyReturnOpportunityRule(),
        RecursionWithoutLimitRule(),
        DeepInheritanceRule(),
        LargeAnonymousFunctionRule(),
        # Phase 9: Debug and comment quality
        DebugCodeLeftRule(),
        StaleCommentRule(),
        # Phase 10: Concurrency, IDOR, and null-check correctness
        ContradictoryNullCheckRule(),
        LockWithoutReleaseRule(),
        IdorRiskRule(),
        ThreadUnsafeGlobalRule(),
        # Phase 11: Call-site design, SQL schema, memory safety, naming
        ManyPositionalArgsRule(),
        RedundantSqlIndexRule(),
        UseAfterFreeRule(),
        WeakFunctionNameRule(),
        # Phase 12: Structure, control flow, and documentation safety
        MultipleClassesPerFileRule(),
        OversizedClassRule(),
        BreakInNestedLoopRule(),
        DangerousShellInMarkdownRule(),
        # Phase 13: API contract detection
        ApiContractBreakingRule(),
    ]
