"""
The Bot class for handling a single IRC server.
"""

import logging

from . import irc
from . import irc_constants
from . import bot_event
from . import bot_user
from . import bot_windows
from . import bot_message

# Modules that require reloading
__reload__ = [irc, irc_constants, bot_event, bot_user, bot_windows, bot_message]


class Bot:
    def __init__(self, app, name, config):
        self.app = app
        self.name = name
        self.config = config

        self.logger = logging.getLogger(__name__)
        self.irc = irc.IRCClient()

        # Event handlers (callbacks that are called with each event that occurs)
        self.event_handlers = []

        # Users
        self.users = []
        # Windows for channels and queries
        self.windows = []

        # Force reload
        self.reboot_identifier = "forcebootbx"

    def _init(self):
        self.irc.parse_received_line = self._intercept_line

    def _intercept_line(self, line):
        """Intercepts all lines received from the IRC client.

        If the line contains the reboot identifier string the bots are rebooted.
        """
        if line.find(self.reboot_identifier) != -1:
            self.app.reboot()
        else:
            irc.IRCClient.parse_received_line(self.irc, line)

    def init(self):
        self._init()
        self.irc.init()
        self.setup_client()
        self.setup_events()

    def start(self):
        self.irc.connect()

    def stop(self):
        pass

    def mainloop(self):
        if self.irc.is_running():
            self.irc.maintain()

    def setup_client(self, use_config=True):
        self.irc.set_host(self.config["host"])
        self.irc.set_port(self.config["port"])
        self.irc.set_nick(self.config["nick"])
        self.irc.set_ident(self.config["ident"])
        self.irc.set_realname(self.config["realname"])

    def setup_events(self):
        self.irc.add_event_handler(self.on_irc_event)

    def on_irc_event(self, name, args):
        """Receive and handle an event from the IRC client."""
        self.logger.debug("self.event_handlers: {}".format(self.event_handlers))
        evt = bot_event.Event(self)
        evt._parse_from_irc_event(name, args)
        self.handle_event(evt)

    def create_message_from_event(self, event):
        msg = bot_message.Message(event.irc_args["nick"], event.irc_args["data"], event.irc_args["target"])
        return msg

    def handle_event(self, event):
        """Handle a single event object.

        Many events are handled by windows, so we don't have to do everything here.
        """
        if event.name == "on_irc_ready":
            self.auto_join()
        if event.name in ["on_parse_nick_hostname", "on_whois_hostname"]:
            user = self.get_user(event.irc_args["nick"])
            if not user:
                user = self.create_user(event.irc_args["nick"])
            user.set_hostname(event.irc_args["hostname"])
        if event.name == "on_nick_changed":
            user = self.get_user(event.irc_args["nick"])
            if user:
                user.set_nick(event.irc_args["new_nick"])
            else:
                self.logger.warning("Unknown user '{}' is now '{}'".format(event.irc_args["nick"], event.irc_args["new_nick"]))
        if event.name == "on_nick_changed":
            user = self.get_user(event.irc_args["nick"])
            if user:
                user.set_nick(event.irc_args["new_nick"])
            else:
                self.logger.warning("Unknown user '{}' is now '{}'".format(event.irc_args["nick"], event.irc_args["new_nick"]))
        self.trigger_event_handlers(event)
        self.handle_debugging_event(event)
        self.log_current_status()

    def handle_debugging_event(self, event):
        if event.name == "on_privmsg":
            if event.user.get_nick() == "wavi":
                self.handle_debugging_msg(event)

    def handle_debugging_msg(self, event):
        self.logger.debug("handle_debugging_msg")
        debug_chr = "!"

        msg = self.create_message_from_event(event)
        text = msg.get_text()
        parts = text.split(" ")
        cmd = parts[0]
        self.logger.debug("handle_debugging_msg {}".format(parts))
        self.logger.debug("cmd: {}".format(cmd))

        if len(cmd) > 1:
            if cmd[0] != debug_chr:
                return False
            cmd = cmd[1:]

        if len(parts) == 1:
            pass
            if cmd == "reboot":
                self.logger.debug("Trying to reboot bots!")
                self.app.reboot()
        else:
            if cmd in ["exec", "eval"]:
                operation = eval
                if cmd == "exec":
                    operation = exec
                result = "Run code: {} failed, sry.".format(cmd)
                try:
                    result = operation(" ".join(parts[1:]))
                except:
                    pass
                event.window.privmsg(result)

    def log_current_status(self):
        self.logger.debug("self.windows: {}".format(self.windows))
        self.logger.debug("self.users: {}".format(self.users))

    def add_event_handler(self, callback):
        self.event_handlers.append(callback)

    def trigger_event_handlers(self, event):
        for handler in self.event_handlers:
            handler(event)

    def auto_join(self):
        self.irc.join_channels(self.config["channels"].keys())

    def create_user(self, nick):
        if self.get_user(nick):
            self.logger.warning("Trying to create an existsing user!")
            return False
        user = bot_user.User(self, nick)
        self.users.append(user)
        return user

    def create_window(self, name):
        if self.get_window(name):
            self.logger.warning("Trying to create an existsing window!")
            return False
        if self.irc.is_channel_name(name):
            window = bot_windows.Channel(self, name)
        else:
            window = bot_windows.Query(self, name)
        self.windows.append(window)
        return window

    def get_user(self, nick):
        for user in self.users:
            if user.get_nick() == nick:
                return user
        return False

    def get_window(self, name):
        for window in self.windows:
            if window.get_name() == name:
                return window
        return False

    def _serialize(self):
        serialized = {
            "name": self.name,
            "irc": self.irc._serialize(),
            "users": [user._serialize() for user in self.users],
            "windows": [window._serialize() for window in self.windows],
        }
        return serialized

    def _unserialize(self, serialized):
        self.name = serialized["name"]

        self.irc = irc.IRCClient()
        self.irc._unserialize(serialized["irc"])

        self.users = []
        for item in serialized["users"]:
            user = bot_user.User(self, item["nick"])
            user._unserialize(item)
            self.users.append(user)

        self.windows = []
        for item in serialized["windows"]:
            window = bot_windows.Channel(self, item["name"])
            window._unserialize(item)
            self.windows.append(window)

        self._init()
