
import subprocess

from bx import bot_module


class GitPull(bot_module.BotModule):
    """Pull the latest changes to the bot from git."""

    @staticmethod
    def declare():
        return {
            "level": 100
        }

    def run_command(self, win, user, data, caller=""):
        try:
            process = subprocess.Popen(["git", "pull"], stdout=subprocess.PIPE, cwd=self.bot.app.app_path)
            output = process.communicate()[0]
            win.send("Done")
        except:
            self.logger.exception("Failed to 'git pull'!")

module_class = GitPull
