
from bx import bot_module


class Op(bot_module.BotModule):
    """Give OPs to yourself (default), or a list of nicks, or everyone (with '*')."""
    @staticmethod
    def declare():
        return {"level": 10}

    def run_command(self, win, user, data, caller=None):
        if not data:
            # Op the calling user
            win.give_op(user)
            return True
        if data == "*":
            # Op everyone on the channel
            users = [user for user in win.get_users() if not win.has_op(user)]
            win.give_op(users)
            return True
        else:
            nicks = data.split(" ")
            users = [self.bot.get_user(nick) for nick in nicks]
            win.give_op(users)
            return True

module_class = Op
