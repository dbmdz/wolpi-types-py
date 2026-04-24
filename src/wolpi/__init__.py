"""Local development placeholder for the injected ``wolpi`` runtime module.

Inside Wolpi/GraalPy, ``import wolpi`` resolves to an injected module that
exposes real runtime values and lazily resolves type-like names on demand.
This package mirrors that public surface for local type checking and editor
support.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from . import errors as errors

HttpStatusError = errors.HttpStatusError

_placeholder_types: dict[str, type[Any]] = {}


def _make_placeholder_type(name: str) -> type[Any]:
    placeholder = _placeholder_types.get(name)
    if placeholder is None:
        placeholder = type(name, (), {})
        placeholder.__module__ = __name__
        _placeholder_types[name] = placeholder
    return placeholder


class WolpiExtension(ABC):
    """Base class for Wolpi extension objects.

    Wolpi's injected Python ``wolpi`` module exposes a matching helper so
    extensions can subclass it both locally and at runtime.
    """

    @abstractmethod
    def info(self) -> Any:
        raise NotImplementedError()

    @abstractmethod
    def cleanup(self) -> None:
        raise NotImplementedError()

    def setup(self) -> None:
        return None

    def destroy(self) -> None:
        return None

    def skippable_hooks(self, request: Any) -> Any:
        return None

    def authorize(self, identifier: str, headers: Any, client_ip: str) -> bool:
        return True

    def resolve(
        self, identifier: str, client_etag: str | None, client_last_modified: str | None
    ) -> Any:
        return None

    def augment_info_json(
        self, identifier: str, current_info_json: Any, iiif_version: int
    ) -> Any:
        return None

    def pre_process_image(
        self, image: Any, identifier: str, image_info: Any, request: Any
    ) -> Any:
        return None

    def pre_scale(
        self, image: Any, identifier: str, image_info: Any, request: Any
    ) -> Any:
        return None

    def pre_crop(
        self, image: Any, identifier: str, image_info: Any, request: Any
    ) -> Any:
        return None

    def pre_rotate(
        self, image: Any, identifier: str, image_info: Any, request: Any
    ) -> Any:
        return None

    def pre_quality(
        self, image: Any, identifier: str, image_info: Any, request: Any
    ) -> Any:
        return None

    def pre_format(
        self, image: Any, identifier: str, image_info: Any, request: Any
    ) -> Any:
        return None


class _UnavailableRuntimeValue:
    def __init__(self, name: str) -> None:
        self._name = name

    def __getattr__(self, name: str) -> Any:
        raise RuntimeError(
            "The real 'wolpi' object is only available when running inside Wolpi/GraalPy. "
            f"Tried to access attribute: {self._name}.{name!r}."
        )

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        raise RuntimeError(
            "The real 'wolpi' object is only available when running inside Wolpi/GraalPy. "
            f"Tried to call runtime value: {self._name!r}."
        )

    def __repr__(self) -> str:
        return f"<unavailable Wolpi runtime value {self._name}>"


config: Any | None = None
wolpiVersion = ""
extensionVersion = ""
logger = _UnavailableRuntimeValue("logger")
metrics = _UnavailableRuntimeValue("metrics")
vipsArena = _UnavailableRuntimeValue("vipsArena")
imageRequestParser = _UnavailableRuntimeValue("imageRequestParser")
httpClient = _UnavailableRuntimeValue("httpClient")
baseUri = None

__all__ = [
    "WolpiExtension",
    "HttpStatusError",
    "config",
    "wolpiVersion",
    "extensionVersion",
    "logger",
    "metrics",
    "vipsArena",
    "imageRequestParser",
    "httpClient",
    "baseUri",
    "errors",
]


def __getattr__(name: str) -> Any:
    if name == "HttpStatusError":
        return errors.HttpStatusError
    if name and name[0].isupper():
        return _make_placeholder_type(name)
    raise RuntimeError(
        "The real 'wolpi' object is only available when running inside Wolpi/GraalPy. "
        f"Tried to access unknown runtime attribute: {name!r}."
    )
