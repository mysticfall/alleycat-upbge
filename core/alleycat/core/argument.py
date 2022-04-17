from __future__ import annotations

from abc import ABC
from collections import OrderedDict
from functools import partial
from typing import Any, Callable, Final, Optional, Tuple, Type, Union, get_type_hints

from returns.maybe import Maybe, Nothing
from returns.primitives.exceptions import UnwrapFailedError
from returns.result import Failure, Result

from alleycat.common.validators import require_type
from alleycat.lifecycle import Startable


class ArgumentsHolder(Startable, ABC):

    def __init_subclass__(cls, **kwargs) -> None:
        get_descriptor = partial(getattr, cls)

        attributes = filter(lambda a: not a.startswith("__"), dir(cls))
        descriptors = filter(lambda d: isinstance(d, ArgumentDescriptor), map(get_descriptor, attributes))
        entries = map(lambda d: d.entry, descriptors)

        cls.args = OrderedDict(entries)

        super().__init_subclass__(**kwargs)


class ArgumentDescriptor:
    type_info: Final[Any]

    value_type: Final[Type[...]]

    def __init__(self, type_info) -> None:
        self.type_info = type_info
        self.value_type = type_info if isinstance(type_info, type) else type(type_info)

        self._name: Optional[str] = None
        self._key: Optional[str] = None
        self._return_type: Optional[Type[...]] = None

    @property
    def name(self) -> str:
        return self._name

    @property
    def key(self) -> str:
        return self._key

    @property
    def return_type(self) -> Optional[Type[...]]:
        return self._return_type

    @property
    def entry(self) -> Optional[Tuple[str, Any]]:
        return self.key, self.type_info if self.key else None

    def validate(self, validator: Callable[[...], bool], message: str = None):
        pass

    def __set_name__(self, owner: Type[ArgumentsHolder], name: str, *args, **kwargs) -> None:
        if not issubclass(owner, ArgumentsHolder):
            raise ValueError(
                f"@arg can only be used in a subclass of ArgumentsHolder (found: {owner.__name__}).")

        self._name = name
        self._key = name.replace("_", " ").title()

        if not self.return_type:
            try:
                self._return_type = get_type_hints(owner)[name].__origin__
            except (KeyError, AttributeError):
                self._return_type = self.value_type

    def __get__(self, instance: ArgumentsHolder, owner: Type[ArgumentsHolder]):
        if instance is None:
            return self

        assert self.key, "The descriptor is not associated with a class."

        def read(args: OrderedDict):
            def fail_for_missing_arg():
                return Failure(ValueError(f"Missing required argument '{self.key}'."))

            if self.key not in args:
                return fail_for_missing_arg()

            arg_value = args[self.key]

            return fail_for_missing_arg() if arg_value is None else require_type(arg_value, self.value_type)

        value = instance.start_args.bind(read)

        if self.return_type == Result:
            return value
        elif self.return_type == Maybe:
            return value.map(Maybe.from_value).value_or(Nothing)
        elif self.return_type == Union and self.value_type != Union:
            return value.value_or(None)
        else:
            try:
                return value.unwrap()
            except UnwrapFailedError:
                raise value.failure()


def arg(type_info) -> ArgumentDescriptor:
    return ArgumentDescriptor(type_info)
