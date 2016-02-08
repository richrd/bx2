
from bx import bot_module


class Join(bot_module.BotModule):
    """Join a channel (or rejoin the current channel)."""

    @staticmethod
    def declare():
        return {"level": 100}

    def run_command(self, win, user, data, caller=None):
        chans = data.split()
        for chan in chans:
            self.bot.irc.join(chan)
