# -*- coding: utf-8 -*-
"""irc.py: IRC Client Implementation

Handles all neccessary parts of the IRC protocol for client connections.

"""

import time
import select
import socket


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
        self.nick = self.default_nick

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

    #
    # Setters
    #
    def set_host(self, host):
        self.host = host

    def set_port(self, port):
        self.port = port

    #
    # Client actions
    #
    def debug_log(self, *args):
        msg = ", ".join(args)
        print(msg)

    def run(self):
        pass

    def start(self, block=True):
        self.debug_log("Starting client...")
        connected = self.connect()
        if connected:
            self.last_connect_time = time.time()
            self.irc_running = 1
            if block:
                status = self.mainloop()
                return status
            else:
                return True
        else:
            return False

    def stop(self):
        self.debug_log("stop()")
        self.disconnect()

    def connect(self):
        self.irc_running = 0

    def disconnect(self):
        pass

    def mainloop(self):
        while self.irc_running:
            result = self.maintain()
            if not result:
                return False

    def maintain(self):
        ret_val = False  # Flag indicating success
        try:
            self.on_loop_start()
            try:
                sockl = [self.socket]
                readable, writable, errored = select.select(sockl, sockl, sockl, self.select_interval)
                time.sleep(self.select_interval)  # TODO: do we really need this?
            except (socket.error) as err:
                self.debug_log("mainloop()", "select error:", socket.error, err)
                ret_val = False
            if self.socket in readable:
                # Socket is readable
                receive_ok = self.receive_to_buffer()  # Try to receive and break on failure
                if not receive_ok:                     # If no data received, sock is dead
                    self.disconnect()
                    ret_val = False
                ret_val = True
            elif self.socket in errored:
                # Socket has an error
                self.debug_log("mainloop()", "socket errored")
                ret_val = False
            elif self.socket in writable:
                # Socket is writable
                send_ok = self.process_send_buffer()  # Try to send and break on failure
                if not send_ok:
                    ret_val = False
            else:
                self.debug_log("mainloop()", "socket inaccessible")
            self.Process()
            ret_val = True
        except KeyboardInterrupt:
            return self.on_kbd_interrupt()
        self.on_loop_end()
        return ret_val

    #
    # Client Events
    #
    def on_connected(self):
        """Called when the client has connected to the server."""
        pass

    def on_loop_start(self):
        """Called before the client loop begins."""
        pass

    def on_loop_end(self):
        """Called when the client loop ends."""
        pass


def run():
    # Test the IRC client implementation
    irc = IRCClient("irc.quakenet.org", 6667, "bx2")
    irc.init()
    irc.run()

if __name__ == "__main__":
    # Run the IRC client test
    run()
