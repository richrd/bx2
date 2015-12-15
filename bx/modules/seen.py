
from bx import helpers
from bx import bot_module


class Seen(bot_module.BotModule):
    """Get information about a nick."""

    @staticmethod
    def declare():
        return {"level": 10}

    def run_command(self, win, user, data, caller=None):
        if not data or len(data.split(" ")) != 1:
            win.send("Please provide a single nick.")
            return False
        target = self.bot.get_user(data)
        if not target:
            win.send("I haven't seen that user.")
            return False
        
        last_active = "not seen for a while"
        active = target.get_last_active()
        if active:
            last_active = "last active: {}".format(helpers.format_timestamp(active, format="%Y-%m-%d %H:%M:%S"))
        info = "{}{} {}, hostname: {}".format(
            target.get_nick(),
            ["", " is online and"][target.is_authed()],
            last_active,
            target.get_hostname(),
            )
        win.send(info)

module_class = Seen
