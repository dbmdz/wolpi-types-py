"""Type hints for the Wolpi Python extension API.

These stubs model the objects injected into GraalPy by Wolpi and the data
shapes accepted or returned by extension hooks.
"""

from __future__ import annotations

from . import errors as errors

from abc import ABC, abstractmethod
import datetime as datetime
from collections.abc import Callable, Iterable, Mapping, Sequence
from typing import Any, Literal, Mapping, NotRequired, Protocol, TypedDict, TypeAlias, TypeVar

HttpStatusError = errors.HttpStatusError

ApiVersion: TypeAlias = Literal[1]
"""Wolpi extension API versions currently supported by the runtime."""

JsonPrimitive: TypeAlias = str | int | float | bool | None
"""Scalar JSON value accepted by Wolpi APIs."""

JsonValue: TypeAlias = JsonPrimitive | "JsonObject" | list["JsonValue"]
"""Recursive JSON value used for `info.json` augmentation and error details."""

JsonObject: TypeAlias = dict[str, JsonValue]
"""JSON object mapping string keys to JSON values."""

ImmutableJsonValue: TypeAlias = JsonPrimitive | "ImmutableJsonObject" | Sequence["ImmutableJsonValue"]
"""Immutable JSON input value."""

ImmutableJsonObject: TypeAlias = Mapping[str, ImmutableJsonValue]
"""Immutable JSON input object."""

HttpHeaders: TypeAlias = Mapping[str, Sequence[str]]
"""HTTP headers."""

ExtensionHooks: TypeAlias = Literal[
    "pre_process_image",
    "pre_crop",
    "pre_scale",
    "pre_rotate",
    "pre_quality",
    "pre_format",
]
"""Names of image-processing hooks that can be marked as skippable."""

IIIFQuality: TypeAlias = Literal["color", "gray", "bitonal"]
"""Supported IIIF quality values."""

_T = TypeVar("_T")

class JavaHostObject(Protocol):
    """Marker protocol for Java host objects exposed to GraalPy.

    Refer to the JavaDoc for the corresponding concrete type to see the
    available methods and behavior.
    """

    def __getattr__(self, name: str) -> Any: ...

class VImage(JavaHostObject, Protocol):
    """Opaque host object for libvips images.

    See the `VImage` JavaDoc:
    https://vipsffm.photofox.app/app.photofox.vipsffm/app/photofox/vipsffm/VImage.html
    """

class Arena(JavaHostObject, Protocol):
    """Java `java.lang.foreign.Arena` host object passed to vips-ffm APIs.

    See the Java `Arena` JavaDoc:
    https://docs.oracle.com/en/java/javase/22/docs/api/java.base/java/lang/foreign/Arena.html

    Treat this as an opaque handle that is only forwarded to vips-ffm. Do not
    store a reference to it or try to manipulate it directly.
    """

class ByteBuffer(JavaHostObject, Protocol):
    """Java `java.nio.ByteBuffer` host object.

    See the JavaDoc:
    https://docs.oracle.com/javase/8/docs/api/java/nio/ByteBuffer.html
    """

class HttpClient(JavaHostObject, Protocol):
    """Java `java.net.http.HttpClient` host object.

    See the JavaDoc:
    https://docs.oracle.com/en/java/javase/11/docs/api/java.net.http/java/net/http/HttpClient.html
    """

class IIIFVersion(JavaHostObject, Protocol):
    """IIIF Image API version exposed guest-side as a Java host enum object."""

    def name(self) -> str:
        """Return the Java enum constant name, for example `V2` or `V3`."""
        ...

    def value(self) -> int:
        """Return the numeric IIIF Image API version, for example `2` or `3`."""
        ...

IIIFVersionInput = IIIFVersion | Literal["v2", "v3"]
"""IIIF version accepted by parser helpers, either as a host enum or a short string."""

