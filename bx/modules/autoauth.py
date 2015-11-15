
from bx import bot_module
from bx import irc_constants


class AutoAuth(bot_module.BotModule):
    """Automatically auths you if you're hostname is trusted."""

    def on_event(self, event):
        if event.name == "bot_user_hostname_changed":
            if not event.user.is_authed():
                self.logger.debug("Autoauthing {} by hostname {}".format(event.user, event.user.hostname))
                event.user.auto_authenticate()

module_class = AutoAuth
