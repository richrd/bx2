
from bx import helpers
from bx import bot_module
from bx import irc_constants


class Module(bot_module.BotModule):
    """Remove all query windows."""

    @staticmethod
    def declare():
        return {"level": 100}

    def run_command(self, win, user, data, caller=None):
        new_wins = []
        for win in self.bot.windows:
            if not win.is_query():
                new_wins.append(win)
        self.bot.windows = new_wins
        win.send("Done.")
