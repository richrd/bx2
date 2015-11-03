
from bx import bot_module


class Reboot(bot_module.BotModule):
    @staticmethod
    def declare():
        return {"level": 100}

    def run_command(self, win, user, data, caller=None):
        self.logger.debug("Trying to reboot bots!")
        self.bot.app.reboot()

module_class = Reboot
