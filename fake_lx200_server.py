#!/usr/bin/env python
"""TCP/IP server which listens for Meade LX200 style serial commands.

Intended to mimick a SkyFi (serial to TCP/IP bridge) and compatible
Meade telescope normally controlled via a serial cable. In theory
this could be modified to listen to an actual serial port too...

The intended goal is that celestial/planetarium software like the
SkySafari applications can talk to this server as if it was an off
the shelf Meade LX200 compatible "Go To" telescope, when in fact
it is a DIY intrumented telescope or simulation.
"""
import socket
import sys
import commands

server_name = socket.gethostbyname(socket.gethostname())
if server_name == "127.0.0.1":
    #This works on Linux but not on Mac OS X or Windows:
    server_name = commands.getoutput("/sbin/ifconfig").split("\n")[1].split()[1][5:]
server_port = 4030 #Default port used by SkySafari

high_precision = False

def get_telescope_ra():
    """For the :GR# command, Get Telescope RA

    Returns: HH:MM.T# or HH:MM:SS#
    Depending which precision is set for the telescope
    """
    if high_precision:
        #TODO - What is the "T" in "HH:MM.T#" for?
        return "03:25.0#"
    else:
        return "03:25.21#"

def get_telescope_de():
    """For the :GD# command, Get Telescope Declination.

    Returns: sDD*MM# or sDD*MM'SS#
    Depending upon the current precision setting for the telescope.
    """
    if high_precision:
        return "+49*54'33#"
    else:
        return "+49*54#"

def slew_rate_max():
    """For the :RS# command, Set Slew rate to max (fastest)

    Returns: Nothing
    """
    return None

def precision_toggle():
    """For the :U# command, Toggle between low/hi precision positions
    
    Low - RA displays and messages HH:MM.T sDD*MM
    High - Dec/Az/El displays and messages HH:MM:SS sDD*MM:SS

    Returns Nothing
    """
    global high_precision
    high_precision = not high_precision
    return None


command_map = {
    ":GD#": get_telescope_de,
    ":GR#": get_telescope_ra,
    ":RS#": slew_rate_max,
    ":U#": precision_toggle,
}

# Create a TCP/IP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_address = (server_name, server_port)
print >>sys.stderr, 'starting up on %s port %s' % server_address
sock.bind(server_address)
sock.listen(1)

while True:
    print >>sys.stderr, 'waiting for a connection'
    connection, client_address = sock.accept()
    try:
        print >>sys.stderr, 'client connected:', client_address
        while True:
            data = connection.recv(16)
            if not data:
                break
            print >>sys.stderr, 'received "%s"' % data
            #For stacked commands like ":RS#:GD#"
            while "#" in data:
                cmd = data[:data.index("#")+1]
                data = data[len(cmd):]
                if cmd in command_map:
                    print "Command %s" % cmd
                    resp = command_map[cmd]()
                    if resp:
                        print >>sys.stderr, "sending %s" % resp
                        connection.sendall(resp)
                else:
                    print "Unknown command: %s" % cmd
            else:
                #TODO
                pass
    finally:
        connection.close()
