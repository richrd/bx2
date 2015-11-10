
from bx import bot_module


class Part(bot_module.BotModule):
    """Part a channel or the current channel (default)."""

    @staticmethod
    def declare():
        return {"level": 100}

    def run_command(self, win, user, data, caller=None):
        if not data:
            self.bot.irc.part(win.get_name())
        chans = data.split()
        for chan in chans:
            self.bot.irc.part(chan)

module_class = Part
