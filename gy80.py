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
from math import pi, sin, cos, asin, acos, atan2, sqrt
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


def _check_close(a, b, error=0.0001):
    if isinstance(a, (tuple, list)):
        assert isinstance(b, (tuple, list))
        assert len(a) == len(b)
        for a1, b1 in zip(a, b):
            diff = abs(a1-b1)
            if diff > error:
                raise ValueError("%s vs %s, for %s vs %s difference %s > %s"
                         % (a, b, a1, b1, diff, error))
        return
    diff = abs(a-b)
    if diff > error:
        raise ValueError("%s vs %s, difference %s > %s"
                         % (a, b, diff, error))

def quaternion_from_rotation_matrix_rows(row0, row1, row2):
    #No point merging three rows into a 3x3 matrix if just want quaternion
    #Based on several sources including the C++ implementation here:
    #http://www.camelsoftware.com/firetail/blog/uncategorized/quaternion-based-ahrs-using-altimu-10-arduino/
    trace = row0[0] + row1[1] + row2[2]
    if trace > row2[2]:
        S = sqrt(1.0 + trace) *  2
        w = 0.25 * S
        x = (row2[1] - row1[2]) / S
        y = (row0[2] - row2[0]) / S
        z = (row1[0] - row0[1]) / S
    elif row0[0] < row1[1] and row0[0] < row2[2]:
        S = sqrt(1.0 + row0[0] - row1[1] - row2[2]) * 2
        w = (row2[1] - row1[2]) / S
        x = 0.25 * S
        y = (row0[1] + row1[0]) / S
        z = (row0[2] + row2[0]) / S
    elif row1[1] < row2[2]:
        S = sqrt(1.0 + row1[1] - row0[0] - row2[2]) * 2
        w = (row0[2] - row2[0]) / S
        x = (row0[1] + row1[0]) / S
        y = 0.25 * S
        z = (row1[2] + row2[1]) / S
    else:
        S = sqrt(1.0 + row2[2] - row0[0] - row1[1]) * 2
        w = (row1[0] - row0[1]) / S
        x = (row0[2] + row2[0]) / S
        y = (row1[2] + row2[1]) / S
        z = 0.25 * S
    return w, x, y, z

#TODO - Double check which angles exactly have I calculated (which frame etc)?
def quaternion_from_euler_angles(yaw, pitch, roll):
    """Returns (w, x, y, z) quaternion from angles in radians."""
    #Roll = phi, pitch = theta, yaw = psi
    return (cos(roll/2)*cos(pitch/2)*cos(yaw/2) + sin(roll/2)*sin(pitch/2)*sin(yaw/2),
            sin(roll/2)*cos(pitch/2)*cos(yaw/2) - cos(roll/2)*sin(pitch/2)*sin(yaw/2),
            cos(roll/2)*sin(pitch/2)*cos(yaw/2) + sin(roll/2)*cos(pitch/2)*sin(yaw/2),
            cos(roll/2)*cos(pitch/2)*sin(yaw/2) - sin(roll/2)*sin(pitch/2)*cos(yaw/2))

def quaternion_to_euler_angles(w, x, y, z):
    """Returns angles about Z, Y, X axes in radians (yaw, pitch, roll)."""
    w2 = w*w
    x2 = x*x
    y2 = y*y
    z2 = z*z
    return (atan2(2.0 * (x*y + z*w), (w2 + x2 - y2 - z2)), # -pi to pi
            asin(2.0 * (w*y - x*z) / (w2 + x2 + y2 + z2)), # -pi/2 to +pi/2
            atan2(2.0 * (y*z + x*w), (w2 - x2 - y2 + z2))) # -pi to pi

_check_close(quaternion_to_euler_angles(0, 1, 0, 0), (0, 0, pi))
_check_close(quaternion_to_euler_angles(0,-1, 0, 0), (0, 0, pi))
_check_close(quaternion_from_euler_angles(0, 0, pi), (0, 1, 0, 0))

_check_close(quaternion_to_euler_angles(0, 0, 1, 0), (pi, 0, pi))
_check_close(quaternion_to_euler_angles(0, 0,-1, 0), (pi, 0, pi))
_check_close(quaternion_from_euler_angles(pi, 0, pi), (0, 0, 1, 0))

_check_close(quaternion_to_euler_angles(0, 0, 0, 1), (pi, 0, 0))
_check_close(quaternion_to_euler_angles(0, 0, 0,-1), (pi, 0, 0))
_check_close(quaternion_from_euler_angles(pi, 0, 0), (0, 0, 0, 1))

_check_close(quaternion_to_euler_angles(0, 0, 0.5*sqrt(2), 0.5*sqrt(2)), (pi, 0, pi/2))
_check_close(quaternion_from_euler_angles(pi, 0, pi/2), (0, 0, 0.5*sqrt(2), 0.5*sqrt(2)))

_check_close(quaternion_to_euler_angles(0, 0.5*sqrt(2), 0, 0.5*sqrt(2)), (0, -pi/2, 0))
_check_close(quaternion_to_euler_angles(0.5*sqrt(2), 0,-0.5*sqrt(2), 0), (0, -pi/2, 0))
_check_close(quaternion_from_euler_angles(0, -pi/2, 0), (0.5*sqrt(2), 0, -0.5*sqrt(2), 0))

_check_close(quaternion_to_euler_angles(0, 1, 1, 0), (pi/2, 0, pi)) #Not normalised
_check_close(quaternion_to_euler_angles(0, 0.5*sqrt(2), 0.5*sqrt(2), 0), (pi/2, 0, pi))
_check_close(quaternion_from_euler_angles(pi/2, 0, pi), (0, 0.5*sqrt(2), 0.5*sqrt(2), 0))

#w, x, y, z = quaternion_from_euler_angles(pi, 0, pi)
#print("quarternion (%0.2f, %0.2f, %0.2f, %0.2f) magnitude %0.2f" % (w, x, y, z, sqrt(w*w + x*x + y*y + z*z)))


class GY80(object):
    def __init__(self, bus=None):
        if bus is None:
            i2c_bus = i2c_raspberry_pi_bus_number()

        #Default ADXL345 range +/- 2g is ideal for telescope use
        self.accel = ADXL345(busnum=i2c_bus)
        #self.gyro = ...
        self.compass = HMC5883L(bus=smbus.SMBus(i2c_bus), address = 0x1e, name="compass")
        self.barometer = BMP085() # Can't set bus as option

    def current_orientation(self):
        """Current orientation using North, East, Down (NED) frame of reference."""
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
        return quaternion_from_rotation_matrix_rows(v_north, v_east, v_down)

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
            w, x, y, z = imu.current_orientation()
            print("Quaternion (%0.2f, %0.2f, %0.2f, %0.2f)" % (w, x, y, z))
            yaw, pitch, roll = quaternion_to_euler_angles(w, x, y, z)
            print("My function gives Euler angles %0.2f, %0.2f, %0.2f (radians), "
                  "yaw %0.1f, pitch %0.2f, roll %0.1f (degrees)" % (yaw, pitch, roll,
                                                                    yaw   * 180.0 / pi,
                                                                    pitch * 180.0 / pi,
                                                                    roll  * 180.0 / pi))
            sleep(1)
    except KeyboardInterrupt:
        print()
        pass
    print("Done")
