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
 * Multi-server support
 * Rebooting of bot(s) without losing connection
 * Integrated HTTP server (for sending logs etc)
 * Remotely updating the bot from the github repository

## Plugins

### Core Plugins

* addaccount
> Add a new bot account.

* alias
> Add an alias for a command.

* auth
> Log in to the bot with an existing username and password.

* autochanmode
> Maintain channel modes (modes are defined in server channel config).

* autoop
> Automatically op trusted users (**How to define user and channel to auto op?**).

* autorejoin
> Automatically rejoin a channel after kick.

* broadcast
> Broadcast messages or command output to channels and/or users (targets) at a defined interval.

* calc
> Calculator: calculate basic math and show result. (Use https://github.com/danthedeckie/simpleeval/)

* clearlogs
> Clear logs in a window. Clear all by default or clear messages since a time or duration.

* commands
> List the commands that the user has access to.

* deauth
> Log out of the bot.

* dropsend
> Clear the remaining send message queue (data queued for sending to the server).

* help
> Bot help command.

* highlight
> Highlight everyone on current channel.

* join
> Make the bot join a channel (or rejoin the current channel).

* level
> Show the permission level of the asking user (or a specified user).

* logs
> Get channel logs. Allows asking for specific channel (if sufficient privileges) and send logs as a HTTP link.

* msg
> Make the bot send a message to a user or channel

* msgcount
> Show log size for window.

* newpass
> Change user password.

* nick
> Change bot nick.

* part
> Make the bot leave the current channel (or a specified channel).

* ping
> ping the bot to see if it's alive

* raw
> Send raw data to IRC server.

* reconnect
> Reconnect to an irc server.

* run
> Run a command as a specifi user on a channel in a certain IRC network.

* topic
> Change channel topic.

* trustme
> Associate a user hostname with their account.

* url
> Show url titles.

### Extra Plugins

* broadcast
> Broadcast a message or command output to a target on a specific interval.

* tell
> Queue a message to a user for sending when they come online.

* weather
> Show weather for different locations.



## Architecture

### IRC Lib
We're using a custom IRC Client library to limit external dependencies (also for learning purpouses)
It's a bit crude with the parsing, but it works well. The new version also emits events instead of relying on callbacks.

### Classes
 * IRCClient
 * Event
 * User
 * Message
 * Window
     * Channel
     * Query
 * Plugin

#### Plugins

Plugins are python files that implement the required minumum API.
Each file must implement a Plugin subclass that implements the required features.
Plugins respond to their names as a commands, or any events they subscribe to.

**Each plugin needs to declare the following:**

 * **name**
     > The unique name of the plugin. If the plugin can be executed as a command, this is the command name that runs it.
     > *Maybe add an override so that another name can be used for running the command?*

 * **permission_level** (optional, default: 0)
     > The default permission level for using the plugin

 * **zones** (optional, default: ZONE_ALL)
     > Where the plugin can be used. Either ZONE_CHANNEL, ZONE_QUERY or ZONE_ALL

 * **throttle*** (optional, default: ZONE_ALL)
     > How often the plugin can be run (interval in seconds)


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

#### Server config

All keys in default server configuration can be overriden. Only the non overridable keys are shown here.

 * server
     * name (server identifier)
     * host
     * port
     * channels
         * channel
             * modes

#### Account config
 * account
     * name (account user name)
     * level (account permission level)
     * servers (servers where the account can be used. corresponds to server name)
         * server
     * hostnames (hostnames that are trusted and used for automatic authentication)
         * hostname
