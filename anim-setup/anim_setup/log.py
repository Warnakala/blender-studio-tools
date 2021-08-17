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
        logger = logging.getLogger(name)
        return logger
