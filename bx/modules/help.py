
from bx import bot_module


class Help(bot_module.BotModule):
    """Provide basic instructions on using the bot.

    Usage: help [module_name]
    """

    def run_command(self, win, user, data, caller=None):
        """Display help or information about a command or module."""
        if not data:
            self.general_help(user)
        else:
            module = self.bot.get_module(data)
            if not module:
                win.send("I don't know that command.")
                return False
            help_text = module.get_help_text()
            if not help_text:
                win.send("Sorry, no help found for that command.")
                return False
            help_text = ' '.join(help_text.split())
            win.send("{} [{}]: {}".format(module.get_name(), module.get_permission_level(), help_text))

    def general_help(self, user):
        """Display general help."""
        lines = [
            "You can run commands by typing a '" + self.bot.config["cmd_prefix"] + "' at the beginning of a message.",
            "To see what commands are available use 'cmds'",
            "and to see what a command does, use 'help command'.",
            "You can login with 'auth' and logout with 'deauth'. Ask the bot owner for an account.",
            "To check your permission level, use 'perm'.",
            "To ask me to remember your account, use 'trustme'.",
            "Check out the code @ github: https://github.com/richrd/bx2",
            "Peace.",
            ]
        for line in lines:
            user.send(line)

module_class = Help
