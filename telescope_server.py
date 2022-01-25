#!/usr/bin/env python
"""TCP/IP server which listens for Meade LX200 style serial commands.

Intended to mimick a SkyFi (serial to TCP/IP bridge) and compatible
Meade telescope normally controlled via a serial cable. 
"""

import socket
import os
import sys
import subprocess
try:
    import configparser
except ImportError:
    import ConfigParser as configparser
import time
import datetime
from datetime import datetime as dt
from math import pi, sin, cos, asin, acos, atan2, modf

from astropy.coordinates import SkyCoord, EarthLocation, AltAz, Longitude, Angle
from astropy import coordinates as coord
from astropy.time import Time
from astropy import units as u
import numpy as np

#Local import
from mpu9250 import GYMOD

print("Checking Configuration")
config_file = "telescope_server.ini"
if not os.path.isfile(config_file):
    print("Using default settings")
    h = open("telescope_server.ini", "w")
    h.write("[server]\nname=127.0.0.1\nport=4030\n")
    #Default to Greenwich as the site
    h.write("[site]\naddress=Greenwich\n")
    #Default to no correction of the angles
    h.write("[offsets]\nazimuth=0\naltitude=0\n")
    h.close()

print("Connecting to sensors...")
imu = GYMOD()
print("Connected to MPU9250 sensor")

print("Opening network port...")
config = configparser.ConfigParser()
config.read("telescope_server.ini")
server_name = config.get("server", "name") #e.g. 10.0.0.1
server_port = config.getint("server", "port") #e.g. 4030
site_address = config.get("site", "address") #e.g. Greenwich

#If default to low precision, SkySafari turns it on anyway:
high_precision = True

#Rather than messing with the system clock, will store any difference
#between the local computer's date/time and any date/time set by the
#client (which should match any location set by the client).
local_time_offset = 0

#These will come from sensor information... storing them in radians
local_alt = 85 * pi / 180.0
local_az = 30 * pi / 180.0
offset_alt = config.getfloat("offsets", "altitude")
offset_az = config.getfloat("offsets", "azimuth")

#These will come from the client... store them in radians
target_ra = 0.0
target_dec = 0.0

#Turn on for lots of logging...
debug = True

def save_config():
    global condig, config_file
    with open(config_file, "w") as handle:
        config.write(handle)

def _check_close(a, b, error=0.0001):
    if isinstance(a, (tuple, list)):
        assert isinstance(b, (tuple, list))
        assert len(a) == len(b)
        for a1, b1 in zip(a, b):
            diff = abs(a1-b1)
            if diff > error:
                raise ValueError("%s vs %s, for %s vs %s difference %s > %s"
                         % (a, b, a1, b1, diff, error))
        return
    diff = abs(a-b)
    if diff > error:
        raise ValueError("%s vs %s, difference %s > %s"
                         % (a, b, diff, error))

def obs_time():
    now = dt.now()
    times = [now]
    t = Time(times, scale='utc')
    obstime = Time(t) + np.linspace(0, 6, 10000) * u.hour
    return obstime

def update_alt_az():
    global imu, offset_alt, offset_az, local_alt, local_az
    yaw, pitch, roll = imu.current_orientation_euler_angles_hybrid()
    #yaw, pitch, roll = imu.current_orientation_euler_angles_mag_acc_only()
    #Yaw is measured from (magnetic) North,
    #Azimuth is measure from true North:
    local_az = (offset_az + yaw) % (2*pi)
    #Pitch is measured downwards (using airplane style NED system)
    #Altitude is measured upwards
    local_alt = (offset_alt + pitch) % (2*pi)
    #We don't care about the roll for the Meade LX200 protocol.
    if debug:
        sys.stdout.write("\nFUNCTION update_alt_az\n")
        sys.stdout.write("local_az %r\n" % local_az)
        sys.stdout.write("local_alt %r\n" % local_alt)

def site_time_gmt_as_epoch():
    global local_time_offset
    return time.time() + local_time_offset

