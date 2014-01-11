#!/usr/bin/env python
"""TCP/IP server which listens for Meade LX200 style serial commands.

Intended to mimick a SkyFi (serial to TCP/IP bridge) and compatible
Meade telescope normally controlled via a serial cable. In theory
this could be modified to listen to an actual serial port too...

The intended goal is that celestial/planetarium software like the
SkySafari applications can talk to this server as if it was an off
the shelf Meade LX200 compatible "Go To" telescope, when in fact
it is a DIY intrumented telescope or simulation.

Testing with Sky Safari Plus v4.0, where the telescope is setup as follows:

Scope Type: Meade LX-200 Classic
Mount Type: Equatorial Push-To
Auto-Detect SkyFi: Off
IP Address: That of the computer running this script (default 10.0.0.1)
Port Number: 4030
Set Time & Location: Off (default)
Readout Rate: 4 per second (default)
Save Log File: Off (default)

With this, the "Connect/Disconnect" button works fine, once connected
the scope queries the position using the :GR# and :GD# commands.

The "Goto" button is disabled (since I configured this as a Push-To
telecope).

The "Align" button gives an are you sure prompt with the currently
selected objects name (e.g. a star), and then sends its position
using the Sr and Sd commands, followed by the :CM# command.

The "Lock/Unlock" button appears to work, I need to start returning
a non-static position to test this.

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

def cm_sync():
    """For the :CM# command, Synchronizes the telescope's position with the currently selected database object's coordinates.

    Returns:
    LX200's - a "#" terminated string with the name of the object that was synced.
    Autostars & LX200GPS - At static string: "M31 EX GAL MAG 3.5 SZ178.0'#"
    """
    return "M31 EX GAL MAG 3.5 SZ178.0'"

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

def set_target_ra(value):
    """For the commands :SrHH:MM.T# or :SrHH:MM:SS#

    Set target object RA to HH:MM.T or HH:MM:SS depending on the current precision setting.
    Returns: 0 - Invalid, 1 - Valid
    """
    return "1"

def set_target_de(value):
    """For the command :SdsDD*MM#

    Set target object declination to sDD*MM or sDD*MM:SS depending on the current precision setting
    Returns: 1 - Dec Accepted, 0 - Dec invalid
    """
    return "1"

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
    "CM": cm_sync,
    "GD": get_telescope_de,
    "GR": get_telescope_ra,
    "RS": slew_rate_max,
    "Sd": set_target_de,
    "Sr": set_target_ra,
    "U": precision_toggle,
}

# Create a TCP/IP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_address = (server_name, server_port)
print >>sys.stderr, 'starting up on %s port %s' % server_address
sock.bind(server_address)
sock.listen(1)

while True:
    #sys.stdout.write("waiting for a connection\n")
    connection, client_address = sock.accept()
    data = ""
    try:
        #sys.stdout.write("Client connected: %s, %s\n" % client_address)
        while True:
            data += connection.recv(16)
            if not data:
                break
            #print >>sys.stderr, 'received "%s"' % data
            #For stacked commands like ":RS#:GD#"
            if data[0] != ":":
                sys.stderr.write("Invalid command: %s" % data)
                data = ""
                break
            while "#" in data:
                cmd = data[1:data.index("#")]
                #print "%r --> %r" % (data, cmd)
                data = data[1+len(cmd)+1:]
                cmd, value = cmd[:2], cmd[2:]
                if cmd in command_map:
                    if value:
                        print "Command %r, argument %r" % (cmd, value)
                        resp = command_map[cmd](value)
                    else:
                        resp = command_map[cmd]()
                    if resp:
                        sys.stdout.write("Command %s, sending %s\n" % (cmd, resp))
                        connection.sendall(resp)
                    else:
                        sys.stdout.write("Command %s, no responce\n" % cmd)
                else:
                    sys.stderr.write("Unknown command: %s\n" % cmd)
    finally:
        connection.close()
