
from bx import bot_module


class Run(bot_module.BotModule):
    """Run a command as another and  window.

    Usage: nick window command
    """

    @staticmethod
    def declare():
        return {"level": 100}

    def run_command(self, win, user, data, caller=None):
        args = data.split(" ")
        # Make sure we have required arguments
        if len(args) < 3:
            win.send("Please provide nick, window, and command.")
            return False
        nick, window = args[:2]
        command = args[2:]

        # Check for valid user and window
        run_user = self.bot.get_user(nick)
        if not run_user:
            win.send("User not found.")
            return False

        run_window = self.bot.get_window(window)
        if not run_window:
            win.send("Window not found.")
            return False

        # Get command and arguments run it
        run_args = ""
        run_command = command[0]
        if len(command) > 1:
            run_args = " ".join(command[1:])
        event = self.bot.create_event()
        event.set_user(run_user)
        event.set_window(run_window)
        self.bot.run_command(run_command, run_args, event, user)
