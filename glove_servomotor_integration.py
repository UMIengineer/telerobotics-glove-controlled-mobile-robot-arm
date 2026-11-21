import RPi.GPIO as GPIO
import time
import threading
from pynput import keyboard
from client_get_pico_data import pico_client
from glove_servomotor_integration import potentiometer_servo_control, flexsensor_servo_control, accelerometer_servo_control, keyboard_servo_control

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

# Motors A and B
ENA, ENB = 13, 20
IN1, IN2, IN3, IN4 = 19, 16, 21, 26
trig_pin, echo_pin= 17, 4

# Set all motor pins as outputs and initialize to LOW
pins = [ENA, ENB, IN1, IN2, IN3, IN4]
for pin in pins:
    GPIO.setup(pin, GPIO.OUT, initial=GPIO.LOW)

# Ultrasonic Sensor Pins
GPIO.setup(trig_pin, GPIO.OUT)
GPIO.setup(echo_pin, GPIO.IN)

# PWM Initialization
Speed = 50
PWM_A = GPIO.PWM(ENA, 1000)
PWM_B = GPIO.PWM(ENB, 1000)
PWM_A.start(0)
PWM_B.start(0)

# Function to set motor speed (0-100)
def Motor_Speed(val):
    PWM_A.ChangeDutyCycle(val)
    PWM_B.ChangeDutyCycle(val)

# --- Movement Functions ---
def Move_Forward():
    GPIO.output([IN1, IN4], True)
    GPIO.output([IN2, IN3], False)
    Motor_Speed(Speed)

def Move_Backward():
    GPIO.output([IN1, IN4], False)
    GPIO.output([IN2, IN3], True)
    Motor_Speed(Speed)

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

latest_data = {}
data_lock = threading.Lock()

def network_loop():
    pico = pico_client()
    while True:
        data = pico.getPicoData()
        if data:
            with data_lock:
                latest_data.update(data)

network_thread = threading.Thread(target=network_loop, daemon=True)
network_thread.start()

def servo_loop():
    while True:
        with data_lock:
            data = dict(latest_data)

        if data:
            ax = data.get('accelerometer', {}).get('x', 0)
            ay = data.get('accelerometer', {}).get('y', 0)
            flex_voltage = data.get('flex', {}).get('Flex Sensor Voltage', 0)
            pot1 = data.get('pot', {}).get('Pot 1 Resistance', 0)
            pot2 = data.get('pot', {}).get('Pot 2 Resistance', 0)
            direction = data.get('mag', {}).get('Direction', "")
            degrees = data.get('mag', {}).get('Degrees', 0)

            accelerometer_servo_control(ax)
            flexsensor_servo_control(flex_voltage)
            potentiometer_servo_control(pot1, pot2)
            keyboard_servo_control(key_state['i'], key_state['k'], key_state['j'], key_state['l'])
            print(f"\rAX: {ax:>6.2f} | AY: {ay:>6.2f} | Flex: {flex_voltage:.2f}V | Mag: {degrees:.1f}° {direction:<3}", end="")

        time.sleep(0.02)

servo_thread = threading.Thread(target=servo_loop, daemon=True)
servo_thread.start()

key_state = {'i': False, 'k': False, 'j': False, 'l': False}

def on_press(key):
    try:
        if key.char in key_state:
            key_state[key.char] = True
    except AttributeError:
        pass

def on_release(key):
    if key == keyboard.Key.esc:
        return False
    try:
        if key.char in key_state:
            key_state[key.char] = False
    except AttributeError:
        pass

listener = keyboard.Listener(on_press=on_press, on_release=on_release)
listener.start()
def ultrasonic_distance_limiter():
    GPIO.setmode(GPIO.BCM)

    trig_pin, echo_pin= 17, 4

    GPIO.setup(trig_pin, GPIO.OUT)
    GPIO.setup(echo_pin, GPIO.IN)

    value = sensor.Measurement(trig_pin, echo_pin)

    distance = value.raw_distance()

    return distance

listener = keyboard.Listener(on_release=on_release)
listener.start()

print("--- System Active ---")
print("Tilt Pico to Drive | Press ESC to Quit")

try:
    while listener.running:
        with data_lock:
            data = dict(latest_data)

        if data:
            ay = data.get('accelerometer', {}).get('y', 0)
            direction = data.get('mag', {}).get('Direction', "")
            distance = 999.0
                
            if ay > 5 and direction == "S" and distance > 30.0:
                Move_Forward()
            elif ay < -5 and direction == "S":
                Move_Backward()
            elif ay > 1 and direction == "W" and distance > 15.0:
                Move_Right()
            elif ay < -1 and direction == "E" and distance > 15.0:
                Move_Left()
            else:
                Stop()
        else:
            Stop()

        time.sleep(0.02)


finally:
    Stop()
    PWM_A.stop()
    PWM_B.stop()
    GPIO.cleanup()
    print("\nGPIO Cleaned up. Goodbye.")