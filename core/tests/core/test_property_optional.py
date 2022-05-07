import re
from collections import OrderedDict
from typing import Optional

from bge.types import KX_GameObject
from bpy.types import Camera
from pytest import mark, raises

from alleycat.common import InvalidTypeError
from alleycat.core import BaseComponent, bootstrap, game_property
from alleycat.lifecycle import AlreadyDisposedError, NotStartedError, RESULT_DISPOSED, RESULT_NOT_STARTED

property_names = (
    "string_value",
    "bool_value",
    "int_value",
    "float_value",
    "object_value",
    "data_value"
)


def assert_exception(obj, attr: str, expected: Exception) -> None:
    with raises(type(expected), match=re.escape(expected.args[0])):
        assert getattr(obj, attr)


def setup():
    bootstrap._initialised = True


def teardown():
    bootstrap._initialised = False


class TestComp(BaseComponent):
    string_value: Optional[str] = game_property("ABC")

    bool_value: Optional[bool] = game_property(True)

    int_value: Optional[int] = game_property(123)

    float_value: Optional[float] = game_property(1.2)

    object_value: Optional[KX_GameObject] = game_property(KX_GameObject)

    data_value: Optional[Camera] = game_property(Camera)

    def assert_exception(self, error: Exception) -> None:
        for name in property_names:
            assert_exception(self, name, error)


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

    events = []
    errors = []

    comp = TestComp()

    comp.assert_exception(RESULT_NOT_STARTED.failure())
    comp.start(args)

    comp.on_property_change("string_value").subscribe(events.append, on_error=errors.append)
    comp.on_property_change("int_value").subscribe(events.append, on_error=errors.append)

    assert comp.string_value == "DEF"
    assert comp.bool_value is False
    assert comp.int_value == 321
    assert comp.float_value == 1.5
    assert comp.object_value == other
    assert comp.data_value == camera

    assert events == ["DEF", 321]
    assert errors == []

    comp.dispose()
    comp.assert_exception(RESULT_DISPOSED.failure())


@mark.parametrize("name", property_names)
def test_empty(name: str):
    args = OrderedDict((
        ("String Value", None),
        ("Bool Value", None),
        ("Int Value", None),
        ("Float Value", None),
        ("Object Value", None),
        ("Data Value", None)
    ))

    events = []
    errors = []

    comp = TestComp()

    comp.assert_exception(RESULT_NOT_STARTED.failure())
    comp.start(args)

    comp.on_property_change("string_value").subscribe(events.append, on_error=errors.append)
    comp.on_property_change("int_value").subscribe(events.append, on_error=errors.append)

    assert comp.string_value is None
    assert comp.bool_value is None
    assert comp.int_value is None
    assert comp.float_value is None
    assert comp.object_value is None
    assert comp.data_value is None

    assert events == [None, None]
    assert errors == []

    comp.dispose()
    comp.assert_exception(RESULT_DISPOSED.failure())


@mark.parametrize("name", property_names)
def test_invalid(name: str):
    args = OrderedDict((
        ("String Value", True),
        ("Bool Value", 123),
        ("Int Value", "ABC"),
        ("Float Value", dict()),
        ("Object Value", list()),
        ("Data Value", 1.2)
    ))

    events = []
    errors = []

    comp = TestComp()

    comp.assert_exception(RESULT_NOT_STARTED.failure())
    comp.start(args)

    comp.on_property_change("string_value").subscribe(events.append, on_error=errors.append)
    comp.on_property_change("int_value").subscribe(events.append, on_error=errors.append)

    assert comp.string_value is None
    assert comp.bool_value is None
    assert comp.int_value is None
    assert comp.float_value is None
    assert comp.object_value is None
    assert comp.data_value is None

    assert events == [None, None]
    assert errors == []

    comp.dispose()
    comp.assert_exception(RESULT_DISPOSED.failure())


def test_update():
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

    events = []
    errors = []

    comp.on_property_change("string_value").subscribe(events.append, on_error=errors.append)
    comp.on_property_change("int_value").subscribe(events.append, on_error=errors.append)

    with raises(NotStartedError):
        comp.string_value = "DEF"

    with raises(NotStartedError):
        comp.int_value = 321

    comp.start(args)

    assert comp.string_value == "DEF"
    assert comp.int_value == 321

    assert events == ["DEF", 321]
    assert errors == []

    comp.string_value = "ABC"

    assert comp.string_value == "ABC"
    assert comp.int_value == 321

    assert events == ["DEF", 321, "ABC"]
    assert errors == []

    comp.string_value = None
    comp.int_value = None

    assert comp.string_value is None
    assert comp.int_value is None

    assert events == ["DEF", 321, "ABC", None, None]
    assert errors == []

    with raises(InvalidTypeError):
        comp.string_value = 123

    with raises(InvalidTypeError):
        comp.int_value = "ABC"

    comp.dispose()

    with raises(AlreadyDisposedError):
        comp.string_value = "DEF"

    with raises(AlreadyDisposedError):
        comp.int_value = 321


def test_inheritance():
    other = KX_GameObject()
    camera = Camera()

    class ChildComp(TestComp):
        string_value: Optional[str] = game_property("DEF")

        new_value: Optional[str] = game_property("GHI")

    assert set(ChildComp.args.items()) == {
        ("String Value", "DEF"),
        ("New Value", "GHI"),
        ("Bool Value", True),
        ("Int Value", 123),
        ("Float Value", 1.2),
        ("Object Value", KX_GameObject),
        ("Data Value", Camera)
    }

    args = OrderedDict((
        ("String Value", "def"),
        ("New Value", None),
        ("Bool Value", False),
        ("Int Value", 321),
        ("Float Value", 1.5),
        ("Object Value", other),
        ("Data Value", camera),
    ))

    comp = ChildComp()

    events = []
    errors = []

    comp.on_property_change("string_value").subscribe(events.append, on_error=errors.append)
    comp.on_property_change("new_value").subscribe(events.append, on_error=errors.append)
    comp.on_property_change("int_value").subscribe(events.append, on_error=errors.append)

    comp.start(args)

    assert comp.string_value == "def"
    assert comp.new_value is None
    assert comp.int_value == 321

    assert events == ["def", None, 321]
    assert errors == []

    comp.string_value = None
    comp.new_value = "GHI"
    comp.int_value = None

    assert comp.string_value is None
    assert comp.new_value == "GHI"
    assert comp.int_value is None

    assert events == ["def", None, 321, None, "GHI", None]
    assert errors == []
