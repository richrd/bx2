"""
The Bot class for handling a single IRC server.
"""

import __future__
import time
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
        self.running = 0

        self.default_reconnect_wait = 5
        self.reconnect_wait = 5
        self.reconnect_wait_increase = 30

        # Setup our logger with module and network name
        self.logger = logging.getLogger("{}[{}]".format(__name__, self.name))

        # Create IRC client
        self.irc = irc.IRCClient()

        # Event handlers (callbacks that are called with each event that occurs)
        self.event_handlers = []

        # Users
        self.users = []

        # Windows for channels and queries
        self.windows = []

        # Modules
        self.modules = {}

        # Force reload TODO: disable when ready for production
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
        self.running = 1
        if not self.irc.connect():
            return False

    def stop(self):
        self.running = 0
        self.irc.disconnect()

    def reconnect(self):
        # TODO: Keep mainloop running and reconnect on a flag. (Allow HTTP to run etc).
        self.logger.debug("Reconnecting in {} seconds...".format(self.reconnect_wait))
        time.sleep(self.reconnect_wait)
        self.logger.debug("Reconnecting...")
        self.irc.connect()

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
        evt = bot_event.Event(self)
        evt._parse_from_irc_event(name, args)
        self.handle_event(evt)

    def on_connected(self):
        pass

    def on_irc_ready(self):
        self.reconnect_wait = self.default_reconnect_wait  # Reset the reconnect time after successfull connect
        self.auto_join()

    def on_connect_throttled(self):
        self.logger.debug("CONNECTION THROTTLED, ADDING TIME!")
        self.reconnect_wait += self.reconnect_wait_increase

    def create_message_from_event(self, event):
        msg = bot_message.Message(event.irc_args["nick"], event.irc_args["data"], event.irc_args["target"])
        return msg

    def handle_event(self, event):
        """Handle a single event object.

        Many events are handled by windows, so we don't have to do everything here.
        """
        if event.name == "on_connected":
            self.on_connected()
        elif event.name == "on_disconnect":
            if self.running and self.config["enabled"]:
                self.reconnect()
        elif event.name == "on_connect_throttled":
            self.on_connect_throttled()
        elif event.name == "on_irc_ready":
            self.on_irc_ready()
        elif event.name in ["on_parse_nick_hostname", "on_whois_hostname"]:
            user = self.get_user(event.irc_args["nick"])
            if not user:
                user = self.create_user(event.irc_args["nick"])
            user.set_hostname(event.irc_args["hostname"])
        elif event.name == "on_nick_changed":
            user = self.get_user(event.irc_args["nick"])
            if user:
                user.set_nick(event.irc_args["new_nick"])
            else:
                self.logger.warning("Unknown user '{}' is now '{}'".format(
                    event.irc_args["nick"],
                    event.irc_args["new_nick"])
                )
        if event.name == "on_nick_changed":
            user = self.get_user(event.irc_args["nick"])
            if user:
                user.set_nick(event.irc_args["new_nick"])
            else:
                self.logger.warning("Unknown user '{}' is now '{}'".format(
                    event.irc_args["nick"], event.irc_args["new_nick"])
                )
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
            if cmd == "reboot":
                self.logger.debug("Trying to reboot bots!")
                self.app.reboot()
            if cmd == "disco":
                self.irc.disconnect()
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

    def handle_http_request(self, request, path):
        window_names = [win.get_name() for win in self.windows]
        data = "BOT:{}\n".format(self.name)
        data += "WINDOWS:{}\n".format(window_names)
        for win_name in window_names:
            data += win_name+"\n"
            win_users = self.get_window(win_name).get_users()
            data += "RAW_USERS:{}\n".format(win_users)
            data += str(win_users) + "\n"
        response = {"data": data}
        return response

    def log_current_status(self):
        return
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

    def get_user_create(self, nick):
        """Get a user instance and create it if it doesn't exist."""
        user = self.get_user(nick)
        if not user:
            user = self.create_user(nick)
        return user

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