class ImageSize(Protocol):
    """Width and height in pixels."""

    width: int
    height: int

class ImageSizeDict(TypedDict):
    """Dictionary form used in nested resolver return metadata."""

    width: int
    height: int

class TileSize(Protocol):
    """Tile size information directly encoded in the image."""

    width: int
    height: int | None
    scaleFactors: Sequence[int]

class TileSizeDict(TypedDict):
    """Dictionary form used in nested resolver return metadata."""

    width: int
    scaleFactors: list[int]
    height: NotRequired[int | None]

class ImageInfo(Protocol):
    """Image metadata exposed to Python as an attribute object.

    This metadata can avoid loading the image just to populate `info.json`.
    """

    format: str | None
    nativeSize: ImageSize
    sizes: Sequence[ImageSize]
    tileSizes: Sequence[TileSize]

class ImageInfoDict(TypedDict):
    """Dictionary form used in resolver return dicts."""

    format: NotRequired[str | None]
    nativeSize: ImageSizeDict
    sizes: list[ImageSizeDict]
    tileSizes: list[TileSizeDict]

class CacheInfo(Protocol):
    """Optional HTTP cache metadata exposed to Python as an attribute object."""

    eTag: str | None

    #: If using a string, must be formatted according to ISO-8601
    lastModified: datetime.datetime | str | None

class CacheInfoDict(TypedDict, total=False):
    """Dictionary form used in resolver return dicts."""

    eTag: str

    #: If using a string, must be formatted according to ISO-8601
    lastModified: datetime.datetime | str

class CropRectangle(Protocol):
    """Rectangular crop region in non-fractional pixels."""

    x: int
    y: int
    width: int
    height: int

class Rotation(Protocol):
    """Parsed rotation information."""

    degrees: float
    mirror: bool

class ImageApiRequest(Protocol):
    """IIIF Image API request object exposed to Python as an attribute object.

    Note that `version` is exposed to Python as a Java host enum object.
    """

    identifier: str
    version: IIIFVersion
    cropSpec: str
    sizeSpec: str
    rotationSpec: str
    qualitySpec: str
    formatSpec: str


class ExtensionInfo(TypedDict):
    """Information returned by the `info()` hook."""

    apiVersion: ApiVersion
    name: str
    description: str

class _ResolvedMeta(TypedDict, total=False):
    """Shared metadata fields accepted by resolver return objects."""

    imageInfo: ImageInfoDict
    cacheInfo: CacheInfoDict

class FilesystemResolvedImage(_ResolvedMeta):
    """An image file in a file system accessible to Wolpi."""

    path: str

class BinaryResolvedImage(_ResolvedMeta):
    """A raw encoded image blob that will be decoded by libvips."""

    rawData: bytes | bytearray

class HttpResolvedImage(_ResolvedMeta):
    """An image accessible via HTTP(S), optionally with custom request headers."""

    url: str
    headers: NotRequired[Mapping[str, str]]

class SourceNotModified(TypedDict):
    """Marker result indicating that the source has not changed since the client's cached copy."""

    notModified: Literal[True]
    imageInfo: NotRequired[ImageInfoDict]
    cacheInfo: NotRequired[CacheInfoDict]

class CustomSourceResolvedImage(Protocol):
    """Custom data source returned from `resolve()`.

    This can be more efficient for large images from backends such as databases
    or object-storage systems. Metadata may be attached as additional attributes.
    """

    def onRead(self, length: int) -> bytes | bytearray:
        """Read up to `length` bytes from the current position.

        The returned buffer is copied, so it is safe to reuse internal buffers
        for subsequent calls.
        """
        ...

    def onSeek(self, offset: int, whence: int) -> int:
        """Seek to a new position.

        `whence` is:
        - `0`: beginning of file
        - `1`: current position
        - `2`: end of file
        """
        ...

    def __getattr__(self, name: str) -> Any: ...

