
import os
import cgi
import time
import string
import random
import datetime
import binascii

from bx import helpers
from bx import bot_module


class Logs(bot_module.BotModule):
    """Get channel logs."""

    # FIXME: check if user is trusted on specific channel
    @staticmethod
    def declare():
        return {"level": 10}

    def init(self):
        self.log_requests = {}
        self.max_hits = 100  # Max 20 hits
        self.max_age = 60*30  # 10 min

    def rand_id(self):
        return binascii.hexlify(os.urandom(8)).decode("utf-8")

    def run_command(self, win, user, data, caller=None):
        if not win.is_trusted(user):
            win.send("Sorry, you can't get logs on this channel.")
            return False
        id = self.rand_id()
        if data.lower() == "count":
            win.send("This window has {} log records.".format(len(win.get_log())))
            return True
        duration = helpers.str_to_seconds(data)
        if duration:
            min_time = time.time() - duration
        else:
            try:
                min_time = user.account.get_last_seen()
                self.logger.debug("Serving logs with automatic minimum time: {}".format(min_time))
            except:
                self.logger.exception("Failed to get automatic log start time :(")
                min_time = time.time() - 60*60  # 1 hour by default

        self.log_requests[id] = {
            "hits": 0,
            "window": win,
            "min_time": min_time,
            "time": time.time(),
            "requestor_nick": user.get_nick()
        }
        
        url = self.get_url()
        user.send("{}?{}".format(url, id))

    def get_log_request(self, id):
        if id not in self.log_requests.keys():
            return False
        log_req = self.log_requests[id]
        if log_req["hits"] == self.max_hits:
            del self.log_requests[id]
            return False
        if time.time() - log_req["time"] > self.max_age:
            del self.log_requests[id]
            return False
        log_req["hits"] += 1
        return log_req

    def on_http_request(self, request):
        self.logger.debug("on_http_request {}".format(request))
        id = request.get_query()
        log_req = self.get_log_request(id)
        if not id:
            return {"data": ""}
        if log_req:
            # response = self.generate_response(log_req["window"], log_req["min_time"],)
            response = self.generate_response(log_req)
            self.logger.debug("response {}".format(response))
            return response
        else:
            data = self.load_template("logs.html", {"records": "This link has expired."})
            
            return {
                "headers": {"Content-Type": "text/html"},
                "data": data
            }
            # return {"data": "This link has expired."}

    def get_records(self, window, min_time):
        all_records = window.get_log()
        records = [record for record in all_records if record.get_time() > min_time]
        return records

    
    def load_template(self, name, args):
        template_path = os.path.join(self.bot.app.app_path, "assets", name)
        f = open(template_path)
        data = f.read()
        f.close()

        template = string.Template(data)
        # title = window.get_name()
        # start_time = helpers.format_timestamp(min_time)
        # descr = "Logs starting from {}".format(start_time)
        # output = template.safe_substitute({"title": title, "description": descr, "records": html})
        output = template.safe_substitute(args)
        # {"title": title, "description": descr, "records": html})
        return output


    # def generate_response(self, window, min_time, nick):
    def generate_response(self, log_request):
        window = log_request["window"]
        min_time = log_request["min_time"]
        requestor_nick = log_request["requestor_nick"]
        #template_path = os.path.join(self.bot.app.app_path, "assets", "logs.html")
        #f = open(template_path)
        #data = f.read()
        #f.close()

        nick_colors = {}

        html = ""
        records = self.get_records(window, min_time)
        prev_date_str = ""
        for record in records:
            classes = ""
            time_str = datetime.datetime.fromtimestamp(record.get_time()).strftime('%H:%M')
            date_str = datetime.datetime.fromtimestamp(record.get_time()).strftime('%A %d.%m.%Y')
            if date_str != prev_date_str:
                html += '<div class="divider">{}</div>'.format(date_str)
                prev_date_str = date_str
            message = str(record.get_data())
            if record.get_name() != "privmsg":
                message = record.get_name()
            if record.get_nick() not in nick_colors.keys():
                random.seed(record.get_nick())
                nick_colors[record.get_nick()] = helpers.hsv_to_rgb(abs(1-random.random()), 0.5, 0.95)
                # nick_colors[record.get_nick()] = helpers.generate_colors(1)[0]
            nick_color = nick_colors[record.get_nick()]
            message = cgi.escape(message)
            message = helpers.replace_url_to_link(message)
            if requestor_nick in message:
                classes += " highlight"
                message = message.replace(requestor_nick, '<span class="highlight">{}</span>'.format(requestor_nick))
                
            item = ('<div class="record {name} {classes}">'
                    '<span class="time">{time}&nbsp;</span>'
                    '<span class="nick" style="color:rgb{nick_color}">{nick}&nbsp;</span>'
                    '<span class="message">{data}</span>'
                    '</div>').format(name=record.get_name(), classes=classes, time=time_str, nick=record.get_nick(), nick_color=nick_color, data=message)

            html += item

        # template = string.Template(data)
        title = window.get_name()
        start_time = helpers.format_timestamp(min_time)
        descr = "Logs starting from {}".format(start_time)
        # output = template.safe_substitute({"title": title, "description": descr, "records": html})
        output = self.load_template("logs.html", {"title": title, "description": descr, "records": html})

        response = {
            "headers": {"Content-Type": "text/html"},
            "data": output,
        }
        return response

module_class = Logs
