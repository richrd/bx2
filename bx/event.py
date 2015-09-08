
import time


class Event:
    def __init__(self, bot, name=None):
        self.bot = bot
        self.name = name
        self.time = time.time()

        self.window = None
        self.user = None
        self.irc_event = None

    def _parse_from_irc_event(self, name, args):
        self.irc_event = (name, args)
        self.name = name

        if "channel" in args.keys():
            channel = args["channel"]
            win = self.bot.get_window(channel)
            if not win:
                win = self.bot.create_window(channel)
            self.window = win

        if "target" in args.keys():
            target = args["target"]
            win = self.bot.get_window(target)
            if not win:
                win = self.bot.create_window(target)
            self.window = win
