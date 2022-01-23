# Items to Check once it runs
Did the refactoring to astropy provide the right values?


# Pending Items to Solve

- Connecting to Sky Safari Plus 7.0 works, however when moving the MPU module the following error which references the function  *alt_az_to_equatorial* which apparently I did not refactor and modify with astropy correctly.
```
Traceback (most recent call last):
  File "/home/pi/longsight/telescope_server.py", line 634, in <module>
    resp = command_map[cmd]()
  File "/home/pi/longsight/telescope_server.py", line 327, in meade_lx200_cmd_GR_get_ra
    ra, dec = alt_az_to_equatorial(local_alt, local_az)
  File "/home/pi/longsight/telescope_server.py", line 153, in alt_az_to_equatorial
    return newAltAzcoordiantes.icrs.ra[0], newAltAzcoordiantes.icrs.dec[0]
  File "/usr/local/lib/python3.9/dist-packages/astropy/coordinates/sky_coordinate.py", line 855, in __getattr__
    return self.transform_to(attr)
  File "/usr/local/lib/python3.9/dist-packages/astropy/coordinates/sky_coordinate.py", line 675, in transform_to
    new_coord = trans(self.frame, generic_frame)
  File "/usr/local/lib/python3.9/dist-packages/astropy/coordinates/transformations.py", line 1481, in __call__
    curr_coord = t(curr_coord, curr_toframe)
  File "/usr/local/lib/python3.9/dist-packages/astropy/coordinates/transformations.py", line 1081, in __call__
    return supcall(fromcoord, toframe)
  File "/usr/local/lib/python3.9/dist-packages/astropy/coordinates/builtin_frames/icrs_observed_transforms.py", line 76, in observed_to_icrs
    astrom = erfa_astrom.get().apco(observed_coo)
  File "/usr/local/lib/python3.9/dist-packages/astropy/coordinates/erfa_astrom.py", line 46, in apco
    lon, lat, height = frame_or_coord.location.to_geodetic('WGS84')
AttributeError: 'NoneType' object has no attribute 'to_geodetic'
```
  
Lines *327, 342* for telescope to *alt_az_to_equatorial*
Lines *184* for telescope to *equatorial_to_alt_az*