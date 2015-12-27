
import time

from bx import helpers
from bx import bot_module


class Status(bot_module.BotModule):
    """Show bot status information."""

    @staticmethod
    def declare():
        return {"level": 100}

    def run_command(self, win, user, data, caller=None):
        connected = []
        for bot in self.bot.app.bots.values():
            if bot.get_connected():
                connected.append(bot.get_name())
        win.send("Connected to: {}".format(", ".join(connected)))

        server = self.bot.get_name()
        if data:
            if data not in self.bot.app.bots.keys():
                win.send("Server '{}' doesn't exist.".format(data))
                return False
            server = data
        self.show_server_status(server, win)

    def show_server_status(self, name, win):
        if name not in self.bot.app.bots.keys():
            return False
        bot = self.bot.app.bots[name]

        conn_time = bot.irc.last_connect_time
        bot_name = bot.get_name()
        timestamp = helpers.format_timestamp(conn_time)
        duration = helpers.seconds_to_duration(time.time() - conn_time)
        user_count = len(bot.users)
        auth_count = len([user for user in bot.users if user.is_authed()])

        win.send("[{}] connected {} ({}), users: {} ({} authed)".format(bot_name, timestamp, duration, user_count, auth_count))

        windows = bot.get_windows()
        joined_channels = [str(win) for win in windows if win.is_channel() and win.get_joined()]
        parted_channels = [str(win) for win in windows if win.is_channel() and not win.get_joined()]
        queries = [str(win) for win in windows if win.is_query()]
        if joined_channels:
            win.send("joined channels: {}".format(", ".join(joined_channels)))
        if parted_channels:
            win.send("parted channels: {}".format(", ".join(parted_channels)))
        if queries:
            win.send("queries: {}".format(", ".join(queries)))
        return True

module_class = Status
