#!/usr/bin/python

import __future__

import sys
import time
import socket
import select
import urllib

if sys.version_info[0] < 3:
    import urlparse
    parseurl = urlparse.urlparse
    unquote = urlparse.unquote
else:
    import urllib.parse
    parseurl = urllib.parse.urlparse
    unquote = urllib.parse.unquote
import traceback


class Request:
    def __init__(self):
        self.time = None
        self.client = (None, None)  # IP / Port
        self.type = ""
        self.uri = ""
        self.parsed_uri = None
        self.headers = {}


class PycoHTTP:
    def __init__(self):
        self.running = 0
        self.logging = 0
        self.host = ""
        self.port = 8080
        self.socket = None
        self.eol = "\r\n"
        self.max_queued_conns = 5
        self.max_request_len = 2048  # 2kb max request size
        self.select_timeout = 0.001
        self.socket_timeout = 0.1
        self.socket_timeout = 2
        self.headers = {
            "Server": "PycoHTTP",
            "Connection": "close",
            "Content-Type": "text/html",
            "Content-Encoding": "utf-8",
        }
        self.request_handler = None

    def log(self, s):
        if self.logging:
            print(s)

    def error(self, s):
        print(s)

    def set_port(self, port):
        self.port = port

    def set_max_queued_conns(self, max_queued_conns):
        self.max_queued_conns = max_queued_conns

    def set_max_request_len(self, max_request_len):
        self.max_request_len = max_request_len

    def set_select_timeout(self, select_timeout):
        self.select_timeout = select_timeout

    def set_socket_timeout(self, socket_timeout):
        self.socket_timeout = socket_timeout

    def set_default_header(self, header, value):
        for key in self.headers.keys():
            if key.lower() == header.lower():
                self.headers[key] = value
                return True
        self.headers[header] = value

    def set_default_headers(self, headers):
        self.headers = headers

    def set_handler(self, request_handler):
        """Set the callback function for handling requests."""
        self.request_handler = request_handler

    def get_error_info(self):
        msg = str(traceback.format_exc()) + "\n" + str(sys.exc_info())
        return msg

    def start(self, blocking=False):
        """Start the server."""
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Avoid "address already in use"
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.settimeout(self.socket_timeout)
        self.socket.setblocking(False)

        self.log("Hosting server...")
        try:
            self.socket.bind((self.host, self.port))
        except socket.error as msg:
            self.log('Bind failed. Error Code : ' + str(msg[0]) + ' Message ' + msg[1])
            return False

        self.socket.listen(self.max_queued_conns)
        self.log('Socket now listening')

        self.running = 1
        if blocking:
            self.serve_blocking()
        return True

    def stop(self):
        """Stop the server."""
        self.running = 0

    def serve(self):
        """Needs to be called periodically to receive connections."""
        readable, writable, errored = select.select([self.socket], [], [], self.select_timeout)
        if self.socket in readable:
            try:
                conn, addr = self.socket.accept()
                conn.settimeout(self.socket_timeout)
                self.handle_connection(conn, addr)
            except KeyboardInterrupt:
                return False
            except:
                self.error(self.get_error_info())

    def serve_blocking(self):
        """Accept connections in blocking mode."""
        while self.running:
            try:
                conn, addr = self.socket.accept()
                self.handle_connection(conn, addr)
            except KeyboardInterrupt:
                return False
            except:
                self.error(self.get_error_info())

    def parse_headers(self, lines):
        """Parse headers from list of lines in response."""
        headers = {}
        for line in lines:
            parts = line.split(":", 1)
            if len(parts) < 2:  # Skip lines without a colon
                continue
            headers[parts[0].strip().lower()] = parts[1].strip()
        return headers

    def get_request_data(self, conn):
        """Receive HTTP request data."""
        # Loop and append received data until sufficent data is received
        received = ""
        while received[-4:] != self.eol*2:
            self.log("Looping receive...")
            self.log("Data is:'"+str(received)+"'")
            try:
                self.log("conn.recv...")
                data = conn.recv(1024)
                self.log("conn.recv done")
                if type(data) == bytes:
                    data = data.decode("utf-8")
            except:
                return received
            if not data:
                break
            received += data
            if len(received) > self.max_request_len:
                received = received[:self.max_request_len]
                break

        # Check for empty requests
        if received.strip() == "":
            return False

        return received

    def parse_request(self, received, addr):
        # We don't support POST so get rid of request body
        needed = received.split(self.eol*2)[0]
        lines = needed.split(self.eol)

        # Get parts of the first request line
        first = lines[0].split(" ")
        lines.pop(0)

        request = Request()
        request.time = time.time()

        # Extract request data
        request.type = first[0]
        request.uri = first[1]
        request.parsed_url = parseurl(request.uri)
        request.client = addr
        # Get request heders
        headers = self.parse_headers(lines)
        request.headers = headers

        return request

    def respond(self, conn, response):
        """Respond to a request."""

        # Set response defaults
        if "status" not in response.keys():
            response["status"] = "200"

        # Build headers
        header_lines = []
        headers = self.headers.copy()
        if "headers" in response.keys():
            # Merge new headers into defaults
            self.log("Headers are:{}".format(response["headers"]))
            headers.update(response["headers"])
            self.log("Headers are now:{}".format(headers))
        for header in headers.items():
            header_lines.append(header[0]+": "+header[1])

        # TODO: Response line should contain textual status too:
        # HTTP/1.0 200 OK
        data = "HTTP/1.1 " + str(response["status"]) + self.eol
        data += self.eol.join(header_lines) + (self.eol*2)
        data += response["data"]

        # Send the entire response
        # FIXME: may want to check for success and retry when necessary
        i = 1
        while i < 11:
            self.log("Trying to respond with data #{}".format(i))
            # try:
            if self.send_all_to_socket(data.encode("utf-8"), conn):
             # conn.sendall(data.encode("utf-8")) is None:
                return True
            # except:
                # self.log("Attempt #{} failed...".format(i))
            i += 1
        self.log("Send failed!")
        return False

    def send_all_to_socket(self, data, sock):
        left = data
        while left != "":
            # try:
            data = left
            # data = left.decode(self.outgoing_encoding)
            # data = bytes(left, "UTF-8")
            # data = bytes(left, self.outgoing_encoding)
            sent = sock.send(data)
            if len(left) == sent:
                return True
            left = left[sent:]
            # except:
            #     self.debug_log("send_all_to_socket errored")
            #     return False
        return False


    def handle_connection(self, conn, addr):
        """Handle a HTTP connection."""
        self.log('Connected with ' + addr[0] + ':' + str(addr[1]))
        self.log("Getting request...")
        data = self.get_request_data(conn)
        self.log("Got request data...")
        request = False
        if data:
            request = self.parse_request(data, addr)
        if request:
            # If we have a request handler give it the request
            if self.request_handler:
                self.log("Handling request...")
                response = self.request_handler(request)
                if response:
                    self.respond(conn, response)
                    self.log("Response sent...")
        else:
            self.log("No request received!")
        conn.close()


# Example for a request handler
def handle_request(request):
    front_uris = ["/", "/index.html"]
    # url = parseurl(request.uri)
    url = request.parsed_url
    if url.path in front_uris:
        response = {
            "data": '<h1>Hello World!</h1>'
        }
    elif url.path == "/text.txt":
        response = {
            "headers": {"Content-Type": "text/plain"},
            "data": 'Hello World!\nNew line?'
        }
    elif url.path == "/close":
        response = False  # Don't respond, just close connection
    else:
        response = {
            "status": 404,  # Default status is 200
            "data": 'Sorry, not found (404). <a href="/">Front page</a>'
        }

    return response

if __name__ == "__main__":
    srv = PycoHTTP()
    srv.set_handler(handle_request)
    #srv.start(True)  # Add true for a blocking server
    # Otherwise use a loop like this:
    srv.start()
    while srv.running:
       srv.serve()
