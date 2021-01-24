import json
import logging
import sys
from validator_collection import validators
from collections import OrderedDict
from logging.config import fileConfig
from pathlib import Path

from bge.types import KX_GameObject, KX_PythonComponent
from bpy.path import abspath
from dependency_injector.providers import Object

from alleycat.event import EventLoopScheduler
from alleycat.game import GameContext
from alleycat.log import LoggingSupport


class Bootstrap(LoggingSupport, KX_PythonComponent):
    args = OrderedDict((
        ("key", "alleycat"),
        ("config", "//config.json")
    ))

    context: GameContext

    scheduler: EventLoopScheduler

    # noinspection PyUnusedLocal
    def __init__(self, obj: KX_GameObject):
        super().__init__()

    def start(self, args: dict) -> None:
        key = validators.string(args["key"])
        config_path = validators.string(args["config"])

        print(f"Starting {key}.")

        self.scheduler = EventLoopScheduler()

        self.context = GameContext(scheduler=Object(self.scheduler))

        config_file = Path(abspath(config_path))

        print(f"Loading configuration from {config_file}.")

        if config_file.exists():
            with open(config_file) as f:
                config = json.load(f)

                self.context.config.from_dict(config)

                if "logging" in config:
                    logging_conf = config["logging"]
                    logging_conf["disable_existing_loggers"] = False

                    logging.config.dictConfig(logging_conf)

        def except_hook(tpe, value, traceback):
            if tpe != KeyboardInterrupt:
                self.logger.exception("Unhandled error occurred:", exc_info=value, stack_info=traceback)

            sys.__excepthook__(tpe, value, traceback)

        # noinspection SpellCheckingInspection
        sys.excepthook = except_hook

        self.context.wire(modules=[sys.modules["alleycat.actor"]])

        self.logger.info("Bootstrap has completed successfully.")

    def update(self) -> None:
        self.scheduler.process()

    def dispose(self) -> None:
        self.logger.info("Disposing context.")

        if self.context:
            self.context.scheduler().dispose()
