# BX2 Planning

## Original BX limitations (stuff to fix)
 * No setup.py
 * Single server only
 * Unclear API
     * Kludgy event system
 * Kludgy config
 * Custom logging system
     * Bloated command line logging
     * Use logging library instead?
 * Unreliable 'bookkeeping' (tracking users, channels and the bot nick)
 * User privileges are global (No channel specific permissions)
 * IRC lib only has multiple callback events (Can't listen to all events via one callback)
 * Only config and modules can be reloaded, but not the core
     * Would be nice to be able to reload core classes
     * Requires serializing all class instances. Only the sockets need to stay.
     * When all the classes are reloaded, they should be re-initialized 

## New Features
 * Multi-server support
 * Rebooting of bot(s) without losing connection
 * Integrated HTTP server (for sending logs etc)
 * Remotely updating the bot from the github repository


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
