
from bx import bot_module


class Msg(bot_module.BotModule):
    """Give OPs to yourself (default), or a list of nicks, or everyone (with '*')."""

    @staticmethod
    def declare():
        return {"level": 100}

    def run_command(self, win, user, data, caller=None):
        parts = data.split(" ")
        if len(parts) < 2:
            win.send("Provide channel or nick and message.")
            return False
        nick = parts[0]
        msg = " ".join(parts[1:])
        self.bot.irc.privmsg(nick, msg)

module_class = Msg
