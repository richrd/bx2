"""
The main class for the IRC bot.
"""


import os
import time
import logging

from .bot import Bot
from .config import Config
from .logger import LoggingHandler

__version__ = "0.0.1"


class App:
    def __init__(self):
        self.debugging = 1
        self.running = 0
        self.app_path = os.path.dirname(os.path.realpath(__file__))

        # Initialize logging
        logging.basicConfig(level=logging.NOTSET)
        self.logger = logging.getLogger()
        self.logger.handlers = []
        self.logger_handler = LoggingHandler()
        self.logger_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        self.logger_handler.setFormatter(self.logger_formatter)
        self.logger.addHandler(self.logger_handler)
        self.logger.info("Starting BX...")

        # Initialize config
        self.config = Config(self)
        self.bots = {}

    def init(self):
        self.config.set_config_dir(os.path.join(self.app_path, "config"))
        if not self.config.init():
            self.logger.error("Failed to initialize configuration.")
            return False
        self.config.load()
        return True

    def run(self):
        self.running = 1
        self.create_bots()
        self.start_bots()
        self.mainloop()

    def create_bots(self):
        servers = self.config.get_servers()
        for server_name in servers.keys():
            server_config = servers[server_name]
            self.create_bot(server_name, server_config)
        self.logger.debug("Bots")
        self.logger.debug(self.bots)

    def create_bot(self, name, config):
        bot = Bot(self, name, config)
        bot.init()
        self.bots[name] = bot

    def start_bots(self):
        [bot.start() for bot in self.bots.values()]

    def mainloop(self):
        while self.running:
            [bot.mainloop() for bot in self.bots.values()]
            time.sleep(0.01)


def main():
    app = App()
    if not app.init():
        app.logger.error("App initialization failed!")
        return False
    app.run()

if __name__ == "__main__":
    main()