def site_time_gmt_as_datetime():
    return datetime.datetime.fromtimestamp(site_time_gmt_as_epoch())

def site_time_local_as_datetime():
    global local_site
    return site_time_gmt_as_datetime() - datetime.timedelta(hours=local_site.tz)

def debug_time():
    global local_site
    if local_site.tz:
        sys.stderr.write("Effective site date/time is %s (local time), %s (GMT/UTC)\n"
                         % (site_time_local_as_datetime(), site_time_gmt_as_datetime()))
    else:
        sys.stderr.write("Effective site date/time is %s (local/GMT/UTC)\n"
                         % site_time_gmt_as_datetime())

def greenwich_sidereal_time_in_radians():
    now = dt.now()
    times = [now]
    t = Time(times, scale='utc')
    return t.sidereal_time('apparent', 'greenwich')

def alt_az_to_equatorial(alt, az, gst=None):
    if debug:
        sys.stdout.write("\nFUNCTION alt_az_to_equatorial\n")
        sys.stdout.write("alt %r\n" % alt)
        sys.stdout.write("az %r\n" % az)
    global local_site #and time offset used too
    if gst is None:
        gst = greenwich_sidereal_time_in_radians()
    obs = obs_time()
    newAltAzcoordiantes = SkyCoord(alt = local_site.alt, az = local_site.az + az*u.deg, obstime = obs, frame = 'altaz')
    alt = Longitude([newAltAzcoordiantes.alt] * u.deg)
    az = Angle([newAltAzcoordiantes.az] * u.deg)
    az.wrap_at('90d', inplace=True)
    if debug:
        sys.stdout.write("Actual Values\n")
        sys.stdout.write("ra %r\n" % alt.radian[0][0])
        sys.stdout.write("dec %r\n" % az.degree[0][0])
    return alt.radian[0][0], az.degree[0][0]

def equatorial_to_alt_az(ra, dec, gst=None):
    if debug:
        sys.stdout.write("\nFUNCTION equatorial_to_alt_az\n")
        sys.stdout.write("ra %r\n" % ra)
        sys.stdout.write("dec %r\n" % dec)
    global local_site #and time offset used too
    if gst is None:
        gst = greenwich_sidereal_time_in_radians()
    c = SkyCoord(ra = ra*u.degree, dec = dec*u.degree, frame='icrs')
    obs = obs_time()
    cAltAz = c.transform_to(AltAz(obstime = obs, location = local_site))
    return cAltAz.alt, cAltAz.az

# ====================
# Meade LX200 Protocol
# ==================== 

def meade_lx200_cmd_CM_sync():
    """For the :CM# command, Synchronizes the telescope's position with the currently selected database object's coordinates.

    Returns:
    LX200's - a "#" terminated string with the name of the object that was synced.
    Autostars & LX200GPS - At static string: "M31 EX GAL MAG 3.5 SZ178.0'#"
    """
    #SkySafari's "align" command sends this after a pair of :Sr# and :Sd# commands.
    global offset_alt, offset_az
    global local_alt, local_az, target_alt, target_dec
    sys.stderr.write("Resetting from current position Alt %s (%0.5f radians), Az %s (%0.5f radians)\n" %
                     (radians_to_sddmmss(local_alt), local_alt, radians_to_hhmmss(local_az), local_az))
    sys.stderr.write("New target position RA %s (%0.5f radians), Dec %s (%0.5f radians)\n" %
                     (radians_to_hhmmss(target_ra), target_ra, radians_to_sddmmss(target_dec), target_dec))
    target_alt, target_az = equatorial_to_alt_az(target_ra, target_dec)
    offset_alt += (target_alt - local_alt)
    offset_az += (target_az - local_az)
    offset_alt %= 2*pi
    offset_az %= 2*pi
    config.set("offsets", "altitude", offset_alt)
    config.set("offsets", "azimuth", offset_az)
    save_config()
    update_alt_az()
    sys.stderr.write("Revised current position Alt %s (%0.5f radians), Az %s (%0.5f radians)\n" %
                     (radians_to_sddmmss(local_alt), local_alt, radians_to_hhmmss(local_az), local_az))
    return "M31 EX GAL MAG 3.5 SZ178.0'"

