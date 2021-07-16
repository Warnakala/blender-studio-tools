import sys
import logging


class LoggerFactory:

    """
    Utility class to streamline logger creation
    """

    formatter = logging.Formatter("%(name)s: %(message)s")
    consoleHandler = logging.StreamHandler(sys.stdout)
    level = logging.INFO

    @classmethod
    def getLogger(cls, name=__name__):
        logger = logging.getLogger(name)

        # cls.consoleHandler.setFormatter(cls.formatter)
        logger.addHandler(cls.consoleHandler)
        logger.setLevel(cls.level)

        return logger
