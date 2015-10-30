
import time
import logging

import irc_constants


class BotModule:
    """Base class for all modules."""
    def __init__(self, bot):
        self.bot = bot
        self.name = ""
        self.initialized = 0
        self.zone = irc_constants.ZONE_BOTH
        self.level = 0
        # Last time the command was run.
        self.last_exec = None
        # How often the command can be run in seconds.
        self.throttle_time = 10
        # list of users of command
        self.users = {}

        self.logger = logging.getLogger("{}[{}]".format(self.bot.name, self.name))

    @staticmethod
    def _declare():
        return {
            
        }

    def init(self):
        """The init method implemented by the subclass."""
        pass

    def run_command(self, win, user, data, caller=None):
        """Invoked when the module is called or run by a user."""
        pass

    def handle_event(self, event):
        """Invoked when the module is called or run by a user."""
        pass

    def _is_allowed_window(self, win):
        if self.zone == irc_constants.IRC_ZONE_BOTH or self.zone == win.zone:
            return True
        return False

    def _is_allowed_user(self, user):
        if user.get_permission_level() < self.level:
            return False
        return True

    def _get_throttle_wait_time(self, user):
        remaining = self.throttle_time - int(time.time() - self.users[user][0])
        if remaining < 1:
            remaining = 1
        return remaining

    def _should_warn_throttle(self, user):
        if self.users[user][1] is False:
            self.users[user][1] = True
            return True
        else:
            return False

    def _execute(self, win, user, data, caller=None):
        if not self._is_allowed_window(win):
            win.send("you can't do that here, use privmsg")
            return False
        if self._is_allowed_user(user):
            if self._is_throttled(user):
                if self._should_warn_throttle(user):
                    win.send("can't do that so often, wait {} sec" %self._get_throttle_wait_time(user))
                return False
        else:
            if user.is_authed():
                win.send("sry, you can't do that")
            else:
                win.send("sry, you need to auth")