def meade_lx200_cmd_MS_move_to_target():
    """For the :MS# command, Slew to Target Object

    Returns:
    0 - Slew is Possible
    1<string># - Object Below Horizon w/string message
    2<string># - Object Below Higher w/string message
    """
    #SkySafari's "goto" command sends this after a pair of :Sr# and :Sd# commands.
    #For return code 1 and 2 the error message is not shown, simply that the
    #target is below the horizon (1) or out of reach of the mount (2).
    global target_ra, target_dec
    if target_dec < 0:
        return "1Target declination negative"
    else:
        return "2Sorry, no goto"

def parse_hhmm(value):
    """Turn string HH:MM.T or HH:MM:SS into radians."""
    parts = value.split(":")
    if len(parts) == 2:
        h = int(parts[0])
        m = float(parts[1])
        s = 0
    else:
        h, m, s = [int(v) for v in parts]
    # 12 hours = 43200 seconds = pi radians
    return (h*3600 + m*60 + s) * pi / 43200
_check_close(parse_hhmm("00:02.3"),  0.010035643198967393)
_check_close(parse_hhmm("00:02.4"),  0.010471975511965976)
_check_close(parse_hhmm("00:02:17"), 0.009962921146800963)
_check_close(parse_hhmm("00:02:18"), 0.010035643198967393)
_check_close(parse_hhmm("12:00:00"), pi)

def parse_sddmm(value):
    """Turn string sDD*MM or sDD*MM:SS into radians."""
    if value[3] != "*":
        if len(value) == 9 and value[3] == chr(223) and value[6] == ":":
            # Stellarium's variant in v0.12.4, since fixed:
            # https://bugs.launchpad.net/stellarium/+bug/1272960
            # http://bazaar.launchpad.net/~stellarium/stellarium/trunk/revision/6529
            value = value.replace(chr(223), "*")
        else:
            raise ValueError("Bad format %r" % value)
    if value[0] == "+":
        sign = +1
    elif value[0] == "-":
        sign = -1
    else:
        raise ValueError("Bad sign in %r" % value)
    deg = int(value[1:3])
    if len(value) == 6:
        arc_minutes = int(value[4:6])
        arc_seconds = 0
    elif len(value) != 9 or value[6] != ":":
        raise ValueError("Bad format %r" % value)
    else:
        arc_minutes = int(value[4:6])
        arc_seconds = int(value[7:9])
    return sign * (deg + arc_minutes/60.0 + arc_seconds/3600.0) * pi / 180.0
_check_close(parse_sddmm("+00*01"), 0.000290888208666)
_check_close(parse_sddmm("+00*01:00"), 0.000290888208666)
_check_close(parse_sddmm("+57*17:45"), 1.0)
_check_close(parse_sddmm("+57*18"), 1.0)

_check_close(parse_hhmm("07:01:55"), 1.84096) # RA
_check_close(parse_sddmm("+22*49:43"), 0.3984) # Dec

def radians_to_hms(angle):
    fraction, hours = modf(angle * 12 / pi)
    fraction, minutes = modf(fraction * 60)
    return hours, minutes, fraction * 60
_check_close(radians_to_hms(0.01), (0, 2, 17.50987083139755))
_check_close(radians_to_hms(6.28), (23.0, 59.0, 16.198882117679716))

def radians_to_hhmmss(angle):
    while angle < 0.0:
        sys.stderr.write("Warning, radians_to_hhmmss called with %0.2f\n" % angle)
        angle += 2*pi
    h, m, s = radians_to_hms(angle)
    return "%02i:%02i:%02i#" % (h, m, round(s))

def radians_to_hhmmt(angle):
    while angle < 0.0:
        sys.stderr.write("Warning, radians_to_hhmmt called with %0.2f\n" % angle)
        angle += 2*pi
    h, m, s = radians_to_hms(angle)
    return "%02i:%02i.%01i#" % (h, m, round(s / 6))

