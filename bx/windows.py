
from . import irc_constants

class Window:
    """Window representing an IRC channel or query"""

    def __init__(self, bot, name=None):
        self.bot = bot
        self.name = name
        self.zone = None
        # Message log
        self.messages = []

    def __repr__(self):
        return "[" + self.get_name() + "]"

    def __str__(self):
        return "[" + self.get_name() + "]"

    def get_name(self):
        return self.name


class Channel(Window):
    """Window representing an IRC channel."""
    def __init__(self, bot, name=None):
        Window.__init__(self, bot, name)
        self.zone = irc_constants.ZONE_CHANNEL
        self.users = []


class Query(Window):
    """Window representing an IRC channel."""
    def __init__(self, bot, name=None):
        Window.__init__(self, bot, name)
        self.zone = irc_constants.ZONE_QUERY
        self.users = []
