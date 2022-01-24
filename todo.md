# Items to Check once it runs
- Did the refactoring to astropy provide the right values?
- Is the perspective and the values all correct, Sky Safari seems off from the perspective I would expect.

Lines *327, 342* for telescope to *alt_az_to_equatorial*
Lines *184* for telescope to *equatorial_to_alt_az*

# Pending Items to Solve

- Connecting to Sky Safari Plus 7.0 works, after connecting if you choose "align" the following comes up and the program crashes *lines 184 - equatorial_to_alt_az*

```
Traceback (most recent call last):
  File "/home/pi/longsight/telescope_server.py", line 650, in <module>
    resp = command_map[cmd]()
  File "/home/pi/longsight/telescope_server.py", line 193, in meade_lx200_cmd_CM_sync
    target_alt, target_az = equatorial_to_alt_az(target_ra, target_dec)
  File "/home/pi/longsight/telescope_server.py", line 172, in equatorial_to_alt_az
    cAltAz = c.transform_to(AltAz(obstime = obs, location = local_site))
  File "/usr/local/lib/python3.9/dist-packages/astropy/coordinates/builtin_frames/altaz.py", line 109, in __init__
    super().__init__(*args, **kwargs)
  File "/usr/local/lib/python3.9/dist-packages/astropy/coordinates/baseframe.py", line 314, in __init__
    values[fnm] = getattr(self, fnm)
  File "/usr/local/lib/python3.9/dist-packages/astropy/coordinates/attributes.py", line 104, in __get__
    out, converted = self.convert_input(out)
  File "/usr/local/lib/python3.9/dist-packages/astropy/coordinates/attributes.py", line 396, in convert_input
    return itrsobj.earth_location, True
  File "/usr/local/lib/python3.9/dist-packages/astropy/coordinates/sky_coordinate.py", line 849, in __getattr__
    if not attr.startswith('_') and hasattr(self._sky_coord_frame, attr):
  File "/usr/local/lib/python3.9/dist-packages/astropy/coordinates/builtin_frames/itrs.py", line 36, in earth_location
    return EarthLocation(x=cart.x, y=cart.y, z=cart.z)
  File "/usr/local/lib/python3.9/dist-packages/astropy/coordinates/earth.py", line 207, in __new__
    raise TypeError('Coordinates could not be parsed as either '
TypeError: Coordinates could not be parsed as either geocentric or geodetic, with respective exceptions "Geocentric coordinates should be in units of length." and "from_geodetic() got an unexpected keyword argument 'x'"
```


