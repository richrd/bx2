
from bx import bot_module


class Module(bot_module.BotModule):
    """Check the permission level of yoursefl or another user."""

    def run_command(self, win, user, data, caller=None):
        if data:
            user = self.bot.get_user(data)
            if user:
                win.send("The permission level of {} is {}.".format(user.get_nick(), user.get_permission_level()))
                return True
            win.send("I don't know that user.")
        else:
            win.send("Your permission level is {}.".format(user.get_permission_level()))
            return True
