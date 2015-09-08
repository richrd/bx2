
import time


class User:
    """User object

    Represents a user the bot is aware of.

    """
    def __init__(self, bot, nick=""):
        self.bot = bot
        self.nick = ""
        self.hostname = ""
        self.ident = ""

        self.online = 1
        self.created = time.time()

        self.first_seen_time = None
        self.quit_time = None
        self.quit_reason = None

        self.last_active = None
        self.last_command = None

        self.account = False     # If False the user hasn't logged in

        self.bot.add_event_handler(self.on_event)

    def __repr__(self):
        return "<" + self.nick + ">"

    def __str__(self):
        return "<" + self.nick + ">"

    def get_nick(self):
        return self.nick

    def on_event(self, event):
        pass