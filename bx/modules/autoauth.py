
from bx import bot_module


class AutoAuth(bot_module.BotModule):
    """Automatically auths you if you're hostname is trusted."""

    def on_event(self, event):
        if event.name in ["bot_user_hostname_changed", "bot_user_online", "irc_channel_join"]:
            if not event.user.is_authed():
                event.user.auto_authenticate()
