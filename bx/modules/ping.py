
from bx import bot_module


class Ping(bot_module.BotModule):
    def run_command(self, win, user, data, caller=None):
        win.send("Pong, {}!".format(user.get_nick()))

module_class = Ping
