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
but will give errors from vibration which can be compensated for by the gyroscope.
The gyroscope alone is prone to drift, so the combination is much more robust.

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
from time import sleep, time
from math import pi, sin, cos, asin, acos, atan2, sqrt
import numpy as np
import smbus

try:
    from adxl345 import ADXL345
    from hmc5883l import HMC5883L
    from bmp085 import BMP085
    from l3g4200d import L3G4200D
    from i2cutils import i2c_raspberry_pi_bus_number
except ImportError:
    sys.stderr.write("Ensure adxl345.py, hmc5883l.py bmp085.py, l3g4200d.py and i2cutils.py are present and importable\n")
    sys.stderr.write("\nSee the following links, tweak the i2cutils import inside hmc58831.py etc:\n")
    sys.stderr.write("https://github.com/bitify/raspi/blob/master/i2c-sensors/bitify/python/sensors/hmc5883l.py\n")
    sys.stderr.write("https://github.com/bitify/raspi/blob/master/i2c-sensors/bitify/python/utils/i2cutils.py\n")
    sys.exit(1)

#Local imports
from quaternions import _check_close
from quaternions import quaternion_to_rotation_matrix_rows, quaternion_from_rotation_matrix_rows
from quaternions import quaternion_from_axis_angle
from quaternions import quaternion_from_euler_angles, quaternion_to_euler_angles
from quaternions import quaternion_multiply, quaternion_normalise


class GY80(object):
    def __init__(self, bus=None):
        if bus is None:
            bus = smbus.SMBus(i2c_raspberry_pi_bus_number())

        #Default ADXL345 range +/- 2g is ideal for telescope use
        self.accel = ADXL345(bus, 0x53, name="accel")
        self.gyro = L3G4200D(bus, 0x69, name="gyro")
        self.compass = HMC5883L(bus, 0x1e, name="compass")
        self.barometer = BMP085(bus, 0x77, name="barometer")

        self._last_gyro_time = 0 #needed for interpreting gyro
        self.read_gyro_delta() #Discard first reading
        q_start = self.current_orientation_quaternion_mag_acc_only()
        self._q_start = q_start
        self._current_hybrid_orientation_q = q_start
        self._current_gyro_only_q = q_start

    def update(self):
        """Read the current sensor values & store them for smoothing. No return value."""
        t = time()
        delta_t = t - self._last_gyro_time
        if delta_t < 0.020:
            #Want at least 20ms of data
            return
        v_gyro = np.array(self.read_gyro(), np.float)
        v_acc = np.array(self.read_accel(), np.float)
        v_mag = np.array(self.read_compass(), np.float)
        self._last_gyro_time = t

        #Gyro only quaternion calculation (expected to drift)
        rot_mag = sqrt(sum(v_gyro**2))
        v_rotation = v_gyro / rot_mag
        q_rotation = quaternion_from_axis_angle(v_rotation, rot_mag * delta_t)
        self._current_gyro_only_q = quaternion_multiply(self._current_gyro_only_q, q_rotation)
        self._current_hybrid_orientation_q = quaternion_multiply(self._current_hybrid_orientation_q, q_rotation)

        if abs(sqrt(sum(v_acc**2)) - 1) < 0.3:
            #Approx 1g, should be stationary, and can use this for down axis...
            v_down = v_acc * -1.0
            v_east = np.cross(v_down, v_mag)
            v_north = np.cross(v_east, v_down)
            v_down /= sqrt((v_down**2).sum())
            v_east /= sqrt((v_east**2).sum())
            v_north /= sqrt((v_north**2).sum())
            #Complementary Filter
            #Combine (noisy) orientation from acc/mag, 2%
            #with (drifting) orientation from gyro, 98%
            q_mag_acc = quaternion_from_rotation_matrix_rows(v_north, v_east, v_down)
            self._current_hybrid_orientation_q = tuple(0.02*a + 0.98*b for a, b in
                                                       zip(q_mag_acc, self._current_hybrid_orientation_q))


        #1st order approximation of quaternion for this rotation (v_rotation, delta_t)
        #using small angle approximation, cos(theta) = 1, sin(theta) = theta
        #w, x, y, z = (1, v_rotation[0] * delta_t/2, v_rotation[1] *delta_t/2, v_rotation[2] * delta_t/2)
        #q_rotation = (1, v_rotation[0] * delta_t/2, v_rotation[1] *delta_t/2, v_rotation[2] * delta_t/2)
        return

    def current_orientation_quaternion_hybrid(self):
        """Current orientation using North, East, Down (NED) frame of reference."""
        self.update()
        return self._current_hybrid_orientation_q

    def current_orientation_quaternion_mag_acc_only(self):
        """Current orientation using North, East, Down (NED) frame of reference."""
        #Can't use v_mag directly as North since it will usually not be
        #quite horizontal (requiring tilt compensation), establish this
        #using the up/down axis from the accelerometer.
        #Note assumes starting at rest so only acceleration is gravity.
        v_acc = np.array(self.read_accel(), np.float)
        v_mag = np.array(self.read_compass(), np.float)
        return self._quaternion_from_acc_mag(v_acc, v_mag)

    def _quaternion_from_acc_mag(self, v_acc, v_mag):
        v_down = v_acc * -1.0 #(sign change depends on sensor design?)
        v_east = np.cross(v_down, v_mag)
        v_north = np.cross(v_east, v_down)
        #Normalise the vectors...
        v_down /= sqrt((v_down ** 2).sum())
        v_east /= sqrt((v_east ** 2).sum())
        v_north /= sqrt((v_north ** 2).sum())
        return quaternion_from_rotation_matrix_rows(v_north, v_east, v_down)

    def current_orientation_euler_angles_hybrid(self):
        """Current orientation using yaw, pitch, roll (radians) using sensor's frame."""
        return quaternion_to_euler_angles(*self.current_orientation_quaternion_hybrid())

    def current_orientation_euler_angles_mag_acc_only(self):
        """Current orientation using yaw, pitch, roll (radians) using sensor's frame."""
        return quaternion_to_euler_angles(*self.current_orientation_quaternion_mag_acc_only())

    def read_accel(self, scaled=True):
        """Returns an X, Y, Z tuple; if scaled in units of gravity."""
        accel = self.accel
        accel.read_raw_data()
        if scaled:
            return accel.accel_scaled_x, accel.accel_scaled_y, accel.accel_scaled_z
        else:
            return accel.accel_raw_x, accel.accel_raw_y, accel.accel_raw_z

    def read_gyro(self, scaled=True):
        """Returns an X, Y, Z tuple; If scaled uses radians/second.

        WARNING: Calling this method directly will interfere with the higher-level
        methods like ``read_gyro_delta`` which integrate the gyroscope readings to
        track orientation (it will miss out on the rotation reported in this call).
        """
        gyro = self.gyro
        gyro.read_raw_data()
        if scaled:
            return gyro.gyro_scaled_x, gyro.gyro_scaled_y, gyro.gyro_scaled_z
        else:
            return gyro.gyro_raw_x, gyro.gyro_raw_y, gyro.gyro_raw_z

    def read_gyro_delta(self):
        """Returns an X, Y, Z tuple - radians since last call."""
        g = self.gyro
        t = time()
        g.read_raw_data()
        d = np.array([g.gyro_scaled_x, g.gyro_scaled_y, g.gyro_scaled_z], np.float) / (t - self._last_gyro_time)
        self._last_gyro_time = t
        return d

    def read_compass(self, scaled=True):
        """Returns an X, Y, Z tuple."""
        compass = self.compass
        compass.read_raw_data()
        if scaled:
            return compass.scaled_x, compass.scaled_y, compass.scaled_z
        else:
            return compass.raw_x, compass.raw_y, compass.raw_z


