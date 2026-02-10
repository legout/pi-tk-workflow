"""Hello-world utility for demo purposes.

This module provides a simple greeting function for demonstrating
the IRF (Implement-Review-Fix) workflow. Ticket: abc-123

The module exposes a single function `hello()` that returns a greeting
string. It can be used as a library import or run as a CLI script.

Examples:
    >>> from demo.hello import hello
    >>> hello()
    'Hello, World!'
    >>> hello("Alice")
    'Hello, Alice!'

CLI Usage:
    $ python -m demo
    Hello, World!
    $ python -m demo Alice
    Hello, Alice!
"""

from __future__ import annotations


def hello(name: str = "World") -> str:
    """Return a greeting message.

    Args:
        name: The name to greet. Defaults to "World".
            Leading and trailing whitespace is stripped.
            Empty strings and whitespace-only strings return
            the full greeting "Hello, World!".

    Returns:
        str: A greeting string in the format "Hello, {name}!".

    Raises:
        TypeError: If name is not a string type.
    """
    if name is None:
        raise TypeError("name must be a string, not None")
    if not isinstance(name, str):
        raise TypeError(f"name must be a string, got {type(name).__name__}")
    cleaned_name = name.strip()
    if not cleaned_name:
        return "Hello, World!"
    return f"Hello, {cleaned_name}!"


__all__ = ["hello"]
