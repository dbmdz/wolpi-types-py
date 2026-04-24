from __future__ import annotations

from typing import Any

class HttpStatusError(Exception):
    """Exception used by Wolpi extensions to return an HTTP error response.

    If Wolpi catches this exception, it returns the given status code and
    message to the client. When `details` is provided, that object becomes the
    response body instead of the default message wrapper.
    """

    message: str
    """Error message associated with the exception."""

    status: int
    """HTTP status code associated with the exception."""

    details: dict[str, Any] | None
    """Optional JSON response body to return instead of the default message body."""

    def __init__(
        self, message: str, status: int, details: dict[str, Any] | None = None
    ) -> None:
        """Create a new structured HTTP error."""
        ...