def radians_to_sddmm(angle):
    """Signed degrees, arc-minutes as sDD*MM# for protocol."""
    if angle < 0.0:
        sign = "-"
        angle = abs(angle)
    else:
        sign = "+"
    fraction, degrees = modf(angle / pi)
    return "%s%02i*%02i#" % (sign, degrees, round(fraction * 60.0))

def radians_to_sddmmss(angle):
    """
    Signed degrees, arc-minutes, arc-seconds as sDD*MM:SS# for protocol.
    FUNCTION radians_to_sddmmss
    angle: 95.71562968082463
    fraction: 0.03387138278878865
    degress: 30.0
    return: -30*28:02#
    """
    if angle < 0.0:
        sign = "-"
        angle = abs(angle)
    else:
        sign = "+"
    fraction, degrees = modf(angle / pi)
    fraction, arcminutes = modf(fraction * 60.0)
    if debug:
        sys.stdout.write("\nFUNCTION radians_to_sddmmss\n")
        sys.stdout.write("angle: %s\n" % angle)
        sys.stdout.write("fraction: %s\n" % fraction)
        sys.stdout.write("degress: %s\n" % degrees)
        sys.stdout.write("arcminutes: %s\n" % arcminutes)
        sys.stdout.write("return: %s\n" % "%s%02i*%02i:%02i#" % (sign, degrees, arcminutes, round(fraction * 60.0)))
    return "%s%02i*%02i:%02i#" % (sign, degrees, arcminutes, round(fraction * 60.0))
'''
for r in [0.000290888208666, 1, -0.49*pi, -1.55, 0, 0.01, 0.1, 0.5*pi]:
    #Testing RA from -pi/2 to pi/2
    assert -0.5*pi <= r <= 0.5*pi, r
    _check_close(parse_sddmm(radians_to_sddmm(r).rstrip("#")), r, 0.0002)
    _check_close(parse_sddmm(radians_to_sddmmss(r).rstrip("#")), r)
for r in [0, 0.01, 0.1, pi, 2*pi]:
    #Testing dec from 0 to 2*pi
    assert 0 <= r <= 2*pi, r
    _check_close(parse_hhmm(radians_to_hhmmt(r).rstrip("#")), r)
    _check_close(parse_hhmm(radians_to_hhmmss(r).rstrip("#")), r)
'''

def meade_lx200_cmd_GR_get_ra():
    """For the :GR# command, Get Telescope RA

    Returns: HH:MM.T# or HH:MM:SS#
    Depending which precision is set for the telescope
    """
    #TODO - Since :GR# and :GD# commands normally in pairs, cache this?
    update_alt_az()
    ra, dec = alt_az_to_equatorial(local_alt, local_az)
    if high_precision:
        return radians_to_hhmmss(ra)
    else:
        #The .T is for tenths of a minute, see e.g.
        #http://www.manualslib.com/manual/295083/Meade-Lx200.html?page=55
        return radians_to_hhmmt(ra)

def meade_lx200_cmd_GD_get_dec():
    """For the :GD# command, Get Telescope Declination.

    Returns: sDD*MM# or sDD*MM'SS#
    Depending upon the current precision setting for the telescope.
    """
    update_alt_az()
    ra, dec = alt_az_to_equatorial(local_alt, local_az)
    if debug:
        sys.stdout.write("\nFUNCTION meade_lx200_cmd_GD_get_dec\n")
        sys.stderr.write("RA %s (%0.5f radians), dec %s (%0.5f radians)\n"
                         % (radians_to_hhmmss(ra), ra, radians_to_sddmmss(dec), dec))
    if high_precision:
        return radians_to_sddmmss(dec)
    else:
        return radians_to_sddmm(dec)