ResolvedImage: TypeAlias = (
    FilesystemResolvedImage
    | BinaryResolvedImage
    | HttpResolvedImage
    | CustomSourceResolvedImage
    | SourceNotModified
)
"""Value returned from the `resolve()` hook."""


class EncodedImage(TypedDict):
    """Encoded image data returned by the `pre_format()` hook."""

    data: bytes | bytearray | ByteBuffer
    contentType: str
    extraHeaders: NotRequired[HttpHeaders]

class CounterMetric(Protocol):
    """Counter metric that should only increase."""

    def increment(self, value: float | None = None) -> None:
        """Increment the counter by `1` or by the given positive amount."""
        ...

class GaugeMetric(Protocol):
    """Gauge metric for values that can go up and down."""

    def set(self, value: float) -> None:
        """Set the gauge to the given value."""
        ...

class RunningTimer(Protocol):
    """Running timer handle returned from `TimerMetric.start()`."""

    def stop(self) -> None:
        """Stop the timer and record the duration."""
        ...

class TimerMetric(Protocol):
    """Timer metric for measuring durations."""

    def record(self, fn: Callable[[], _T]) -> _T:
        """Run a callback and record how long it took to complete."""
        ...

    def start(self) -> RunningTimer:
        """Start a timer that can be stopped later."""
        ...

class ExtensionMetrics(Protocol):
    """Entry point for creating custom metrics in extensions.

    Metrics are registered in Wolpi's meter registry. Duplicate registrations
    with the same name and labels are deduplicated by the underlying metrics
    library.
    """

    def counter(
        self,
        name: str,
        unit: str | None = None,
        description: str | None = None,
        labels: Mapping[str, str] | None = None,
    ) -> CounterMetric:
        """Create or retrieve a counter metric."""
        ...

    def gauge(
        self,
        name: str,
        unit: str | None = None,
        description: str | None = None,
        labels: Mapping[str, str] | None = None,
    ) -> GaugeMetric:
        """Create or retrieve a gauge metric."""
        ...

    def timer(
        self,
        name: str,
        description: str | None = None,
        labels: Mapping[str, str] | None = None,
    ) -> TimerMetric:
        """Create or retrieve a timer metric."""
        ...

class ExtensionLogger(Protocol):
    """Logger exposed to extensions.

    Loggers are prefixed with `wolpi.extension.<extension-name>` and support
    additional structured key-value details.
    """

    def getLogger(self, name: str) -> "ExtensionLogger":
        """Create a child logger with `name` appended to the current logger name."""
        ...

    def debug(self, message: str, keyVals: Mapping[str, Any] | None = None) -> None:
        """Log a message at DEBUG level."""
        ...

    def info(self, message: str, keyVals: Mapping[str, Any] | None = None) -> None:
        """Log a message at INFO level."""
        ...

    def warn(self, message: str, keyVals: Mapping[str, Any] | None = None) -> None:
        """Log a message at WARN level."""
        ...

    def error(self, message: str, keyVals: Mapping[str, Any] | None = None) -> None:
        """Log a message at ERROR level."""
        ...

class ImageRequestParserProxy(Protocol):
    """Parser for IIIF Image API requests.

    Use this when implementing custom behavior that still wants to rely on
    Wolpi's parsing and validation of official IIIF request syntax.
    """

    def parseRegion(self, spec: str, source_size: ImageSize) -> CropRectangle:
        """Parse a region specification.

        Supports `full`, `square`, `x,y,w,h`, and `pct:x,y,w,h`.
        """
        ...

    def parseSize(
        self, version: IIIFVersionInput, spec: str, source_size: ImageSize
    ) -> ImageSize:
        """Parse a size specification for IIIF v2 or v3.

        Supports official IIIF size syntax such as `full`, `max`, `^max`,
        `w,`, `,h`, `pct:n`, `w,h`, and `!w,h` variants where applicable.
        """
        ...

    def parseRotation(self, spec: str) -> Rotation:
        """Parse a rotation specification.

        Supported forms are `n` and `!n`, where `n` is a clockwise angle in
        degrees between `0` and `360`.
        """
        ...

    def parseQuality(self, spec: str) -> IIIFQuality:
        """Parse and validate a quality specification."""
        ...

    def toCanonicalForm(
        self, request: ImageApiRequest, source_size: ImageSize
    ) -> ImageApiRequest | None:
        """Convert a request into its canonical form, or return `None` if unavailable."""
        ...

