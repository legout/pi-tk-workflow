"""Tests for demo hello module.

Test suite for the hello-world utility demonstrating IRF workflow.
Covers default parameter, custom names, and edge cases.
"""
from __future__ import annotations

import pytest

from demo.hello import hello

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
    """Test hello with empty string."""
    result = hello("")
    assert result == "Hello, !"
