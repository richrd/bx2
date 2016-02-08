
from bx import bot_module


class Disconnect(bot_module.BotModule):
    """Disconnect the connection to the current IRC server."""

    @staticmethod
    def declare():
        return {"level": 100}

    def run_command(self, win, user, data, caller=None):
        self.bot.stop()
