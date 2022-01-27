# Items to Check once it runs
- Did the refactoring to astropy provide the right values?
- *meade_lx200_cmd_St_set_latitude* and *meade_lx200_cmd_Sg_set_longitude* so far never called

# Pending Items to Solve

The perspective/screen of Sky Safari jumps all over the place as if the values are jumping eractically from one extreme to another. It's possible with Astropy some of the math is not required in the *alt_az_to_equatorial*?

- Connecting to Sky Safari Plus 7.0 works, after connecting if you choose "align" the following comes up and the program crashes *lines 184 - equatorial_to_alt_az*

> *equatorial_to_alt_az* needs to be rewritten
