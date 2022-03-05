import json
import sys
from collections import OrderedDict
from pathlib import Path
from typing import cast

from bge.types import KX_GameObject
from bpy.path import abspath
from dependency_injector.providers import Configuration
from validator_collection import validators

from alleycat.core import Feature


class Bootstrap(KX_GameObject):
    args = OrderedDict((
        ("key", "alleycat"),
        ("config", "//config.json"),
    ))

    def start(self, args: OrderedDict) -> None:
        key = validators.string(args["key"])
        config_path = validators.string(args["config"])

        self.logger.info("Starting %s.", key)

        config_file = Path(abspath(config_path))

        print(f"Loading configuration from {config_file}.")

        if config_file.exists():
            with open(config_file) as f:
                config = Configuration()
                config.from_dict(json.load(f))

                features = filter(lambda c: isinstance(c, Feature), self.components)

                for feature in features:
                    self.logger.info("Configuring feature %s.", type(feature).__name__)

                    # noinspection PyBroadException
                    try:
                        cast(Feature, feature).config(config)
                    except BaseException as e:
                        self.logger.error("Failed to initialise feature.", exc_info=e)

        def except_hook(tpe, value, traceback):
            if tpe != KeyboardInterrupt:
                self.logger.exception("Unhandled error occurred:", exc_info=value, stack_info=traceback)

            sys.__excepthook__(tpe, value, traceback)

        # noinspection SpellCheckingInspection
        sys.excepthook = except_hook

        self.logger.info("Bootstrap has completed successfully.")
