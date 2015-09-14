
import logging

from . import irc_constants
from . import bot_message

__reload__ = [irc_constants, bot_message]


class Window:
    """Window representing an IRC channel or query"""
    def __init__(self, bot, name=None):
        self.bot = bot
        self.name = name
        self.zone = None

        self.logger = logging.getLogger("{}.{}".format(__name__, name))

        # Message log
        self.log = []

        # Subscribe to all events
        self.bot.add_event_handler(self.on_event)

    def __repr__(self):
        return "[{}]".format(self.get_name())

    def __str__(self):
        return "[{}]".format(self.get_name())

    def get_name(self):
        # FIXME: Return correct name for channels AND queries
        if self.zone == irc_constants.ZONE_QUERY:
            return self.user.get_nick()
        return self.name

    def add_message(self, msg_obj):
        self.messages.append(msg_obj)

    def on_privmsg(self, event):
        msg = self.bot.create_message_from_event(event)
        self.log.append(msg)

    def on_event(self, event):
        if event.name == "on_privmsg":
            if event.window == self:
                self.on_privmsg(event)

    #
    # IRC Actions
    #

    def privmsg(self, msg):
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
            msg = bot_message.Message()
            msg._unserialize(item)
            self.log.append(msg)


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

    def add_user(self, user):
        if isinstance(user, str):
            self.logger.error("Trying to call add_user with a nick instead of a user instance!")
            return False
        if user not in self.users.keys():
            self.users[user] = {}
            return True
        self.logger.warning("Trying add existing user to channel!")
        return False

    def remove_user(self, user):
        if isinstance(user, str):
            self.logger.error("Trying to call remove_user with a nick instead of a user instance!")
            return False
        if user in self.users.keys():
            del self.users[user]
            return True
        self.logger.warning("Trying to remove non-existing user from channel!")
        return False

    def on_event(self, event):
        Window.on_event(self, event)
        if event.name == "on_join":
            if event.channel == self:
                self.add_user(event.user)
        elif event.name == "on_part":
            if event.channel == self:
                self.remove_user(event.user)

    def _serialize(self):
        serialized = Window._serialize(self)
        serialized["zone"] = self.zone
        serialized["modes"] = self.modes
        serialized["created"] = self.created
        serialized["topic"] = self.topic
        serialized["topic_by"] = self.topic_by
        serialized["topic_time"] = self.topic_time
        serialized["users"] = [user._serialize() for user in self.users]
        return serialized

    def _unserialize(self, serialized):
        Window._unserialize(self, serialized)
        self.zone = serialized["zone"]
        self.modes = serialized["modes"]
        self.created = serialized["created"]
        self.topic = serialized["topic"]
        self.topic_by = serialized["topic_by"]
        self.topic_time = serialized["topic_time"]
        self.users = []
        for user in serialized["users"]:
            self.users.append(self.bot.get_user(user["nick"]))


class Query(Window):
    """Window representing an IRC query (one to one chat)."""
    def __init__(self, bot, name=None):
        Window.__init__(self, bot, name)
        self.zone = irc_constants.ZONE_QUERY
        self.user = None

    def _serialize(self):
        serialized = Window._serialize(self)
        serialized["zone"] = self.zone
        serialized["user"] = self.user
        return serialized

    def _unserialize(self, serialized):
        Window._unserialize(self, serialized)
        self.zone = serialized["zone"]
        self.user = self.bot.get_user(serialized["user"]["nick"])