def meade_lx200_cmd_Sr_set_target_ra(value):
    """For the commands :SrHH:MM.T# or :SrHH:MM:SS#

    Set target object RA to HH:MM.T or HH:MM:SS depending on the current precision setting.
    Returns: 0 - Invalid, 1 - Valid

    Stellarium breaks the specification and sends things like ':Sr 20:39:38#'
    with an extra space.
    """
    global target_ra
    try:
        target_ra = parse_hhmm(value.strip()) # Remove any space added by Stellarium
        # The extra space sent by Stellarium v0.12.4 has been fixed:
        # https://bugs.launchpad.net/stellarium/+bug/1272960
        sys.stderr.write("Parsed right-ascension :Sr%s# command as %0.5f radians\n" % (value, target_ra))
        return "1"
    except Exception as err:
        sys.stderr.write("Error parsing right-ascension :Sr%s# command: %s\n" % (value, err))
        return "0"

def meade_lx200_cmd_Sd_set_target_de(value):
    """For the command :SdsDD*MM# or :SdsDD*MM:SS#

    Set target object declination to sDD*MM or sDD*MM:SS depending on the current precision setting
    Returns: 1 - Dec Accepted, 0 - Dec invalid

    Stellarium breaks this specification and sends things like ':Sd +15\xdf54:44#'
    with an extra space, and the wrong characters. Apparently chr(223) is the
    degrees symbol on some character sets.
    """
    global target_dec
    try:
        target_dec = parse_sddmm(value.strip()) # Remove any space added by Stellarium
        # The extra space sent by Stellarium v0.12.4 has been fixed:
        # https://bugs.launchpad.net/stellarium/+bug/1272960 
        sys.stderr.write("Parsed declination :Sd%s# command as %0.5f radians\n" % (value, target_dec))
        return "1"
    except Exception as err:
        sys.stderr.write("Error parsing declination :Sd%s# command: %s\n" % (value, err))
        return "0"

def meade_lx200_cmd_U_precision_toggle():
    """For the :U# command, Toggle between low/hi precision positions
    
    Low - RA displays and messages HH:MM.T sDD*MM
    High - Dec/Az/El displays and messages HH:MM:SS sDD*MM:SS

    Returns Nothing
    """
    global high_precision
    high_precision = not high_precision
    if high_precision:
        sys.stderr.write("Toggled high precision, now ON.\n")
    else:
        sys.stderr.write("Toggled high precision, now OFF.\n")
    return None

def meade_lx200_cmd_St_set_latitude(value):
    """For the :StsDD*MM# command, Sets the current site latitdue to sDD*MM

    Returns: 0 - Invalid, 1 - Valid
    """
    if debug:
        sys.stderr.write("meade_lx200_cmd_St_set_latitude: %s\n" % value)
    #Expect this to be followed by an Sg command to set the longitude...
    global local_site, config
    try:
        value = value.replace("*", "d")
        local_site.latitude = value
        #That worked, should be safe to save the value to disk later...
        config.set("site", "latitude", value)
        return "1"
    except Exception as err:
        sys.stderr.write("Error with :St%s# latitude: %s\n" % (value, err))
        return "0"

def meade_lx200_cmd_Sg_set_longitude(value):
    """For the :SgDDD*MM# command, Set current site longitude to DDD*MM

    Returns: 0 - Invalid, 1 - Valid
    """
    if debug:
        sys.stderr.write("meade_lx200_cmd_Sg_set_longitude: %s\n" % value)
    #Expected immediately after the set latitude command
    #e.g. :St+56*29# then :Sg003*08'#
    global local_site, config
    try:
        value = value.replace("*", "d")
        local_site.longitude = value
        sys.stderr.write("Local site now latitude %s, longitude %s\n" % (local_site.latitude, local_site.longitude))
        #That worked, should be safe to save the value to disk:
        config.set("site", "longitude", value)
        save_config()
        return "1"
    except Exception as err:
        sys.stderr.write("Error with :Sg%s# longitude: %s\n" % (value, err))
        return "0"

def meade_lx200_cmd_SG_set_local_timezone(value):
    """For the :SGsHH.H# command, Set the number of hours added to local time to yield UTC

    Returns: 0 - Invalid, 1 - Valid
    """
    #Expected immediately after the set latitude and longitude commands
    #Seems the decimal is optional, e.g. :SG-00#
    global local_site
    try:
        local_site.tz = float(value) # Can in theory be partial hour, so not int
        sys.stderr.write("Local site timezone now %s\n" % local_site.tz)
        return "1"
    except Exception as err:
        sys.stderr.write("Error with :SG%s# time zone: %s\n" % (value, err))
        return "0"

