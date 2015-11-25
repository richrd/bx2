# -*- coding: utf-8 -*-
"""irc.py: IRC Client Implementation

Handles all neccessary parts of the IRC protocol for client connections.
Sits in IRC doing nothing except respond to PINGs.
"""

import sys
import time
import select
import socket
import inspect
import logging
import traceback

from . import irc_constants


class IRCClient:
    """Independet IRC client that will connect and sit on an IRC server doing nothing.

    It can be subclassed to do whatever, without any need to worry about the protocol.
    """

    def __init__(self, host="", port=6667, nick="bx-irc-lib"):
        # Logging
        self.logger = logging.getLogger(__name__)

        self.debugging = 1

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

        # The socket object for the connection
        self.socket = None

        # TODO: Implement setter
        # How many seconds to wait between lines sent to the server
        self.send_throttling = 0.05

        # TODO: Implement setter
        # What encoding to use when sending to the IRC server
        self.outgoing_encoding = "utf-8"

        # TODO: Implement setter
        # Encodings to use when trying to decode incomming data
        self.incomming_encodings = ["utf-8", "latin-1", "cp1251", "cp1252", "win1251", "iso-8859-1"]

        # TODO: Implement setter
        # Maximum size for data sent to the IRC server
        self.max_send_length = 400

        # Event handlers (callbacks called with events)
        self.event_handlers = []

        # Exclude event log
        self.exclude_events = [
            "on_ping",
            "on_pong",
            "on_i_joined",
            "on_channel_has_users",
            "on_nick_in_use",
            "on_parse_nick_hostname",
            "on_channel_join",
            "on_parse_nick_hostname",
            "on_channel_topic_is",
            "on_channel_user_modes_changed",
            "on_channel_creation_time",
            "on_channel_modes_are",
        ]

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
        # Last time we've pinged the server (resets after the pong response)
        self.pinged_server = False
        # Maximum time of inactivity before reconnecting to the server
        self.max_inactivity = 180  # 3 minutes (NOTE: must be greater than 'self.ping_after'!)

        # Lines waiting to be sent to the IRC server
        self.send_buffer = []
        # Time of last successfull socket send to the server
        self.last_send_time = None

        # Event handlers (callbacks called with events)
        self.event_handlers = []

        # Indicate that init has been done
        self.inited = True

    def debug_log(self, *args):
        if not self.debugging:
            return False
        msg = " ".join(map(str, args))
        print("IRC DEBUG:" + msg)

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

    def set_ident(self, ident):
        self.ident = ident

    def set_realname(self, realname):
        self.realname = realname

    def set_debugging(self, val):
        self.debugging = val

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

    def is_running(self):
        return self.irc_running

    def connect(self):
        self.irc_running = 1
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.settimeout(self.socket_timeout)
        self.debug_log("Connecting to " + self.host + ":" + str(self.port) + "...")
        try:
            self.socket.connect((self.host, self.port))
        except socket.error as err:
            # FIXME: no fallback when this occurs, bot stays offline in infinite loop
            # Simulate by just returning False before the try/except
            self.debug_log("Error connecting:", str(socket.error), str(err))
            return False
        self.on_connected()
        return True

    def disconnect(self):
        self.irc_connected = 0
        self.irc_running = 0
        self.socket.close()
        self.on_disconnect()

    def mainloop(self):
        while self.irc_connected:
            self.on_loop_start()
            result = self.maintain()
            self.on_loop_end()
            if not result:
                return False

    def send(self, data):
        if len(data) > 3 and data[:4] not in ["PING", "PONG"]:
            self.debug_log("send:", data)
        if len(data) > 510:
            self.debug_log("send(): data too long!")
        data += "\r\n"
        self.send_buffer.append(data)

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
            if not self.receive_to_buffer():  # If no data received, sock is dead
                self.disconnect()
                return False
            return True
        # Try to send to the socket
        elif self.socket in writable:
            if not self.process_send_buffer():  # Try to send and break on failure
                return False
        # Die if the socket is errored
        elif self.socket in errored:
            self.debug_log("mainloop()", "socket errored")
            return False
        else:
            self.debug_log("mainloop()", "socket inaccessible")
            self.disconnect()
            return False
        self.process()
        return True

    def keep_alive(self):
        if not self.irc_connected:
            return False
        if self.last_receive_time is not None:
            elapsed = time.time() - self.last_receive_time
        else:
            return
        # Ping the server after inactivity and wait for reply.
        # If no timely response is received, cut the connection and reconnect.
        if elapsed > self.max_inactivity:
            self.debug_log("KeepAlive()", "server not responding to ping, reconnecting.")
            self.on_connection_timeout()
            self.disconnect()
            return
        elif (not self.pinged_server) and elapsed > self.ping_after:
            self.ping_server()

    def ping_server(self):
        self.send("PING " + self.current_nick)
        self.pinged_server = time.time()

    #
    # IRC Actions
    #

    def introduce(self, nick=None, ident=None, realname=None):   # Send NICK and USER messages
        self.debug_log("Introducing as:", "nick:", nick, ", ident:", ident, ", realname:", realname)
        if nick is None:
            nick = self.current_nick
        if ident is None:
            ident = self.ident
        if realname is None:
            realname = self.realname
        self.change_nick(nick)
        self.send("USER {} 8 * :{}".format(ident, realname))

    def change_nick(self, nick=None):
        self.debug_log("Changing nick to:", nick)
        if nick is None:
            nick = self.default_nick
        self.set_nick(nick)
        self.send("NICK {}".format(nick))

    def join_channels(self, channels, keys=[]):
        if isinstance(channels, str):
            channels = [channels]
        chanlist = ",".join(channels)
        keylist = ",".join(keys)
        self.send("JOIN {} {}".format(chanlist, keylist))

    def part_channels(self, channels):
        if type(channels) in [str]:
            channels = [channels]
        chanlist = ",".join(channels)
        self.send("PART {}".format(chanlist))

    def join(self, channel, keys=[]):
        self.join_channels(channel, keys)

    def part(self, channel):
        self.part_channels(channel)

    def whois(self, nick):
        self.send("WHOIS {} {}".format(nick, nick))

    def kick(self, chan, nick, message=""):
        self.send("KICK {} {} {}".format(chan, nick, message))

    def privmsg(self, dest, msg):
        if not msg:
            return False
        # TODO: wrap long msgs into multiple PRIVMSGs
        self.send("PRIVMSG {} :{}".format(dest, msg))

    def notice(self, dest, msg):
        if not msg:
            return False
        # TODO: wrap long msgs into multiple NOTICEs
        self.send("NOTICE {} :{}".format(dest, msg))

    def action(self, dest, msg):
        self.privmsg(dest, "\x01ACTION {}\x01".format(msg))

    def set_channel_user_modes(self, chan, nickmodes, operation=True):
        """Set user modes on channel."""
        if operation:
            modes = "+"
        else:
            modes = "-"
        nicks = []
        for item in nickmodes:
            nicks.append(item[0])
            modes += item[1]
        self.send(u"MODE {} {} {}".format(chan, modes, (" ".join(nicks))))

    def set_channel_topic(self, chan, topic):
        self.send("TOPIC {} :{}".format(chan, topic))

    def set_channel_modes(self, chan, modes):
        self.send("MODE {} {}".format(chan, modes))

    def ask_channel_modes(self, chan):
        self.send("MODE {}".format(chan))

    #
    # Client Events
    #

    def on_connected(self):
        """Called when the client has connected to the server."""
        self.irc_connected = True
        self.last_receive_time = time.time()
        self._dispatch_event()
        self.introduce()

    def on_disconnect(self):
        self.irc_connected = False
        self._dispatch_event()

    def on_ready(self):
        self._dispatch_event()

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
        self._dispatch_event()

    def on_connection_timeout(self):
        """Called when the server connecting isn't respondig."""
        self.debug_log("Connection timed out.")
        self._dispatch_event()

    def on_ping(self, data):
        """Callend when a PING event is received."""
        self._dispatch_event()
        self.send("PONG {}".format(data))

    def on_pong(self, data):
        """Callend when a PONG event is received."""
        self._dispatch_event()
        self.pinged_server = False

    def on_motd(self, data=""):
        """Called for each line in the MOTD (Message Of The Day)"""
        # self._dispatch_event()  # TODO: Enable

    def on_end_motd(self):
        """Called when the MOTD ends or when there is no MOTD."""
        self._dispatch_event()

    def on_nick_in_use(self, nick, data):
        self._dispatch_event()
        self.change_nick(self.get_nick() + "_")

    def on_welcome_info(self, data):
        """Sent when welcome info is received."""  # TODO: More elaborate docstring.
        self._dispatch_event()

    def on_support_info(self, data):
        """Sent when support info is received."""  # TODO: More elaborate docstring.
        self._dispatch_event()

    def on_server_info(self, data):
        """Sent when server info is received."""  # TODO: More elaborate docstring.
        self._dispatch_event()

    def on_processing_connection(self, data):
        self._dispatch_event()

    def on_your_id(self, id, data):
        self._dispatch_event()

    def on_parse_nick_hostname(self, nick, hostname):
        self._dispatch_event()

    def on_whois_hostname(self, nick, hostname):
        self._dispatch_event()

    def on_privmsg(self, nick, target, data):
        self._dispatch_event()

    def on_notice(self, nick, target, data):
        self._dispatch_event()

    def on_quit(self, nick, reason):
        self._dispatch_event()

    def on_nick_changed(self, nick, new_nick):
        self._dispatch_event()

    def on_my_modes_changed(self, modes):
        self._dispatch_event()

    def on_channel_user_modes_changed(self, channel, modes, nick):
        self._dispatch_event()

    def on_channel_modes_changed(self, channel, modes, nick):
        self._dispatch_event()

    # Channel specific events
    def on_channel_topic_is(self, channel, data):
        self._dispatch_event()

    def on_channel_topic_changed(self, channel, nick, data):
        self._dispatch_event()

    def on_channel_topic_meta(self, channel, nick, utime):
        self._dispatch_event()

    def on_channel_invite_only(self, channel, data):
        self._dispatch_event()

    def on_channel_needs_password(self, channel, data):
        self._dispatch_event()

    def on_channel_creation_time(self, channel, value):
        self._dispatch_event()

    def on_channel_modes_are(self, channel, modes):
        self._dispatch_event()

    def on_channel_has_users(self, channel, users):
        self._dispatch_event()

    def on_i_joined(self, channel):
        self._dispatch_event()

    def on_channel_join(self, channel, nick):
        self._dispatch_event()

    def on_channel_part(self, channel, nick, data):
        self._dispatch_event()

    def on_channel_kick(self, channel, nick, who, reason):
        self._dispatch_event()

    # All events
    def on_event(self, name, args):
        """Called for each event that occurs, with event name and arguments."""
        if name not in self.exclude_events:
            self.debug_log("EVT: {} {}".format(name, args))
        for handler in self.event_handlers:
            handler(name, args)

    def add_event_handler(self, callback):
        self.event_handlers.append(callback)

    def _dispatch_event(self):
        """Should be called from event handling methods.

        It automagically determins the event name and arguments given to it and forwards them to on_event.
        """
        try:
            frame_info = inspect.getouterframes(inspect.currentframe())[1]
            frame = frame_info[0]
            name = frame_info[3]
            args = self._get_frame_args(frame)
            args["time"] = time.time()
        except Exception:
            self.logger.exception("_dispatch_event failed")
            return False
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
            self.pinged_server = False  # Reset ping status
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
            self.keep_alive()
        except Exception as e:
            print(traceback.format_exc())
            print(sys.exc_info()[0])
            self.debug_log("Process()", e)

    def process_send_buffer(self):
        """Send a single line from the send buffer."""
        if self.send_buffer != []:
            # Make sure we don't send lines to the server too often and get kicked out
            if self.last_send_time is None or time.time() - self.last_send_time > self.send_throttling:
                line = self.send_buffer.pop(0)
                if not self.send_all_to_socket(line):
                    self.debug_log("process_send_buffer: send_all_to_socket failed")
                    return False
                self.last_send_time = time.time()
        return True

    def send_all_to_socket(self, data):
        # TODO: Might want to check irc_connected and irc_running before trying to send
        left = data
        while left != "":
            # try:
            # data = left
            # data = left.decode(self.outgoing_encoding)
            data = bytes(left, self.outgoing_encoding)
            sent = self.socket.send(data)
            if len(left) == sent:
                return True
            left = left[sent:]
            # except:
            #     self.debug_log("send_all_to_socket errored")
            #     return False
        return False

    def process_receive_buffer(self):
        if self.recv_buffer != []:
            line = self.recv_buffer.pop(0)
            parsed = self.parse_received_line(line)
            if not parsed:
                self.debug_log("UNPARSED {} LINE:{}".format(parsed, line))
                # IRC DEBUG:UNPARSED False LINE:NOTICE AUTH :*** Looking up your hostname
                # IRC DEBUG:UNPARSED False LINE:NOTICE AUTH :*** Checking Ident
                # IRC DEBUG:UNPARSED False LINE:NOTICE AUTH :*** Found your hostname
                # IRC DEBUG:UNPARSED False LINE:NOTICE AUTH :*** No ident response
                # IRC DEBUG:UNPARSED False LINE::servercentral.il.us.quakenet.org 221 bx +i

    # ======================================================================== #
    # Warning: Here be dragons!                                                #
    # From here on we do stupidply manual parsing of the received IRC commands #
    # TODO: Refactor and use regex!                                            #
    # ======================================================================== #

    def get_text_data(self, line):
        """Return the last (multi word) parameter in the line, or False if not present."""
        line = line[1:]
        index = line.find(":")
        if index != -1:
            return line[index+1:]
        else:
            data = line.split()[-1]
            if data[0] == ":":
                data = data[1:]
            return data

    def get_clean_nick(self, nick):
        """Remove the mode char from a nick if it exists."""
        if self.get_mode_char(nick) != irc_constants.MODE_CHAR_NONE:
            return nick[1:]
        return nick

    def get_mode_char(self, s):
        """Get the mode from an irc nick."""
        if s[:1] in [irc_constants.MODE_CHAR_VOICE, irc_constants.MODE_CHAR_OP]:
            return s[:1]
        return irc_constants.MODE_CHAR_NONE

    def get_nick_mode(self, nick):
        modechr = self.get_mode_char(nick)
        if modechr == irc_constants.MODE_CHAR_NONE:
            return irc_constants.MODE_NONE
        elif modechr == irc_constants.MODE_CHAR_OP:
            return irc_constants.MODE_OP
        elif modechr == irc_constants.MODE_CHAR_VOICE:
            return irc_constants.MODE_VOICE

    def is_channel_name(self, name):
        return name[0] in irc_constants.CHANNEL_PREFIXES

    def get_text_command(self, line):
        # Commands that are implemented
        cmds = ["ping", "pong", "join", "part", "kick", "topic", "quit", "privmsg", "nick", "mode", "notice"]
        parts = line.split(" ")
        if len(parts) < 2:
            return False
        if parts[1].lower() in cmds:
            return parts[1].lower()
        return False

    def get_numeric_command(self, line):
        parts = line.split(" ")
        if len(parts) > 1:
            try:
                numeric = int(parts[1])
                return numeric
            except:
                return False
        return False

    def parse_nick_host(self, line):
        nick = ""
        part = line.split(" ")[0][1:]
        ind = part.find("!")
        if ind != -1:
            nick = part[:ind]
            hostname = part[ind+1:]
        else:
            hostname = part[1:]
        if nick != "":
            self.on_parse_nick_hostname(nick, hostname)
        return nick, hostname

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
        # False or a IRC text command
        command = self.get_text_command(line)
        # False or a numeric IRC command if one exists
        numeric = self.get_numeric_command(line)

        # Basic commands
        if first_word in ["ping", "error", "notice"]:
            if first_word == "ping":
                self.on_ping(" ".join(parts[1:]))
            elif first_word == "pong":
                self.on_pong()
            elif first_word == "error":
                # ERROR :Closing Link: bot by portlane.se.quakenet.org (G-lined)
                # ERROR :Your host is trying to (re)connect too fast -- throttled
                # ERROR :Your host is trying to (re)connect too fast -- throttled
                self.debug_log("ERROR:", line)
                text = line.lower()
                throttle_indicators = [":closing link:", "throttled", "g-lined"]
                if any(indicator in text for indicator in throttle_indicators):
                    self.on_connect_throttled(text_data)
            else:
                return False
            return True
        # IRC text commands
        elif command:
            nick, hostname = self.parse_nick_host(line)
            target = parts[2]  # Channel or user
            if command == "pong":
                self.on_pong(text_data)
            elif command == "join":
                if text_data is not False:
                    channel = text_data
                else:
                    channel = parts[2]
                if nick == self.current_nick:
                    self.on_i_joined(channel)
                else:
                    self.on_channel_join(channel, nick)
            elif command == "part":
                if text_data is not False:
                    target = text_data
                self.on_channel_part(target, nick, text_data)
            elif command == "topic":
                self.on_channel_topic_changed(target, nick, text_data)
            elif command == "privmsg":
                self.on_privmsg(nick, target, text_data)
            elif command == "notice":
                if nick:
                    self.on_notice(nick, target, text_data)
            elif command == "quit":
                self.on_quit(nick, text_data)
            elif command == "kick":
                who = parts[3]
                kicked_by = nick
                self.on_channel_kick(target, who, kicked_by, text_data)
            elif command == "nick":
                self.on_nick_changed(nick, text_data)
            elif command == "mode":
                if target == self.current_nick:
                    modes = parts[3]
                    self.on_my_modes_changed(modes)
                else:
                    # TODO: move this to a method!
                    types = ["-", "+"]
                    modes = parts[3]
                    if len(parts) > 4:      # Channel user modes are being set
                        nicks = parts[4:]
                        i = 0
                        operation = True
                        users = []
                        for mode in modes:
                            char = modes[i]
                            if char in types:
                                if char == "-":
                                    operation = False
                                elif char == "+":
                                    operation = True
                                modes = modes[1:]
                                continue
                            modechr = modes[i]
                            if modechr == "o":
                                modeval = irc_constants.MODE_OP
                            elif modechr == "v":
                                modeval = irc_constants.MODE_VOICE
                            else:
                                modeval = modechr
                            if i < len(nicks)-1:
                                mnick = nicks[i]
                            else:
                                mnick = nicks[-1]
                            user = (mnick, modeval, operation)
                            users.append(user)
                            i += 1
                        self.on_channel_user_modes_changed(target, users, nick)
                    else:
                        modes = parts[3]
                        self.on_channel_modes_changed(target, modes, nick)
            else:
                return False
            return True

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
            elif numeric in [311, 312, 319, ]:         # Parse whois responses
                nick = parts[3]
                if numeric == 311:
                    hostname = parts[4] + "@" + parts[5]
                    self.on_whois_hostname(nick, hostname)
                if numeric == 312:
                    # TODO: Whois server
                    pass
                if numeric == 319:
                    # TODO: Whois channels
                    pass
            # MOTD (Message Of The Day)
            elif numeric in [375, 372]:    # Start of MOTD, First line of MOTD
                self.on_motd(text_data)
            elif numeric in [376, 422]:    # End of MOTD, No MOTD
                self.on_end_motd()
                self.on_ready()
            # Channel specific numeric commands
            elif numeric in [324, 329, 332, 333, 353, 366, 473]:  # Channel numerics
                channel = parts[3]
                # Channel creation and modes
                if numeric in [324, 329]:
                    value = parts[4]
                    if numeric == 329:                                  # Channel creation time
                        self.on_channel_creation_time(channel, value)
                    elif numeric == 324:                                # Channel modes
                        modes = list(value.replace("+", ""))
                        if "o" in modes:
                            modes["o"] == irc_constants.MODE_OP
                        if "v" in modes:
                            modes["v"] == irc_constants.MODE_VOICE
                        self.on_channel_modes_are(channel, modes)
                # Topic
                elif numeric == 332:                                    # Channel topic
                    self.on_channel_topic_is(channel, text_data)
                # Topic metadata (creation time)
                elif numeric == 333:                                    # Channel topic metadata
                    nick = parts[4]
                    utime = int(parts[5])
                    self.on_channel_topic_meta(channel, nick, utime)
                elif numeric == 353:                                    # Reply to NAMES
                    channel = parts[4]
                    nicks = text_data.split(" ")
                    users = []
                    for raw_nick in nicks:
                        nick = self.get_clean_nick(raw_nick)
                        mode = self.get_nick_mode(raw_nick)
                        users.append((nick, mode))
                    self.on_channel_has_users(channel, users)
                elif numeric == 366:                                    # End of NAMES
                    pass
                elif numeric == 473:                                    # Channel is invite only
                    self.on_channel_invite_only(channel, text_data)
                elif numeric == 475:
                    self.on_channel_needs_password(channel, text_data)
                else:
                    return False
                return True
            elif numeric == 433:
                nick = parts[3]
                self.on_nick_in_use(nick, text_data)
            elif numeric == 465:
                self.on_connect_throttled(text_data)
            else:
                return False
            return True
        # If the command type wasn't detected (and handled) at all
        else:
            return False
        return True

    def _serialize(self):
        serialized = {
            "host": self.host,
            "port": self.port,
            "default_nick": self.default_nick,
            "default_realname": self.default_realname,
            "default_ident": self.default_ident,
            "realname": self.realname,
            "ident": self.ident,
            "send_throttling": self.send_throttling,
            "outgoing_encoding": self.outgoing_encoding,
            "incomming_encodings": self.incomming_encodings,
            "max_send_length": self.max_send_length,
            "current_nick": self.current_nick,
            "irc_connected": self.irc_connected,
            "last_connect_time": self.last_connect_time,
            "irc_ready": self.irc_ready,
            "irc_running": self.irc_running,
            "socket": self.socket,
            "socket_timeout": self.socket_timeout,
            "select_interval": self.select_interval,
            "read_chunk_size": self.read_chunk_size,
            "raw_buffer": self.raw_buffer,
            "recv_buffer": self.recv_buffer,
            "last_receive_time": self.last_receive_time,
            "last_ping_time": self.last_ping_time,
            "last_pong_time": self.last_pong_time,
            "ping_after": self.ping_after,
            "pinged_server": self.pinged_server,
            "max_inactivity": self.max_inactivity,
            "send_buffer": self.send_buffer,
            "last_send_time": self.last_send_time,
        }
        return serialized

    def _unserialize(self, serialized):
        self.host = serialized["host"]
        self.port = serialized["port"]
        self.default_nick = serialized["default_nick"]
        self.default_realname = serialized["default_realname"]
        self.default_ident = serialized["default_ident"]
        self.realname = serialized["realname"]
        self.ident = serialized["ident"]
        self.send_throttling = serialized["send_throttling"]
        self.outgoing_encoding = serialized["outgoing_encoding"]
        self.incomming_encodings = serialized["incomming_encodings"]
        self.max_send_length = serialized["max_send_length"]
        self.current_nick = serialized["current_nick"]
        self.irc_connected = serialized["irc_connected"]
        self.last_connect_time = serialized["last_connect_time"]
        self.irc_ready = serialized["irc_ready"]
        self.irc_running = serialized["irc_running"]
        self.socket = serialized["socket"]
        self.socket_timeout = serialized["socket_timeout"]
        self.select_interval = serialized["select_interval"]
        self.read_chunk_size = serialized["read_chunk_size"]
        self.raw_buffer = serialized["raw_buffer"]
        self.recv_buffer = serialized["recv_buffer"]
        self.last_receive_time = serialized["last_receive_time"]
        self.last_ping_time = serialized["last_ping_time"]
        self.last_pong_time = serialized["last_pong_time"]
        self.ping_after = serialized["ping_after"]
        self.pinged_server = serialized["pinged_server"]
        self.max_inactivity = serialized["max_inactivity"]
        self.send_buffer = serialized["send_buffer"]
        self.last_send_time = serialized["last_send_time"]


class CustomIRCClient(IRCClient):
    def on_irc_ready(self):
        IRCClient.on_irc_ready(self)
        self.send("JOIN #wavi")


def test_blocking(irc):
    # Test the IRC default client implementation (blocking)
    irc.init()
    irc.run()
    return irc


def test_nonblocking(irc):
    # Test the IRC client without blocking
    irc.init()
    if irc.connect():
        while irc.irc_connected:
            try:
                irc.maintain()
                time.sleep(0.05)
            except KeyboardInterrupt:
                break
    return irc


def test_custom():
    # Test the IRC client with a custom non-blocking implementation
    irc = CustomIRCClient("irc.quakenet.org", 6667, "bx2-draft")
    test_nonblocking(irc)
    return irc


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
    irc = run("custom")
