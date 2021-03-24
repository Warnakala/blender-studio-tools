import logging 
import sys

class ZLoggerFactory():
        
    @classmethod
    def getLogger(cls, name=""): 
        name = name 
        formatter = logging.Formatter("%(levelname)s:%(name)s: %(message)s")
        consoleHandler = logging.StreamHandler(sys.stdout)
        consoleHandler.setFormatter(formatter)

        logger = logging.getLogger(name)
        logger.addHandler(consoleHandler)
        logger.setLevel(logging.INFO)
        logger.propagate = False
        return logger