class ExtensionGuestContext(Protocol):
    """Runtime context available to Python extensions via `import wolpi`."""

    config: Mapping[str, Any] | None
    wolpiVersion: str
    extensionVersion: str
    logger: ExtensionLogger
    metrics: ExtensionMetrics
    vipsArena: Arena
    imageRequestParser: ImageRequestParserProxy
    httpClient: HttpClient
    baseUri: str | None

InfoHook: TypeAlias = Callable[[], ExtensionInfo]
"""Hook returning static extension metadata."""

SetupHook: TypeAlias = Callable[[], None]
"""Hook called when the extension is initialized."""

DestroyHook: TypeAlias = Callable[[], None]
"""Hook called when the extension is destroyed."""

CleanupHook: TypeAlias = Callable[[], None]
"""Hook called after a request to clean up request-scoped extension state."""

SkippableHooksHook: TypeAlias = Callable[
    [ImageApiRequest], Iterable[ExtensionHooks] | None
]
"""Hook returning the set of image-processing hooks that can be skipped for a request."""

AuthorizeHook: TypeAlias = Callable[[str, HttpHeaders, str], bool]
"""Authorization hook returning `True` to allow access and `False` to deny it."""

ResolveHook: TypeAlias = Callable[[str, str | None, str | None], ResolvedImage | None]
"""Resolve an image identifier to an image source.

The hook receives client caching headers, if present, and may also return
`imageInfo` and `cacheInfo` metadata to avoid extra probing by Wolpi.
"""

AugmentInfoJsonHook: TypeAlias = Callable[
    [str, Mapping[str, JsonValue], int], JsonObject | None
]
"""Augment the generated `info.json` response.

Return a new object rather than mutating the input object in place.
"""

ImageProcessingHook: TypeAlias = Callable[
    [VImage, str, ImageInfo, ImageApiRequest], VImage | None
]
"""Hook signature shared by image-processing hooks such as `pre_process_image`,
`pre_scale`, `pre_crop`, `pre_rotate`, and `pre_quality`.

For `pre_process_image` specifically, the returned image must keep the same
dimensions as the input image. Wolpi ignores results with different width or
height.
"""

PreFormatHook: TypeAlias = Callable[
    [VImage, str, ImageInfo, ImageApiRequest], EncodedImage | None
]
"""Hook called before the image is encoded to the requested output format.

Return an `EncodedImage` to take over encoding or `None` to let Wolpi
continue with its default encoding.
"""

class WolpiExtensionDict(TypedDict):
    """Dictionary form of a Wolpi extension.

    All hooks except for `info` and `cleanup` are optional.
    """

    info: InfoHook
    cleanup: CleanupHook
    setup: NotRequired[SetupHook]
    destroy: NotRequired[DestroyHook]
    skippable_hooks: NotRequired[SkippableHooksHook]
    authorize: NotRequired[AuthorizeHook]
    resolve: NotRequired[ResolveHook]
    augment_info_json: NotRequired[AugmentInfoJsonHook]
    pre_process_image: NotRequired[ImageProcessingHook]
    pre_scale: NotRequired[ImageProcessingHook]
    pre_crop: NotRequired[ImageProcessingHook]
    pre_rotate: NotRequired[ImageProcessingHook]
    pre_quality: NotRequired[ImageProcessingHook]
    pre_format: NotRequired[PreFormatHook]

