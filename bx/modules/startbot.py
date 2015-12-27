
from bx import bot_module


class StartBot(bot_module.BotModule):
    """Start a bot."""

    @staticmethod
    def declare():
        return {
            "level": 100,
        }

    def run_command(self, win, user, data, caller=None):
        bot_name = data
        if bot_name in self.bot.app.bots.keys():
            bot = self.bot.app.bots[bot_name]
            if bot.running:
                win.send("That bot is already running.")
                return False
            bot.setup_client()
            bot.start()
            win.send("Done.")
        else:
            servers = self.bot.app.config.get_servers()
            if bot_name not in servers.keys():
                win.send("No such server available. Servers are: {}".format(", ".join(servers.keys())))
                return False

            config = servers[bot_name]
            bot = self.bot.app.create_bot(bot_name, config)
            bot.start()
            win.send("Done.")

module_class = StartBot
