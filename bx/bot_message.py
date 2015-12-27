

import time


class Message:
    """Message object

    Stores an irc message and its details.

    """
    def __init__(self, nick="", text="", dest="", user=None):
        # Creation time of the message
        self.time = time.time()
        self.nick = nick
        self.text = text
        self.dest = dest
        self.user = user

    def __str__(self):
        return "[{}] {} -> {} :{}".format(self.time, self.nick, self.dest, self.text)

    def get_text(self):
        return self.text

    def _serialize(self):
        serialized = {
            "time": self.time,
            "nick": self.nick,
            "text": self.text,
            "dest": self.dest,
        }
        return serialized

    def _unserialize(self, data):
        self.time = data["time"]
        self.nick = data["nick"]
        self.text = data["text"]
        self.dest = data["dest"]
