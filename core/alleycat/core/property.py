from __future__ import annotations

from abc import ABC
from functools import partial
from typing import Any, Dict, Final, Generic, Mapping, Optional, OrderedDict, Type, TypeVar, Union, get_type_hints

from returns.maybe import Maybe, Nothing
from returns.result import Failure, Result, ResultE, Success

from alleycat.common import MapReader
from alleycat.lifecycle import RESULT_DISPOSED, RESULT_NOT_STARTED, Startable

T = TypeVar("T")


class PropertyHolder(Startable, ABC):
    _prop_descriptors: Mapping[str, PropertyDescriptor]

    def __init__(self) -> None:
        super().__init__()

        self._prop_values: ResultE[Dict[str, ResultE]] = RESULT_NOT_STARTED

    def _do_start(self) -> None:
        super()._do_start()

        descriptors = self._prop_descriptors.values()

        def validate(args: MapReader) -> Dict[str, ResultE]:
            return dict(map(lambda d: (d.key, d.validate(args)), descriptors))

        self._prop_values = self.start_args.map(validate)

    def __init_subclass__(cls, **kwargs) -> None:
        get_descriptor = partial(getattr, cls)

        attributes = filter(lambda a: not a.startswith("__"), dir(cls))
        descriptors = tuple(filter(lambda d: isinstance(d, PropertyDescriptor), map(get_descriptor, attributes)))
        entries = map(lambda d: (d.key, d.default_value.value_or(d.value_type)), descriptors)

        cls.args = OrderedDict[str, Any](entries)
        cls._prop_descriptors = dict(map(lambda d: (d.key, d), descriptors))

        super().__init_subclass__(**kwargs)

    def dispose(self) -> None:
        super().dispose()

        self._prop_values = RESULT_DISPOSED


class PropertyDescriptor(Generic[T]):
    value_type: Final[Type[T]]

    default_value: Final[Maybe[T]]

    def __init__(
            self,
            value_type: Type[T],
            default_value: Maybe[T] = Nothing) -> None:
        self.value_type = value_type
        self.default_value = default_value

        self.__name: Optional[str] = None
        self.__key: Optional[str] = None
        self.__return_type: Maybe[Type[...]] = Nothing

    @property
    def name(self) -> Optional[str]:
        return self.__name

    @property
    def key(self) -> Optional[str]:
        return self.__key

    @property
    def return_type(self) -> Maybe[Type[...]]:
        return self.__return_type

    def validate(self, args: MapReader) -> ResultE[T]:
        return args.require(self.key, self.value_type)

    def __set_name__(self, owner: Type[...], name: str, *args, **kwargs) -> None:
        if not issubclass(owner, PropertyHolder):
            raise ValueError(
                f"@{game_property.__name__} can only be used in a subclass of "
                f"{PropertyHolder.__name__} (found: {owner.__name__}).")

        self.__name = name
        self.__key = name.replace("_", " ").title()

        try:
            self.__return_type = get_type_hints(owner)[name].__origin__
        except (KeyError, AttributeError):
            self.__return_type = self.value_type

    def __get__(self, instance: Optional[PropertyHolder], owner: Type[PropertyHolder]):
        if instance is None:
            return self

        assert self.key, "The descriptor is not associated with a class."

        # noinspection PyProtectedMember
        value = instance._prop_values.bind(lambda a: a[self.key])

        if self.return_type == Result:
            return value
        elif self.return_type == Maybe:
            return value.map(Maybe.from_value).value_or(Nothing)
        elif self.return_type == Union and self.value_type != Union:
            return value.value_or(None)
        else:
            match value:
                case Success(v):
                    return v
                case Failure(e):
                    raise e


def game_property(arg: Union[T, Type[T]]) -> PropertyDescriptor[T]:
    if isinstance(arg, type):
        # noinspection PyTypeChecker
        return PropertyDescriptor(arg)
    else:
        return PropertyDescriptor(type(arg), default_value=Maybe.from_value(arg))
