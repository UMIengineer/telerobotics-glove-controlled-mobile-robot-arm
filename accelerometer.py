from machine import I2C, Pin
from math import atan2, copysign, cos, pi, sin, sqrt
from mpu9250 import MPU9250
from time import sleep

MPU = 0x68
id = 0
sda = Pin(0)
scl = Pin(1)

i2c = I2C(id=0, scl=Pin(1), sda=Pin(0))

print(i2c.scan())
k = MPU9250(i2c)

def get_acceleration_data():

    accel = k.acceleration
    return accel