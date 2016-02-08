
from bx import bot_module


class AutoOp(bot_module.BotModule):
    """Automatically OPs you when you auth."""

    def on_event(self, event):
        if event.name == "bot_user_authed":
            for win in self.bot.get_windows():
                if event.user.is_trusted_channel(win):
                    if win.has_op(self.bot.get_bot_user()):
                        win.give_op(event.user)

        elif event.name == "irc_channel_join":
            if event.window.has_op(self.bot.get_bot_user()):
                return False
            if event.user.is_trusted_channel(event.window):
                event.window.give_op(event.user)

        elif event.name == "irc_channel_user_modes_changed":
            if event.window.has_op(self.bot.get_bot_user()):
                return False
            if event.user == self.bot.get_bot_user():
                for win_user in event.window.get_users():
                    if win_user.is_trusted_channel(event.window):
                        event.window.give_op(win_user)