def meade_lx200_cmd_SL_set_local_time(value):
    """For the :SLHH:MM:SS# command, Set the local Time

    Returns: 0 - Invalid, 1 - Valid
    """
    global local_time_offset
    local = time.time() + local_time_offset
    #e.g. :SL00:10:48#
    #Expect to be followed by an SC command to set the date.
    try:
        hh, mm, ss = (int(v) for v in value.split(":"))
        if not (0 <= hh <= 24):
            raise ValueError("Bad hour")
        if not (0 <= mm <= 59):
            raise ValueError("Bad minutes")
        if not (0 <= ss <= 59):
            raise ValueError("Bad seconds")
        desired_seconds_since_midnight = 60*60*(hh + local_site.tz) + 60*mm + ss
        t = time.gmtime(local)
        current_seconds_since_midnight = 60*60*t.tm_hour + 60*t.tm_min + t.tm_sec
        new_offset = desired_seconds_since_midnight - current_seconds_since_midnight
        local_time_offset += new_offset
        sys.stderr.write("Requested site time %i:%02i:%02i (TZ %s), new offset %is, total offset %is\n"
                         % (hh, mm, ss, local_site.tz, new_offset, local_time_offset))
        debug_time()
        return "1"
    except ValueError as err:
        sys.stderr.write("Error with :SL%s# time setting: %s\n" % (value, err))
        return "0"

def meade_lx200_cmd_SC_set_local_date(value):
    """For the :SCMM/DD/YY# command, Change Handbox Date to MM/DD/YY

    Returns: <D><string>

    D = '0' if the date is invalid. The string is the null string.
    D = '1' for valid dates and the string is
    'Updating Planetary Data#                              #',

    Note: For LX200GPS/RCX400/Autostar II this is the UTC data!
    """
    #Expected immediately after an SL command setting the time.
    #
    #Exact list of values from http://www.dv-fansler.com/FTP%20Files/Astronomy/LX200%20Hand%20Controller%20Communications.pdf
    #return "1Updating        planetary data. #%s#" % (" "*32)
    #
    #This seems to work but SkySafari takes a while to finish
    #if setup as a Meade LX200 Classic - much faster on other
    #models.
    #
    #Idea is to calculate any difference between the computer's
    #date (e.g. 1 Jan 1980 if the Raspberry Pi booted offline)
    #and the client's date in days (using the datetime module),
    #and add this to our offset (converting it into seconds).
    #
    global local_time_offset
    #TODO - Test this in non-GMT/UTC other time zones, esp near midnight
    current = datetime.date.fromtimestamp(time.time() + local_time_offset)
    try:
        wanted = datetime.date.fromtimestamp(time.mktime(time.strptime(value, "%m/%d/%y")))
        days = (wanted - current).days
        local_time_offset += days * 24 * 60 * 60 # 86400 seconds in a day
        sys.stderr.write("Requested site date %s (MM/DD/YY) gives offset of %i days\n" % (value, days))
        debug_time()
        return "1Updating Planetary Data#%s#" % (" "*30)
    except ValueError as err:
        sys.stderr.write("Error with :SC%s# date setting: %s\n" % (value, err))
        return "0"

def return_one(value=None):
    """Dummy command implementation returning value 1."""
    return "1"

def return_none(value=None):
    """Dummy command implementation returning nothing."""
    return None

# :F+# move in - returns nothing
# :F-# move out - returns nothing
# :FQ# halt Focuser Motion - returns: nothing
# :FF# Set Focus speed to fastest - Returns: Nothing
# :FS# Set Focus speed to slowest - Returns: Nothing
# :F<n># set focuser speed to <n> where <n> is 1..4 - Returns: Nothing

# ================
# Main Server Code
# ================

