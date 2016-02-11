
from bx import bot_module


class Module(bot_module.BotModule):
    """Provide basic instructions on using the bot.

    Usage: help [module_name]
    """

    def run_command(self, win, user, data, caller=None):
        """Display help or information about a command or module."""
        commands = []
        for module in self.bot.get_modules():
            if module.get_permission_level() > user.get_permission_level():
                continue
            if module.is_command():
                commands.append(module.get_name())
        commands.sort()
        win.send("Commands available to you: {}".format(", ".join(commands)))
