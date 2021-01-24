import sys
from abc import ABC
from collections import OrderedDict

from bge.types import KX_PythonComponent


class Debugger(KX_PythonComponent, ABC):
    args = OrderedDict((
        ("debug", False),
        ("suspend", False),
        ("debug_port", 1099)))

    def start(self, args: dict):
        if args["debug"]:
            path = args["pydevd_path"]

            if not any("pycharm-debug" in p for p in sys.path):
                sys.path.append(path)

            print("### Path = ", sys.path)

            import pydevd_pycharm

            port = int(args["debug_port"])
            suspend = bool(args["suspend"])

            pydevd_pycharm.settrace("localhost", port=port, stdoutToServer=True, stderrToServer=True, suspend=suspend)

    def update(self) -> None:
        print("Update!")


class PyCharmDebugger(Debugger):
    args = OrderedDict(tuple(Debugger.args.items()) + (
        ("pydevd_path", "/opt/pycharm-eap/debug-eggs/pydevd-pycharm.egg"),))


class PyDevDebugger(Debugger):
    pass
