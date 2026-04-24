# wolpi-extension-api

Type hints for writing Wolpi Python extensions.

This package provides stubs for:
- `import wolpi`
- `from wolpi.errors import HttpStatusError`
- a minimal `import java` surface for `java.type(...)`
- Wolpi hook signatures and resolver/data-model types
- opaque host-object types such as `VImage`, `ByteBuffer`, `HttpClient`, and `Arena`

The exported type names match the Java types used in Wolpi itself.

The package is for local type checking and editor support. Inside Wolpi/GraalPy, the real `wolpi`
and `java` modules are injected by the runtime.

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

## Typing extension classes

In Python, only `info()` and `cleanup()` are always required. The `WolpiExtension` helper base
class models those required hooks and provides typed defaults for the optional ones.

```py
from typing import Mapping, Sequence

import java
from wolpi import ExtensionInfo, ImageInfo, ImageApiRequest, VImage, WolpiExtension


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
        headers: Mapping[str, Sequence[str]],
        client_ip: str
    ) -> bool:
        return client_ip == '127.0.0.1'
```

The `wolpi` module exports common helper classes, annotation types, and runtime values directly,
so a single `from wolpi import ...` statement works for normal extension code.

Hook names are snake_case in Python, but runtime objects exposed by Wolpi keep their camelCase
member names, for example `request.sizeSpec` and `image_info.nativeSize`.

## Using `java.type`

Use `java.type()` when you need to resolve a Java class for static helpers, factories, enums, or
other host APIs that are not already passed into the hook as values.

For example, image-processing hooks already receive a `VImage` instance as the `image` parameter,
but you can still resolve the `VImage` class itself to call static vips-ffm helpers such as
`VImage.text(...)`.

```py
import java
from wolpi import ImageInfo, ImageApiRequest, VImage, vipsArena


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
    self,
    image: VImage,
    identifier: str,
    image_info: ImageInfo,
    request: ImageApiRequest,
) -> VImage | None:
    if request.sizeSpec != "most-interesting":
        return None
    smallest_dim = min(image_info.nativeSize.width, image_info.nativeSize.height)
    return image.smartcrop(
        smallest_dim, smallest_dim,
        VipsEnumOption("interesting", VipsInteresting.INTERESTING_ATTENTION)
    )
```

The `image` parameter is already a `VImage` host object, so you call instance methods on it
directly. The `java.type()` for `VImage` is only needed here for the static helper on the Java class.
