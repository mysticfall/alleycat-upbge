class InvalidTypeError(ValueError):
    pass


class IllegalStateError(Exception):
    pass


class NotStartedError(IllegalStateError):
    pass
