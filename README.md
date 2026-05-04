# wolpi-extension-api

Type hints for writing Wolpi Python extensions.

Install this package to get type checking and editor IntelliSense for Wolpi APIs.
The types cover all the values accessible via the `wolpi`, `wolpi.errors`, and
`java` modules, as well as all types passed into or returned from the extension
hooks.
Inside Wolpi/GraalPy, the real `wolpi` and `java` modules are injected by the
runtime; this package is for local type checking and editor support.

## Install

```sh
python -m pip install wolpi-extension-api
```

Or add it to your development environment with your preferred tool, for example:

```sh
uv add --dev wolpi-extension-api
```

Once the package is installed in the environment used by Pyright, Pylance, mypy, or another type
checker, no extra configuration is required.

## Examples

### Class-based Extensions

The `WolpiExtension` base class models the required hooks and provides typed defaults for the optional ones.

```py
from wolpi import ExtensionInfo, WolpiExtension, HttpHeaders


class Extension(WolpiExtension):
    def info(self) -> ExtensionInfo:
        return {
            "apiVersion": 1,
            "name": "Example",
            "description": "Typed hooks",
        }

    def cleanup(self) -> None:
        pass

    def authorize(
        self,
        identifier: str,
        headers: HttpHeaders,
        client_ip: str,
    ) -> bool:
        return client_ip == "127.0.0.1"
```

### Dict-based Extensions
```py
from wolpi import ExtensionInfo, WolpiExtensionDict, HttpHeaders


def info() -> ExtensionInfo:
    return {
        "apiVersion": 1,
        "name": "Example",
        "description": "Dict-based extension",
    }


def cleanup() -> None:
    pass


def authorize(
    identifier: str,
    headers: HttpHeaders,
    client_ip: str,
) -> bool:
    return client_ip == "127.0.0.1"


def wolpi_extension() -> WolpiExtensionDict:
    return {
        "info": info,
        "cleanup": cleanup,
        "authorize": authorize,
    }
```

### Using `java.type`

Use `java.type()` when you need to resolve a Java class for static helpers, factories, enums, or
other host APIs that are not already passed into the hook as values.

For example, image-processing hooks already receive a `VImage` instance as the `image` parameter,
but you can still resolve the `VImage` class itself to call static vips-ffm helpers such as
`VImage.text(...)`.

```py
import java
from wolpi import (
    ImageApiRequest,
    ImageInfo,
    ExtensionInfo,
    VImage,
    WolpiExtensionDict,
    vipsArena,
)


VImageClass = java.type("app.photofox.vipsffm.VImage")
VipsInteresting = java.type("app.photofox.vipsffm.enums.VipsInteresting")
VipsEnumOption = java.type("app.photofox.vipsffm.VipsOption.Enum")


# Inserts the image identifier as a text watermark in the upper right corner
def pre_process_image(
    image: VImage,
    identifier: str,
    image_info: ImageInfo,
    request: ImageApiRequest,
) -> VImage | None:
    watermark = VImageClass.text(vipsArena, identifier)
    return image.insert(watermark, 16, 16)


# Adds a custom `most-interesting` cropping parameter syntax that uses vips'
# smartcrop feature to select the most interesting square region of the image
def pre_crop(
    image: VImage,
    identifier: str,
    image_info: ImageInfo,
    request: ImageApiRequest,
) -> VImage | None:
    if request.cropSpec != "most-interesting":
        return None
    smallest_dim = min(image_info.nativeSize.width, image_info.nativeSize.height)
    return image.smartcrop(
        smallest_dim,
        smallest_dim,
        VipsEnumOption("interesting", VipsInteresting.INTERESTING_ATTENTION),
    )


def info() -> ExtensionInfo:
    return {
        "apiVersion": 1,
        "name": "smartcrop-watermark",
        "description": "Example extension",
    }


def wolpi_extension() -> WolpiExtensionDict:
    return {
        "info": info,
        "cleanup": lambda: None,
        "pre_process_image": pre_process_image,
        "pre_crop": pre_crop,
    }
```

The `image` parameter is already a `VImage` host object, so you call instance methods on it
directly. The `java.type()` for `VImage` is only needed here for the static helper on the Java class.
