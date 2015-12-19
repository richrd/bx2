
import time

from bx import bot_module


class Uptime(bot_module.BotModule):
    """Check bot uptime and status."""

    def run_command(self, win, user, data, caller=None):
        m, s = divmod(time.time()-self.bot.app.init_time, 60)
        h, m = divmod(m, 60)
        d, h = divmod(h, 24)
        run_time = "%d days %d:%02d:%02d" % (d, h, m, s)
        win.send(run_time)


module_class = Uptime
