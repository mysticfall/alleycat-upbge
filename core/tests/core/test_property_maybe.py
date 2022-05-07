import re
from collections import OrderedDict

from bge.types import KX_GameObject
from bpy.types import Camera
from pytest import mark, raises
from returns.maybe import Maybe, Nothing, Some

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


def assert_exception(obj, attr: str, expected: Exception) -> Nothing:
    with raises(type(expected), match=re.escape(expected.args[0])):
        assert getattr(obj, attr)


def setup():
    bootstrap._initialised = True


def teardown():
    bootstrap._initialised = False


class TestComp(BaseComponent):
    string_value: Maybe[str] = game_property("ABC")

    bool_value: Maybe[bool] = game_property(True)

    int_value: Maybe[int] = game_property(123, read_only=False)

    float_value: Maybe[float] = game_property(1.2, read_only=True)

    object_value: Maybe[KX_GameObject] = game_property(KX_GameObject)

    data_value: Maybe[Camera] = game_property(Camera)

    def assert_exception(self, error: Exception) -> Nothing:
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

    assert comp.string_value == Some("DEF")
    assert comp.bool_value == Some(False)
    assert comp.int_value == Some(321)
    assert comp.float_value == Some(1.5)
    assert comp.object_value == Some(other)
    assert comp.data_value == Some(camera)

    assert events == [Some("DEF"), Some(321)]
    assert errors == []

    comp.dispose()
    comp.assert_exception(RESULT_DISPOSED.failure())


@mark.parametrize("name", property_names)
def test_empty(name: str):
    args = OrderedDict((
        ("String Value", Nothing),
        ("Bool Value", Nothing),
        ("Int Value", Nothing),
        ("Float Value", Nothing),
        ("Object Value", Nothing),
        ("Data Value", Nothing)
    ))

    events = []
    errors = []

    comp = TestComp()

    comp.assert_exception(RESULT_NOT_STARTED.failure())
    comp.start(args)

    comp.on_property_change("string_value").subscribe(events.append, on_error=errors.append)
    comp.on_property_change("int_value").subscribe(events.append, on_error=errors.append)

    assert comp.string_value == Nothing
    assert comp.bool_value == Nothing
    assert comp.int_value == Nothing
    assert comp.float_value == Nothing
    assert comp.object_value == Nothing
    assert comp.data_value == Nothing

    assert events == [Nothing, Nothing]
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

    assert comp.string_value == Nothing
    assert comp.bool_value == Nothing
    assert comp.int_value == Nothing
    assert comp.float_value == Nothing
    assert comp.object_value == Nothing
    assert comp.data_value == Nothing

    assert events == [Nothing, Nothing]
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
        comp.string_value = Some("DEF")

    with raises(NotStartedError):
        comp.int_value = Some(321)

    comp.start(args)

    assert comp.string_value == Some("DEF")
    assert comp.int_value == Some(321)

    assert events == [Some("DEF"), Some(321)]
    assert errors == []

    comp.string_value = Some("ABC")

    assert comp.string_value == Some("ABC")
    assert comp.int_value == Some(321)

    assert events == [Some("DEF"), Some(321), Some("ABC")]
    assert errors == []

    comp.string_value = Nothing
    comp.int_value = Nothing

    assert comp.string_value == Nothing
    assert comp.int_value == Nothing

    assert events == [Some("DEF"), Some(321), Some("ABC"), Nothing, Nothing]
    assert errors == []

    with raises(InvalidTypeError):
        comp.string_value = Some(123)

    with raises(InvalidTypeError):
        comp.int_value = Some("ABC")

    comp.dispose()

    with raises(AlreadyDisposedError):
        comp.string_value = Some("DEF")

    with raises(AlreadyDisposedError):
        comp.int_value = Some(321)


def test_inheritance():
    other = KX_GameObject()
    camera = Camera()

    class ChildComp(TestComp):
        string_value: Maybe[str] = game_property("DEF")

        new_value: Maybe[str] = game_property("GHI")

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
        ("New Value", Nothing),
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

    assert comp.string_value == Some("def")
    assert comp.new_value == Nothing
    assert comp.int_value == Some(321)

    assert events == [Some("def"), Nothing, Some(321)]
    assert errors == []

    comp.string_value = Nothing
    comp.new_value = Some("GHI")
    comp.int_value = Nothing

    assert comp.string_value == Nothing
    assert comp.new_value == Some("GHI")
    assert comp.int_value == Nothing

    assert events == [Some("def"), Nothing, Some(321), Nothing, Some("GHI"), Nothing]
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
        comp.float_value = Some(2.0)
