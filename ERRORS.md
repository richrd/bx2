
# Unresolved

## Reconnect Race

*Description*

The bot seems to get stuck when simultaneously reconnecting to multiple servers.
If multiple servers deny connecting the round trip time to update a working bot becomes high.
Example: 1 bot out of 4 is connected and 3 bots are failing to connect.
Each failing bot waits at least 5 seconds before moving on.
Sleep time increases by 30 seconds by default with each failed connect.
The worst case scenario is an infinite wait time for one server, blocking the others forever.

*Solution*
 - Add hard limit to reconnect wait time 
 > This only serve as the last safety guard
 
 - Implement waiting via non-blocking polling instead of raw time.sleep()
 > Add reconnect_schedule (unix timestamp) to bot and check it on each maintain
 > When time.time() passes reconnect_schedule initiate the reconnect and remove reconnect_schedule


18

# Resolved

## Reboot Error

    socket = <socket.socket [closed] fd=-1, family=AddressFamily.AF_INET, type=2049, proto=0>

    2016-02-20 19:29:12,194 - root - ERROR - Failed to iterate bots!
    Traceback (most recent call last):
      File "/home/wavi/code/python/bx2/bx/main.py", line 151, in maintain
        bot.mainloop()
      File "/home/wavi/code/python/bx2/bx/bot_main.py", line 105, in mainloop
        self.irc.maintain()
      File "/home/wavi/code/python/bx2/bx/irc.py", line 237, in maintain
        readable, writable, errored = select.select(sockl, sockl, sockl, self.select_interval)
    ValueError: file descriptor cannot be a negative integer (-1)
    

