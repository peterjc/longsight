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

def quaternion_from_axis_rotations(angle_x, angle_y, angle_z):
    """Quaternion from axis-angle rotation representation (in radians).

    e.g. Use the X, Y, Z values from a gyroscope as input.
    """
    #http://en.wikipedia.org/wiki/Conversion_between_quaternions_and_Euler_angles
    speed = sqrt(angle_x*angle_x + angle_y*angle_y + angle_z*angle_z)
    if speed < 0.000001:
        return 1, 0, 0, 0
    #Normalise
    angle_x /= speed
    angle_y /= speed
    angle_z /= speed
    half_a = speed * 0.5
    sin_half_a = sin(half_a)
    return cos(half_a), sin_half_a * cos(angle_x), sin_half_a * cos(angle_y), sin_half_a * cos(angle_z)

def quaternion_to_axis_rotations(w, x, y, z):
    """Quaternion to three axis-angle rotation representation (in radians)."""
    half_a = acos(w)
    speed = half_a * 2
    sin_half_a = sin(half_a)
    if sin_half_a:
        angle_x = acos(x / sin_half_a)
        angle_y = acos(y / sin_half_a)
        angle_z = acos(z / sin_half_a)
        return angle_x * speed, angle_y * speed, angle_z * speed
    else:
        return 0.0, 0.0, 0.0

_check_close((0, 0, 0), quaternion_to_axis_rotations(*quaternion_from_axis_rotations(0, 0, 0)))
_check_close((0, 0, pi), quaternion_to_axis_rotations(*quaternion_from_axis_rotations(0, 0, pi)))
_check_close((0, pi, 0), quaternion_to_axis_rotations(*quaternion_from_axis_rotations(0, pi, 0)))
_check_close((pi, 0, 0), quaternion_to_axis_rotations(*quaternion_from_axis_rotations(pi, 0, 0)))
_check_close((0, 0, pi/2), quaternion_to_axis_rotations(*quaternion_from_axis_rotations(0, 0, pi/2)))
_check_close((0, pi/2, 0), quaternion_to_axis_rotations(*quaternion_from_axis_rotations(0, pi/2, 0)))
_check_close((pi/2, 0, 0), quaternion_to_axis_rotations(*quaternion_from_axis_rotations(pi/2, 0, 0)))
_check_close((1, 2, 3), quaternion_to_axis_rotations(*quaternion_from_axis_rotations(1, 2, 3)))

_check_close((0,0,0,1), quaternion_from_axis_rotations(*quaternion_to_axis_rotations(0,0,0,1)))
_check_close((-0.58655456819291307, 0.3349104965197246, 0.37472678876858784, 0.6351130069775921),
             quaternion_from_axis_rotations(*quaternion_to_axis_rotations(
              -0.58655456819291307, 0.3349104965197246, 0.37472678876858784, 0.6351130069775921)))


def quaternion_to_rotation_matrix_rows(w, x, y, z):
    """Returns a tuple of three rows which make up a 3x3 rotatation matrix.

    It is trival to turn this into a NumPy array/matrix if desired."""
    x2 = x*x
    y2 = y*2
    z2 = z*2
    row0 = (1 - 2*y2 - 2*z2,
            2*x*y - 2*w*z,
            2*x*z + 2*w*y)
    row1 = (2*x*y + 2*w*z,
            1 - 2*x2 - 2*z2,
            2*y*z - 2*w*x)
    row2 = (2*x*z - 2*w*y,
            2*y*z + 2*w*x,
            1 - 2*x2 - 2*y2)
    return row0, row1, row2

def quaternion_from_rotation_matrix_rows(row0, row1, row2):
    #No point merging three rows into a 3x3 matrix if just want quaternion
    #Based on several sources including the C++ implementation here:
    #http://www.camelsoftware.com/firetail/blog/uncategorized/quaternion-based-ahrs-using-altimu-10-arduino/
    #http://www.camelsoftware.com/firetail/blog/c/imu-maths/
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

w, x, y, z = quaternion_from_axis_rotations(pi, 0, 0)
_check_close(quaternion_from_rotation_matrix_rows(*quaternion_to_rotation_matrix_rows(w, x, y, z)), (w, x, y, z))
w, x, y, z = quaternion_from_axis_rotations(0, pi, 0)
_check_close(quaternion_from_rotation_matrix_rows(*quaternion_to_rotation_matrix_rows(w, x, y, z)), (w, x, y, z))
w, x, y, z = quaternion_from_axis_rotations(0, 0, pi)
_check_close(quaternion_from_rotation_matrix_rows(*quaternion_to_rotation_matrix_rows(w, x, y, z)), (w, x, y, z))
w, x, y, z = quaternion_from_axis_rotations(1, 2, 3)
_check_close(quaternion_from_rotation_matrix_rows(*quaternion_to_rotation_matrix_rows(w, x, y, z)), (w, x, y, z))

