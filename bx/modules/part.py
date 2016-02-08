
from bx import bot_module


class Module(bot_module.BotModule):
    """Part a channel or the current channel (default)."""

    @staticmethod
    def declare():
        return {"level": 100}

    def run_command(self, win, user, data, caller=None):
        if not data:
            win.part()
            return

        chans = data.split()
        for chan in chans:
            chan = self.bot.get_window(chan)
            if chan:
                chan.part()
