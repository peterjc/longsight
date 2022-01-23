# Items to Check once it runs
Did the refactoring to astropy provide the right values?

Lines *327, 342* for telescope to *alt_az_to_equatorial*
Lines *184* for telescope to *equatorial_to_alt_az*

# Pending Items to Solve

- Connecting to Sky Safari Plus 7.0 works, after connecting the following comes up and then Sky Safari disconnects. Could be the 2488 degrees?
```
def radians_to_sddmmss(angle):
    """Signed degrees, arc-minutes, arc-seconds as sDD*MM:SS# for protocol."""
    if angle < 0.0:
        sign = "-"
        angle = abs(angle)
    else:
        sign = "+"
    fraction, degrees = modf(angle * 180 / pi)
    fraction, arcminutes = modf(fraction * 60.0)
    if debug:
        sys.stdout.write("\nradians_to_sddmmss function\n")
        sys.stdout.write("angle: %s\n" % angle)
        sys.stdout.write("fraction: %s\n" % fraction)
        sys.stdout.write("degress: %s\n" % degrees)
        sys.stdout.write("return: %s\n" % "%s%02i*%02i:%02i#" % (sign, degrees, arcminutes, round(fraction * 60.0)))
    return "%s%02i*%02i:%02i#" % (sign, degrees, arcminutes, round(fraction * 60.0))

def meade_lx200_cmd_GD_get_dec():
    """For the :GD# command, Get Telescope Declination.

    Returns: sDD*MM# or sDD*MM'SS#
    Depending upon the current precision setting for the telescope.
    """
    update_alt_az()
    ra, dec = alt_az_to_equatorial(local_alt, local_az)
    if debug:
        sys.stdout.write("\nmeade_lx200_cmd_GD_get_dec function\n")
        sys.stderr.write("RA %s (%0.5f radians), dec %s (%0.5f radians)\n"
                         % (radians_to_hhmmss(ra), ra, radians_to_sddmmss(dec), dec))
    if high_precision:
        return radians_to_sddmmss(dec)
    else:
        return radians_to_sddmm(dec)
```

The function *meade_lx200_cmd_GD_get_dec* calls the *alt_az_to_equatorial* as passes data to *radians_to_sddmmss* but due to the "degrees" value seeming way off, I think this is causing the "QUIT" command to be generated and close the connection.

```
meade_lx200_cmd_GD_get_dec function

radians_to_sddmmss function
angle: 26.66940372615943
fraction: 0.6565383644219764
degress: 1528.0
RA 23:48:14# (6.23183 radians), dec -1528*02:39# (-26.66940 radians)

radians_to_sddmmss function
angle: 26.66940372615943
fraction: 0.6565383644219764
degress: 1528.0
Command ':GD', sending '-1528*02:39#'
Processing ':Q#'
Command ':Q', no response
```
