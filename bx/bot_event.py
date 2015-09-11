
import time
import logging


class Event:
    """Event object represenging all events that the bots emit.

    Events contain at minimum the following attributes:
    :bot: bot that emitted the event
    :time: the unix timestamp indicating when the event occured
    :name: name of the event

    Other attributes:
    :user: the user that initiated or is associated with the
    :window: the window that the event occured in
    :irc_event: the original event object if the event source is the irc client
    :irc_args: the arguments that are specific to the
    """
    def __init__(self, bot, name=None):
        self.bot = bot
        self.time = time.time()
        self.logger = logging.getLogger(__name__)

        self.name = name
        self.user = None
        self.window = None
        self.irc_event = None
        self.irc_args = {}

    def _parse_from_irc_event(self, name, irc_args):
        """Parse IRC event data and store it."""
        self.name = name
        self.irc_args = irc_args

        # Store the correct event time if available
        if "time" in irc_args.keys():
            self.time = irc_args["time"]

        # If channel is present, try to create it
        if "channel" in irc_args.keys():
            channel = irc_args["channel"]
            win = self.bot.get_window(channel)
            if not win:
                win = self.bot.create_window(channel)
            self.window = win

        # If channel or query is present, try to create it
        if "target" in irc_args.keys():
            target = irc_args["target"]
            win = self.bot.get_window(target)
            if not win:
                win = self.bot.create_window(target)
            self.window = win

        # If nick is present, try to create the user
        if "nick" in irc_args.keys():
            nick = irc_args["nick"]
            if nick:
                user = self.bot.get_user(nick)
                if not user:
                    user = self.bot.create_user(nick)
                self.user = user
        return self