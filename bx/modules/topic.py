
from bx import bot_module


class Module(bot_module.BotModule):
    """Topic a channel (or rejoin the current channel)."""

    @staticmethod
    def declare():
        return {"level": 10}

    def run_command(self, win, user, data, caller=None):
        if not win.is_trusted(user):
            win.send("sorry, you can't do that")
            return False
        win.change_topic(data)
