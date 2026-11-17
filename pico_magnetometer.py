from machine import I2C, Pin
from math import atan2, pi
from mpu9250 import MPU9250
from time import sleep

MPU = 0x68
i2c = I2C(id=0, scl=Pin(1), sda=Pin(0))
print("I2C devices found:", i2c.scan())

m = MPU9250(i2c)
m.ak8963.calibrate(count=100)

filtered_x_value = 0.0
filtered_y_value = 0.0


def degrees_to_heading(degrees):
    if (degrees > 337) or (0 <= degrees <= 22):
        return "N"
    if 22 < degrees <= 67:
        return "NE"
    if 67 < degrees <= 112:
        return "E"
    if 112 < degrees <= 157:
        return "SE"
    if 157 < degrees <= 202:
        return "S"
    if 202 < degrees <= 247:
        return "SW"
    if 247 < degrees <= 292:
        return "W"
    if 292 < degrees <= 337:
        return "NW"
    return "N"


def low_pass_filter(raw_value: float, remembered_value: float) -> float:
    alpha = 0.8
    return (alpha * remembered_value) + ((1.0 - alpha) * raw_value)


def get_reading():
    global filtered_y_value, filtered_x_value
    mag_x, mag_y, _ = m.magnetic

    filtered_x_value = low_pass_filter(mag_x, filtered_x_value)
    filtered_y_value = low_pass_filter(mag_y, filtered_y_value)

    az = -atan2(filtered_y_value, filtered_x_value) * 180 / pi
    if az < 0:
        az += 360

    heading = degrees_to_heading(az)
    return az, heading


if __name__ == "__main__":
    while True:
        az, heading = get_reading()
        print(f"Compass: {az:.2f} deg | Heading: {heading}", end="\r")
        sleep(0.05)
