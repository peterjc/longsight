# Corrections

These are the basic script changes currently being attempted.

```
#TODO - Try astropy if I can get it to compile on Mac OS X...
from astropysics import coords
from astropysics import obstools
```

*astropysics* is no longer maintained and the work has been invested into *astropy*

```
from astropy.coordinates import SkyCoord, EarthLocation, AltAz, Longitude, Angle
from astropy import coordinates as coord
from astropy.time import Time
from astropy import units as u
import numpy as np
```

The following has been added

```
from datetime import datetime as dt
```

For the Hardware module as the GY80 is no longer easily found. The reference is now simply GYMOD and changed throughout where GY80 was before and an alternative local import has been made.

```
#Local import
from mpu9250 import GYMOD
```

The first major portion of code that required changing was lines *111 - 118*

```
#Default to Greenwich, GMT - Latitude 51deg 28' 38'' N, Longitude zero
local_site = obstools.Site(coords.AngularCoordinate(config.get("site", "latitude")),
                           coords.AngularCoordinate(config.get("site", "longitude")),
                           tz=0)
#Rather than messing with the system clock, will store any difference
#between the local computer's date/time and any date/time set by the
#client (which should match any location set by the client).
local_time_offset = 0
```

I believe the following is the correct way using *astropy*

```
obs = obs_time()
location = EarthLocation.of_address(site_address)
```

The next major code portion was with lines *191-197*

```
def greenwich_sidereal_time_in_radians():
    """Calculate using GMT (according to client's time settings)."""
    #Function astropysics.obstools.epoch_to_jd wants a decimal year as input
    #Function astropysics.obstools.calendar_to_jd can take a datetime object
    gmt_jd = obstools.calendar_to_jd(site_time_gmt_as_datetime())
    #Convert from hours to radians... 24hr = 2*pi
    return coords.greenwich_sidereal_time(gmt_jd) * pi / 12
```

I believe the following is the correct way using *astropy*

```
def greenwich_sidereal_time_in_radians():
    return t.sidereal_time('apparent', 'greenwich').radian[0] 
```

The next items were in the *def alt_az_to_equatorial* and *def equatorial_to_alt_az(ra, dec, gst=None):* and are related to getting the latitude and longitude of the local_site object.

If correct then this should be the solution

```
def alt_az_to_equatorial(alt, az, gst=None):
    global site_longitude, site_latitude, location #and time offset used too
    if gst is None:
        gst = greenwich_sidereal_time_in_radians()

    lat = Angle(location.geodetic.lat, u.radian)
    #Calculate these once only for speed
    sin_lat = sin(lat.radian)
    cos_lat = cos(lat.radian)
    sin_alt = sin(alt)
    cos_alt = cos(alt)
    sin_az = sin(az)
    cos_az = cos(az)
    # DEC based on latitude in radians
    dec  = asin(sin_alt*sin_lat + cos_alt*cos_lat*cos_az)
    hours_in_rad = acos((sin_alt - sin_lat*sin(dec)) / (cos_lat*cos(dec)))
    if sin_az > 0.0:
        hours_in_rad = 2*pi - hours_in_rad
    # Now figure out RA based on Longitude in Radians
    lon = Angle(site_longitude, u.radian)
    ra = gst - lon.radian - hours_in_rad
    return ra % (pi*2), dec

def equatorial_to_alt_az(gst=None):
    > PENDING
```

With Python 3 socket connection handling changed slightly.

Slight modification to line *751* and *791*

```
            data_received = connection.recv(16)
            data = data_received.decode()
```

```
connection.sendall(resp.encode())
```

Configuration section has been altered and changed, extended variables

```
print("Checking Configuration")
config_file = "telescope_server.ini"
if not os.path.isfile(config_file):
    print("Using default settings")
    h = open("telescope_server.ini", "w")
    h.write("[server]\nname=127.0.0.1\nport=4030\n")
    #Default to Greenwich as the site, 1 as tz
    h.write("[site]\naddress=Greenwich\n")
    h.write("[site]\ntz=1\n")
    h.write("[site]\nlatitude=51.4934\n")
    h.write("[site]\nlongitude=0.0098\n")
    #Default to no correction of the angles
    h.write("[offsets]\nazimuth=0\naltitude=0\n")
    h.close()
```
To help with debugging, and I added a lot of debugging statements

```
def debug_info(str):
    if debug:
        sys.stdout.write("%s\n" % str)
```

Usage is 

> debug_info("FUNCTION update_alt_az - local_alt %r - local_aaz %r" % (local_alt, local_az) )
