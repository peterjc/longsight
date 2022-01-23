# Items to Check once it runs
Did the refactoring to astropy provide the right values?

Lines *327, 342* for telescope to *alt_az_to_equatorial*
Lines *184* for telescope to *equatorial_to_alt_az*

# Pending Items to Solve

- Connecting to Sky Safari Plus 7.0 works, after connecting the following comes up and then Sky Safari disconnects. Could be the 2488 degrees?
```
Processing ':St+51*40#'
Command ':St', argument '+51*40'
Error with :St+51d40# latitude: Cannot parse first argument data "" for attribute ra
Command ':St', sending '0'
Processing ':Sg351*40#'
Command ':Sg', argument '351*40'
Error with :Sg351d40# longitude: Cannot parse first argument data "" for attribute dec
Command ':Sg', sending '0'
Processing ':SG-01.0#'
Command ':SG', argument '-01.0'
Local site timezone now -1.0
Command ':SG', sending '1'
Processing ':SG-01.0#'
Command ':SG', argument '-01.0'
Local site timezone now -1.0
Command ':SG', sending '1'
Processing ':SL22:57:48#'
Command ':SL', argument '22:57:48'
Requested site time 22:57:48 (TZ -1.0), new offset -1s, total offset -1s
Effective site date/time is 2022-01-23 23:57:48.546640 (local time), 2022-01-23 22:57:48.546867 (GMT/UTC)
Command ':SL', sending '1'
Processing ':SC01/23/22#'
Command ':SC', argument '01/23/22'
Requested site date 01/23/22 (MM/DD/YY) gives offset of 0 days
Effective site date/time is 2022-01-23 23:57:48.597357 (local time), 2022-01-23 22:57:48.597577 (GMT/UTC)
Command ':SC', sending '1Updating Planetary Data#                              #'
Processing ':GR#'
alt 0.7364696897183051
az 0.32560018147626457
Command ':GR', sending '00:04:05#'
Processing ':RS#'
Command ':RS', no response
Processing ':GD#'
alt 6.240148157794611
az 4.87558243585766
angle: 43.426638705069934
fraction: 0.7869743984392699
degress: 2488.0
RA 00:26:06# (0.11388 radians), dec -2488*09:47# (-43.42664 radians)
angle: 43.426638705069934
fraction: 0.7869743984392699
degress: 2488.0
Command ':GD', sending '-2488*09:47#'
Processing ':Q#'
Command ':Q', no response
```
