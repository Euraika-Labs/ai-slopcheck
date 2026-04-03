.PHONY: install test lint check scan-fixture

install:
	python -m pip install -e .[dev]

test:
	pytest

lint:
	ruff check .

check: test lint

scan-fixture:
	python -m slopcheck scan . --repo-root tests/fixtures/sample_repo --output /tmp/findings.json --fail-on none
	python -m slopcheck summary /tmp/findings.json
