from logging import Handler, NOTSET

import bpy


class ConsoleLogger(Handler):
    def __init__(self, level=NOTSET) -> None:
        super().__init__(level)

        self._context = None

    def emit(self, record) -> None:
        context = None

        for area in bpy.context.screen.areas:
            if area.type == "CONSOLE":
                context = {
                    "area": area,
                    "space_data": area.spaces.active,
                    "region": area.regions[-1],
                    "window": bpy.context.window,
                    "screen": bpy.context.screen
                }

        if not context:
            return

        # noinspection PyBroadException
        try:
            msg = self.format(record)

            for line in msg.split("\n"):
                # noinspection PyArgumentList
                bpy.ops.console.scrollback_append(context, text=line)
                pass

            self.flush()
        except RecursionError:
            raise
        except Exception:
            self.handleError(record)
