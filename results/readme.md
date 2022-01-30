# Items to Check once it runs
- Did the refactoring to astropy provide the right values?
- *meade_lx200_cmd_St_set_latitude* and *meade_lx200_cmd_Sg_set_longitude* so far never called

# Pending Items to Solve

The perspective/screen of Sky Safari jumps all over the place as if the values are jumping eractically from one extreme to another. It's possible with Astropy some of the math is not required in the *alt_az_to_equatorial*?

> FUNCTION alt_az_to_equatorial - actual values: ra 4.906959035779865 - dec -0.12529272564088567
> FUNCTION alt_az_to_equatorial - actual values: ra 5.705811927991121 - dec -0.2685587555830068
> FUNCTION alt_az_to_equatorial - actual values: ra 6.05825076135398 - dec -0.2923727888350321
> FUNCTION alt_az_to_equatorial - actual values: ra 0.15035517998866865 - dec -0.25484069778244123
> FUNCTION alt_az_to_equatorial - actual values: ra 0.4378421902937326 - dec -0.22571091432518617
> FUNCTION alt_az_to_equatorial - actual values: ra 0.6687224615932523 - dec -0.18638351681985768
> FUNCTION alt_az_to_equatorial - actual values: ra 0.9406634036803876 - dec -0.18057505980703245
> FUNCTION alt_az_to_equatorial - actual values: ra 1.3600532749398022 - dec -0.19879488006946985

Without moving the sensor it seems the values are somehow quite varying

- Connecting to Sky Safari Plus 7.0 works, after connecting if you choose "align" the program crashes *lines 191 - equatorial_to_alt_az*

> *equatorial_to_alt_az* needs to be rewritten
