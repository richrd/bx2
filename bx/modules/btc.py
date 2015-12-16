
from bx import bot_module

import time
import json


class BTC(bot_module.BotModule):
    """Check the latest bitcoin exchange rate."""

    def init(self):
        self.sources = {
            "bitstamp": "http://www.bitstamp.net/api/ticker/",
        }
        self.cache_max_age = 60*2   # cache results for 2 minutes
        self.cache = {}
        self.source = "bitstamp"

    def get_rate(self, source):
        """Gets the exchange rate as USD from given exchange, and caches results."""
        if source in self.cache.keys():
            if time.time() - self.cache[source][0] < self.cache_max_age:
                return self.cache[source][1]
        data = self.retrieve_url(self.sources[source])  # TODO: move this to helpers module
        self.logger.debug("Exchange data is:{}".format(data))
        try:
            obj = json.loads(data.decode("utf-8"))
        except:
            return False
            self.logger.exception("Couldn't read or decode response.")
        rate = False
        if source == "bitstamp":
            rate = obj["bid"]

        self.cache[source] = (time.time(), rate)
        return rate

    def run_command(self, win, user, data, caller=None):
        rate = self.get_rate(self.source)
        self.logger.debug("Rate is:{}".format(rate))
        if rate is False:
            win.send("Sorry, couldn't get exchage rate :(")
            return False
        win.send("BTC: {} USD [{}]".format(rate, self.source))

module_class = BTC
