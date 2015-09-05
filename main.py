
import os


class App:
    def __init__(self):
        self.debugging = 1
        self.running = 0
        self.app_path = os.path.dirname(os.path.realpath(__file__))

    def init(self):
        pass

    def run(self):
        self.running = 1


def run():
    app = App()
    app.init()
    app.run()

if __name__ == "__main__":
    run()
