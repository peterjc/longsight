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
  File "/home/pi/longsight/telescope_server.py", line 170, in equatorial_to_alt_az
    c = SkyCoord(ra, dec, frame='icrs')
  File "/usr/local/lib/python3.9/dist-packages/astropy/coordinates/sky_coordinate.py", line 331, in __init__
    skycoord_kwargs, components, info = _parse_coordinate_data(
  File "/usr/local/lib/python3.9/dist-packages/astropy/coordinates/sky_coordinate_parsers.py", line 296, in _parse_coordinate_data
    _components[frame_attr_name] = attr_class(arg, unit=unit)
  File "/usr/local/lib/python3.9/dist-packages/astropy/coordinates/angles.py", line 670, in __new__
    self = super().__new__(cls, angle, unit=unit, **kwargs)
  File "/usr/local/lib/python3.9/dist-packages/astropy/coordinates/angles.py", line 138, in __new__
    return super().__new__(cls, angle, unit, dtype=dtype, copy=copy,
  File "/usr/local/lib/python3.9/dist-packages/astropy/units/quantity.py", line 526, in __new__
    value._set_unit(value_unit)
  File "/usr/local/lib/python3.9/dist-packages/astropy/coordinates/angles.py", line 160, in _set_unit
    super()._set_unit(self._convert_unit_to_angle_unit(unit))
  File "/usr/local/lib/python3.9/dist-packages/astropy/units/quantity.py", line 1933, in _set_unit
    raise UnitTypeError(
astropy.units.core.UnitTypeError: Longitude instances require units equivalent to 'rad', but no unit was given.
```


