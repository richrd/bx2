
class Console:
    def __init__(self, app):
        self.app = app
        self.cmds = {
            "reboot": self.reboot,
            "exit": self.exit,
            "help": self.help,
            "eval": self.eval,
            "exec": self.exec,
        }

    def interrupt(self):
        self.handle_input()

    def help(self, args=""):
        cmds = ", ".join(self.cmds.keys())
        print("COMMANDS: {}".format(cmds))

    def reboot(self, args=""):
        self.app.reboot()

    def exit(self, args=""):
        self.app.stop()

    def eval(self, args=""):
        try:
            print(eval(args))
        except:
            print("Failed.")

    def exec(self, args=""):
        try:
            print(exec(args))
        except:
            print("Failed.")

    def handle_input(self):
        print("")
        try:
            data = input("[CONSOLE]:")
        except:
            print("")
            print("Run 'exit' to quit the bot.")
            return False

        words = data.split(" ")
        start = words[0]
        args = ""
        if len(words) > 1:
            args = " ".join(words[1:])
        if start in self.cmds.keys():
            self.cmds[start](args)
        else:
            print("Invalid command.")
