from __future__ import annotations
import inspect
from pathlib import Path
from typing import Optional, Sequence

import numpy as np
import rx
from alleycat.reactive import RV, functions as rv
from cairocffi import FontOptions, ImageSurface, Surface
from returns.maybe import Maybe, Nothing, Some

from alleycat.ui import Context, Dimension, FakeMouseInput, FontRegistry, Image, ImageRegistry, Input, \
    LookAndFeel, Toolkit, ToyFontRegistry, WindowManager
from alleycat.ui.context import ContextBuilder, ErrorHandler


class FixtureContext(Context):
    window_size: RV[Dimension] = rv.new_view()

    def __init__(self,
                 size: Dimension,
                 toolkit: FixtureToolkit,
                 look_and_feel: Optional[LookAndFeel] = None,
                 font_options: Optional[FontOptions] = None,
                 window_manager: Optional[WindowManager] = None,
                 error_handler: Optional[ErrorHandler] = None) -> None:
        if size is None:
            raise ValueError("Argument 'size' is required.")

        # noinspection PyTypeChecker
        self.window_size = rx.of(size)

        super().__init__(toolkit, look_and_feel, font_options, window_manager, error_handler)


class FixtureToolkit(Toolkit[FixtureContext]):

    def __init__(self, resource_path: Path = Path("../alleycat/ui"),
                 error_handler: Optional[ErrorHandler] = None) -> None:
        super().__init__(resource_path, error_handler)

        self._font_registry = ToyFontRegistry(self.error_handler)
        self._image_registry = FixtureImageRegistry(self.error_handler)

    @property
    def fonts(self) -> FontRegistry:
        return self._font_registry

    @property
    def images(self) -> ImageRegistry:
        return self._image_registry

    def create_inputs(self, context: Context) -> Sequence[Input]:
        return FakeMouseInput(context),


class UI(ContextBuilder[FixtureContext]):

    def __init__(self, toolkit: Optional[FixtureToolkit] = None) -> None:
        super().__init__(toolkit if toolkit is not None else FixtureToolkit())

        self._size: Optional[Dimension] = None

    def of_size(self, size: Dimension = Dimension(100, 100)) -> UI:
        if size is None:
            raise ValueError("Argument 'size' is required.")

        self._size = size

        return self

    def create_context(self) -> FixtureContext:
        size = self._size if self._size is not None else Dimension(100, 100)

        return FixtureContext(size, **self.args)


class TestImage(Image):
    def __init__(self, source: ImageSurface) -> None:
        if source is None:
            raise ValueError("Argument 'source' is required.")

        super().__init__()

        self._source = source
        self._size = Dimension(source.get_width(), source.get_height())

    @property
    def surface(self) -> Surface:
        return self._source

    @property
    def size(self) -> Dimension:
        return self._size


class FixtureImageRegistry(ImageRegistry[TestImage]):

    def __init__(self, error_handler: ErrorHandler) -> None:
        super().__init__(error_handler)

    def create(self, key: str) -> Maybe[TestImage]:
        if key is None:
            raise ValueError("Argument 'key' is required.")

        if not Path(key).exists():
            return Nothing

        source = ImageSurface.create_from_png(key)

        return Some(TestImage(source))


def assert_image(name: str, context: Context, tolerance: float = 0):
    if name is None:
        raise ValueError("Argument 'name' is required.")

    if context is None:
        raise ValueError("Argument 'context' is required.")

    if tolerance < 0:
        raise ValueError("Argument 'tolerance' should be zero or a positive number.")

    surface = context.surface

    basedir = Path(__file__).parent

    frame = inspect.stack()[1]
    parent = inspect.getmodule(frame[0]).__name__.split(".")[-1]

    fixture_dir = basedir.joinpath(Path("fixtures", parent))
    output_dir = basedir.joinpath(Path("output", parent))

    fixture_path = fixture_dir / (name + ".png")

    if not fixture_path.exists():
        fixture_path.parent.mkdir(parents=True, exist_ok=True)

        surface.write_to_png(str(fixture_path))

    fixture = ImageSurface.create_from_png(str(fixture_path))

    expected = np.array(fixture.get_data())
    actual = np.array(surface.get_data())

    assert len(actual) == len(expected)

    mse = np.sum((expected - actual) ** 2) / len(expected)

    try:
        assert mse <= tolerance

        fixture.finish()
    except AssertionError as e:
        output_path = output_dir / (name + ".png")
        output_path.parent.mkdir(parents=True, exist_ok=True)

        surface.write_to_png(str(output_path))

        fixture.finish()

        raise e
