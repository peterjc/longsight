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

The "Goto" button is disabled (when configured as a Push-To telecope).

The "Align" button gives an are you sure prompt with the currently
selected objects name (e.g. a star), and then sends its position
using the Sr and Sd commands, followed by the :CM# command.

The "Lock/Unlock" button appears to work, I need to start returning
a non-static position to test this.

If configured as a Goto telescope, additional left/right and up/down
buttons appear on screen (which send East/West, North/South movement
commands. Also, a slew rate slider control appears. Depending on which
model telescope was selected, this may give four rates via the
RC/RG/RM/RS commands, or Sw commands (range 2 to 8).

If SkySafari's "Set Time & Location" feature is selected, it will
send commands St and Sg (for the location) then SG, SL, SC to set
the time and date. If using "Meade LX-200 Classic" this imposes
a 15s delay, using a newer model like the "Meade LX-200 GPS" there
is no noticeable delay on connection.

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
    #SkySafari's "align" command sends this after a pair of :Sr# and :Sd# commands.
    return "M31 EX GAL MAG 3.5 SZ178.0'"

def move_to_target():
    """For the :MS# command, Slew to Target Object

    Returns:
    0 - Slew is Possible
    1<string># - Object Below Horizon w/string message
    2<string># - Object Below Higher w/string message
    """
    #SkySafari's "goto" command sends this after a pair of :Sr# and :Sd# commands.
    #For return code 1 and 2 the error message is not shown, simply that the
    #target is below the horizon (1) or out of reach of the mount (2).
    return "2Sorry, no goto"

def get_telescope_ra():
    """For the :GR# command, Get Telescope RA

    Returns: HH:MM.T# or HH:MM:SS#
    Depending which precision is set for the telescope
    """
    if high_precision:
        #The .T is for tenths of a minute, see e.g.
        #http://www.manualslib.com/manual/295083/Meade-Lx200.html?page=55
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

def precision_toggle():
    """For the :U# command, Toggle between low/hi precision positions
    
    Low - RA displays and messages HH:MM.T sDD*MM
    High - Dec/Az/El displays and messages HH:MM:SS sDD*MM:SS

    Returns Nothing
    """
    global high_precision
    high_precision = not high_precision
    return None

def set_site_latitude(value):
    """For the :StsDD*MM# command, Sets the current site latitdue to sDD*MM

    Returns: 0 - Invalid, 1 - Valid
    """
    return "1"

def set_site_longitude(value):
    """For the :SgDDD*MM# command, Set current site longitude to DDD*MM

    Returns: 0 - Invalid, 1 - Valid
    """
    #Expected immediately after the set latitude command
    #e.g. :St+56*29# then :Sg003*08'#
    return "1"

def set_site_timezone(value):
    """For the :SGsHH.H# command, Set the number of hours added to local time to yield UTC

    Returns: 0 - Invalid, 1 - Valid
    """
    #Expected immediately after the set latitude and longitude commands
    #Seems the decimal is optional, e.g. :SG-00#
    return "1"

def set_site_localtime(value):
    """For the :SLHH:MM:SS# command, Set the local Time

    Returns: 0 - Invalid, 1 - Valid
    """
    #e.g. :SL00:10:48#
    return "1"

def set_site_calendar(value):
    """For the :SCMM/DD/YY# command, Change Handbox Date to MM/DD/YY

    Returns: <D><string>

    D = '0' if the date is invalid. The string is the null string.
    D = '1' for valid dates and the string is
    'Updating Planetary Data#                              #',

    Note: For LX200GPS/RCX400/Autostar II this is the UTC data!
    """
    #Exact list of values from http://www.dv-fansler.com/FTP%20Files/Astronomy/LX200%20Hand%20Controller%20Communications.pdf
    #return "1Updating        planetary data. #%s#" % (" "*32)
    #
    #This seems to work but SkySafari takes a while to finish,
    #making me guess it is expecting something else and times out?
    return "1Updating Planetary Data#%s#" % (" "*30)

def return_one(value=None):
    """Dummy command implementation returning value 1."""
    return "1"

def return_none(value=None):
    """Dummy command implementation returning nothing."""
    return None

# TODO - Can SkySafari show focus control buttons?
# Would be very cool to connect my motorised focuser to this...
#
# :F+# move in - returns nothing
# :F-# move out - returns nothing
# :FQ# halt Focuser Motion - returns: nothing
# :FF# Set Focus speed to fastest - Returns: Nothing
# :FS# Set Focus speed to slowest - Returns: Nothing
# :F<n># set focuser speed to <n> where <n> is 1..4 - Returns: Nothing


command_map = {
    "CM": cm_sync,
    "GD": get_telescope_de,
    "GR": get_telescope_ra,
    "Me": return_none, #start moving East
    "Mn": return_none, #start moving North
    "Ms": return_none, #start moving South
    "Mw": return_none, #start moving West
    "MS": move_to_target,
    "Q": return_none, #abort all current slewing
    "Qe": return_none, #abort slew East
    "Qn": return_none, #abort slew North
    "Qs": return_none, #abort slew South
    "Qw": return_none, #abort slew West
    "RC": return_none, #set slew rate to centering (2nd slowest)
    "RG": return_none, #set slew rate to guiding (slowest)
    "RM": return_none, #set slew rate to find (2nd fastest)
    "RS": return_none, #set Slew rate to max (fastest)
    "Sd": set_target_de,
    "Sr": set_target_ra,
    "St": set_site_latitude,
    "Sg": set_site_longitude,
    "Sw": return_one, #set max slew rate
    "SG": set_site_timezone,
    "SL": set_site_localtime,
    "SC": set_site_calendar,
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
                        sys.stdout.write("Command %s, no response\n" % cmd)
                else:
                    if value:
                        sys.stderr.write("Unknown command: %s %s\n" % (cmd, value))
                    else:
                        sys.stderr.write("Unknown command: %s\n" % cmd)
    finally:
        connection.close()
