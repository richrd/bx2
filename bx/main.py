"""
The main class for the IRC bot.
"""


import os
import logging

from .config import Config

__version__ = "0.0.1"


class App:
    def __init__(self):
        self.debugging = 1
        self.running = 0
        self.app_path = os.path.dirname(os.path.realpath(__file__))
        self.config = Config(self)
        self.servers = {}

    def init(self):
        # Initialize logging
        logging.basicConfig(level=logging.NOTSET)
        self.logger = logging.getLogger()
        self.logger.info("Starting BX...")

        self.config.set_config_dir(os.path.join(self.app_path, "config"))
        if not self.config.init():
            self.logger.error("Failed to initialize configuration.")
            return False

        self.config.load()
        self.logger.debug("self.config.defaults: {}".format(self.config.defaults))
        self.logger.debug("self.config.servers: {}".format(self.config.servers))
        self.logger.debug("self.config.accounts: {}".format(self.config.accounts))
        return True

    def run(self):
        self.running = 1


def main():
    app = App()
    if not app.init():
        app.logger.error("App initialization failed!")
        return False
    app.run()

if __name__ == "__main__":
    main()
