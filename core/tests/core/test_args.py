import re
from collections import OrderedDict

from bge.types import KX_GameObject
from bpy.types import Camera
from pytest import raises

from alleycat.common import AlreadyDisposedError, InvalidTypeError, NotStartedError
from alleycat.core import BaseComponent, arg


def assert_exception(obj, attr: str, expected: Exception) -> None:
    with raises(type(expected), match=re.escape(expected.args[0])):
        assert getattr(obj, attr)


class TestComp(BaseComponent):
    string_value: str = arg("ABC")

    bool_value: bool = arg(True)

    int_value: int = arg(123)

    float_value: float = arg(1.2)

    object_value: KX_GameObject = arg(KX_GameObject)

    data_value: Camera = arg(Camera)

    def assert_exception(self, error: Exception) -> None:
        assert_exception(self, "string_value", error)
        assert_exception(self, "bool_value", error)
        assert_exception(self, "int_value", error)
        assert_exception(self, "float_value", error)
        assert_exception(self, "object_value", error)
        assert_exception(self, "data_value", error)


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

    comp.assert_exception(NotStartedError("The proxy has not been started yet."))
    comp.start(args)

    assert comp.string_value == "DEF"
    assert comp.bool_value is False
    assert comp.int_value == 321
    assert comp.float_value == 1.5
    assert comp.object_value == other
    assert comp.data_value == camera

    comp.dispose()
    comp.assert_exception(AlreadyDisposedError("The proxy instance has been disposed already."))


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

    comp.assert_exception(NotStartedError("The proxy has not been started yet."))
    comp.start(args)

    assert_exception(comp, "string_value", ValueError("Missing required argument 'String Value'."))
    assert_exception(comp, "bool_value", ValueError("Missing required argument 'Bool Value'."))
    assert_exception(comp, "int_value", ValueError("Missing required argument 'Int Value'."))
    assert_exception(comp, "float_value", ValueError("Missing required argument 'Float Value'."))
    assert_exception(comp, "object_value", ValueError("Missing required argument 'Object Value'."))
    assert_exception(comp, "data_value", ValueError("Missing required argument 'Data Value'."))

    comp.dispose()
    comp.assert_exception(AlreadyDisposedError("The proxy instance has been disposed already."))


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

    comp.assert_exception(NotStartedError("The proxy has not been started yet."))
    comp.start(args)

    error = InvalidTypeError

    assert_exception(comp, "string_value", error("Value True is not of expected type 'str' (actual: 'bool')."))
    assert_exception(comp, "bool_value", error("Value 123 is not of expected type 'bool' (actual: 'int')."))
    assert_exception(comp, "int_value", error("Value ABC is not of expected type 'int' (actual: 'str')."))
    assert_exception(comp, "float_value", error("Value {} is not of expected type 'float' (actual: 'dict')."))
    assert_exception(comp, "object_value", error("Value [] is not of expected type 'KX_GameObject' (actual: 'list')."))
    assert_exception(comp, "data_value", error("Value 1.2 is not of expected type 'Camera' (actual: 'float')."))

    comp.dispose()
    comp.assert_exception(AlreadyDisposedError("The proxy instance has been disposed already."))
