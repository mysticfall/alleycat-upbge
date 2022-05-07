import re
from collections import OrderedDict

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
    string_value: str = game_property("ABC")

    bool_value: bool = game_property(True)

    int_value: int = game_property(123, read_only=False)

    float_value: float = game_property(1.2, read_only=True)

    object_value: KX_GameObject = game_property(KX_GameObject)

    data_value: Camera = game_property(Camera)

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

    errors = []

    comp = TestComp()

    comp.on_property_change(name).subscribe(on_error=errors.append)

    assert errors == []

    comp.assert_exception(RESULT_NOT_STARTED.failure())
    comp.start(args)

    expected = AttributeError(f"'{name}' has failed to initialise. Please see the log for details.")

    assert_exception(comp, name, expected)

    assert len(errors) == 1
    assert type(errors[0]) == ValueError

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

    errors = []

    comp = TestComp()

    comp.on_property_change(name).subscribe(on_error=errors.append)

    assert errors == []

    comp.assert_exception(RESULT_NOT_STARTED.failure())
    comp.start(args)

    expected = AttributeError(f"'{name}' has failed to initialise. Please see the log for details.")

    assert_exception(comp, name, expected)

    assert len(errors) == 1
    assert type(errors[0]) == InvalidTypeError

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
    comp.string_value = "ABC"

    assert comp.string_value == "ABC"
    assert comp.int_value == 321

    assert events == ["DEF", 321, "ABC"]
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
        string_value: str = game_property("DEF")

        new_value: str = game_property("GHI")

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
        ("New Value", "ghi"),
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
    assert comp.new_value == "ghi"
    assert comp.int_value == 321

    assert events == ["def", "ghi", 321]
    assert errors == []

    comp.string_value = "DEF"
    comp.new_value = "GHI"
    comp.int_value = 123

    assert comp.string_value == "DEF"
    assert comp.new_value == "GHI"
    assert comp.int_value == 123

    assert events == ["def", "ghi", 321, "DEF", "GHI", 123]
    assert errors == []


def test_read_only():
    args = OrderedDict((
        ("String Value", "DEF"),
        ("Bool Value", False),
        ("Int Value", 321),
        ("Float Value", 1.5),
        ("Object Value", KX_GameObject()),
        ("Data Value", Camera()),
    ))

    comp = TestComp()

    comp.start(args)

    with raises(AttributeError):
        comp.float_value = 2.0
