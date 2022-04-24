import re
from collections import OrderedDict

from bge.types import KX_GameObject
from bpy.types import Camera
from pytest import raises

from alleycat.common import InvalidTypeError
from alleycat.core import BaseComponent, bootstrap, game_property
from alleycat.lifecycle import RESULT_DISPOSED, RESULT_NOT_STARTED


def assert_exception(obj, attr: str, expected: Exception) -> None:
    with raises(type(expected), match=re.escape(expected.args[0])):
        assert getattr(obj, attr)


def setup():
    bootstrap._initialised = True


def teardown():
    bootstrap._initialised = False


class TestComp(BaseComponent):
    string_value: str = game_property("ABC")

    bool_value: bool = game_property(True)

    int_value: int = game_property(123)

    float_value: float = game_property(1.2)

    object_value: KX_GameObject = game_property(KX_GameObject)

    data_value: Camera = game_property(Camera)

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


def test_inherited_args():
    class ParentComp(TestComp):
        string_value: str = game_property("DEF")

        string_value2: str = game_property("GHI")

    assert set(ParentComp.args.items()) == {
        ("String Value", "DEF"),
        ("String Value2", "GHI"),
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

    comp.assert_exception(RESULT_NOT_STARTED.failure())
    comp.start(args)

    assert comp.string_value == "DEF"
    assert comp.bool_value is False
    assert comp.int_value == 321
    assert comp.float_value == 1.5
    assert comp.object_value == other
    assert comp.data_value == camera

    comp.dispose()
    comp.assert_exception(RESULT_DISPOSED.failure())


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

    comp.assert_exception(RESULT_NOT_STARTED.failure())
    comp.start(args)

    assert_exception(comp, "string_value", ValueError("Missing required argument 'String Value'."))
    assert_exception(comp, "bool_value", ValueError("Missing required argument 'Bool Value'."))
    assert_exception(comp, "int_value", ValueError("Missing required argument 'Int Value'."))
    assert_exception(comp, "float_value", ValueError("Missing required argument 'Float Value'."))
    assert_exception(comp, "object_value", ValueError("Missing required argument 'Object Value'."))
    assert_exception(comp, "data_value", ValueError("Missing required argument 'Data Value'."))

    comp.dispose()
    comp.assert_exception(RESULT_DISPOSED.failure())


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

    comp.assert_exception(RESULT_NOT_STARTED.failure())
    comp.start(args)

    error = InvalidTypeError

    assert_exception(comp, "string_value", error("Argument 'String Value' has an invalid value: 'True'."))
    assert_exception(comp, "bool_value", error("Argument 'Bool Value' has an invalid value: '123'."))
    assert_exception(comp, "int_value", error("Argument 'Int Value' has an invalid value: 'ABC'."))
    assert_exception(comp, "float_value", error("Argument 'Float Value' has an invalid value: '{}'."))
    assert_exception(comp, "object_value", error("Argument 'Object Value' has an invalid value: '[]'."))
    assert_exception(comp, "data_value", error("Argument 'Data Value' has an invalid value: '1.2'."))

    comp.dispose()
    comp.assert_exception(RESULT_DISPOSED.failure())
