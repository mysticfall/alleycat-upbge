from collections import OrderedDict

from bge.types import KX_GameObject
from bpy.types import Camera
from returns.result import ResultE, Success

from alleycat.common import InvalidTypeError
from alleycat.core import BaseComponent, arg, bootstrap
from alleycat.lifecycle import RESULT_DISPOSED, RESULT_NOT_STARTED
from alleycat.test import assert_failure


def setup():
    bootstrap._initialised = True


def teardown():
    bootstrap._initialised = False


class TestComp(BaseComponent):
    string_value: ResultE[str] = arg("ABC")

    bool_value: ResultE[bool] = arg(True)

    int_value: ResultE[int] = arg(123)

    float_value: ResultE[float] = arg(1.2)

    object_value: ResultE[KX_GameObject] = arg(KX_GameObject)

    data_value: ResultE[Camera] = arg(Camera)

    def assert_failure(self, error: Exception) -> None:
        assert_failure(self.string_value, error)
        assert_failure(self.bool_value, error)
        assert_failure(self.int_value, error)
        assert_failure(self.float_value, error)
        assert_failure(self.object_value, error)
        assert_failure(self.data_value, error)


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

    comp.assert_failure(RESULT_NOT_STARTED.failure())
    comp.start(args)

    assert comp.string_value == Success("DEF")
    assert comp.bool_value == Success(False)
    assert comp.int_value == Success(321)
    assert comp.float_value == Success(1.5)
    assert comp.object_value == Success(other)
    assert comp.data_value == Success(camera)

    comp.dispose()
    comp.assert_failure(RESULT_DISPOSED.failure())


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

    comp.assert_failure(RESULT_NOT_STARTED.failure())
    comp.start(args)

    assert_failure(comp.string_value, ValueError("Missing required argument 'String Value'."))
    assert_failure(comp.bool_value, ValueError("Missing required argument 'Bool Value'."))
    assert_failure(comp.int_value, ValueError("Missing required argument 'Int Value'."))
    assert_failure(comp.float_value, ValueError("Missing required argument 'Float Value'."))
    assert_failure(comp.object_value, ValueError("Missing required argument 'Object Value'."))
    assert_failure(comp.data_value, ValueError("Missing required argument 'Data Value'."))

    comp.dispose()
    comp.assert_failure(RESULT_DISPOSED.failure())


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

    comp.assert_failure(RESULT_NOT_STARTED.failure())
    comp.start(args)

    error = InvalidTypeError

    assert_failure(comp.string_value, error("Value True is not of expected type 'str' (actual: 'bool')."))
    assert_failure(comp.bool_value, error("Value 123 is not of expected type 'bool' (actual: 'int')."))
    assert_failure(comp.int_value, error("Value ABC is not of expected type 'int' (actual: 'str')."))
    assert_failure(comp.float_value, error("Value {} is not of expected type 'float' (actual: 'dict')."))
    assert_failure(comp.object_value, error("Value [] is not of expected type 'KX_GameObject' (actual: 'list')."))
    assert_failure(comp.data_value, error("Value 1.2 is not of expected type 'Camera' (actual: 'float')."))

    comp.dispose()
    comp.assert_failure(RESULT_DISPOSED.failure())
