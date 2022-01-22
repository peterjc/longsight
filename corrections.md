# Corrections

These are the basic script changes currently being attempted.

'''
#TODO - Try astropy if I can get it to compile on Mac OS X...
from astropysics import coords
from astropysics import obstools
'''

*astropysics* is no longer maintained and the work has been invested into *astropy*

'''
from astropy.coordinates import SkyCoord, EarthLocation, AltAz
from astropy import coordinates as coord
from astropy.time import Time
from astropy import units as u
import numpy as np
'''

The following has been added

'''
from datetime import datetime as dt
'''

For the Hardware module as the GY80 is no longer easily found. The reference is now simply GYMOD and changed throughout where GY80 was before and an alternative local import has been made.

'''
#Local import
from mpu9250 import GYMOD
'''

The first major portion of code that required changing was lines *111 - 118*

'''
#Default to Greenwich, GMT - Latitude 51deg 28' 38'' N, Longitude zero
local_site = obstools.Site(coords.AngularCoordinate(config.get("site", "latitude")),
                           coords.AngularCoordinate(config.get("site", "longitude")),
                           tz=0)
#Rather than messing with the system clock, will store any difference
#between the local computer's date/time and any date/time set by the
#client (which should match any location set by the client).
local_time_offset = 0
'''

I believe the following is the correct way using *astropy*

'''
#Default to Greenwich, GMT - Latitude 51deg 28' 38'' N, Longitude zero
now = dt.now()
times = [now]
t = Time(times, scale='utc')
obstime = Time(t) + np.linspace(0, 6, 10000) * u.hour
location = location = EarthLocation.of_address('Greenwich')
frame = AltAz(obstime=obstime, location=location)
# Or is this simply what is needed, is this the same as the old obstools.Site?
local_site = coord.EarthLocation.of_address('Greenwich')
'''

The next major code portion was with lines *191-197*

'''
def greenwich_sidereal_time_in_radians():
    """Calculate using GMT (according to client's time settings)."""
    #Function astropysics.obstools.epoch_to_jd wants a decimal year as input
    #Function astropysics.obstools.calendar_to_jd can take a datetime object
    gmt_jd = obstools.calendar_to_jd(site_time_gmt_as_datetime())
    #Convert from hours to radians... 24hr = 2*pi
    return coords.greenwich_sidereal_time(gmt_jd) * pi / 12
'''

I believe the following is the correct way using *astropy*

'''
def greenwich_sidereal_time_in_radians():
    return t.sidereal_time('apparent', 'greenwich') 
'''

The next items were in the *def alt_az_to_equatorial* and *def equatorial_to_alt_az(ra, dec, gst=None):* and are related to getting the latitude and longitude of the local_site object.

If correct then this should be the solution

'''
def alt_az_to_equatorial(alt, az, gst=None):
    global local_site #and time offset used too
    if gst is None:
        gst = greenwich_sidereal_time_in_radians()
    #lat = local_site.latitude.r
    lat = local_site.lat.value
    #Calculate these once only for speed
    sin_lat = sin(lat)
    cos_lat = cos(lat)
    sin_alt = sin(alt)
    cos_alt = cos(alt)
    sin_az = sin(az)
    cos_az = cos(az)
    dec  = asin(sin_alt*sin_lat + cos_alt*cos_lat*cos_az)
    hours_in_rad = acos((sin_alt - sin_lat*sin(dec)) / (cos_lat*cos(dec)))
    if sin_az > 0.0:
        hours_in_rad = 2*pi - hours_in_rad
    #ra = gst - local_site.longitude.r - hours_in_rad
    ra = gst - local_site.lon.value - hours_in_rad
    return ra % (pi*2), dec
    
def equatorial_to_alt_az(gst=None):
    global local_site #and time offset used too
    if gst is None:
        gst = greenwich_sidereal_time_in_radians()
    location = EarthLocation(lat=local_site.lat, lon=local_site.lon, height=0*u.m)
    now = dt.now()
    times = [now]
    t = Time(times, scale='utc')
    obs_time = Time(t)
    alt_az_frame = AltAz(location=location, obstime=obs_time) 
    return alt_az_frame
'''


