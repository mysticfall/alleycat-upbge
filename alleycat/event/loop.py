from abc import ABC, abstractmethod

from alleycat.reactive import ReactiveObject
from rx import operators as ops
from validator_collection import not_empty

from alleycat.common import ErrorHandlerSupport
from alleycat.event import EventLoopScheduler


class EventLoopAware(ErrorHandlerSupport, ReactiveObject, ABC):

    def __init__(self, scheduler: EventLoopScheduler) -> None:
        not_empty(scheduler)

        super().__init__()

        scheduler.on_process \
            .pipe(ops.take_until(self.on_dispose)) \
            .subscribe(lambda _: self.process(), on_error=self.error_handler)

    @abstractmethod
    def process(self) -> None:
        pass
