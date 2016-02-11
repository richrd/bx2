
from bx import helpers
from bx import bot_module


class Module(bot_module.BotModule):
    """Execute python code."""

    @staticmethod
    def declare():
        return {"level": 100}

    def run_command(self, win, user, data, caller=None):
        try:
            result = exec(data)
            win.send(result)
        except:
            self.logger.exception("Exec failed")
            win.send("Exec failed.")
