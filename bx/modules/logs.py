
import os
import cgi
import time
import string
import datetime
import binascii

from bx import helpers
from bx import bot_module


class Logs(bot_module.BotModule):
    @staticmethod
    def declare():
        return {"level": 100}

    def init(self):
        self.log_requests = {}

    def rand_id(self):
        return binascii.hexlify(os.urandom(8)).decode("utf-8")

    def run_command(self, win, user, data, caller=None):
        id = self.rand_id()
        duration = helpers.str_to_seconds(data)
        if not duration:
            duration = 60*60  # 1 hour by default
        min_time = time.time() - duration
        self.log_requests[id] = [win, min_time]
        url = self.get_url()
        win.send("{}?{}".format(url, id))

    def on_http_request(self, request):
        id = request.get_query()
        if id in self.log_requests.keys():
            log_req = self.log_requests[id]
            del self.log_requests[id]
            response = self.generate_response(log_req[0], log_req[1])
            return response
        else:
            return {"data": "expired"}

    def get_records(self, window, min_time):
        all_records = window.get_log()
        records = [record for record in all_records if record.get_time() > min_time]
        return records

    def generate_response(self, window, min_time):
        template_path = os.path.join(self.bot.app.app_path, "assets", "logs.html")
        f = open(template_path)
        data = f.read()
        f.close()

        html = ""
        records = self.get_records(window, min_time)
        for record in records:
            time_str = datetime.datetime.fromtimestamp(record.get_time()).strftime('%H:%M')
            message = record.get_data()
            if record.get_name() != "privmsg":
                message = record.get_name()
            message = cgi.escape(message)
            message = helpers.replace_url_to_link(message)
            item = ('<div class="record {name}">'
                    '<span class="time">{time}</span>'
                    '<span class="nick">{nick}</span>'
                    '<span class="message">{data}</span>'
                    '</div>').format(name=record.get_name(), time=time_str, nick=record.get_nick(), data=message)
            html += item

        template = string.Template(data)
        title = window.get_name()
        start_time = helpers.format_timestamp(min_time)
        descr = "Logs starting from {}".format(start_time)
        output = template.safe_substitute({"title": title, "description": descr, "records": html})

        response = {
            "headers": {"Content-Type": "text/html"},
            "data": output,
        }
        return response


module_class = Logs
