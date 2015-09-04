# -*- coding: utf-8 -*-
"""irc.py: IRC Client Implementation

Handles all neccessary parts of the IRC protocol for client connections.
Sits in IRC doing nothing except respond to PINGs.
"""

import sys
import time
import select
import socket
import string
import inspect
import traceback

import irc_constants


class IRCClient:
    """Independet IRC client that will connect and sit on an IRC server doing nothing.

    It can be subclassed to do whatever, without needing to worry about the protocol.
    """

    def __init__(self, host="", port=6667, nick="bx-irc-lib"):
        # Server details
        self.host = host
        self.port = port

        # User info defaults
        self.default_nick = nick
        self.default_realname = nick
        self.default_ident = nick

        # User info
        self.realname = self.default_realname
        self.ident = self.default_ident

        # TODO: Implement setter
        # How many seconds to wait between lines sent to the server
        self.send_throttling = 1

        # TODO: Implement setter
        # What encoding to use when sending to the IRC server
        self.outgoing_encoding = "utf-8"

        # TODO: Implement setter
        # Encodings to use when trying to decode incomming data
        self.incomming_encodings = ["utf-8", "latin-1", "cp1251", "cp1252", "win1251", "iso-8859-1"]

        # TODO: Implement setter
        # Maximum size for data sent to the IRC server
        self.max_send_length = 400

        # Flag indicating if the client has been initialized
        self.inited = False

    def init(self):
        # The nick to use for the client
        self.current_nick = self.default_nick

        # Flag indicating wether the socket is connected
        self.irc_connected = False
        # Time of last successfull connect
        self.last_connect_time = None
        # Flag indicating wether the client is connected and can interact with the server
        self.irc_ready = False
        # Flag indicating wether the client is running
        self.irc_running = False

        # The socket object for the connection
        self.socket = None
        # Timeout for connecting
        self.socket_timeout = 20
        # Maximum time to wait for socket select (checking if there's new activity on the socket)
        self.select_interval = .02

        # How much data to (at most) to receive from the socket
        self.read_chunk_size = 1024
        # Buffer for raw data received from the socket
        self.raw_buffer = ""
        # Buffer for separate lines received from the IRC server
        self.recv_buffer = []
        # Time of last successfull socket receive from the server
        self.last_receive_time = None

        # Time of last PING by the server
        self.last_ping_time = None
        # Time of last sent PONG reply
        self.last_pong_time = None
        # Minimum time of inactivity before pinging the server (to check that the connection)
        self.ping_after = 120  # 2 minutes
        # Time of the last PING by the client
        self.last_client_ping_time = None
        # Maximum time of inactivity before reconnecting to the server
        self.max_inactivity = 180  # 3 minutes

        # Lines waiting to be sent to the IRC server
        self.send_buffer = []
        # Time of last successfull socket send to the server
        self.last_send_time = None

        # Indicate that init has been done
        self.inited = True

        # TODO: DEBUG
        self.events_run = []

    def debug_log(self, *args):
        msg = " ".join(map(str, args))
        print(msg)

    #
    # Getters
    #

    def get_nick(self):
        return self.current_nick

    #
    # Setters
    #

    def set_host(self, host):
        self.host = host

    def set_port(self, port):
        self.port = port

    def set_nick(self, nick):
        self.current_nick = nick

    #
    # Client actions
    #

    def run(self):
        self.start()

    def start(self, block=True):
        self.debug_log("Starting client...")
        connected = self.connect()
        if connected:
            self.last_connect_time = time.time()
            self.irc_running = True
            if block:
                return self.mainloop()
            else:
                return True
        else:
            return False

    def stop(self):
        self.debug_log("stop()")
        self.disconnect()

    def connect(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.settimeout(self.socket_timeout)
        self.debug_log("Connecting to " + self.host + ":" + str(self.port) + "...")
        try:
            self.socket.connect((self.host, self.port))
        except socket.error as err:
            self.debug_log("Error connecting:", str(socket.error), str(err))
            return False
        self.on_connected()
        return True

    def disconnect(self):
        self.irc_connected = 0

    def mainloop(self):
        while self.irc_connected:
            self.on_loop_start()
            result = self.maintain()
            self.on_loop_end()
            if not result:
                return False

    def send(self, data):
        self.debug_log("send:", data)
        if len(data) > 510:
            self.debug_log("send(): data too long!")
        data += "\r\n"
        self.send_buffer.append(data)

    def introduce(self, nick=None, ident=None, realname=None):   # Send NICK and USER messages
        self.debug_log("Introducing as:", "nick:", nick, ", ident:", ident, ", realname:", realname)
        if nick is None:
            nick = self.default_nick
        if ident is None:
            ident = self.default_ident
        if realname is None:
            realname = self.default_realname
        self.change_nick(nick)
        self.send("USER {} 8 * :{}".format(ident, realname))

    def change_nick(self, nick=None):
        self.debug_log("Changing nick to:", nick)
        if nick is None:
            nick = self.default_nick
        self.set_nick(nick)
        self.send("NICK {}".format(nick))

    def join(self, channels):
        self.send("JOIN {}".format(",".join(channels)))

    def maintain(self):
        """Maintain the IRC server connection.

        Handles the socket sending and receiving, and checking that the connection is alive.
        Returns False if the socket is dead.
        """
        # Try and check the socket state
        try:
            sockl = [self.socket]
            readable, writable, errored = select.select(sockl, sockl, sockl, self.select_interval)
            time.sleep(self.select_interval)  # TODO: do we really need this?
        except (socket.error) as err:
            self.debug_log("mainloop()", "select error:", socket.error, err)
            return False
        # Try to read from the socket
        if self.socket in readable:
            #self.debug_log("MAINTAIN:", "readable")
            if not self.receive_to_buffer():  # If no data received, sock is dead
                self.disconnect()
                return False
            return True
        # Try to send to the socket
        elif self.socket in writable:
            #self.debug_log("MAINTAIN:", "writable")
            if not self.process_send_buffer():  # Try to send and break on failure
                return False
        # Die if the socket is errored
        elif self.socket in errored:
            #self.debug_log("MAINTAIN:", "errored")
            self.debug_log("mainloop()", "socket errored")
            return False
        else:
            self.debug_log("mainloop()", "socket inaccessible")
        self.process()
        return True

    #
    # Client Events
    #

    def on_connected(self):
        """Called when the client has connected to the server."""
        self._dispatch_event()
        # self.
        self.irc_connected = True
        self.introduce()

    def on_disconnect(self):
        self._dispatch_event()
        self.irc_connected = 0

    def on_irc_ready(self):
        pass

    def on_receive(self, data):
        """Called emediately when a line is received."""
        self._dispatch_event()

    def on_loop_start(self):
        """Called before the client loop begins."""

    def on_loop_end(self):
        """Called when the client loop ends."""

    def on_connect_throttled(self, reason=""):
        """Called when the server has throttled a connection attempt."""
        self.debug_log("Connection was throttled because:", reason)

    def on_ping(self, data):
        """Callend when a PING event is received."""
        self._dispatch_event()
        self.send("PONG {}".format(data))

    def on_pong(self):
        """Callend when a PONG event is received."""
        self._dispatch_event()

    def on_motd(self, data=""):
        """Called for each line in the MOTD (Message Of The Day)"""
        # self._dispatch_event()

    def on_end_motd(self):
        """Called when the MOTD ends or when there is no MOTD."""
        # self._dispatch_event()

    def on_nick_in_use(self, nick, data):
        self._dispatch_event()
        self.change_nick(self.get_nick() + "_")

    def on_welcome_info(self, data):
        """Sent when welcom info is received."""  # TODO: More elaborate docstring.
        # self._dispatch_event()

    def on_support_info(self, data):
        """Sent when support info is received."""  # TODO: More elaborate docstring.
        # self._dispatch_event()

    def on_server_info(self, data):
        """Sent when server info is received."""  # TODO: More elaborate docstring.
        self._dispatch_event()

    def on_processing_connection(self, data):
        self._dispatch_event()

    def on_your_id(self, id, data):
        self._dispatch_event()

    def on_whois_hostname(self, nick, hostname):
        self._dispatch_event()

    def on_channel_topic_is(self, channel, text_data):
        self._dispatch_event()

    def on_channel_topic_meta(self, channel, nick, utime):
        self._dispatch_event()

    def on_channel_invite_only(self, channel, text_data):
        self._dispatch_event()

    def on_channel_needs_password(self, channel, text_data):
        self._dispatch_event()

    def on_event(self, name, args):
        """Called for each event that occurs, with event name and arguments."""
        self.debug_log("on_event", name, args)
        # TODO: DEBUG
        if name not in self.events_run:
            self.events_run.append(name)

    def _dispatch_event(self):
        """Should be called from event handling methods.

        It automagically determins the event name and arguments given to it and forwards them to on_event.
        """
        frame_info = inspect.getouterframes(inspect.currentframe())[1]
        frame = frame_info[0]
        name = frame_info[3]
        args = self._get_frame_args(frame)
        self.on_event(name, args)

    def _get_frame_args(self, frame):
        """Return function call arguments for frame as a dict."""
        key_args = {}
        args, _, _, values = inspect.getargvalues(frame)
        for i in args:
            if i == "self":
                continue
            key_args[i] = values[i]
        return key_args

    #
    # The gory implementation details (eveything from here on shouldn't be used directly)
    #

    def receive_to_buffer(self):
        try:
            received = self.socket.recv(self.read_chunk_size)
        except socket.timeout as e:
            err = e.args[0]
            self.debug_log("receive_to_buffer()", "timed out", "ERR:", err)
            if err == "timed out":
                return True
        except socket.error as e:
            self.debug_log("receive_to_buffer()", "failed sock.recv", e)
            return False
        if len(received) == 0:
            self.debug_log("receive_to_buffer()", "received empty data")
            return False
        if not received:
            self.debug_log("receive_to_buffer()", "received nothing, sock dead?!")
            return False
        data = self.decode_received_data(received)
        self.raw_buffer = self.raw_buffer + data
        lines = self.raw_buffer.split("\n")
        self.raw_buffer = lines.pop()
        for line in lines:
            line = line.rstrip()
            self.recv_buffer.append(line)
            self.on_receive(line)
        self.last_receive_time = time.time()
        return True

    def decode_received_data(self, data):
        for enc in self.incomming_encodings:
            try:
                return data.decode(enc)
            except:
                continue
        return self.force_decode(data)

    def force_decode(self, data):
        """Forcefully 'decode' a received line. Replaces failed characters with '?'."""
        try:
            return str(data)
        except:
            decoded = ""
            for char in data:
                try:
                    decoded += str(char)
                except:
                    decoded += "?"
            return decoded

    def process(self):
        try:
            self.process_receive_buffer()
            # self.keep_alive()
        except Exception as e:
            print(traceback.format_exc())
            print(sys.exc_info()[0])
            self.debug_log("Process()", e)

    def process_send_buffer(self):
        """Send a single line from the send buffer."""
        # self.debug_log("process_send_buffer")
        if self.send_buffer != []:
            # Make sure we don't send lines to the server too often and get kicked out
            if self.last_send_time is None or time.time() - self.last_send_time > self.send_throttling:
                line = self.send_buffer.pop(0)
                if not self.send_all_to_socket(line):
                    self.debug_log("process_send_buffer fail")
                    return False
                self.debug_log("SEND:", line[:-2])
                self.last_send_time = time.time()
        return True

    def send_all_to_socket(self, data):
        # TODO: Might want to check irc_connected and irc_running before trying to send
        left = data
        while left != "":
            # try:
            # data = left
            # data = left.decode(self.outgoing_encoding)
            data = bytes(data, self.outgoing_encoding)
            sent = self.socket.send(data)
            if len(left) == sent:
                return True
            left = left[sent:]
            # except:
                # self.debug_log("send_all_to_socket errored")
                # return False

    def process_receive_buffer(self):
        if self.recv_buffer != []:
            line = self.recv_buffer.pop(0)
            self.parse_received_line(line)

    # ==============================================================================================
    # Warning: Here be dragons!
    # From here on we do stupidply manual parsing of the received IRC commands
    # ==============================================================================================

    def get_text_data(self, line):
        """Return the last (multi word) parameter in the line, or False if not present."""
        line = line[1:]
        index = line.find(":")
        if index != -1:
            return line[index+1:]
        else:
            return False

    def get_clean_nick(self, nick):
        """Remove the mode char from a nick if it exists."""
        if self.get_mode_chr(nick) != irc_constants.MODE_CHAR_NONE:
            return nick[1:]
        return nick

    def get_mode_chr(self, s):
        """Get the mode from an irc nick."""
        if s[:1] in [irc_constants.MODE_CHAR_VOICE, irc_constants.MODE_CHAR_OP]:
            return s[:1]
        return irc_constants.MODE_CHAR_NONE

    def is_channel_name(self, name):
        return name[0] in irc_constants.CHANNEL_PREFIXES

    def is_command_line(self, line):
        # Commands that are implemented
        cmds = ["ping", "pong", "join", "part", "kick", "topic", "quit", "privmsg", "nick", "mode", "notice"]
        parts = line.split(" ")
        if len(parts) < 2:
            return False
        if parts[1].lower() in cmds:
            return True
        return False

    def is_numeric_line(self, line):
        parts = line.split(" ")
        if len(parts) > 1:
            try:
                numeric = int(parts[1])
                return numeric
            except:
                return False
        return False

    # Beware, this is the real monster!
    # TL;DR: This calls various event methods with relevant arguments
    #         based on the contents of a received IRC command.
    def parse_received_line(self, line):
        """Parse a line from the server and call the apropriate event."""
        # Split line into parts separated by whitespace
        parts = line.split(" ")
        # Get the last argument (that might whitespace) preceded by a colon
        text_data = self.get_text_data(line)
        # The first word of the line delimited first whitespace
        first_word = parts[0].lower()
        # False or a numeric IRC command if one exists
        numeric = self.is_numeric_line(line)

        # Basic commands
        if first_word in ["ping", "error", "notice"]:
            if first_word == "ping":
                self.on_ping(" ".join(parts[1:]))
            elif first_word == "pong":
                self.on_pong()
            elif first_word == "error":
                # ERROR :Closing Link: bot by portlane.se.quakenet.org (G-lined)
                # ERROR :Your host is trying to (re)connect too fast -- throttled
                text = line.lower()
                throttle_indicators = [":closing link:", "throttled", "g-lined"]
                if any(indicator in text for indicator in throttle_indicators):
                    self.on_connect_throttled(text_data)
            else:
                return False

        # Numeric commands
        elif numeric:
            if numeric in [1, 2, 3]:       # Welcome info
                self.on_welcome_info(text_data)
            elif numeric == 4:
                self.on_welcome_info(" ".join(parts[3:]))
            elif numeric == 5:
                self.on_support_info(" ".join(parts[3:]))
            elif numeric == 20:
                self.on_processing_connection(text_data)
            elif numeric == 42:
                self.on_your_id(parts[3], text_data)
            elif numeric in [251, 252, 253, 254, 255]:
                self.on_server_info(" ".join(parts[3:]))
            # WHOIS responses
            elif numeric in [311]:         # Parse whois responses
                nick = parts[3]
                if numeric == 311:
                    hostname = parts[4] + "@" + parts[5]
                    self.on_whois_hostname(nick, hostname)
            # MOTD (Message Of The Day)
            elif numeric in [375, 372]:    # Start of MOTD, First line of MOTD
                self.on_motd(text_data)
            elif numeric in [376, 422]:    # End of MOTD, No MOTD
                self.on_end_motd()
                self.on_irc_ready()
            # Channel specific numeric commands
            elif numeric in [324, 329, 332, 333, 353, 366, 473]:  # Channel numerics
                self.debug_log("CHAN LINE:", line)
                channel = parts[3]
                # Channel creation and modes
                if numeric in [324, 329]:
                    value = parts[4]
                    if numeric == 329:                                  # Channel creation time
                        self.on_channel_created(channel, value)
                    elif numeric == 324:                                # Channel modes
                        modes = list(value.replace("+", ""))
                        self.on_channel_modes_are(channel, modes)
                # Topic
                elif numeric == 332:                                    # Channel topic
                    self.on_channel_topic_is(channel, text_data)
                # Topic metadata (creation time)
                elif numeric == 333:                                    # Channel topic metadata
                    nick = parts[4]
                    utime = int(parts[5])
                    self.on_channel_topic_meta(channel, nick, utime)
                # elif numeric == 353:                                    # Reply to NAMES
                #     channel = parts[4]
                #     nicks = self.get_text_data(line).split(" ")
                #     users = []
                #     for raw_nick in nicks:
                #         nick = self.GetCleanNick(raw_nick)
                #         mode = self.GetMode(raw_nick)
                #         users.append((nick, mode))
                #     self.OnChannelHasUsers(channel, users)
                elif numeric == 366:                                    # End of NAMES
                    pass
                elif numeric == 473:                                    # Channel is invite only
                    self.on_channel_invite_only(channel, text_data)
                elif numeric == 475:
                    self.on_channel_needs_password(channel, text_data)
                elif numeric == 433:
                    nick = parts[3]
                    self.on_nick_in_use(nick, text_data)
            elif numeric == 465:
                self.on_connect_throttled(text_data)
        # If the command type wasn't detected (and handled) at all
        else:
            return False
        return True


class CustomIRCClient(IRCClient):
    def on_connected(self):
        IRCClient.on_connected(self)
        self.send("JOIN #wavi")

    def on_irc_ready(self):
        IRCClient.on_connected(self)
        self.send("JOIN #wavi")


def test_blocking(irc):
    # Test the IRC default client implementation (blocking)
    irc.init()
    irc.run()
    print(irc.events_run)


def test_nonblocking(irc):
    # Test the IRC client without blocking
    irc.init()
    if irc.connect():
        while irc.irc_connected:
            irc.maintain()
            time.sleep(0.05)
    print(irc.events_run)


def test_custom():
    # Test the IRC client with a custom non-blocking implementation
    irc = CustomIRCClient("irc.quakenet.org", 6667, "bx2-draft")
    irc.init()
    if irc.connect():
        while irc.irc_connected:
            irc.maintain()
            time.sleep(0.05)
    print(irc.events_run)


def run(mode=None):
    irc_client = IRCClient("irc.quakenet.org", 6667, "bx2-draft")
    if mode == "nonblocking":
        return test_nonblocking(irc_client)
    elif mode == "custom":
        irc_client = CustomIRCClient("irc.quakenet.org", 6667, "bx2-draft")
        return test_custom()
    else:
        return test_blocking(irc_client)


if __name__ == "__main__":
    # Run the IRC client test
    run("custom")
    # run()
