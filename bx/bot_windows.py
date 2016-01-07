
import time
import logging

from . import irc_constants
from . import bot_message

__reload__ = [irc_constants, bot_message]


class LogRecord:
    """A window log record for representing messages, joins, parts etc."""
    def __init__(self):
        self.name = ""
        self.time = time.time()
        self.data = ""
        self.nick = ""
        self.event = None
        self.name_map = {
            "irc_privmsg": "privmsg",
            "irc_channel_join": "join",
            "irc_channel_part": "part",
            "irc_quit": "quit",
        }

    def set_name(self, name):
        self.name = name

    def set_time(self, time):
        self.time = time

    def set_data(self, data):
        self.data = data

    def set_nick(self, nick):
        self.nick = nick

    def get_name(self):
        return self.name

    def get_time(self):
        return self.time

    def get_data(self):
        return self.data

    def get_nick(self):
        return self.nick

    def parse_from_event(self, event):
        """Initialize the record by parsing event data."""
        if event.name not in self.name_map:
            return False
        self.name = self.name_map[event.name]
        self.event = event
        self.time = event.time
        if event.user:
            self.nick = event.user.get_nick()
        if event.data:
            self.data = event.data
        return self

    def __str__(self):
        return "{} {} {} {}".format(self.time, self.name, self.nick, self.data)

    def _serialize(self):
        serialized = {}
        serialized["name"] = self.name
        serialized["time"] = self.time
        serialized["data"] = self.data
        serialized["nick"] = self.nick
        return serialized

    def _unserialize(self, serialized):
        self.name = serialized["name"]
        self.time = serialized["time"]
        self.data = serialized["data"]
        self.nick = serialized["nick"]


class Window:
    """Window representing an IRC channel or query"""
    def __init__(self, bot, name=None):
        self.bot = bot
        self.name = name
        self.zone = None

        self.logger = logging.getLogger("{}[{}].{}".format(__name__, bot.get_name(), name))

        # Message log
        self.log = []

        # Subscribe to all events
        self.bot.add_event_handler(self.on_event)

    def __repr__(self):
        return "[{}]".format(self.get_name())

    def __str__(self):
        return "[{}]".format(self.get_name())

    def get_name(self):
        """Get window name. Returns either the channel name or query nick."""
        if self.zone == irc_constants.ZONE_QUERY:
            # FIXME: safety debugging check. Fix asap.
            if self.user:
                return self.user.get_nick()
            else:
                self.logger.error("Query has no user, this shouldn't happen!")
                return ""
        return self.name

    def get_log(self):
        """Get window log records."""
        return self.log

    def get_log_limit(self):
        return self.bot.config["log_limit"]

    def is_channel(self):
        """Check if window is a channel."""
        return self.zone == irc_constants.ZONE_CHANNEL

    def is_query(self):
        """Check if window is a query."""
        return self.zone == irc_constants.ZONE_QUERY

    def is_trusted(self, user):
        """Check if user is trusted in this window."""
        return False

    def on_privmsg(self, event):
        self.logger.info("{} {}".format(event.user, event.data))
        self.add_log_record_from_event(event)

    def on_event(self, event):
        if event.name == "irc_privmsg":
            if event.window == self:
                self.on_privmsg(event)

    def add_log_record_from_event(self, event):
        while len(self.log) > self.get_log_limit():
            self.log.pop(0)
        record = LogRecord().parse_from_event(event)
        self.log.append(record)

    #
    # IRC Actions
    #

    def send(self, msg):
        """Send a message to the window."""
        self.logger.info("{} {}".format(self.bot.get_bot_user(), msg))
        self.privmsg(msg)
        record = LogRecord()
        record.set_name("privmsg")
        record.set_nick(self.bot.get_bot_user().get_nick())
        record.set_data(str(msg))
        self.log.append(record)

    def privmsg(self, msg):
        """Send a privmsg to the window."""
        self.bot.irc.privmsg(self.get_name(), msg)

    #
    # Serialization
    #

    def _serialize(self):
        serialized = {
            "name": self.name,
            "zone": self.zone,
            "log": [msg._serialize() for msg in self.log],
        }
        return serialized

    def _unserialize(self, serialized):
        self.name = serialized["name"]
        self.zone = serialized["zone"]
        for item in serialized["log"]:
            msg = LogRecord()
            msg._unserialize(item)
            self.log.append(msg)


