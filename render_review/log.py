import logging


class LoggerFactory:

    """
    Utility class to streamline logger creation
    """

    @staticmethod
    def getLogger(name=__name__):
        logger = logging.getLogger(name)
        return logger