command_map = {
    #Meade LX200 commands:
    ":CM": meade_lx200_cmd_CM_sync,
    ":GD": meade_lx200_cmd_GD_get_dec,
    ":GR": meade_lx200_cmd_GR_get_ra,
    ":Me": return_none, #start moving East
    ":Mn": return_none, #start moving North
    ":Ms": return_none, #start moving South
    ":Mw": return_none, #start moving West
    ":MS": meade_lx200_cmd_MS_move_to_target,
    ":Q": return_none, #abort all current slewing
    ":Qe": return_none, #abort slew East
    ":Qn": return_none, #abort slew North
    ":Qs": return_none, #abort slew South
    ":Qw": return_none, #abort slew West
    ":RC": return_none, #set slew rate to centering (2nd slowest)
    ":RG": return_none, #set slew rate to guiding (slowest)
    ":RM": return_none, #set slew rate to find (2nd fastest)
    ":RS": return_none, #set Slew rate to max (fastest)
    ":Sd": meade_lx200_cmd_Sd_set_target_de,
    ":Sr": meade_lx200_cmd_Sr_set_target_ra,
    ":St": meade_lx200_cmd_St_set_latitude,
    ":Sg": meade_lx200_cmd_Sg_set_longitude,
    ":Sw": return_one, #set max slew rate
    ":SG": meade_lx200_cmd_SG_set_local_timezone,
    ":SL": meade_lx200_cmd_SL_set_local_time,
    ":SC": meade_lx200_cmd_SC_set_local_date,
    ":U":  meade_lx200_cmd_U_precision_toggle,
}

#Set local site (AltAz)
#obs = obs_time()
#c = SkyCoord(ra=51.6712*u.degree, dec=8.3406*u.degree, frame='icrs')

'''
loc = EarthLocation.of_address(site_address)
local_site = c.transform_to(AltAz(obstime = obs, location = loc))
if debug:
    sys.stderr.write("\nSkycoord %s\n" % c)
    sys.stderr.write("\nloc %s\n" % loc)
    sys.stderr.write("\local_site %s\n" % local_site)
'''

# Create a TCP/IP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_address = (server_name, server_port)
sys.stderr.write("\nStarting up on %s port %s\n" % server_address)
sock.bind(server_address)
sock.listen(5)

while True:
    #sys.stdout.write("waiting for a connection\n")
    connection, client_address = sock.accept()
    data = ""
    try:
        #sys.stdout.write("Client connected: %s, %s\n" % client_address)
        while True:
            data_received = connection.recv(16)
            data = data_received.decode()
            if not data:
                imu.update()
                break
            if debug:
                sys.stdout.write("Processing %r\n" % data)
                #For stacked commands like ":RS#:GD#",
            while data:
                while data[0:1] == "#":
                    #sys.stderr.write("Problem in data: %r - dropping leading #\n" % data)
                    data = data[1:]
                if not data:
                    break
                if "#" in data:
                    raw_cmd = data[:data.index("#")]
                    #sys.stderr.write("%r --> %r as command\n" % (data, raw_cmd))
                    data = data[len(raw_cmd)+1:]
                    cmd, value = raw_cmd[:3], raw_cmd[3:]
                else:
                    raw_cmd = data
                    cmd = raw_cmd[:3]
                    value = raw_cmd[3:]
                    data = ""
                if not cmd:
                    sys.stderr.write("Eh? No command?\n")
                elif cmd in command_map:
                    if value:
                        if debug:
                            sys.stdout.write("Command %r, argument %r\n" % (cmd, value))
                        resp = command_map[cmd](value)
                    else:
                        resp = command_map[cmd]()
                    if resp:
                        if debug:
                            sys.stdout.write("Command %r, sending %r\n" % (cmd, resp))
                        connection.sendall(resp.encode())
                    else:
                        if debug:
                            sys.stdout.write("Command %r, no response\n" % cmd)
                else:
                    sys.stderr.write("Unknown command %r, from %r (data %r)\n" % (cmd, raw_cmd, data))
    finally:
        connection.close()
