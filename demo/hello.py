from __future__ import annotations

"""Hello-world utility for demo purposes."""


def hello(name: str = "World") -> str:
    """Return a greeting message.

    Args:
        name: The name to greet. Defaults to "World".

    Returns:
        str: A greeting string.
    """
    return f"Hello, {name}!"


if __name__ == "__main__":
    print(hello())
