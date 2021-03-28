from abc import ABC

from alleycat.reactive import RP, RV, ReactiveObject, functions as rv

from alleycat.common import IllegalStateError


class AlreadyInitializedError(IllegalStateError):
    pass


class Initializable(ReactiveObject, ABC):
    _initialized: RP[bool] = rv.from_value(False)

    initialized: RV[bool] = _initialized.as_view()

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

    def initialize(self) -> None:
        if self._initialized:
            raise AlreadyInitializedError("Class has been initialized already.")

        # noinspection PyTypeChecker
        self._initialized = True
