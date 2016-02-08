
from bx import bot_module


class Raw(bot_module.BotModule):
    """Give OPs to yourself (default), or a list of nicks, or everyone (with '*')."""

    @staticmethod
    def declare():
        return {"level": 100}

    def run_command(self, win, user, data, caller=None):
        if not data:
            return False
        self.bot.irc.send(data)
