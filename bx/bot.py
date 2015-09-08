"""
The Bot class for handling a single IRC server.
"""

import logging

from . import irc
from .event import Event
from .user import User
from .windows import Channel, Query


class Bot:
    def __init__(self, app, name, config):
        self.app = app
        self.name = name
        self.config = config

        self.logger = logging.getLogger(__name__)
        self.irc = irc.IRCClient()

        # Event handlers (callbacks that are called with each event that occurs)
        self.event_handlers = []

        # Windows for channels and queries
        self.windows = []
        # Users
        self.users = []

    def init(self):
        self.irc.init()
        self.setup_client()

    def start(self):
        self.irc.connect()

    def stop(self):
        pass

    def mainloop(self):
        if self.irc.is_running():
            self.irc.maintain()

    def setup_client(self):
        self.irc.add_event_handler(self.on_event)
        self.irc.set_host(self.config["host"])
        self.irc.set_port(self.config["port"])
        self.irc.set_nick(self.config["nick"])
        self.irc.set_ident(self.config["ident"])
        self.irc.set_realname(self.config["realname"])

    def on_event(self, name, args):
        event = Event(self)
        event._parse_from_irc_event(name, args)
        if name == "on_irc_ready":
            self.auto_join()
        self.logger.debug("self.windows: {}".format(self.windows))
        self.logger.debug("self.users: {}".format(self.users))

    def add_event_handler(self, callback):
        self.event_handlers.append(callback)

    def auto_join(self):
        self.irc.join_channels(self.config["channels"].keys())

    def create_user(self, nick):
        if self.get_user(nick):
            self.logger.warning("Trying to create an existsing user!")
            return False
        user = User(self, nick)
        self.users.append(user)
        return user

    def create_window(self, name):
        if self.get_window(name):
            self.logger.warning("Trying to create an existsing window!")
            return False
        if self.irc.is_channel_name(name):
            window = Channel(self, name)
        else:
            window = Query(self, name)
        self.windows.append(window)
        return window

    def get_user(self, name):
        for user in self.users:
            if user.get_name() == name:
                return user
        return False

    def get_window(self, name):
        for window in self.windows:
            if window.get_name() == name:
                return window
        return False
