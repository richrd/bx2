
from bx import bot_module


class Reboot(bot_module.BotModule):
    """Reboot the bot. Reloads most of the bot code and modules but stays connected."""

    @staticmethod
    def declare():
        return {"level": 100}

    def run_command(self, win, user, data, caller=None):
        self.logger.debug("Trying to reboot bots!")
        self.bot.app.reboot()

module_class = Reboot
