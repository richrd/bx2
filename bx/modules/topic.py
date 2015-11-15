
from bx import bot_module


class Topic(bot_module.BotModule):
    """Topic a channel (or rejoin the current channel)."""

    @staticmethod
    def declare():
        return {"level": 100}

    def run_command(self, win, user, data, caller=None):
        win.change_topic(data)

module_class = Topic
