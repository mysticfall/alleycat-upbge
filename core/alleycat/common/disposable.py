from typing import Final, List, Optional, TypeVar, Union

from reactivex import Observable
from reactivex.abc import DisposableBase, ObserverBase, OnCompleted, OnError, OnNext, SchedulerBase
from reactivex.disposable import Disposable
from validator_collection import not_empty

from alleycat.common import IllegalStateError


class AlreadyDisposedError(IllegalStateError):
    pass


class DisposableCollection(Disposable):
    def __init__(self) -> None:
        super().__init__()

        self.__disposables: List[DisposableBase] = []

    def append(self, disposable: DisposableBase) -> None:
        if not_empty(disposable) not in self.__disposables:
            self.__disposables.append(disposable)

    def dispose(self) -> None:
        if self.is_disposed:
            raise AlreadyDisposedError("The object has already been disposed.")

        for disposable in self.__disposables:
            # noinspection PyBroadException
            try:
                disposable.dispose()
            except BaseException:
                pass

        super().dispose()


T = TypeVar("T")


class DisposableCollector(Disposable):
    _disposables: Final[DisposableCollection]

    def __init__(self) -> None:
        super().__init__()

        self._disposables = DisposableCollection()

    def _subscribe(self,
                   stream: Observable[T],
                   on_next: Optional[Union[ObserverBase[T], OnNext[T], None]] = None,
                   on_error: Optional[OnError] = None,
                   on_completed: Optional[OnCompleted] = None,
                   scheduler: Optional[SchedulerBase] = None, ) -> None:
        subscription = stream.subscribe(
            on_next=on_next,
            on_error=on_error,
            on_completed=on_completed,
            scheduler=scheduler)

        self._disposables.append(subscription)

    def dispose(self) -> None:
        self._disposables.dispose()

        super().dispose()
