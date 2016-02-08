
from bx import helpers
from bx import bot_module


class Eval(bot_module.BotModule):
    """Evaluate a python expression."""

    @staticmethod
    def declare():
        return {"level": 100}

    def run_command(self, win, user, data, caller=None):
        try:
            result = eval(data)
            win.send(result)
        except:
            self.logger.exception("Eval failed")
            win.send("Eval failed.")
