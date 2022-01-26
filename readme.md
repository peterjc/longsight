# Original Project

In 2014 or there abouts [Peter Cook](https://github.com/peterjc) put together an amzing little project.

[Blog Posts](http://astrobeano.blogspot.com/2014/01/instrumented-telescope-with-raspberry.html)

The idea was to use a Raspberry Pi and Gyro sensors to create a "Push To" style mount for his telescope.

>Instrumented Telescope with Raspberry Pi and orientation sensor
>A "Push To" telescope mount is like a fully automated "Go To" telescope mount, but without the motors. You must manually move the telescope, but because the >telescope knows where it is pointed, you get live tracking telling you where it needs to go.

Fast forward to 2022, 
- the GY-80 module originally used is out of date.
- astropysics - a Python module used is no longer maintained
- SkySafari has a whole lot of new versions

This project is now an attempt to perseve the original hard work and begin to refactor the code. The needs I have are limited to the "Push To", image capturing and camera connection are not something I am focused on.

# Current Progress

- [Corrections to Date](corrections.md)
- [Open Items](todo.md)

# Sky Safari Plus

Testing in the original project was done in Sky Safari Plus 4.0, current testing is in Sky Safari Plus 7.0
 
Telescope usually setup as:

```
Scope Type: Meade LX-200 GPS
Mount Type: Equatorial Push-To (or any push to setting)
Auto-Detect SkyFi: Off
IP Address: That of the computer running this script (default 10.0.0.1)
Port Number: 4030 (default)
Set Time & Location: On (default is off)
Readout Rate: 4 per second (default)
Save Log File: Off (default)
```

# Tools 

In order to try and understand Latitude and Longitude, and how to convert that to degrees and then to radians

- [Decimal Degrees Units to Degrees, Minutes and Seconds Converter](https://www.engineeringtoolbox.com/latitude-longitude-d_1371.html)
- [Converting degrees to radians and vice versa](https://planetcalc.com/71/)

Example Greenwich
- 51.4934° N, 0.0098° E
- > Latitude : 51 deg 29 min 36.24 sec
  > Longitude: 0 deg 0 min 35.28 sec
- Radians 0.898729 0.000171
