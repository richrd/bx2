
from bx import bot_module


class AutoChanMode(bot_module.BotModule):
    """Automatically maintain channel modes according to config."""

    def on_event(self, event):
        if event.name in ["irc_channel_modes_are", "irc_channel_modes_changed", "irc_channel_user_modes_changed"]:
            config_modes = self.bot.get_server_channel_modes(event.window.get_name())
            if not config_modes:
                return False
            window_modes = event.window.get_modes()
            add = [mode for mode in config_modes if mode not in window_modes]
            remove = [mode for mode in window_modes if mode not in config_modes]
            if add:
                event.window.change_modes(add)
            if remove:
                event.window.change_modes(remove, True)