class WolpiExtension(ABC):
    """Typing convenience base class for class-based Wolpi extensions.

    `info()` and `cleanup()` stay abstract because every extension must provide
    them. The remaining hook methods are modeled with default implementations so
    extension authors can subclass this type and only override the hooks they
    actually implement.
    """

    @abstractmethod
    def info(self) -> ExtensionInfo:
        """Return static metadata describing the extension."""
        ...

    @abstractmethod
    def cleanup(self) -> None:
        """Reset any request-scoped state accumulated during request handling."""
        ...

    def setup(self) -> None:
        """Run initialization logic before the extension instance handles requests."""
        ...

    def destroy(self) -> None:
        """Clean up resources previously allocated in `setup()`."""
        ...

    def skippable_hooks(
        self, request: ImageApiRequest
    ) -> Iterable[ExtensionHooks] | None:
        """Return image-processing hooks that can be skipped for `request`."""
        ...

    def authorize(self, identifier: str, headers: HttpHeaders, client_ip: str) -> bool:
        """Authorize access to `identifier` for the given request context."""
        ...

    def resolve(
        self,
        identifier: str,
        client_etag: str | None,
        client_last_modified: str | None,
    ) -> ResolvedImage | None:
        """Resolve an image identifier to an image source or return `None`."""
        ...

    def augment_info_json(
        self,
        identifier: str,
        current_info_json: ImmutableJsonObject,
        iiif_version: int,
    ) -> JsonObject | None:
        """Return a **modified** `info.json` object or `None` to keep the current one.

        Implementers must not modify the input `current_info_json` dict in place and instead
        return a new dict.
        """
        ...

    def pre_process_image(
        self,
        image: VImage,
        identifier: str,
        image_info: ImageInfo,
        request: ImageApiRequest,
    ) -> VImage | None:
        """Run before the standard processing pipeline.

        The returned image must keep the same dimensions as the input image.
        Wolpi ignores results with different width or height.
        """
        ...

    def pre_scale(
        self,
        image: VImage,
        identifier: str,
        image_info: ImageInfo,
        request: ImageApiRequest,
    ) -> VImage | None:
        """Override or augment the image scaling step."""
        ...

    def pre_crop(
        self,
        image: VImage,
        identifier: str,
        image_info: ImageInfo,
        request: ImageApiRequest,
    ) -> VImage | None:
        """Override or augment the image crop step."""
        ...

    def pre_rotate(
        self,
        image: VImage,
        identifier: str,
        image_info: ImageInfo,
        request: ImageApiRequest,
    ) -> VImage | None:
        """Override or augment the image rotation step."""
        ...

    def pre_quality(
        self,
        image: VImage,
        identifier: str,
        image_info: ImageInfo,
        request: ImageApiRequest,
    ) -> VImage | None:
        """Override or augment the image quality step."""
        ...

    def pre_format(
        self,
        image: VImage,
        identifier: str,
        image_info: ImageInfo,
        request: ImageApiRequest,
    ) -> EncodedImage | None:
        """Run before the image is encoded to the requested output format."""
        ...

# Runtime-injected Wolpi context is exposed directly via `import wolpi` in GraalPy.
config: Mapping[str, Any] | None
"""Immutable extension configuration object, if one was provided."""

wolpiVersion: str
"""Wolpi version currently running."""

extensionVersion: str
"""Version of the currently running extension."""

logger: ExtensionLogger
"""Logger instance for extension log output."""

metrics: ExtensionMetrics
"""Metrics entry point for custom counters, gauges, and timers."""

vipsArena: Arena
"""Opaque arena handle for vips-related host APIs."""

imageRequestParser: ImageRequestParserProxy
"""Helper for parsing official IIIF request syntax."""

httpClient: HttpClient
"""Shared Java HTTP client instance."""

baseUri: str | None
"""Configured base URI for this Wolpi instance, if available."""
