
from bx import bot_module


class StopBot(bot_module.BotModule):
    """Stop a bot."""

    @staticmethod
    def declare():
        return {
            "level": 100,
        }

    def run_command(self, win, user, data, caller=None):
        bot_name = data
        if bot_name not in self.bot.app.bots.keys():
            win.send("That bot doesn't exist.")
            return False
        bot = self.bot.app.bots[bot_name]
        bot.stop()

module_class = StopBot
