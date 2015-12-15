"""
The main class for the IRC bot.
"""


import os
import imp
import time
import copy
import logging


from . import config

from . import bot_main
from .logger import LoggingHandler
from . import http_handler

from .lib import pyco_http

__version__ = "0.0.1"


def reload(module):
    """Recursively reload a module.

    Simple recursive module reloader that reloads any submodules specified in the modules __reload__ attribute."""

    imp.reload(module)
    if "__reload__" in dir(module):
        for m in module.__reload__:
            reload(m)
    imp.reload(module)


class App:
    def __init__(self):
        self.debugging = 1
        self.running = 0
        self.app_path = os.path.dirname(os.path.realpath(__file__))
        self.init_time = time.time()

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
        self.config = config.Config(self)
        self.bots = {}

        # HTTP Server
        self.http_server = None

        # HTTP Handler
        self.http_handler = None
        # http_handler.HTTPHandler(self)

        # Stores serialized bots that have been stopped. Used when 'rebooting' the bots.
        # The only thing that is NOT serialized is the IRCClient instances.
        self.bot_snapshots = {}

    def init(self):
        """Initialize the app."""
        if not self.setup_config():
            self.logger.error("Failed to initialize configuration.")
            return False
        self.setup_http()
        return True

    def setup_config(self):
        self.config = config.Config(self)
        self.config.set_config_dir(os.path.join(self.app_path, "config"))
        if not self.config.init():
            return False
        self.config.load()
        return True

    def setup_http(self):
        self.http_handler = http_handler.HTTPHandler(self)
        self.http_server = pyco_http.PycoHTTP()
        self.http_server.set_default_header("content-type", "text/plain")
        self.http_server.set_port(self.config.get_item("http")["port"])
        self.http_server.set_handler(self.handle_http_request)
        if self.running:
            self.http_server.start()

    def run(self):
        """Run the app.

        Creates and runs all bots.
        """
        self.running = 1
        self.create_bots()
        self.start_bots()
        try:
            self.http_server.start()
        except:
            self.logger.error("Starting HTTP Server Failed!")
        self.mainloop()

    def create_bots(self):
        """Create bots for each server in config."""
        servers = self.config.get_servers()
        for server_name in servers.keys():
            server_config = servers[server_name]
            self.create_bot(server_name, server_config)

    def create_bot(self, name, config):
        """Create a single bot with a name and config."""
        irc_bot = bot_main.Bot(self, name, config)
        irc_bot.init()
        self.bots[name] = irc_bot
        return irc_bot

    def start_bots(self):
        """Start all bots."""
        for bot in self.bots.values():
            if bot.config["enabled"]:
                bot.start()

    def mainloop(self):
        """Run mainloops for all bots."""
        while self.running:
            for bot in self.bots.values():
                bot.mainloop()
            # FIXME: This has performance issues. Checking for connections wastes time :(
            if self.http_server:
                if self.http_server.running:
                    try:
                        self.http_server.serve()
                    except:
                        self.logger.exception("Failed to serve HTTP!")
            time.sleep(0.001)

    def reboot(self):
        """Stores a snapshot of all bots, shuts down them down and reloads them with the snapshots."""
        self.logger.debug("Rebooting bots!")
        try:
            # HTTP
            self.http_server = None
            self.http_handler = None
            reload(pyco_http)
            reload(http_handler)
            self.setup_http()
            # Serialize
            self._serialize()
            # Config
            self.config = None
            reload(config)
            self.setup_config()
            # Reload the bot and its submodules
            reload(bot_main)
            # Unserialize
            self._unserialize()
            return True
        except:
            # Try to unserialize bots anyway
            self._unserialize()
            self.logger.exception("Reboot failed!")
            return False

    def handle_http_request(self, request):
        """Handle a HTTP request object from the HTTP server."""
        return self.http_handler.handle_request(request)

    def _serialize(self):
        """Serialize all bots."""
        for bot_name in self.bots.keys():
            bot_data = self.bots[bot_name]._serialize()
            self.bot_snapshots[bot_name] = copy.copy(bot_data)
        for bot_name in self.bot_snapshots.keys():
            del self.bots[bot_name]
        self.http_handler = None

    def _unserialize(self):
        """Unserialize all bots."""
        for bot_name in self.bot_snapshots.keys():
            self._unserialize_bot(bot_name)
        self.http_handler = http_handler.HTTPHandler(self)

    def _unserialize_bot(self, bot_name):
        """Unserialize a single bot."""
        config = self.config.get_servers()[bot_name]
        irc_bot = bot_main.Bot(self, bot_name, config)
        irc_bot.init()
        irc_bot.setup_client()
        irc_bot._unserialize(self.bot_snapshots[bot_name])
        irc_bot.setup_events()
        self.bots[bot_name] = irc_bot


def main():
    """Initialize the app and run it."""
    app = App()
    if not app.init():
        app.logger.error("App initialization failed!")
        return False
    app.run()

if __name__ == "__main__":
    main()
