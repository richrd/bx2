"""
The Bot class for handling a single IRC server.
"""

import __future__
import os
import time
import logging

from . import irc
from . import irc_constants
from . import bot_event
from . import bot_user
from . import bot_windows
from . import bot_message
from . import bot_module
from . import module_loader

# Modules that require reloading
__reload__ = [irc, irc_constants, bot_event, bot_user, bot_windows, bot_message, module_loader, bot_module]


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

        # Module Loader
        self.module_loader = module_loader.ModuleLoader()
        self.module_loader.set_module_path(os.path.join(self.app.app_path, "modules"))

        # Event handlers (callbacks that are called with each event that occurs)
        self.event_handlers = []

        # Users
        self.users = []

        # Windows for channels and queries
        self.windows = []

        # Modules
        self.modules = {}

        # Force reload FIXME: disable when ready for production
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
            return irc.IRCClient.parse_received_line(self.irc, line)

    def init(self):
        """Initialize the bot.

        Sets up the IRC client, events and loads modules.
        """
        self._init()
        self.irc.init()
        self.setup_client()
        self.setup_events()
        self.load_modules()

    def start(self):
        """Start the bot and connects."""
        self.running = 1
        if not self.irc.connect():
            return False

    def stop(self):
        """Stop running the bot."""
        self.running = 0
        self.irc.disconnect()

    def reconnect(self):
        """Reconnect to the irc server after a disconnect."""
        # TODO: Keep mainloop running and reconnect on a flag. (Allow HTTP to run etc).
        self.logger.debug("Reconnecting in {} seconds...".format(self.reconnect_wait))
        time.sleep(self.reconnect_wait)
        self.logger.debug("Reconnecting...")
        self.irc.connect()

    def mainloop(self):
        """Run an iteration of the bot mainloop."""
        if self.irc.is_running():
            self.irc.maintain()

    def setup_client(self, use_config=True):
        """Set up the IRC client settings."""
        self.irc.set_host(self.config["host"])
        self.irc.set_port(self.config["port"])
        self.irc.set_ssl(self.config["ssl"])
        self.irc.set_nick(self.config["nick"])
        self.irc.set_ident(self.config["ident"])
        self.irc.set_realname(self.config["realname"])

    def setup_events(self):
        """Setup event handlers."""
        self.irc.add_event_handler(self.on_irc_event)

    def load_modules(self):
        """Load bot modules."""
        mod_names = self.module_loader.get_available_modules()
        for name in mod_names:
            module = self.module_loader.load_module(name)
            if not module:
                self.logger.warning("Failed to load module '{}'".format(name))
                continue
            try:
                cls = module.Module
                inst = cls(self)
                options = cls.declare()
                self.set_module_options(name, inst, options)
                self.modules[name] = inst
            except:
                self.logger.exception("Failed to load module '{}'!".format(name))

    def set_running(self, running):
        self.running = running

    def set_module_options(self, name, instance, options):
        """Set module options on a module instance.

        :param name: Module name.
        :param instance: Module instance.
        :param options: Option dictionary.
        """
        instance.set_name(name)
        if "zone" in options.keys():
            instance.set_zone(options["zone"])
        if "level" in options.keys():
            instance.set_level(options["level"])
        if "throttle_time" in options.keys():
            instance.set_throttle_time(options["throttle_time"])
        if "essential" in options.keys():
            instance.set_essential(options["essential"])

    def get_name(self):
        """Return the bots name (servers name in config)."""
        return self.name

    def get_nick(self):
        """Return the bots current nick."""
        return self.irc.get_nick()

    def get_connected(self):
        return self.irc.get_irc_connected()

    def get_server_channels(self):
        """Return channel names from server configuration."""
        return self.config["channels"].keys()

    def get_server_channel_modes(self, channel):
        if channel not in self.get_server_channels():
            return ""
        if "modes" in self.config["channels"][channel].keys():
            modes = self.config["channels"][channel]["modes"]
            return list(modes)
        return ""

    def get_bot_user(self):
        """Return the user object of the bot."""
        try:
            return self.get_user(self.get_nick())
        except:
            self.logger.exception("Bot user not found in user list!")
        return False

    def get_user(self, nick):
        """Return a user by nick."""
        for user in self.users:
            if user.get_nick().lower() == nick.lower():
                return user
        return False

    def get_users(self):
        """Return list of bot users."""
        return self.users

    def get_user_create(self, nick):
        """Get a user instance and create it if it doesn't exist."""
        user = self.get_user(nick)
        if not user:
            user = self.create_user(nick)
        return user

    def get_windows(self):
        """Return list of bot windows."""
        return self.windows

    def get_window(self, name):
        """Return a window by name (channel or query)."""
        for window in self.windows:
            if window.get_name() == name:
                return window
        return False

    def get_module(self, name):
        """Return a module instance by its name."""
        if name in self.modules.keys():
            return self.modules[name]
        return False

    def get_modules(self):
        """Return list of all module instances."""
        return self.modules.values()

    def on_irc_event(self, name, args):
        """Receive and handle an event from the IRC client."""
        evt = bot_event.Event(self)
        evt._parse_from_irc_event(name, args)
        self.handle_event(evt)

    def on_connected(self):
        self.logger.info("Connected!")
        # Create the bot user if it doesn't exist
        # Needs to be done when no channels are joined
        self.create_user(self.irc.get_nick())

    def on_disconnect(self):
        self.logger.debug("on_disconnect: running:{} enabled:{}".format(self.running, self.config["enabled"]))
        # Set users offline
        for user in self.get_users():
            user.set_online(0)
            user.deauthenticate()
            if user == self.get_bot_user():
                # Remove bot user, might join with different nick
                self.users.remove(user)
        if self.running and self.config["enabled"]:
            self.reconnect()

    def on_irc_ready(self):
        self.reconnect_wait = self.default_reconnect_wait  # Reset the reconnect time after successfull connect
        self.auto_send()
        self.auto_join()

    def on_connect_throttled(self):
        self.logger.debug("Connection throttled, increasing reconnect delay!")
        self.reconnect_wait += self.reconnect_wait_increase

    def on_privmsg(self, event):
        cmd_str = self.get_message_command(event.data)
        if cmd_str:
            parts = cmd_str.split(" ")
            cmd = parts[0].lower()
            args = " ".join(parts[1:])
            self.run_command(cmd, args, event)

    def get_message_command(self, msg):
        nick = self.get_nick()
        # Check nick command
        if len(msg) > len(nick)+1:
            if msg.lower()[:len(nick)] == nick.lower():
                if msg[len(nick)] in [",", ":", " "]:
                    return msg[len(nick)+1:].strip()
        # Check prefix command
        prefix = self.config["cmd_prefix"]
        if len(msg) < len(prefix)+1:
            return False
        if msg[:len(prefix)] == prefix:
            return msg[len(prefix):]
        return False

    def run_command(self, command, args, event, caller=None):
        command = self.get_command_by_alias(command)
        if command in self.modules.keys():
            module = self.modules[command]
            # Block non essential modules in stealth mode
            if not module.get_essential():
                if self.config.get_stealth():
                    if not event.user.is_authed():
                        return False
            module._execute(event.window, event.user, args, caller)

    def get_command_by_alias(self, alias):
        if alias in self.config["aliases"]:
            return self.config["aliases"][alias]
        return alias

    def create_message_from_event(self, event):
        msg = bot_message.Message(event.irc_args["nick"], event.irc_args["data"], event.irc_args["target"])
        return msg

    def create_event(self, name=None):
        return bot_event.Event(self, name)

    def handle_event(self, event):
        """Handle a single event object.

        Many events are handled by windows, so we don't have to do everything here.
        """
        if event.name == "irc_connected":
            self.on_connected()
        elif event.name == "irc_disconnect":
            self.on_disconnect()
        elif event.name == "irc_connect_throttled":
            self.on_connect_throttled()
        elif event.name == "irc_ready":
            self.on_irc_ready()
        elif event.name == "irc_i_joined":
            # Aquire channel modes. Ensures the bot knows the modes of channels it joins.
            event.window.ask_modes()
        elif event.name == "irc_privmsg":
            self.on_privmsg(event)
        elif event.name in ["irc_parse_nick_hostname", "irc_whois_hostname"]:
            user = self.get_user(event.irc_args["nick"])
            if not user:
                user = self.create_user(event.irc_args["nick"])
            user.set_hostname(event.irc_args["hostname"])
        if event.name == "irc_nick_changed":
            if not event.user:
                self.logger.warning("Unknown user '{}' is now '{}'".format(
                    event.irc_args["nick"], event.irc_args["new_nick"])
                )
            else:
                old_user = self.get_user(event.irc_args["new_nick"])
                if old_user:
                    # This isn't possible if the new nick
                    # exists so we just remove the old user
                    self.remove_user(old_user)
                event.user.set_nick(event.irc_args["new_nick"])
        self.trigger_event_handlers(event)

    def add_event_handler(self, callback):
        """Add a callback for receiving events."""
        self.event_handlers.append(callback)

    def trigger_event_handlers(self, event):
        """Trigger all event handlers after bot event handling is done."""
        # Trigger explicitly registered event handlers
        for handler in self.event_handlers:
            handler(event)
        # Trigger event on all modules
        try:
            for module in self.get_modules():
                module.on_event(event)
        except Exception:
            self.logger.exception("Failed to trigger module events!")

    def trigger_event(self, event):
        self.trigger_event_handlers(event)

    def auto_send(self):
        """Send auto_send contents specified in server config."""
        for line in self.config["auto_send"]:
            self.irc.send(line)

    def auto_join(self):
        """Join channels specified in server config."""
        self.irc.join_channels(self.config["channels"].keys())

    def create_user(self, nick):
        """Create a user from nick."""
        if self.get_user(nick):
            self.logger.warning("Trying to create an existsing user!")
            return False
        user = bot_user.User(self, nick)
        self.users.append(user)
        return user

    def remove_user(self, user):
        """Remove a user by nick or object."""
        if isinstance(user, str):
            user = self.get_user(user)
        if user:
            del self.users[self.users.index(user)]
            return True
        return False

    def create_window(self, name):
        """Create a window from nick or channel name."""
        self.logger.warning("Creating win:{}".format(name))
        if self.get_window(name):
            self.logger.warning("Trying to create an existsing window!")
            return False
        if self.irc.is_channel_name(name):
            window = bot_windows.Channel(self, name)
        else:
            window = bot_windows.Query(self, name)
        self.windows.append(window)
        return window

    def remove_window(self, win):
        """Remove a window. Takes a name or a window object."""
        self.logger.debug("Removing window {}...".format(win))
        if isinstance(win, str):
            win = self.get_window(win)
        if not win:
            self.logger.warning("Trying to remove window that doesn't exist!")
            return False
        # del self.windows[self.windows.index(win)]
        self.windows.remove(win)
        return True

    def handle_http_request(self, request, path):
        return

    def _serialize(self):
        serialized = {
            "name": self.name,
            "running": self.running,
            "irc": self.irc._serialize(),
            "users": [user._serialize() for user in self.users],
            "windows": [window._serialize() for window in self.windows],
        }
        self.windows = []
        return serialized

    def _unserialize(self, serialized):
        self.name = serialized["name"]
        self.running = serialized["running"]

        self.irc = irc.IRCClient()
        self.irc._unserialize(serialized["irc"])
        self.users = []
        for item in serialized["users"]:
            user = bot_user.User(self, item["nick"])
            user._unserialize(item)
            self.users.append(user)

        self.windows = []
        for item in serialized["windows"]:
            if item["zone"] == irc_constants.ZONE_QUERY:
                window = bot_windows.Query(self, item["name"])
            else:
                window = bot_windows.Channel(self, item["name"])
            window._unserialize(item)
            self.windows.append(window)

        self._init()
