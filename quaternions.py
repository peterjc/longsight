"""Crude code for quaternions in Python.

TODO - Define a quaternion class?
"""

from __future__ import print_function

from math import pi, sin, cos, asin, acos, atan2, sqrt

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

def quaternion_mgnitude(w, x, y, z):
    return sqrt(w*w + x*x + y*y + z*z)

def quaternion_normalise(w, x, y, z):
    mag = sqrt(w*w + x*x + y*y + z*z)
    return w/mag, x/mag, y/mag, z/mag

def quaternion_from_axis_rotations(angle_x, angle_y, angle_z):
    """Quaternion from axis-angle rotation representation (in radians).

    e.g. Use the X, Y, Z values from a gyroscope as input.
    """
    #http://en.wikipedia.org/wiki/Conversion_between_quaternions_and_Euler_angles
    #Normalise angles to range -pi to +pi
    angle_x = angle_x % (2*pi)
    if angle_x > pi:
        angle_x -= 2*pi
    angle_y = angle_y % (2*pi)
    if angle_y > pi:
        angle_y -= 2*pi
    angle_z = angle_z % (2*pi)
    if angle_z > pi:
        angle_z -= 2*pi
    speed = sqrt(angle_x*angle_x + angle_y*angle_y + angle_z*angle_z)
    if speed < 0.000001:
        return 1, 0, 0, 0
    assert speed < 2*pi, "Angle overflow (%0.1f %0.1f %0.1f)" % (angle_x, angle_y, angle_z)
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

_check_close(quaternion_from_axis_rotations(0.334910, 0.374726, 0.635113),
             (0.9191202975975377, 0.3607701930128949, 0.3525546624578296, 0.2789234947407001))
_check_close(quaternion_to_axis_rotations(0.9191202975975377, 0.3607701930128949, 0.3525546624578296, 0.2789234947407001),
             (0.3349099999999998, 0.37472599999999995, 0.6351130000000001))


for a, b, c in [(1, 2, 3),
                #(-1, 2, 3),
                #(1, -2, 3),
                #(1, 2, -3),
                (4, 3, 2),
                (6, 1, 1),
                (5, 4, 3), #fails
                (6, 5, 4), #fails
                (1, 6, 1),
                (1, 2, 5),
                (1, 2, 6), #fails
                (1, 1, 6),
                (4, 1, 4),
                (5, 1, 5), #fails
                (6, 1, 6), #fails,
                ]:
    w, x, y, z = quaternion_from_axis_rotations(a, b, c)
    if a > pi: a -= 2*pi
    if b > pi: b -= 2*pi
    if c > pi: c -= 2*pi
    _check_close((w, x, y, z), quaternion_from_axis_rotations(a, b, c))
    a, b, c = abs(a), abs(b), abs(c) #TODO - fix loss of sign
    _check_close((a, b, c), quaternion_to_axis_rotations(w, x, y, z))
    _check_close((w, x, y, z), quaternion_from_axis_rotations(*quaternion_to_axis_rotations(w, x, y, z)))
#w, x, y, z = (-0.58655456819291307, 0.3349104965197246, 0.37472678876858784, 0.6351130069775921)
#_check_close(sqrt(w*w + x*x + y*y + z*z), 1.0)
#_check_close((w, x, y, z), quaternion_from_axis_rotations(*quaternion_to_axis_rotations(w, x, y, z)))
del w, x, y, z, a, b, c

def quaternion_from_axis_angle(vector, theta):
    sin_half_theta = sin(theta/2)
    return cos(theta/2), vector[0]*sin_half_theta, vector[1]*sin_half_theta, vector[2]*sin_half_theta

#TODO - Write quaternion_to_axis_angle and cross-validate

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
