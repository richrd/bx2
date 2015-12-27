
from bx import bot_module


class Whois(bot_module.BotModule):
    """Send whois request to server

    Usage: whois nick
    """

    @staticmethod
    def declare():
        return {"level": 100}

    def run_command(self, win, user, data, caller=None):
        self.bot.irc.send("WHOIS {}".format(data))

module_class = Whois
