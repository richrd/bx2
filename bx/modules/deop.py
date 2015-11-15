
from bx import bot_module


class Deop(bot_module.BotModule):
    """Take OPs to yourself (default), or a list of nicks, or everyone (with '*')."""
    @staticmethod
    def declare():
        return {"level": 10}

    def run_command(self, win, user, data, caller=None):
        if not data:
            # Deop the calling user
            win.take_op(user)
            return True
        if data == "*":
            # Deop everyone on the channel
            win.take_op(win.get_users())
            return True
        else:
            nicks = data.split(" ")
            users = [self.bot.get_user(nick) for nick in nicks]
            win.take_op(users)
            return True

module_class = Deop
