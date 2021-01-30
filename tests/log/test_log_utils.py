from alleycat import log
from alleycat.log import ConsoleLogger, LoggingSupport


def test_get_logger_name():
    assert log.get_logger_name(LoggingSupport) == "alleycat.log.LoggingSupport"
    assert log.get_logger_name(LoggingSupport, drop_last_path=True) == "alleycat.log.LoggingSupport"
    assert log.get_logger_name(LoggingSupport, drop_last_path=False) == "alleycat.log.support.LoggingSupport"

    logger = ConsoleLogger()

    assert log.get_logger_name(logger) == "alleycat.log.ConsoleLogger"
    assert log.get_logger_name(logger, drop_last_path=True) == "alleycat.log.ConsoleLogger"
    assert log.get_logger_name(logger, drop_last_path=False) == "alleycat.log.console.ConsoleLogger"
