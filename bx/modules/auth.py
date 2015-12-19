
from bx import bot_module
from bx import irc_constants


class Auth(bot_module.BotModule):
    """Identify yourself with the bot (login).

    WARNING: This can only be used via private messages to avoid exposing your username and password.
    Usage: auth username password
    """

    @staticmethod
    def declare():
        return {
            "zone": irc_constants.ZONE_QUERY,
            "throttle_time": 2,
            "essential": 1,
        }

    def run_command(self, win, user, data, caller=None):
        stealth = self.bot.config.get_stealth()
        if user.is_authed():
            win.send("You're already authed!")
            return False
        parts = data.split(" ")
        if len(parts) != 2:
            if not stealth:
                win.send("Please provide username and password")
            return False
        username, password = parts
        account = user.authenticate(username, password)
        if account:
            win.send("Authed! You are now level {}.".format(user.get_permission_level()))
            return True
        if not stealth:
            win.send("Wrong username or password.")
        return False

module_class = Auth
