"""Local stand-in for Wolpi's injected ``wolpi.errors`` module.

We keep a tiny concrete implementation here so ``from wolpi.errors import
HttpStatusError`` works during local development, tests, and type-checking
outside Wolpi/GraalPy. Inside Wolpi itself, the runtime injects a module with
the same public shape.
"""

from __future__ import annotations

from typing import Any


class HttpStatusError(Exception):
    """Exception used by Wolpi extensions to return a structured HTTP error response."""

    message: str
    status: int
    details: dict[str, Any] | None

    def __init__(
        self, message: str, status: int, details: dict[str, Any] | None = None
    ):
        self.message = message
        self.status = status
        self.details = details
        super().__init__(message)
