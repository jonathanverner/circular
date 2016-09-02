"""
    Provides the Logger class for logging messages.

    Typical use is as follows:

    ```

        from circular.utils.logger import Logger
        logger = Logger(__name__)

        msg = 'warning'
        logger.debug("A debug message")
        logger.warn("A warning message:", msg)
        try:
            raise Exception("Test")
        except Exception as ex:
            logger.exception(ex)

    ```

"""
from time import time

from browser import console


class Logger:
    """
        The logger class providing log methods for varying severity levels.
        The optional :param:`level` argument can be set to a number and
        only messages of >= severity will be logged. The log messages
        are prefixed with a timestamp and the prefix given as the :param:`prefix`
        parameter to the constructor.

    """
    SEVERITY_DEBUG = 0
    SEVERITY_LOG = 1
    SEVERITY_INFO = 2
    SEVERITY_WARN = 3
    SEVERITY_ERROR = 4
    SEVERITY_CRITICAL = 5

    global_level = 0

    def __init__(self, prefix, level=None):
        """
            :param:`prefix` all messages will be prefixed with this prefix
            :param:`level`  only messages >= this level will be printed
        """
        self.prefix = prefix
        self.level = level

    def debug(self, *args):
        self.do_log(*args, severity=Logger.SEVERITY_DEBUG)

    def log(self, *args):
        self.do_log(*args, severity=Logger.SEVERITY_LOG)

    def info(self, *args):
        self.do_log(*args, severity=Logger.SEVERITY_INFO)

    def warn(self, *args):
        self.do_log(*args, severity=Logger.SEVERITY_WARN)

    def error(self, *args):
        self.do_log(*args, severity=Logger.SEVERITY_ERROR)

    def critical(self, *args):
        self.do_log(*args, severity=Logger.SEVERITY_CRITICAL)

    def exception(self, ex):
        # pylint: disable=bare-except
        try:
            msg = '{0.info}\n{0.__name__}: {0.args[0]}'.format(ex)
            self.critical(msg)
        except:
            self.critical("Exception. Additionally, the exception cannot be printed.", ex)


    def do_log(self, *args, severity=0):
        if (self.level is None and severity >= Logger.global_level) or (severity >= self.level):
            self._print_log(*args)

    def _print_log(self, *args):
        console.log(str(time()) + ":" + self.prefix + ":", *args)
