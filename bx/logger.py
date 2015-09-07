"""
Basic logging handler.
"""
import logging


class LoggingHandler(logging.Handler):
    def __init__(self):
        logging.Handler.__init__(self)
        self.messages = []

    def emit(self, record):
        msg = self.format(record)
        print(msg)

    def close(self):
        logging.Handler.close(self)
