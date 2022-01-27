# Items to Check once it runs
- Did the refactoring to astropy provide the right values?
- Is the perspective and the values all correct, Sky Safari seems off from the perspective I would expect.
- *meade_lx200_cmd_St_set_latitude* and *meade_lx200_cmd_Sg_set_longitude* so far never called

Lines *327, 342* for telescope to *alt_az_to_equatorial*
Lines *184* for telescope to *equatorial_to_alt_az*

# Pending Items to Solve

- Connecting to Sky Safari Plus 7.0 works, after connecting if you choose "align" the following comes up and the program crashes *lines 184 - equatorial_to_alt_az*

```
FUNCTION meade_lx200_cmd_GD_get_dec
FUNCTION radians_to_hhmmss
FUNCTION radians_to_hms
FUNCTION radians_to_sddmmss - passed values: 0.007224547520221727
FUNCTION radians_to_sddmmss - actual values: angle = 0.007224547520221727, fraction = 0.1379786939334699, degrees = 0.0, arcminutes = 0.0

FUNCTION radians_to_sddmmss - return values: +00*00:08#

RA 03:26:42# (0.90189 radians), dec +00*00:08# (0.00722 radians)
FUNCTION radians_to_sddmmss - passed values: 0.007224547520221727
FUNCTION radians_to_sddmmss - actual values: angle = 0.007224547520221727, fraction = 0.1379786939334699, degrees = 0.0, arcminutes = 0.0

FUNCTION radians_to_sddmmss - return values: +00*00:08#

Command ':GD', sending '+00*00:08#'
Processing ':Q#'
Command ':Q', no response 
```

Resulting in a disconnect with Sky Safari Plus 7.0, possible value of DEC is incorrect from *alt_az_to_equatorial*



*equatorial_to_alt_az* needs to be rewritten
