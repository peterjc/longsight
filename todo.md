# Pending Items to Solve

- Connecting to Sky Safari Plus 7.0 works, however when moving the MPU module the following error which references the function  *alt_az_to_equatorial* which apparently I did not refactor and modify with astropy correctly.
```
Traceback (most recent call last):
  File "/home/pi/longsight/telescope_server.py", line 731, in <module>
    resp = command_map[cmd]()
  File "/home/pi/longsight/telescope_server.py", line 352, in meade_lx200_cmd_GR_get_ra
    ra, dec = alt_az_to_equatorial(local_alt, local_az)
  File "/home/pi/longsight/telescope_server.py", line 162, in alt_az_to_equatorial
    ra = gst - local_site.lon.value - hours_in_rad
  File "/usr/local/lib/python3.9/dist-packages/astropy/coordinates/angles.py", line 699, in __array_ufunc__
    results = super().__array_ufunc__(*args, **kwargs)
  File "/usr/local/lib/python3.9/dist-packages/astropy/units/quantity.py", line 594, in __array_ufunc__
    converters, unit = converters_and_unit(function, method, *inputs)
  File "/usr/local/lib/python3.9/dist-packages/astropy/units/quantity_helper/converters.py", line 192, in converters_and_unit
    raise UnitConversionError(
astropy.units.core.UnitConversionError: Can only apply 'subtract' function to dimensionless quantities when other argument is not a quantity (unless the latter is all zero/infinity/nan)
```

# Items to Check once it runs
Did the refactoring to astropy provide the right values?
  
