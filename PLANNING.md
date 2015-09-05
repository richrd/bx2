# BX2 Planning

## Original BX limitations
 * No setup.py
 * Single server only
 * Unclear API
     * Kludgy event system
 * Kludgy config
 * Custom logging system
     * Use logging library instead?
 * Bloated command line logging
 * Unreliable 'bookkeeping' (tracking users, channels and the bot nick)
 * User privileges are global (No channel specific permissions)
 * IRC lib only has multiple callback events (Can't listen to all events via one callback)
 * Only config and modules can be reloaded, but not the core
     * Would be nice to be able to reload core classes
   

## Architecture

### Classes
 * User
 * Message
 * Window
     * Channel
     * Query
 * 
 
### Config
 * global-config
     * aliases
     * 

 * server
     * host
     * port
     * send_throttle

     * cmd_prefix
     * cmd_separator
     * cmd_throttle

     * identity
         * nick
         * nick_suffix
         * realname
         * ident
         
     * channels
         * channel
             * modes
         

 * accounts
     * account
         * name
         * level
         * servers
             * server ...
         * hostnames
             * hostname ...
