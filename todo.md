# Items to Check once it runs
Did the refactoring to astropy provide the right values?

Lines *327, 342* for telescope to *alt_az_to_equatorial*
Lines *184* for telescope to *equatorial_to_alt_az*

# Pending Items to Solve

- Connecting to Sky Safari Plus 7.0 works, however when moving the MPU module the following error which references the function  *alt_az_to_equatorial* which apparently I did not refactor and modify with astropy correctly.
```
Traceback (most recent call last):
  File "/home/pi/longsight/telescope_server.py", line 635, in <module>
    resp = command_map[cmd]()
  File "/home/pi/longsight/telescope_server.py", line 346, in meade_lx200_cmd_GD_get_dec
    % (radians_to_hhmmss(ra), ra, radians_to_sddmmss(dec), dec))
  File "/home/pi/longsight/telescope_server.py", line 304, in radians_to_sddmmss
    fraction, degrees = modf(angle * 180 / pi)
  File "/usr/local/lib/python3.9/dist-packages/astropy/units/quantity.py", line 1265, in __float__
    raise TypeError('only dimensionless scalar quantities can be '
TypeError: only dimensionless scalar quantities can be converted to Python scalars
```
