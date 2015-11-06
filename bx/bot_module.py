
import time
import urllib
import logging

from bx import irc_constants


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
        self.throttle_time = self.bot.config["cmd_throttle"]
        # list of users of command
        self.users = {}

        self.logger = logging.getLogger("{}[{}]".format(self.bot.name, self.name))

        self.init()

    @staticmethod
    def declare():
        """Return default options for this module."""
        return {}

    def get_help_text(self):
        return self.__doc__

    def get_name(self):
        return self.name

    def get_zone(self):
        return self.zone

    def get_permission_level(self):
        return self.level

    def get_throttle_time(self):
        return self.throttle_time

    def get_url(self):
        parts = ["server", self.bot.get_name(), "module", self.get_name()]
        path = "/".join(parts)
        host = self.bot.app.config.get_item("http")["host"]
        port = self.bot.app.config.get_item("http")["port"]
        return "http://{}:{}/{}".format(host, port, path)

    def set_name(self, name):
        self.name = name
        self.logger = logging.getLogger("{}[{}]".format(self.bot.name, self.name))

    def set_zone(self, zone):
        self.zone = zone

    def set_level(self, level):
        self.level = level

    def set_throttle_time(self, throttle_time):
        self.throttle_time = throttle_time

    def init(self):
        """The init method implemented by the subclass."""
        pass

    def run_command(self, win, user, data, caller=None):
        """Invoked when the module is called or run by a user."""
        pass

    def on_event(self, event):
        """Invoked when the module is called or run by a user."""
        pass

    def on_http_request(self, request):
        pass

    #
    # Special helper functions
    #

    def retrieve_url(self, url):
        try:
            u = urllib.request.urlopen(url, timeout=5)
            data = u.read()
            u.close()
            return data
        except Exception:
            self.logger.warning("Failed to get url '{}'".format(url))
            return False

    def _is_allowed_window(self, win):
        if self.zone == irc_constants.ZONE_BOTH or self.zone == win.zone:
            return True
        return False

    def _is_allowed_user(self, user):
        if user.get_permission_level() < self.level:
            return False
        return True

    # Determine wether the command can be run
    # Blocks command spamming
    def _is_throttled(self, user):
        if user in self.users.keys():
            t = self.users[user][0]
            if (time.time()-t) < self.throttle_time:
                return True
            else:
                self.users[user] = [time.time(), False]
                return False
        else:
            self.users[user] = [time.time(), False]
            return False

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
                    win.send("can't do that so often, wait {} sec".format(self._get_throttle_wait_time(user)))
                return False
            else:
                self._safe_run(win, user, data, caller)
        else:
            if user.is_authed():
                win.send("sorry, you can't do that")
            else:
                win.send("sorry, you need to auth")

    def _safe_run(self, win, user, data, caller=None):
        try:
            self.run_command(win, user, data, caller)
        except:
            self.logger.exception("Failed to run module {}".format(self.name))
