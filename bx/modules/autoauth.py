
from bx import bot_module
from bx import irc_constants


class AutoAuth(bot_module.BotModule):
    """Automatically auths you if you're hostname is trusted."""

    def on_event(self, event):
        if event.user:
            if not event.user.is_authed():
                event.user.auto_authenticate()

module_class = AutoAuth
