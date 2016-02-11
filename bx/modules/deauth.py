
from bx import bot_module


class Module(bot_module.BotModule):
    """Logout of the bot."""

    def run_command(self, win, user, data, caller=None):
        if user.deauthenticate():
            win.send("You have now logged out.")
            return True
        win.send("You aren't logged in!")
        return False
