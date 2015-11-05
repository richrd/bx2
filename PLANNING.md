# BX2 Planning

## Original BX limitations (stuff to fix)
 * No setup.py
 * Single server only
 * Unclear API
 * Kludgy event system
 * Kludgy config
 * Custom logging system
     * Bloated command line logging
     * Should use logging library instead?
 * Unreliable 'bookkeeping' (tracking users, channels and the bot nick)
 * User privileges are global (No channel specific permissions)
 * Custom IRC lib only has multiple callback events (Can't listen to all events via one callback)
 * Only config and modules can be reloaded, but not the core
     * Would be nice to be able to reload core classes
     * Requires serializing all class instances. Only the sockets need to stay.
     * When all the classes are reloaded, they should be re-initialized 

## New Features
 * [X] Multi-server support
 * [X] Rebooting of bot(s) without losing connection
 * [X] Integrated HTTP server (for sending logs, providing API etc)
 * [ ] Remotely updating the bot from the github repository
 * [ ] Support server passwords
 * [ ] Verify all core modules before reloading to avoid syntax error crashes
 * [ ] Automatically get a hostname with USERHOST
 * [ ] MAYBE use 005:
       > In early implementations of IRC this had to be hard-coded in the
       > client but there is now a de facto standard extension to the protocol
       > called ISUPPORT that sends this information to the client at connect
       >time using numeric 005.

## Plugins

### Core Plugins

* [ ] addaccount
> Add a new bot account.

* [ ] alias
> Add an alias for a command.

* [X] auth
> Log in to the bot with an existing username and password.

* [ ] autochanmode
> Maintain channel modes (modes are defined in server channel config).

* [ ] autoop
> Automatically op trusted users (**How to define user and channel to auto op?**).

* [ ] autorejoin
> Automatically rejoin a channel after kick.

* [ ] broadcast
> Broadcast messages or command output to channels and/or users (targets) at a defined interval.

* [ ] calc
> Calculator: calculate basic math and show result. (Use https://github.com/danthedeckie/simpleeval/)

* [ ] clearlogs
> Clear logs in a window. Clear all by default or clear messages since a time or duration.

* [ ] commands
> List the commands that the user has access to.

* [ ] deauth
> Log out of the bot.

* [ ] dropsend
> Clear the remaining send message queue (data queued for sending to the server).

* [X] help
> Bot help command.

* [ ] highlight
> Highlight everyone on current channel.

* [X] join
> Make the bot join a channel (or rejoin the current channel).

* [X] level
> Show the permission level of the asking user (or a specified user).

* [ ] logs
> Get channel logs. Allows asking for specific channel (if sufficient privileges) and send logs as a HTTP link.

* [ ] msg
> Make the bot send a message to a user or channel

* [ ] msgcount
> Show log size for window.

* [ ] newpass
> Change user password.

* [X] nick
> Change bot nick.

* [X] part
> Make the bot leave the current channel (or a specified channel).

* [X] ping
> ping the bot to see if it's alive

* [ ] raw
> Send raw data to IRC server.

* [ ] reconnect
> Reconnect to an irc server.

* [ ] run
> Run a command as a specifi user on a channel in a certain IRC network.

* [ ] topic
> Change channel topic.

* [ ] trustme
> Associate a user hostname with their account.

* [X] url
> Show url titles.

### Extra Plugins

* broadcast
> Broadcast a message or command output to a target on a specific interval.

* tell
> Queue a message to a user for sending when they come online.

* vote
> Voting feature.

* weather
> Show weather for different locations.


## Architecture

### IRC Lib
We're using a custom IRC Client library to limit external dependencies (also for learning purpouses)
It's a bit crude with the parsing, but it works well. The new version also emits events instead of relying on callbacks.

### Classes
 * App
     * HTTPServer
         * PycoHTTP
     * Bot
         * IRCClient
         * Event
         * User
         * Message
         * Window
             * Channel
             * Query
             * self.log of channel activity (for logs etc)
         * Module

### Bookkeeping

* [ ] Bot
    * [X] Own nick
    * [ ] What channels are really joined (check kick & ban etc)

* [ ] User status (online/authed/last_action etc).
    * [ ] online
        * [ ] User must be set to online when:
            * [ ] They are seen
            * [ ] They perform an action
        * [X] User must be set offline when:
            * [X] They quit
            * [X] The bot gets disconnected (no chance of bookkeeping when not connected)
    * [ ] authed
        * [X] The user should be deauthed when they go offline
        * [X] When the bot disconnects
        * [ ] The user should be authed when their hostname

* [ ] Window status
    * [ ] Users
        * [X] All users in a window must be cleared when:
            * [X] The bot parts that channel
            * [X] When the bot gets disconnected
        * [ ] Modes
    * [X] Channel modes
        * [X] Get modes on join
        * [X] Detect mode changes
    * [ ] Channel topic

### Modules

Modules are python files that implement the required minumum API.
Each file must implement a Module subclass that implements the required features.
Modules respond to their names as a commands, or any events they subscribe to.

**Each module can optionally declare the following:**

 * **name** (the filename without '.py' is automatically the module name)
     > The unique name of the module. If the module can be executed as a command, this is the command name that runs it.
     > *Maybe add an override so that another name can be used for running the command?*

 * **permission_level** (optional, default: 0)
     > The permission level for using the module. By default 0 (available to anyone)

 * **zones** (optional, default: ZONE_ALL)
     > Where the module can be used. Either ZONE_CHANNEL, ZONE_QUERY or ZONE_ALL

 * **throttle*** (optional, default: 1.5)
     > How often the module can be run (interval in seconds)


### Config (global config and defaults)
 * server (used as defaults for all servers, can be overriden in a server config file)
     * nick
     * nick_suffix
     * realname
     * ident
     * send_throttle
     * cmd_prefix
     * cmd_separator
     * cmd_throttle
 * module_aliases

### Server config

All keys in default server configuration can be overriden. Only the non overridable keys are shown here.

 * server
     * enabled (whether the server is used or ignored)
     * name (server identifier)
     * host
     * port
     * channels
         * channel
             * modes

### Account config
 * account
     * name (account user name)
     * password (sha224 or md5 hexdigest)
     * level (account permission level)
     * servers (servers where the account can be used. corresponds to server name)
         * server_name
     * hostnames (hostnames that are trusted and used for automatic authentication)
         * hostname
     * enabled True/False ???

### Permission system

Basic permissions are defined by an intiger. By default it ranges from 0 to 100.

**Levels:**

 * 0: GUEST - Not truested at all.
 > No special access. This is the default permission level for everyone.

 * 1 - 9: AQUAINTANCE - Slightly trusted.
 > Lowest tier permissions. Might have some basic access that normal users don't have.

 * 10 - 19: FRIEND - Trusted.
 > Can use features such as auto op, getting logs on certain channels etc.

 * 20 - 99: CURRENTLY UNDEFINED

 * 100 and up: OWNER - Can do anything, and potentially run arbitrary code on the server


