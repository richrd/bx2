
from bx import bot_module


class AutoOp(bot_module.BotModule):
    """Automatically OPs you when you auth."""

    def on_event(self, event):
        if event.name == "bot_user_authed":
            for win in self.bot.get_windows():
                if event.user.is_trusted_channel(win):
                    win.give_op(event.user)
        elif event.name == "irc_channel_join":
            if event.user.is_trusted_channel(event.window):
                event.window.give_op(event.user)

module_class = AutoOp
