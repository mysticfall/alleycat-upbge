from bge.types import SCA_InputEvent


def create_event(status, values=(0, 0)) -> SCA_InputEvent:
    event = SCA_InputEvent()

    event.status = status
    event.values = values

    return event
