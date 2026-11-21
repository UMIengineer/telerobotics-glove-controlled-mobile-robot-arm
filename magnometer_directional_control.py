from machine import I2C, Pin
from math import sqrt, atan2, pi, copysign, sin, cos
from mpu9250 import MPU9250
from time import sleep

MPU = 0x68
id = 0
sda = Pin(0)
scl = Pin(1)

i2c = I2C(id=id, scl=scl, sda=sda)

print(i2c.scan())
m = MPU9250(i2c)

# Calibration and bias offset
m.ak8963.calibrate(count=100)

# For low pass filtering
filtered_x_value = 0.0
filtered_y_value = 0.0

def degrees_to_heading(degrees):
    heading = ""
    if (degrees >= 337.5) or (degrees < 22.5):
        heading = 'N'
    if 22.5 <= degrees < 67.5:
        heading = "NE"
    if 67.5 <= degrees < 112.5:
        heading = "E"
    if 112.5 <= degrees < 157.5:
        heading = "SE"
    if 157.5 <= degrees < 202.5:
        heading = "S"
    if 202.5 <= degrees < 247.5:
        heading = "SW"
    if 247.5 <= degrees < 292.5:
        heading = "W"
    if 292.5 <= degrees < 337.5:
        heading = "NW"
    return heading
def get_magnometer_readings(ax, ay, az) -> tuple:
    ''' Returns the readings from the sensor '''
    global filtered_y_value, filtered_x_value

    mag_x, mag_y, mag_z = m.magnetic

    mx = mag_y
    my = mag_x
    mz = -mag_z
    roll = atan2(ay, az + 1e-6)
    pitch = atan2(-ax, sqrt(ay*ay + az*az))
    x_horizontal = mx * cos(pitch) + my * sin(roll) * sin(pitch) + mz * cos(roll) * sin(pitch)
    y_horizontal = my * cos(roll) - mz * sin(roll)
    filtered_x_value = low_pass_filter(x_horizontal, filtered_x_value)
    filtered_y_value = low_pass_filter(y_horizontal, filtered_y_value)

    azimuth = atan2(filtered_y_value, filtered_x_value) * 180 / pi

    # make sure the angle is always positive, between 0 and 360 degrees
    if azimuth < 0:
        azimuth += 360
    heading = degrees_to_heading(azimuth)

    return azimuth, heading

def low_pass_filter(raw_value:float, remembered_value):
    alpha = 0.5
    filtered = 0
    filtered = (alpha * remembered_value) + (1.0 - alpha) * raw_value
    return filtered