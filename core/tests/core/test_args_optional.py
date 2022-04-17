from collections import OrderedDict
from typing import Optional

from bge.types import KX_GameObject
from bpy.types import Camera

from alleycat.core import BaseComponent, arg, bootstrap


def setup():
    bootstrap._initialised = True


def teardown():
    bootstrap._initialised = False


class TestComp(BaseComponent):
    string_value: Optional[str] = arg("ABC")

    bool_value: Optional[bool] = arg(True)

    int_value: Optional[int] = arg(123)

    float_value: Optional[float] = arg(1.2)

    object_value: Optional[KX_GameObject] = arg(KX_GameObject)

    data_value: Optional[Camera] = arg(Camera)

    def assert_is_none(self):
        assert self.string_value is None
        assert self.bool_value is None
        assert self.int_value is None
        assert self.float_value is None
        assert self.object_value is None
        assert self.data_value is None


def test_args():
    assert set(TestComp.args.items()) == {
        ("String Value", "ABC"),
        ("Bool Value", True),
        ("Int Value", 123),
        ("Float Value", 1.2),
        ("Object Value", KX_GameObject),
        ("Data Value", Camera)
    }


def test_success():
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

    comp.assert_is_none()
    comp.start(args)

    assert comp.string_value == "DEF"
    assert comp.bool_value is False
    assert comp.int_value == 321
    assert comp.float_value == 1.5
    assert comp.object_value == other
    assert comp.data_value == camera

    comp.dispose()
    comp.assert_is_none()


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

    comp.assert_is_none()
    comp.start(args)

    comp.assert_is_none()

    comp.dispose()
    comp.assert_is_none()


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

    comp.assert_is_none()
    comp.start(args)

    comp.assert_is_none()

    comp.dispose()
    comp.assert_is_none()
