from dependency_injector import providers
from dependency_injector.containers import DeclarativeContainer
from dependency_injector.providers import Configuration, Container, Singleton

from alleycat.event import EventLoopScheduler
from alleycat.input import InputContext


class GameContext(DeclarativeContainer):
    config: Configuration = Configuration()

    scheduler: providers.Provider[EventLoopScheduler] = Singleton(EventLoopScheduler)

    input: Container[InputContext] = Container(InputContext, config=config.input, scheduler=scheduler)
