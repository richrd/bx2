
from bx import bot_module


class AutoRejoin(bot_module.BotModule):
    """Take OPs to yourself (default), or a list of nicks, or everyone (with '*')."""
    @staticmethod
    def declare():
        return {"level": 100}

    def on_event(self, event):
        if event.name == "irc_channel_kick":
            if event.window.get_name() in self.bot.get_server_channels():
                if event.user == self.bot.get_bot_user():
                    self.bot.irc.join(event.window.get_name())

module_class = AutoRejoin
