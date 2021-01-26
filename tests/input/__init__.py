from enum import Enum
from typing import Optional, Sequence

from bge.types import SCA_InputEvent


class InputState(Enum):
    Active = 0
    JustActivated = 1
    Released = 2


def create_event(status: InputState, values: Optional[Sequence[int]] = None) -> SCA_InputEvent:
    event = SCA_InputEvent()

    event.status = [
        2 if status in [InputState.Active, InputState.JustActivated] else 0]  # KX_INPUT_ACTIVE or KX_INPUT_NONE

    if values:
        event.values = values
    else:
        event.values = [
            1 if status in [InputState.Active, InputState.Released] else 0,
            1 if status in [InputState.Active, InputState.JustActivated] else 0
        ]

    return event
