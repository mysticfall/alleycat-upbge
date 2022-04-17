from typing import Final, List, Optional, TypeVar, Union, final

from reactivex import Observable, Subject
from reactivex.abc import DisposableBase, ObserverBase, OnCompleted, OnError, OnNext, SchedulerBase
from reactivex.disposable import Disposable
from returns.result import Result
from validator_collection import not_empty

from alleycat.common import IllegalStateError


class AlreadyDisposedError(IllegalStateError):
    pass


RESULT_DISPOSED: Final = Result.from_failure(
    AlreadyDisposedError("The object has already been disposed."))


class DisposableCollection(Disposable):
    def __init__(self) -> None:
        super().__init__()

        self.__disposables: List[DisposableBase] = []

    @final
    def append(self, disposable: DisposableBase) -> None:
        if not_empty(disposable) not in self.__disposables:
            self.__disposables.append(disposable)

    def dispose(self) -> None:
        if self.is_disposed:
            raise RESULT_DISPOSED.failure()

        for disposable in self.__disposables:
            # noinspection PyBroadException
            try:
                disposable.dispose()
            except BaseException:
                pass

        super().dispose()


T = TypeVar("T")


class BaseDisposable(Disposable):
    _disposables: Final[DisposableCollection]

    def __init__(self) -> None:
        super().__init__()

        self.__on_dispose = Subject[None]()
        self._disposables = DisposableCollection()

    def dispose(self) -> None:
        super().dispose()

        self._disposables.dispose()

        self.__on_dispose.on_next(None)
        self.__on_dispose.on_completed()
        self.__on_dispose.dispose()

    @final
    @property
    def on_dispose(self) -> Observable[None]:
        return self.__on_dispose

    @final
    def _check_disposed(self) -> None:
        if self.is_disposed:
            raise RESULT_DISPOSED.failure()

    @final
    def _subscribe_until_dispose(self,
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
