
import time


class User:
    """User object

    Represents a user the bot is aware of.

    """
    def __init__(self, bot, nick=""):
        self.bot = bot
        self.nick = nick
        self.hostname = ""
        self.ident = ""

        self.online = 1
        self.created = time.time()

        self.first_seen_time = time.time()
        self.quit_time = None
        self.quit_reason = None

        self.last_active = None
        self.last_command = None

        self.account = False     # If False the user hasn't logged in

        # Listen to all bot events
        self.bot.add_event_handler(self.on_event)

    def __repr__(self):
        return "<{} / {}>".format(self.nick, self.hostname)

    def __str__(self):
        return "<{} / {}>".format(self.nick, self.hostname)

    def get_nick(self):
        return self.nick

    def set_nick(self, nick):
        self.nick = nick

    def set_hostname(self, hostname):
        self.hostname = hostname

    def on_event(self, event):
        pass

    #
    # IRC Actions
    #

    def privmsg(self, msg):
        self.bot.irc.privmsg(self.get_nick(), msg)

    #
    # Serialization
    #

    def _serialize(self):
        serialized = {
            "nick": self.nick,
            "hostname": self.hostname,
            "ident": self.ident,
            "online": self.online,
            "created": self.created,
            "first_seen_time": self.first_seen_time,
            "quit_time": self.quit_time,
            "quit_reason": self.quit_reason,
            "last_active": self.last_active,
            "last_command": self.last_command,
            "account": self.account,
        }
        return serialized

    def _unserialize(self, serialized):
        self.nick = serialized["nick"]
        self.hostname = serialized["hostname"]
        self.ident = serialized["ident"]
        self.online = serialized["online"]
        self.created = serialized["created"]
        self.first_seen_time = serialized["first_seen_time"]
        self.quit_time = serialized["quit_time"]
        self.quit_reason = serialized["quit_reason"]
        self.last_active = serialized["last_active"]
        self.last_command = serialized["last_command"]
        self.account = serialized["account"]
