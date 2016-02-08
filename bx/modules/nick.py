
from bx import bot_module


class Module(bot_module.BotModule):
    """Change the bot nick."""

    @staticmethod
    def declare():
        return {"level": 100}

    def run_command(self, win, user, data, caller=None):
        if not data:
            return False
        if(len(data.split(" "))) > 1:
            win.send("No spaces allowed!")
            return False
        self.bot.irc.change_nick(data)
