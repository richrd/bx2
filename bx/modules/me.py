
from bx import bot_module


class Module(bot_module.BotModule):
    """Send an action message."""

    @staticmethod
    def declare():
        return {"level": 100}

    def run_command(self, win, user, data, caller=None):
        parts = data.split(" ")
        if len(parts) < 2:
            win.send("Provide channel or nick and message.")
            return False
        target = parts[0]
        msg = " ".join(parts[1:])
        self.bot.irc.ctcp_action(target, msg)
