
from bx import bot_module


class Ping(bot_module.BotModule):
    """Ping the bot to see if it's alive."""

    def run_command(self, win, user, data, caller=None):
        win.send("Pong, {}!".format(user.get_nick()))
