
import os
import sys
import cgi
import time
import datetime
import traceback
import mimetypes
import string

from . import helpers
from .lib import pyco_http

__reload__ = [helpers]


class HTTPResponse:
    def __init__(self):
        self.headers = {}
        self.response = {
            "status": 200,
            "data": "",
            "headers": {},
        }

    def __getitem__(self, item):
        return self.response[item]

    def __setitem__(self, item, value):
        self.response[item] = value

    def set_status(self, status):
        self.response["status"] = status

    def set_data(self, data):
        self.response["data"] = data

    def set_content_type(self, t):
        self.response["headers"]["Content-Type"] = t

    def keys(self):
        return self.response.keys()

    def load_from_file(self, path):
        mime = mimetypes.guess_type(path, strict=True)
        try:
            f = open(path)
            data = f.read()
            f.close()
        except:
            self.set_status(404)
            self.set_data("404")
            return False
        self.set_content_type(mime[0])
        self.set_data(data)


class HTTPRequest:
    def __init__(self, request):
        self.request = request

    def get_path(self):
        return self.request.parsed_url.path

    def get_query(self):
        return self.request.parsed_url.query

    def get_path_list(self):
        path = self.get_path()
        if path[0] == "/":
            path = path[1:]
        parts = path.split("/")
        return parts


class HTTPHandler:
    def __init__(self, app):
        self.app = app
        self.file_routes = {
            "assets": os.path.join(self.app.app_path, "assets")
        }

    def handle_request(self, request):
        try:
            return self._handle_request(request)
        except (Exception) as e:
            # FIXME: use logging lib
            print(traceback.format_exc())
            print(sys.exc_info()[0])
            return False

    def _handle_request(self, request):
        request = HTTPRequest(request)
        parts = request.get_path_list()
        if not parts[-1]:
            parts.pop(-1)
        if not parts:
            return
        if parts[0] in self.file_routes.keys():
            return self.handle_file_request(request)

        if parts[0] == "server":
            parts.pop(0)
            server = parts.pop(0)
            if server in self.app.bots.keys():
                bot = self.app.bots[server]
                if not parts:
                    return bot.handle_http_request(request, parts)
                else:
                    object = parts.pop(0)
                    if object in ["channel", "module"]:
                        if not parts:
                            return
                        name = parts.pop(0)
                        if object == "channel":
                            return False
                        elif object == "module":
                            module = bot.get_module(name)
                            if module:
                                return module.on_http_request(request)

    def handle_file_request(self, request):
        parts = request.get_path_list()
        base_dir = self.file_routes[parts[0]]
        parts.pop(0)
        file_path = os.path.join(base_dir, *parts)
        response = HTTPResponse()
        response.load_from_file(file_path)
        return response
