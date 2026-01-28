"""Test code examples in documentation."""

from __future__ import annotations

import pytest
from pytest_examples import CodeExample, EvalExample, find_examples


@pytest.mark.parametrize("example", find_examples("docs"), ids=str)
def test_docs_examples(example: CodeExample, eval_example: EvalExample) -> None:
    """Lint code examples in documentation files."""
    if example.prefix_settings().get("test") == "skip":
        pytest.skip("Marked as skip")

    eval_example.lint(example)
