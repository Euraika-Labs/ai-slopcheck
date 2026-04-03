from __future__ import annotations

from pathlib import Path

from ai_slopcheck.config import AppConfig
from ai_slopcheck.rules.generic.stub_function_body import StubFunctionBodyRule


def _scan(content: str, config: AppConfig | None = None) -> list:
    rule = StubFunctionBodyRule()
    return rule.scan_file(
        repo_root=Path("/repo"),
        relative_path="src/example.py",
        content=content,
        config=config or AppConfig(),
    )


def test_detects_return_none():
    code = 'def get_user(user_id):\n    return None\n'
    findings = _scan(code)
    assert len(findings) == 1
    assert "get_user" in findings[0].message
    assert findings[0].confidence.value == "high"  # get_ prefix


def test_detects_return_empty_list():
    code = "def fetch_items():\n    return []\n"
    findings = _scan(code)
    assert len(findings) == 1
    assert findings[0].confidence.value == "high"  # fetch_ prefix


def test_detects_pass_body():
    code = "def process_data(data):\n    pass\n"
    findings = _scan(code)
    assert len(findings) == 1
    assert "process_data" in findings[0].message
    assert findings[0].confidence.value == "high"  # process_ prefix


def test_detects_ellipsis_body():
    code = "def my_function():\n    ...\n"
    findings = _scan(code)
    assert len(findings) == 1


def test_ignores_real_implementation():
    code = "def get_user(user_id):\n    result = db.query(user_id)\n    return result\n"
    findings = _scan(code)
    assert len(findings) == 0


def test_ignores_docstring_plus_real_code():
    code = 'def my_func():\n    """Does stuff."""\n    x = compute()\n    return x\n'
    findings = _scan(code)
    assert len(findings) == 0


def test_ignores_abstract_method():
    code = "    @abstractmethod\n    def my_func(self):\n        pass\n"
    findings = _scan(code)
    assert len(findings) == 0


def test_ignores_excluded_function():
    code = "def __init__(self):\n    pass\n"
    findings = _scan(code)
    assert len(findings) == 0


def test_detects_return_empty_dict():
    code = "def build_config():\n    return {}\n"
    findings = _scan(code)
    assert len(findings) == 1


def test_detects_return_false():
    code = "def is_valid():\n    return False\n"
    findings = _scan(code)
    assert len(findings) == 1


def test_medium_confidence_for_plain_name():
    code = "def helper():\n    return None\n"
    findings = _scan(code)
    assert len(findings) == 1
    assert findings[0].confidence.value == "medium"


def test_docstring_plus_stub_still_fires():
    code = 'def load_data():\n    """Load the data."""\n    return []\n'
    findings = _scan(code)
    assert len(findings) == 1


def test_skips_non_python():
    rule = StubFunctionBodyRule()
    findings = rule.scan_file(
        repo_root=Path("/repo"),
        relative_path="src/example.js",
        content="function getData() { return null; }",
        config=AppConfig(),
    )
    assert len(findings) == 0


def test_disabled_rule():
    from ai_slopcheck.config import StubFunctionBodyConfig

    config = AppConfig()
    config.rules.stub_function_body = StubFunctionBodyConfig(enabled=False)
    findings = _scan("def get_x():\n    return None\n", config)
    assert len(findings) == 0


def test_ignores_overload_decorator():
    # @overload is intentional typing scaffolding — must NOT fire
    code = "@overload\ndef process(x: int) -> int: ...\n"
    findings = _scan(code)
    assert len(findings) == 0


def test_detects_return_zero():
    # return 0 is a stub return value for a counting function
    code = "def count():\n    return 0\n"
    findings = _scan(code)
    assert len(findings) == 1
    assert "count" in findings[0].message


def test_ignores_multiline_body():
    # Two real statements — definitely not a stub
    code = "def get_user(user_id):\n    user = db.get(user_id)\n    return user\n"
    findings = _scan(code)
    assert len(findings) == 0
