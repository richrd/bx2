
from bx import bot_module


class GainOp(bot_module.BotModule):
    """Have the bot request OPs from QuakeNet (if channel has no OPs)."""

    @staticmethod
    def declare():
        return {"level": 100}

    def run_command(self, win, user, data, caller=None):
        self.bot.irc.privmsg("R", "requestop {}".format(win.get_name()))

module_class = GainOp
