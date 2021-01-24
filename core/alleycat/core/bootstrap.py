import json
from collections import OrderedDict
from importlib import import_module
from pathlib import Path
from typing import Callable, List, Sequence, cast

import sys
from bge.types import KX_GameObject
from bpy.path import abspath
from dependency_injector.providers import Configuration
from validator_collection import not_empty, validators

from alleycat.common import Feature, GameContext

Initializer = Callable[[], None]

_initialized = False
_initializers: List[Initializer] = []


class Bootstrap(KX_GameObject):
    args = OrderedDict((
        ("key", "alleycat"),
        ("config", "//config.json"),
    ))

    context: GameContext

    def start(self, args: OrderedDict) -> None:
        key = validators.string(args["key"])
        config_path = validators.string(args["config"])

        self.logger.info("Starting %s.", key)

        self.context = GameContext()

        config_file = Path(abspath(config_path))

        print(f"Loading configuration from {config_file}.")

        injection_targets: Sequence[str] = ()

        if config_file.exists():
            with open(config_file) as f:
                config = Configuration()
                config.from_dict(json.load(f))

                self.context.config = config

                features = filter(lambda c: isinstance(c, Feature), self.components)

                for feature in features:
                    self.logger.info("Configuring feature %s.", type(feature).__name__)

                    try:
                        cast(Feature, feature).config(config)
                    except:
                        self.logger.exception("Failed to initialise feature.")

        def except_hook(tpe, value, traceback):
            if tpe != KeyboardInterrupt:
                self.logger.exception("Unhandled error occurred:", exc_info=value, stack_info=traceback)

            sys.__excepthook__(tpe, value, traceback)

        # noinspection SpellCheckingInspection
        sys.excepthook = except_hook

        if len(injection_targets) > 0:
            self.logger.info("Injecting dependencies to modules: %s", injection_targets)

            self.context.wire(modules=tuple(map(import_module, injection_targets)))

        for callback in _initializers:
            try:
                callback()
            except Exception as e:
                self.logger.exception(e, exc_info=True)

        global _initialized

        _initialized = True
        _initializers.clear()

        self.logger.info("Bootstrap has completed successfully.")

    def dispose(self) -> None:
        self.logger.info("Disposing context.")

        if self.context:
            self.context.unwire()
            self.context.shutdown_resources()

    @staticmethod
    def on_ready(callback: Initializer) -> None:
        not_empty(callback)

        if _initialized:
            callback()
        else:
            _initializers.append(callback)
