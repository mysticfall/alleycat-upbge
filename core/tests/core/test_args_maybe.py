from collections import OrderedDict

from bge.types import KX_GameObject
from bpy.types import Camera
from returns.maybe import Maybe, Nothing, Some

from alleycat.core import BaseComponent, arg


class TestComp(BaseComponent):
    string_value: Maybe[str] = arg("ABC")

    bool_value: Maybe[bool] = arg(True)

    int_value: Maybe[int] = arg(123)

    float_value: Maybe[float] = arg(1.2)

    object_value: Maybe[KX_GameObject] = arg(KX_GameObject)

    data_value: Maybe[Camera] = arg(Camera)

    def assert_nothing(self) -> None:
        assert self.string_value == Nothing
        assert self.bool_value == Nothing
        assert self.int_value == Nothing
        assert self.float_value == Nothing
        assert self.object_value == Nothing
        assert self.data_value == Nothing


def test_args():
    assert set(TestComp.args.items()) == {
        ("String Value", "ABC"),
        ("Bool Value", True),
        ("Int Value", 123),
        ("Float Value", 1.2),
        ("Object Value", KX_GameObject),
        ("Data Value", Camera)
    }


def test_valid():
    other = KX_GameObject()
    camera = Camera()

    args = OrderedDict((
        ("String Value", "DEF"),
        ("Bool Value", False),
        ("Int Value", 321),
        ("Float Value", 1.5),
        ("Object Value", other),
        ("Data Value", camera),
    ))

    comp = TestComp()

    comp.assert_nothing()
    comp.start(args)

    assert comp.string_value == Some("DEF")
    assert comp.bool_value == Some(False)
    assert comp.int_value == Some(321)
    assert comp.float_value == Some(1.5)
    assert comp.object_value == Some(other)
    assert comp.data_value == Some(camera)

    comp.dispose()
    comp.assert_nothing()


def test_empty():
    args = OrderedDict((
        ("String Value", None),
        ("Bool Value", None),
        ("Int Value", None),
        ("Float Value", None),
        ("Object Value", None),
        ("Data Value", None),
    ))

    comp = TestComp()

    assert comp.string_value == Nothing
    assert comp.bool_value == Nothing
    assert comp.int_value == Nothing
    assert comp.float_value == Nothing
    assert comp.object_value == Nothing
    assert comp.data_value == Nothing

    comp.start(args)

    assert comp.string_value == Nothing
    assert comp.bool_value == Nothing
    assert comp.int_value == Nothing
    assert comp.float_value == Nothing
    assert comp.object_value == Nothing
    assert comp.data_value == Nothing

    comp.dispose()

    assert comp.string_value == Nothing
    assert comp.bool_value == Nothing
    assert comp.int_value == Nothing
    assert comp.float_value == Nothing
    assert comp.object_value == Nothing
    assert comp.data_value == Nothing


def test_invalid():
    args = OrderedDict((
        ("String Value", True),
        ("Bool Value", 123),
        ("Int Value", "ABC"),
        ("Float Value", dict()),
        ("Object Value", list()),
        ("Data Value", 1.2),
    ))

    comp = TestComp()

    assert comp.string_value == Nothing
    assert comp.bool_value == Nothing
    assert comp.int_value == Nothing
    assert comp.float_value == Nothing
    assert comp.object_value == Nothing
    assert comp.data_value == Nothing

    comp.start(args)

    assert comp.string_value == Nothing
    assert comp.bool_value == Nothing
    assert comp.int_value == Nothing
    assert comp.float_value == Nothing
    assert comp.object_value == Nothing
    assert comp.data_value == Nothing

    comp.dispose()

    assert comp.string_value == Nothing
    assert comp.bool_value == Nothing
    assert comp.int_value == Nothing
    assert comp.float_value == Nothing
    assert comp.object_value == Nothing
    assert comp.data_value == Nothing
