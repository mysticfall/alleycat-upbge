from __future__ import annotations

from abc import ABC
from functools import partial
from logging import Logger
from typing import Any, Final, Generic, Mapping, Optional, OrderedDict, Type, TypeVar, Union, \
    get_type_hints

from reactivex import Observable, operators as ops
from reactivex.subject import BehaviorSubject
from returns.iterables import Fold
from returns.maybe import Maybe, Nothing, Some
from returns.result import Failure, Result, ResultE, Success
from validator_collection import not_empty

from alleycat.common import InvalidTypeError, LoggingSupport, MapReader, require_type
from alleycat.lifecycle import Startable

T = TypeVar("T")


class PropertyHolder(Startable, LoggingSupport, ABC):
    _prop_descriptors: Mapping[str, PropertyDescriptor]

    def __init__(self) -> None:
        super().__init__()

        self.__prop_values = BehaviorSubject[MapReader](MapReader(dict()))

    def _do_start(self, args: MapReader) -> ResultE[MapReader]:
        self.logger.debug("Starting with arguments: %s", args)

        start_args = super()._do_start(args)

        descriptors = self._prop_descriptors.values()

        self._subscribe_until_dispose(self.__prop_values, on_error=self.logger.error)

        def validate(d: PropertyDescriptor, a: MapReader):
            return d.from_args(a, self.logger).map(lambda v: (d.name, v))

        def collect(a: MapReader):
            return Fold \
                .collect(map(lambda d: validate(d, a), descriptors), Success(())) \
                .map(dict) \
                .map(MapReader)

        match start_args.bind(collect):
            case Success(values):
                self.__prop_values.on_next(values)

                self.logger.info("Successfully started with arguments: %s", values)

                return start_args
            case Failure(e):
                self.__prop_values.on_error(e)

                self.logger.error("Failed to start with an error: %s", e, exc_info=e)

                return Result.from_failure(e)

    def on_property_change(self, name: str) -> Observable:
        return self.__prop_values.pipe(
            ops.filter(lambda v: name in v),
            ops.map(lambda v: v[name]),
            ops.distinct_until_changed())

    @property
    def _prop_values(self) -> MapReader:
        self._check_started()
        self._check_disposed()

        return self.__prop_values.value

    def _set_property(self, name: str, value: Any) -> None:
        values = dict(**self._prop_values)
        values[name] = value

        self.__prop_values.on_next(MapReader(values))

    def __init_subclass__(cls, **kwargs) -> None:
        get_descriptor = partial(getattr, cls)

        attributes = filter(lambda a: not a.startswith("__"), dir(cls))
        descriptors = tuple(filter(lambda d: isinstance(d, PropertyDescriptor), map(get_descriptor, attributes)))
        entries = map(lambda d: (d.key, d.default_value.value_or(d.value_type)), descriptors)

        cls.args = OrderedDict[str, Any](entries)

        cls._prop_descriptors = dict(map(lambda d: (d.name, d), descriptors))

        super().__init_subclass__(**kwargs)

    def dispose(self) -> None:
        super().dispose()

        if not self.__prop_values.exception:
            self.__prop_values.on_completed()

        self.__prop_values.dispose()


class PropertyDescriptor(Generic[T]):
    value_type: Final[Type[T]]

    default_value: Final[Maybe[T]]

    read_only: Final[bool]

    def __init__(
            self,
            value_type: Type[T],
            default_value: Maybe[T] = Nothing,
            read_only: bool = False) -> None:
        self.value_type = value_type
        self.default_value = default_value
        self.read_only = read_only

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
    def return_type(self) -> Optional[Type[...]]:
        return self.__return_type

    def from_args(self, args: MapReader, logger: Logger) -> ResultE[Any]:
        if self.return_type == Maybe or self.return_type == Union:
            match args.read(self.key, self.value_type).map(self.validate):
                case Some(Success(v)):
                    logger.debug("'%s'(%s) = '%s'", self.key, self.name, v)

                    return Success(Some(v)) if self.return_type == Maybe else Success(v)
                case Some(Failure(e)):
                    logger.warning("Failed to parse '%s'(%s).", self.key, self.name, exc_info=e)

                    return Success(Nothing) if self.return_type == Maybe else Success(None)
                case _:
                    logger.debug("'%s'(%s) = <empty>", self.key, self.name)

                    return Success(Nothing if self.return_type == Maybe else None)

        value = args.require(self.key, self.value_type).bind(self.validate)

        match value:
            case Success(v):
                logger.debug("'%s'(%s) = '%s'", self.key, self.name, v)
            case Failure(e):
                logger.error("Failed to parse '%s'(%s).", self.key, self.name, exc_info=e)

        return value

    def validate(self, value: Any) -> ResultE[Any]:
        return require_type(value, self.value_type)

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

    def __get__(self, instance: Optional[PropertyHolder], owner: Type[PropertyHolder]) -> Any:
        if instance is None:
            return self

        assert self.key, "The descriptor is not associated with a class."

        try:
            # noinspection PyProtectedMember
            return instance._prop_values[self.name]
        except KeyError:
            raise AttributeError(f"'{self.name}' has failed to initialise. Please see the log for details.")

    def __set__(self, instance: Optional[PropertyHolder], value: Any) -> None:
        if self.read_only:
            raise AttributeError(f"'{self.name}' is a read-only property.")

        def validate_or_fail(v):
            match self.validate(v):
                case Success(v):
                    return v
                case Failure(e):
                    raise e

        if self.return_type == Maybe:
            if not isinstance(value, Maybe):
                raise InvalidTypeError(f"Expected a Maybe value but found '{value}' instead.")

            validated = value.map(validate_or_fail)
        elif self.return_type == Union and value is None:
            validated = None
        else:
            validated = validate_or_fail(value)

        # noinspection PyProtectedMember
        not_empty(instance)._set_property(self.name, validated)


def game_property(arg: Union[T, Type[T]], read_only: bool = False) -> PropertyDescriptor[T]:
    if isinstance(arg, type):
        # noinspection PyTypeChecker
        return PropertyDescriptor(arg)
    else:
        return PropertyDescriptor(
            type(arg),
            default_value=Maybe.from_value(arg),
            read_only=read_only)
