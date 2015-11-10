
from bx import bot_module


class TrustMe(bot_module.BotModule):
    """Remember your hostname for automatic auth."""

    def run_command(self, win, user, data, caller=None):
        if not user.is_authed():
            win.send("You need to auth before you can be trusted!")
            return False
        hostnames = user.account.get_hostnames()
        if user.get_hostname() in hostnames:
            win.send("Your hostname is already trusted!")
            return False
        user.account.add_hostname(user.get_hostname())
        win.send("Your hostname is now trusted. You should be automatically logged in next time we meet.")
        user.account.store()

module_class = TrustMe
