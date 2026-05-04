"""Local development placeholder for GraalPy's injected ``java`` module.

Inside Wolpi/GraalPy, ``import java`` resolves to GraalPy's real interop module.
This local placeholder only exists to give type checkers a minimal surface.
"""

from __future__ import annotations

from typing import Any


def type(class_name: str) -> Any:
    raise RuntimeError(
        "The real 'java' module is only available when running inside GraalPy/Wolpi. "
        f"Tried to resolve Java class: {class_name!r}."
    )
