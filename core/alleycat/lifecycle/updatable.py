from abc import ABC, abstractmethod
from typing import final


class Updatable(ABC):

    @property
    def can_update(self) -> bool:
        return True

    @abstractmethod
    def _do_update(self) -> None:
        pass

    @final
    def update(self) -> None:
        if self.can_update:
            self._do_update()
