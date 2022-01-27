# Items to Check once it runs
- Did the refactoring to astropy provide the right values?
- Is the perspective and the values all correct, Sky Safari seems off from the perspective I would expect.
- *meade_lx200_cmd_St_set_latitude* and *meade_lx200_cmd_Sg_set_longitude* so far never called

Lines *327, 342* for telescope to *alt_az_to_equatorial*
Lines *184* for telescope to *equatorial_to_alt_az*

# Pending Items to Solve

> UNCTION alt_az_to_equatorial - gst: 7h41m02.26394328s
> FUNCTION alt_az_to_equatorial - hours_in_rad: 3.4434746708437443
> FUNCTION alt_az_to_equatorial - site_longitude: 351d40
> FUNCTION alt_az_to_equatorial - lon: 6.137741202846726
> FUNCTION alt_az_to_equatorial - Forumula: ra = gst - lon.radian - hours_in_rad

Crash on formula *gst* is in hours and minutes, first need to get it to all seconds, then convert to radians.

```
Traceback (most recent call last):
  File "/home/pi/longsight/telescope_server.py", line 719, in <module>
    resp = command_map[cmd]()
  File "/home/pi/longsight/telescope_server.py", line 405, in meade_lx200_cmd_GR_get_ra
    ra, dec = alt_az_to_equatorial(local_alt, local_az)
  File "/home/pi/longsight/telescope_server.py", line 186, in alt_az_to_equatorial
    ra = gst - lon.radian - hours_in_rad
  File "/usr/local/lib/python3.9/dist-packages/astropy/coordinates/angles.py", line 699, in __array_ufunc__
    results = super().__array_ufunc__(*args, **kwargs)
  File "/usr/local/lib/python3.9/dist-packages/astropy/units/quantity.py", line 594, in __array_ufunc__
    converters, unit = converters_and_unit(function, method, *inputs)
  File "/usr/local/lib/python3.9/dist-packages/astropy/units/quantity_helper/converters.py", line 192, in converters_and_unit
    raise UnitConversionError(
astropy.units.core.UnitConversionError: Can only apply 'subtract' function to dimensionless quantities when other argument is not a quantity (unless the latter is all zero/infinity/nan)
```

- Connecting to Sky Safari Plus 7.0 works, after connecting if you choose "align" the following comes up and the program crashes *lines 184 - equatorial_to_alt_az*

> *equatorial_to_alt_az* needs to be rewritten