class Query(Window):
    """Window representing an IRC query (one to one chat)."""
    def __init__(self, bot, name):
        Window.__init__(self, bot, name)
        self.zone = irc_constants.ZONE_QUERY
        self.user = self.bot.get_user(name)

    def get_users(self):
        """Get user list."""
        return [self.user]

    def is_trusted(self, user):
        # Bot owner is always trusted
        if user.get_permission_level() >= 100:
            return True
        return False

    def notice(self, msg):
        """Send a notice."""
        self.bot.irc.notice(self.get_name(), msg)

    def _serialize(self):
        serialized = Window._serialize(self)
        serialized["zone"] = self.zone
        serialized["nick"] = self.user.get_nick()
        return serialized

    def _unserialize(self, serialized):
        Window._unserialize(self, serialized)
        self.zone = serialized["zone"]
        self.user = self.bot.get_user(serialized["nick"])


class Channel(Window):
    """Window representing an IRC channel."""
    def __init__(self, bot, name=None):
        Window.__init__(self, bot, name)
        self.zone = irc_constants.ZONE_CHANNEL
        # Channel modes
        self.modes = []
        # Channel creation time
        self.created = None
        # Channel topic
        self.topic = ""
        # Channel topic author
        self.topic_by = None
        # Channel topic set time
        self.topic_time = None
        # All users on the channel
        self.users = {}
        # If we're on the channel or not
        self.joined = 0

    def get_joined(self):
        """Check if the bot is currently joined to this channel."""
        return self.joined

    def get_modes(self):
        """Get channel modes."""
        return self.modes

    def get_users(self):
        """Get list of users."""
        return list(self.users.keys())

    def get_user_modes(self, user):
        """Get modes of a user."""
        return self.users[user]["modes"]

    def is_trusted(self, user):
        self.logger.debug("Checking user: {}".format(user))
        if not user.is_authed():
            return False
        if self.get_name() in user.account.get_server_channels(self.bot.get_name()):
            return True
        return False

    def set_current_modes(self, modes):
        self.modes = modes

    def set_changed_modes(self, modes):
        target = self.add_mode
        for char in modes:
            if char == "+":
                target = self.add_mode
            elif char == "-":
                target = self.remove_mode
            else:
                target(char)

    def set_changed_user_modes(self, modes):
        for item in modes:
            user = self.bot.get_user(item[0])
            mode = item[1]
            oper = item[2]
            func = [self.remove_user_mode, self.add_user_mode][oper]
            func(user, mode)

    def add_mode(self, mode):
        if mode not in self.modes:
            self.modes.append(mode)
            return True
        return False

    def remove_mode(self, mode):
        if mode in self.modes:
            self.modes.pop(self.modes.index(mode))
            return True
        return False

    def add_user_mode(self, user, mode):
        if mode not in self.get_user_modes(user):
            self.users[user]["modes"].append(mode)

    def remove_user_mode(self, user, mode):
        if mode in self.get_user_modes(user):
            self.users[user]["modes"].pop(self.users[user]["modes"].index(mode))

    def change_topic(self, topic):
        self.bot.irc.set_channel_topic(self.get_name(), topic)

    def change_modes(self, modes, remove=False):
        chr = "+"
        if remove:
            chr = "-"
        # TODO: construct mode change string here
        self.bot.irc.set_channel_modes(self.get_name(), "{}{}".format(chr, "".join(modes)))

    def give_voice(self, users):
        if not isinstance(users, list):
            users = [users]
        nickmodes = [(user.get_nick(), "v") for user in users]
        self.bot.irc.set_channel_user_modes(self.get_name(), nickmodes)

    def give_op(self, users):
        if not isinstance(users, list):
            users = [users]
        nickmodes = [(user.get_nick(), "o") for user in users]
        self.bot.irc.set_channel_user_modes(self.get_name(), nickmodes)

    def take_voice(self, users):
        if not isinstance(users, list):
            users = [users]
        nickmodes = [(user.get_nick(), "v") for user in users]
        self.bot.irc.set_channel_user_modes(self.get_name(), nickmodes, False)

    def take_op(self, users):
        if not isinstance(users, list):
            users = [users]
        nickmodes = [(user.get_nick(), "o") for user in users]
        self.bot.irc.set_channel_user_modes(self.get_name(), nickmodes, False)

    def has_voice(self, user):
        if not self.has_user(user):
            return False
        modes = self.get_user_modes(user)
        return irc_constants.MODE_VOICE in modes

    def has_op(self, user):
        if not self.has_user(user):
            return False
        modes = self.get_user_modes(user)
        return irc_constants.MODE_OP in modes

    def has_user(self, user):
        return user in self.users.keys()

    def add_user(self, user, mode=None):
        if isinstance(user, str):
            self.logger.error("Trying to call add_user with a nick instead of a user instance!")
            return False
        if user not in self.users.keys():
            modes = []
            if mode:
                modes = [mode]
            user_data = {"modes": modes}
            self.users[user] = user_data
            return True
        self.logger.warning("Trying add existing user to channel!")
        return False

    def remove_user(self, user):
        if isinstance(user, str):
            self.logger.error("Trying to call remove_user with a nick instead of a user instance!")
            return False
        if self.has_user(user):
            del self.users[user]
            return True
        if user == self.bot.get_bot_user():
            self.logger.warning("Removing myself from empty channel (parted).")
            return False
        self.logger.warning("Trying to remove non-existing user {} from channel! ".format(user))
        return False

    def ask_modes(self):
        self.bot.irc.ask_channel_modes(self.get_name())

    def part(self):
        self.bot.irc.part(self.get_name())
        self.clear_state()

    def clear_state(self):
        self.logger.debug("Clearing window state.")
        self.users = {}
        self.modes = []
        self.joined = 0

    def clear_users(self):
        self.users = {}

    def on_event(self, event):
        Window.on_event(self, event)
        if event.name == "irc_quit":
            if self.has_user(event.user):
                self.add_log_record_from_event(event)
                self.remove_user(event.user)
        if event.name == "irc_disconnect":
            # Clear all users on disconnect (cant do bookkeeping)
            self.clear_state()
        # Event that requires the current channel
        if event.window == self:
            if event.name == "irc_i_joined":
                self.logger.info("Joined {}".format(event.window))
                self.joined = 1
            if event.name == "irc_channel_join":
                self.logger.info("{} joined.".format(event.user))
                self.add_user(event.user)
                self.add_log_record_from_event(event)
            elif event.name in ["irc_channel_part", "irc_channel_kick"]:
                if event.name != "irc_channel_kick":
                    self.add_log_record_from_event(event)
                self.remove_user(event.user)
                if event.user == self.bot.get_bot_user():
                    event.window.clear_state()
            elif event.name == "irc_channel_has_users":
                # Can't clear users, since this event occurs multiple times
                # when joining a channel with lots of users (userlist sent in chunks)
                self.logger.debug("irc_channel_has_users {}".format(event.irc_args["users"]))
                for user_item in event.irc_args["users"]:
                    user = self.bot.get_user_create(user_item[0])
                    user.set_online(1)
                    self.add_user(user, user_item[1])
            elif event.name == "irc_channel_topic_is":
                self.topic = event.data
            elif event.name == "irc_channel_topic_changed":
                self.topic = event.data
            elif event.name == "irc_channel_modes_are":
                self.set_current_modes(event.modes)
            elif event.name == "irc_channel_modes_changed":
                self.set_changed_modes(event.modes)
            elif event.name == "irc_channel_user_modes_changed":
                self.set_changed_user_modes(event.modes)

    def _serialize(self):
        self.logger.debug("Serializing window {}".format(self))
        serialized = Window._serialize(self)
        serialized["zone"] = self.zone
        serialized["modes"] = self.modes
        serialized["created"] = self.created
        serialized["topic"] = self.topic
        serialized["topic_by"] = self.topic_by
        serialized["topic_time"] = self.topic_time
        serialized["joined"] = self.joined
        serialized["users"] = []
        for user in self.users:
            serialized["users"].append([user._serialize(), self.users[user]])
        return serialized

    def _unserialize(self, serialized):
        Window._unserialize(self, serialized)
        self.zone = serialized["zone"]
        self.modes = serialized["modes"]
        self.created = serialized["created"]
        self.topic = serialized["topic"]
        self.topic_by = serialized["topic_by"]
        self.topic_time = serialized["topic_time"]
        self.joined = serialized["joined"]
        self.users = {}
        for user in serialized["users"]:
            self.users[self.bot.get_user(user[0]["nick"])] = user[1]
