import logging
from queue import Queue
from typing import Callable, Optional

import trio
from trio import Nursery

from alleycat.common import LoggingSupport
from alleycat.lifecycle import BaseDisposable, Updatable


class CoroutineRunner(Updatable, BaseDisposable, LoggingSupport):
    logger: logging.Logger = logging.getLogger(__name__)

    def __init__(self) -> None:
        super().__init__()

        self.__queue = Queue()
        self.__nursery: Optional[Nursery] = None

        def run_sync_soon_threadsafe(fn):
            self.__queue.put(fn, block=False)

        def done_callback(trio_main_outcome):
            self.logger.debug("Trio loop ended with: %s.", trio_main_outcome)

        async def trio_main():
            async with trio.open_nursery() as nursery:
                self.__nursery = nursery

                while not self.is_disposed:
                    await trio.sleep(0.01)

        self.logger.debug("Starting Trio event loop.")

        trio.lowlevel.start_guest_run(
            trio_main,
            run_sync_soon_threadsafe=run_sync_soon_threadsafe,
            done_callback=done_callback)

    def run_async(self, task: Callable, *args, name: str = None) -> None:
        self._check_disposed()

        self.__nursery.start_soon(task, *args, name=name)

    def _do_update(self) -> None:
        self._check_disposed()

        super()._do_update()

        while not self.__queue.empty():
            task = self.__queue.get(block=False)

            # noinspection PyBroadException
            try:
                task()
            except Exception:
                self.logger.exception("Failed to execute a coroutine.")
