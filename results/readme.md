# Items to Check once it runs
- Did the refactoring to astropy provide the right values?

# Pending Items to Solve

```
Processing ':CM#'
':CM#' --> ':CM' as command
FUNCTION meade_lx200_cmd_CM_sync
FUNCTION radians_to_sddmmss - passed values: 6.102735949907029
FUNCTION radians_to_sddmmss - actual values: angle = 6.102735949907029, fraction = 0.5536711374780481, degrees = 1.0, arcminutes = 56.0

FUNCTION radians_to_sddmmss - return values: +01*56:33#

FUNCTION radians_to_hhmmss
FUNCTION radians_to_hms
Resetting from current position Alt +01*56:33# (6.10274 radians), Az 19:20:10# (5.06215 radians)
FUNCTION radians_to_hhmmss
FUNCTION radians_to_hms
FUNCTION radians_to_sddmmss - passed values: -0.2921487242366064
FUNCTION radians_to_sddmmss - actual values: angle = 0.2921487242366064, fraction = 0.5796296296296308, degrees = 0.0, arcminutes = 5.0

FUNCTION radians_to_sddmmss - return values: -00*05:35#

New target position RA 06:46:07# (1.77202 radians), Dec -00*05:35# (-0.29215 radians)
FUNCTION equatorial_to_alt_az - passed values: ra 1.7720182451394093 - dec -0.2921487242366064
FUNCTION equatorial_to_alt_az - returned values: alt '177' - az '17'
Traceback (most recent call last):
  File "/home/pi/longsight/telescope_server.py", line 732, in <module>
    resp = command_map[cmd]()
  File "/home/pi/longsight/telescope_server.py", line 257, in meade_lx200_cmd_CM_sync
    offset_alt += (target_alt - local_alt)
TypeError: unsupported operand type(s) for -: 'str' and 'float'
```

- Connecting to Sky Safari Plus 7.0 works, after connecting if you choose "align" the program crashes *lines 191 - equatorial_to_alt_az*

