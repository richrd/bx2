
import os
import cgi
import time
import string
import datetime
import binascii

from bx import helpers
from bx import bot_module


class Logs(bot_module.BotModule):
    # FIXME: check if user is trusted on specific channel
    @staticmethod
    def declare():
        return {"level": 10}

    def init(self):
        self.log_requests = {}
        self.max_hits = 15
        self.max_age = 120

    def rand_id(self):
        return binascii.hexlify(os.urandom(8)).decode("utf-8")

    def run_command(self, win, user, data, caller=None):
        id = self.rand_id()
        duration = helpers.str_to_seconds(data)
        if not duration:
            duration = 60*60  # 1 hour by default
        min_time = time.time() - duration

        self.log_requests[id] = {
            "hits": 0,
            "window": win,
            "min_time": min_time,
            "time": time.time()
        }
        
        url = self.get_url()
        win.send("{}?{}".format(url, id))

    def get_log_request(self, id):
        if id not in self.log_requests.keys():
            return False
        log_req = self.log_requests[id]
        if log_req["hits"] == self.max_hits:
            del self.log_requests[id]
            return False
        if time.time() - log_req["time"] > self.max_hits:
            del self.log_requests[id]
            return False
        log_req["hits"] += 1
        return log_req

    def on_http_request(self, request):
        self.logger.debug("on_http_request {}".format(request))
        id = request.get_query()
        log_req = self.get_log_request(id)
        if log_req:
            response = self.generate_response(log_req["window"], log_req["min_time"])
            self.logger.debug("response {}".format(response))
            return response
        else:
            return {"data": "This link has expired."}

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
        prev_date_str = ""
        for record in records:
            time_str = datetime.datetime.fromtimestamp(record.get_time()).strftime('%H:%M')
            date_str = datetime.datetime.fromtimestamp(record.get_time()).strftime('%A %d.%m.%Y')
            if date_str != prev_date_str:
                html += '<div class="divider">{}</div>'.format(date_str)
                prev_date_str = date_str
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
