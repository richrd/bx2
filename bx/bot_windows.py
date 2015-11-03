
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

    def send(self, msg):
        self.privmsg(msg)

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

    def has_user(self, user):
        return user in self.users.keys()

    def get_users(self):
        return self.users.keys()

    def add_user(self, user, mode=None):
        if isinstance(user, str):
            self.logger.error("Trying to call add_user with a nick instead of a user instance!")
            return False
        if user not in self.users.keys():
            user_data = {"modes": []}
            if mode:
                user_data["modes"].append(mode)
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
        self.logger.warning("Trying to remove non-existing user from channel!")
        return False

    def clear_users(self):
        self.users = {}

    def on_event(self, event):
        Window.on_event(self, event)
        if event.name == "on_quit":
            self.remove_user(event.user)
        if event.name == "on_disconnect":
            # Clear all users on disconnect (cant do bookkeeping)
            self.clear_users()
        # Event that requires the current channel
        if event.window == self:
            if event.name == "on_channel_join":
                self.add_user(event.user)
            elif event.name == "on_channel_part":
                self.remove_user(event.user)
            elif event.name == "on_channel_kick":
                self.remove_user(event.user)
            elif event.name == "on_channel_has_users":
                # Clear all users since this event declares them
                self.clear_users()
                for user_item in event.irc_args["users"]:
                    user = self.bot.get_user_create(user_item[0])
                    self.add_user(user, user_item[1])
            elif event.name == "on_channel_topic_is":
                self.topic = event.data
            elif event.name == "on_channel_topic_changed":
                self.topic = event.data

    def _serialize(self):
        serialized = Window._serialize(self)
        serialized["zone"] = self.zone
        serialized["modes"] = self.modes
        serialized["created"] = self.created
        serialized["topic"] = self.topic
        serialized["topic_by"] = self.topic_by
        serialized["topic_time"] = self.topic_time
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
        self.users = {}
        for user in serialized["users"]:
            self.users[self.bot.get_user(user[0]["nick"])] = user[1]


class Query(Window):
    """Window representing an IRC query (one to one chat)."""
    def __init__(self, bot, name):
        Window.__init__(self, bot, name)
        self.zone = irc_constants.ZONE_QUERY
        self.user = self.bot.get_user(name)

    def get_users(self):
        return [self.user]

    def notice(self, msg):
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
