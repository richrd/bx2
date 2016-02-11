
from bx import bot_module
from bx import irc_constants


class Module(bot_module.BotModule):
    """Highlight everyone on a channel."""

    @staticmethod
    def declare():
        return {"zone": irc_constants.ZONE_CHANNEL}

    def run_command(self, win, user, data, caller=None):
        users = win.get_users()
        my_nick = self.bot.get_nick()
        nicks = [u.get_nick() for u in users if u.get_nick() != my_nick]
        win.send(" ".join(nicks))