#TODO - Double check which angles exactly have I calculated (which frame etc)?
def quaternion_from_euler_angles(yaw, pitch, roll):
    """Returns (w, x, y, z) quaternion from angles in radians.

    Assuming angles given in the moving frame of reference of the sensor,
    not a fixed Earth bound observer.
    """
    #Roll = phi, pitch = theta, yaw = psi
    return (cos(roll/2)*cos(pitch/2)*cos(yaw/2) + sin(roll/2)*sin(pitch/2)*sin(yaw/2),
            sin(roll/2)*cos(pitch/2)*cos(yaw/2) - cos(roll/2)*sin(pitch/2)*sin(yaw/2),
            cos(roll/2)*sin(pitch/2)*cos(yaw/2) + sin(roll/2)*cos(pitch/2)*sin(yaw/2),
            cos(roll/2)*cos(pitch/2)*sin(yaw/2) - sin(roll/2)*sin(pitch/2)*cos(yaw/2))

def quaternion_to_euler_angles(w, x, y, z):
    """Returns angles about Z, Y, X axes in radians (yaw, pitch, roll).

    Using moving frame of reference of the sensor, not the fixed frame of
    an Earth bound observer..
    """
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

def quaternion_multiply(a, b):
    a_w, a_x, a_y, a_z = a
    b_w, b_x, b_y, b_z = b
    return (a_w*b_w - a_x*b_x - a_y*b_y - a_z*b_z,
            a_w*b_x + a_x*b_w + a_y*b_z - a_z*b_y,
            a_w*b_y - a_x*b_z + a_y*b_w + a_z*b_x,
            a_w*b_z + a_x*b_y - a_y*b_x + a_z*b_w)

_check_close(quaternion_multiply((0, 0, 0, 1), (0, 0, 1, 0)), (0, -1, 0, 0))

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
        self._current_hybrid_orientation_q = self.current_orientation_quaternion_mag_acc_only()
        self._current_gryo_only_q = self._current_hybrid_orientation_q
        self._current_gryo_only_v = quaternion_to_axis_rotations(*self._current_gryo_only_q)
        _check_close(self._current_gryo_only_q, quaternion_from_axis_rotations(*self._current_gryo_only_v))


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

        #Gyro only vector calculation (expected to drift)
        self._current_gryo_only_v += v_gyro * delta_t

        #Gyro only quaternion calculation (expected to drift)
        q_rotation = quaternion_from_axis_rotations(*tuple(v_gyro * delta_t))
        self._current_gryo_only_q = quaternion_multiply(self._current_gryo_only_q, q_rotation)

        #Now update self.current_orientation
        if abs(sqrt(sum(v_acc**2)) - 1) < 0.3:
            correction_stength = 0.1
            #Approx 1g, should be stationary, and can use this for down axis...
            v_down = v_acc * -1.0
            v_east = np.cross(v_down, v_mag)
            v_north = np.cross(v_east, v_down)
            v_down /= sqrt((v_down**2).sum())
            v_east /= sqrt((v_east**2).sum())
            v_north /= sqrt((v_north**2).sum())
            row0, row1, row2 = quaternion_to_rotation_matrix_rows(*self._current_hybrid_orientation_q)
            correction = np.cross(v_north, row0) + np.cross(v_east, row1) + np.cross(v_down, row2)
            v_rotation = v_gyro + correction*correction_stength
        else:
            #Use just the gyro
            v_rotation = v_gyro

        #1st order approximation of quaternion for this rotation (v_rotation, delta_t)
        #using small angle approximation, cos(theta) = 1, sin(theta) = theta
        #w, x, y, z = (1, v_rotation[0] * delta_t/2, v_rotation[1] *delta_t/2, v_rotation[2] * delta/2)
        q_rotation = quaternion_from_axis_rotations(*tuple(v_rotation * delta_t))

        #Apply the (possibly corrected) angular motion
        self._current_hybrid_orientation_q = quaternion_multiply(self._current_hybrid_orientation_q, q_rotation)

        return

    def current_orientation_quaternion_hybrid(self):
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

    def current_orientation_euler_angles(self):
        """Current orientation using yaw, pitch, roll (radians) using sensor's frame."""
        return quaternion_to_euler_angles(*self._current_hybrid_orientation_q_mag_acc_only())

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
          
    try:
        while True:
            print()
            imu.update()
            w, x, y, z = imu.current_orientation_quaternion_hybrid()
            #print("Gyroscope/Accl/Comp q (%0.2f, %0.2f, %0.2f, %0.2f)" % (w, x, y, z))
            yaw, pitch, roll = quaternion_to_euler_angles(w, x, y, z)
            print("Gyroscope/Accl/Comp q (%0.2f, %0.2f, %0.2f, %0.2f), "
                  "yaw %0.1f, pitch %0.2f, roll %0.1f (degrees)" % (w, x, y, z,
                                                                    yaw   * 180.0 / pi,
                                                                    pitch * 180.0 / pi,
                                                                    roll  * 180.0 / pi))

            w, x, y, z = quaternion_from_axis_rotations(*imu._current_gryo_only_v)
            yaw, pitch, roll = quaternion_to_euler_angles(w, x, y, z)
            print("Gyro-only with vector (%0.2f, %0.2f, %0.2f, %0.2f), "
                  "yaw %0.1f, pitch %0.2f, roll %0.1f (degrees)" % (w, x, y, z,
                                                                    yaw   * 180.0 / pi,
                                                                    pitch * 180.0 / pi,
                                                                    roll  * 180.0 / pi))            

            w, x, y, z = imu._current_gryo_only_q
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
            sleep(1)
    except KeyboardInterrupt:
        print()
        pass
    print("Done")