if __name__ == "__main__":
    print("Starting...")
    imu = GY80()

    #Sanity test:
    x, y, z = imu.read_accel()
    g = sqrt(x*x + y*y + z*z)
    print("Magnitude of acceleration %0.2fg (%0.2f %0.2f %0.2f)" % (g, x, y, z))
    if abs(g - 1) > 0.3:
        sys.stderr.write("Not starting from rest, acceleration %0.2f\n" % g)
        sys.exit(1)
    print("Starting q by acc/mag (%0.2f, %0.2f, %0.2f, %0.2f)" % imu._q_start)

    try:
        while True:
            print()
            imu.update()
            #w, x, y, z = imu.current_orientation_quaternion_hybrid()
            w, x, y, z = imu._current_hybrid_orientation_q
            #print("Gyroscope/Accl/Comp q (%0.2f, %0.2f, %0.2f, %0.2f)" % (w, x, y, z))
            yaw, pitch, roll = quaternion_to_euler_angles(w, x, y, z)
            print("Gyroscope/Accl/Comp q (%0.2f, %0.2f, %0.2f, %0.2f), "
                  "yaw %0.1f, pitch %0.2f, roll %0.1f (degrees)" % (w, x, y, z,
                                                                    yaw   * 180.0 / pi,
                                                                    pitch * 180.0 / pi,
                                                                    roll  * 180.0 / pi))

            w, x, y, z = imu._current_gyro_only_q
            #print("Gyro-only quaternion  (%0.2f, %0.2f, %0.2f, %0.2f)" % (w, x, y, z))
            yaw, pitch, roll = quaternion_to_euler_angles(w, x, y, z)
            print("Gyro-only quaternion  (%0.2f, %0.2f, %0.2f, %0.2f), "
                  "yaw %0.1f, pitch %0.2f, roll %0.1f (degrees)" % (w, x, y, z,
                                                                    yaw   * 180.0 / pi,
                                                                    pitch * 180.0 / pi,
                                                                    roll  * 180.0 / pi))

            w, x, y, z = imu.current_orientation_quaternion_mag_acc_only()
            #print("Accel/Comp quaternion (%0.2f, %0.2f, %0.2f, %0.2f)" % (w, x, y, z))
            yaw, pitch, roll = quaternion_to_euler_angles(w, x, y, z)
            print("Accel/Comp quaternion (%0.2f, %0.2f, %0.2f, %0.2f), "
                  "yaw %0.1f, pitch %0.2f, roll %0.1f (degrees)" % (w, x, y, z,
                                                                    yaw   * 180.0 / pi,
                                                                    pitch * 180.0 / pi,
                                                                    roll  * 180.0 / pi))
            sleep(0.25)
    except KeyboardInterrupt:
        print()
        pass
    print("Done")
