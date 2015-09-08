

import time


class Message:
    """Message object

    Stores an irc message and its details.

    """
    def __init__(self, nick, text, dest=""):
        self.time = time.time()
        self.nick = nick
        self.text = text
        self.dest = dest

    def __str__(self):
        return "[{}] {} -> {} :{}".format(self.time, self.nick, self.dest, self.text)
