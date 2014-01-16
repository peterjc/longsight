#!/usr/bin/env python
"""Code for talking to an GY-80 sensor chip via I2C, intended for use on Raspberry Pi.

The GY-80 is a tiny orientation sensor chip with nine degrees of freedom (9-DOF,
from 3-DOF each for the accelerometer, compass and gyroscope) plus a barometer
which means it gets marketed as a ten dgree of freedom (10-DOF) sensor. Chips:

- HMC5883L (3-Axis Digital Compass / vector magnetometer), I2C Address 0x1E
- ADXL345 (3-Axis Digital Accelerometer), I2C Address 0x53
- L3G4200D (3-Axis Angular Rate Sensor / Gyro), I2C Address 0x69
- BMP085 (Barometric Pressure / Temperature Sensor), I2C Address 0x77

For my notes on how to connect this to a Raspberry Pi, including the wiring and the
system configuration hanges and some useful I2C software, see:
http://astrobeano.blogspot.com/2014/01/gy-80-orientation-sensor-on-raspberry-pi.html

Gyroscopes can track rotation of the sensor, but need an external point of reference
to give an absolute orientation or heading. This is provided by the accelerometer
(when at rest this tells us which way is down due to gravity), and the compass or
(more accurately vector magnetometer) tells us the direction of (magnetic) North.

Using the accelerometer and magnetometer/compass alone would give an orientation,
but will give errors from vibration which can be compensated for by the gryoscope.
The gryoscope alone is prone to drift, so the combination is much more robust.

In aeronautics and also submarines the standard axes convention is North, East, Down
(NED), while for ground based systems instead East, North, Up (ENU) is used. Most of
the online example code I've found is for remote control planes and gyrocopters and
therefore used NED. This does the same (even though I have a ground based project).

Rotation angles in both aeronautics and nautical terminology can be defined relative
to the local frame of reference: pitch is about the X axis (direction of travel),
pitch is about the Y axis (lateral to right of travel) and yaw is about the Z axis
(down).
"""
from __future__ import print_function

import sys
from time import sleep
from math import pi, sin, cos, atan2, sqrt
import numpy as np
import smbus

#Non-standard modules:
try:
    from Adafruit_I2C import Adafruit_I2C
    from Adafruit_ADXL345 import Adafruit_ADXL345 as ADXL345
    from Adafruit_BMP085 import BMP085
except ImportError:
    sys.stderr.write("Ensure Adafruit_ADXL345.py, Adafruit_BMP085.py and Adafruit_I2C.py are present\n")
    sys.stderr.write("\nSee: https://github.com/adafruit/Adafruit-Raspberry-Pi-Python-Code\n")
    sys.exit(1)

try:
    from hmc5883l import HMC5883L
    from i2cutils import i2c_raspberry_pi_bus_number
except ImportError:
    sys.stderr.write("Ensure hmc5883l.py and i2cutils.py are present and importable\n")
    sys.stderr.write("\nSee the following links, tweak the i2cutils import inside hmc58831.py:\n")
    sys.stderr.write("https://github.com/bitify/raspi/blob/master/i2c-sensors/bitify/python/sensors/hmc5883l.py\n")
    sys.stderr.write("https://github.com/bitify/raspi/blob/master/i2c-sensors/bitify/python/utils/i2cutils.py\n")
    sys.exit(1)
        

class GY80(object):
    def __init__(self, bus=None):
        if bus is None:
            i2c_bus = i2c_raspberry_pi_bus_number()

        #Default ADXL345 range +/- 2g is ideal for telescope use
        self.accel = ADXL345(busnum=i2c_bus)
        #self.gyro = ...
        self.compass = HMC5883L(bus=smbus.SMBus(i2c_bus), address = 0x1e, name="compass")
        self.barometer = BMP085() # Can't set bus as option

        #Establish NED frame of reference (North, East, Down)
        #Can't use v_mag directly as North since it will usually not be
        #quite horizontal (requiring tilt compensation), establish this
        #using the up/down axis from the accelerometer.
        #Note assumes starting at rest so only acceleration is gravity.
        v_acc = np.array(self.read_accel(), np.float)
        v_mag = np.array(self.read_compass(), np.float)
        v_down = v_acc * -1.0 #(sign change depends on sensor design?)
        v_east = np.cross(v_down, v_mag)
        v_north = np.cross(v_east, v_down)
        #Normalise the vectors...
        v_down /= sqrt((v_down ** 2).sum())
        v_east /= sqrt((v_east ** 2).sum())
        v_north /= sqrt((v_north ** 2).sum())
        print("Down: %s, East: %s, North: %s" % (v_down, v_east, v_north))

    def read_accel(self):
        """Returns an X, Y, Z tuple."""
        return self.accel.read()

    def read_compass(self, scaled=True):
        """Returns an X, Y, Z tuple."""
        compass = self.compass
        compass._read_raw_data()
        if scaled:
            return compass.scaled_x, compass.scaled_y, compass.scaled_z
        else:
            return compass.raw_x, compass.raw_y, compass.raw_z

                          

if __name__ == "__main__":
    print("Starting...")
    imu = GY80()
    try:
        while True:
            print(imu.read_accel())
            sleep(1)
    except KeyboardInterrupt:
        print()
        pass
    print("Done")
