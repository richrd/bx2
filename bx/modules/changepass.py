
from bx import bot_module
from bx import irc_constants


class Module(bot_module.BotModule):
    """Change your account password.

    WARNING: This can only be used via private messages to avoid exposing your password.
    Usage: changepass oldpass newpass newpass
    """

    @staticmethod
    def declare():
        return {
            "zone": irc_constants.ZONE_QUERY,
        }

    def run_command(self, win, user, data, caller=None):
        stealth = self.bot.config.get_stealth()
        if not user.is_authed():
            if not stealth:
                win.send("You need to authenticate before changing your password.")
            return False

        parts = data.split(" ")
        if len(parts) != 3:
            if not stealth:
                win.send("Please provide old password and new password twice. (changepass oldpass newpass newpass)")
            return False

        old, new1, new2 = parts[:3]
        account = user.get_account()
        if not account.valid_password(old):
            if not stealth:
                win.send("Old password doesn't match!")
            return False

        if new1 != new2:
            if not stealth:
                win.send("Your new passwords don't match!")
            return False

        account.set_password(new1)
        account.store()
        win.send("Your password has been changed.")
