import RPi.GPIO as GPIO
import time
import threading
from pynput import keyboard
from client_get_pico_data import pico_client
from glove_servomotor_integration import (
    potentiometer_servo_control,
    flexsensor_servo_control,
    accelerometer_servo_control,
)
from hand_gesture_motor_control import RobotVision

# GPIO Setup (BCM)
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

ENA, ENB = 13, 20
IN1, IN2, IN3, IN4 = 19, 16, 21, 26

pins = [ENA, ENB, IN1, IN2, IN3, IN4]
for pin in pins:
    GPIO.setup(pin, GPIO.OUT, initial=GPIO.LOW)

# PWM Initialisation
Speed = 50
PWM_A = GPIO.PWM(ENA, 1000)
PWM_B = GPIO.PWM(ENB, 1000)
PWM_A.start(0)
PWM_B.start(0)

# Computer Vision Control Initialisation
vision = RobotVision()
current_vision_speed = Speed


def Motor_Speed(val):
    PWM_A.ChangeDutyCycle(val)
    PWM_B.ChangeDutyCycle(val)


def Move_Forward(speed_val):
    GPIO.output([IN1, IN4], True)
    GPIO.output([IN2, IN3], False)
    Motor_Speed(speed_val)


def Move_Backward(speed_val):
    GPIO.output([IN1, IN4], False)
    GPIO.output([IN2, IN3], True)
    Motor_Speed(speed_val)


def Move_Right():
    GPIO.output([IN1, IN3], False)
    GPIO.output([IN2, IN4], True)
    Motor_Speed(Speed)


def Move_Left():
    GPIO.output([IN1, IN3], True)
    GPIO.output([IN2, IN4], False)
    Motor_Speed(Speed)


def Stop():
    GPIO.output([IN1, IN2, IN3, IN4], False)
    Motor_Speed(0)


# Shared latest sensor state from Pico W persistent TCP stream
latest_data = {}
data_lock = threading.Lock()


def network_loop():
    pico = pico_client()
    while True:
        data = pico.getPicoData()
        if data:
            with data_lock:
                latest_data.update(data)


def servo_loop():
    while True:
        with data_lock:
            data = dict(latest_data)
        if data:
            ax = data.get("accelerometer", {}).get("x", 0)
            flex_voltage = data.get("flex", {}).get("Flex Sensor Voltage", 0)
            pot1 = data.get("pot", {}).get("Pot 1 Resistance", 0)
            pot2 = data.get("pot", {}).get("Pot 2 Resistance", 0)

            accelerometer_servo_control(ax)
            flexsensor_servo_control(flex_voltage)
            potentiometer_servo_control(pot1, pot2)
        time.sleep(0.02)  # 50 Hz control loop


threading.Thread(target=network_loop, daemon=True).start()
threading.Thread(target=servo_loop, daemon=True).start()


def on_release(key):
    if key == keyboard.Key.esc:
        return False


listener = keyboard.Listener(on_release=on_release)
listener.start()

speed_map = {
    "sp1": 25,
    "sp2": 50,
    "sp3": 75,
    "sp4": 100,
}

print("--- System Active: Vision & Wearable Glove Control (Press ESC to Quit) ---")

try:
    while listener.running:
        label, confidence = vision.get_gesture(show_debug=False)
        if confidence > 0.75 and label in speed_map:
            current_vision_speed = speed_map[label]

        with data_lock:
            data = dict(latest_data)

        if data:
            ay = data.get("accelerometer", {}).get("y", 0)
            direction = data.get("mag", {}).get("Direction", "")

            if confidence > 0.80 and label == "left":
                Move_Left()
            elif confidence > 0.80 and label == "right":
                Move_Right()
            elif ay > 5 and direction == "S":
                Move_Forward(current_vision_speed)
            elif ay < -2 and direction == "S":
                Move_Backward(current_vision_speed)
            else:
                Stop()
        else:
            Stop()

        time.sleep(0.02)

except KeyboardInterrupt:
    pass
finally:
    Stop()
    PWM_A.stop()
    PWM_B.stop()
    vision.release()
    GPIO.cleanup()
    print("\nGPIO Cleaned up. Goodbye.")
