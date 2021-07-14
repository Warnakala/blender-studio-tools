import logging
import sys
from typing import List, Tuple


class LoggerFactory:

    """
    Utility class to streamline logger creation
    """

    @staticmethod
    def getLogger(name=__name__):
        name = name
        """
        formatter = logging.Formatter("%(levelname)s:%(name)s: %(message)s")
        consoleHandler = logging.StreamHandler(sys.stdout)
        consoleHandler.setFormatter(formatter)
        """
        logger = logging.getLogger(name)
        """
        logger.addHandler(consoleHandler)
        logger.setLevel(logging.INFO)
        logger.propagate = False
        """
        return logger


logger = LoggerFactory.getLogger(__name__)


class LoggerLevelManager:
    logger_levels: List[Tuple[logging.Logger, int]] = []

    @classmethod
    def configure_levels(cls):
        cls.logger_levels = []
        for key in logging.Logger.manager.loggerDict:
            if key.startswith("urllib3"):
                # save logger and value
                logger = logging.getLogger(key)
                cls.logger_levels.append((logger, logger.level))

                logger.setLevel(logging.CRITICAL)
        logger.info("Configured logging Levels")

    @classmethod
    def restore_levels(cls):
        for logger, level in cls.logger_levels:
            logger.setLevel(level)
        logger.info("Restored logging Levels")
