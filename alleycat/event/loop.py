from abc import abstractmethod

from alleycat.reactive import ReactiveObject
from rx import operators as ops
from validator_collection import not_empty

from alleycat.event import EventLoopScheduler
from alleycat.log import ErrorHandlerSupport


class EventLoopAware(ErrorHandlerSupport, ReactiveObject):

    def __init__(self, scheduler: EventLoopScheduler) -> None:
        self._scheduler = not_empty(scheduler)

        super().__init__()

        scheduler.on_process \
            .pipe(ops.take_until(self.on_dispose)) \
            .subscribe(lambda _: self.process(), on_error=self.error_handler)

    @property
    def scheduler(self) -> EventLoopScheduler:
        return self._scheduler

    @abstractmethod
    def process(self) -> None:
        pass
