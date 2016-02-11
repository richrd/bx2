
import subprocess

from bx import bot_module


class Module(bot_module.BotModule):
    """Raspberry Pi status."""

    @staticmethod
    def declare():
        return {"level": 100}

    def run_command(self, win, user, data, caller=""):
        temps = self.get_temps()
        win.send("CPU: {} GPU: {}".format(temps["cpu"], temps["gpu"]))

    def get_temps(self):
        cpu_out = self.shell_command("cat /sys/class/thermal/thermal_zone0/temp")
        gpu_out = self.shell_command("/opt/vc/bin/vcgencmd measure_temp|cut -c6-9")

        return {
            "cpu": cpu_out,
            "gpu": gpu_out,
        }

    def shell_command(self, cmd):
        parts = cmd.split(" ")
        try:
            process = subprocess.Popen(parts, stdout=subprocess.PIPE, cwd=self.bot.app.app_path)
            output = process.communicate()[0]
            output = output.decode("utf-8")
            return output
        except:
            return False
