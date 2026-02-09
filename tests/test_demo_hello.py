"""Tests for demo hello module.

Test suite for the hello-world utility demonstrating IRF workflow.
Covers default parameter, custom names, and edge cases (6 tests total).
"""

from __future__ import annotations

import pytest

from demo.hello import hello
from demo.__main__ import main

pytestmark = pytest.mark.unit


def test_hello_default() -> None:
    """Test hello with default name."""
    result = hello()
    assert result == "Hello, World!"


def test_hello_custom_name() -> None:
    """Test hello with custom name."""
    result = hello("Alice")
    assert result == "Hello, Alice!"


def test_hello_empty_string() -> None:
    """Test hello with empty string falls back to World."""
    result = hello("")
    assert result == "Hello, World!"


def test_hello_whitespace_only() -> None:
    """Test hello with whitespace-only strings fall back to World."""
    # Various whitespace characters (spaces, tabs, newlines)
    for whitespace in ["   ", "\t\n\r", "  \t\n  "]:
        result = hello(whitespace)
        assert result == "Hello, World!", f"Failed for whitespace: {repr(whitespace)}"


def test_cli_default(capsys: pytest.CaptureFixture[str]) -> None:
    """Test CLI entry point with no arguments."""
    result = main([])
    assert result == 0
    captured = capsys.readouterr()
    assert "Hello, World!" in captured.out


def test_cli_with_name(capsys: pytest.CaptureFixture[str]) -> None:
    """Test CLI entry point with a name argument."""
    result = main(["Alice"])
    assert result == 0
    captured = capsys.readouterr()
    assert "Hello, Alice!" in captured.out
