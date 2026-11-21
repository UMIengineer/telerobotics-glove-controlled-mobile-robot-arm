import pigpio
import math

cam_servo_1 = 9
cam_servo_2 = 10

# Start them in the middle position (90 degrees)
cam_initial_1 = 1500
cam_initial_2 = 1500

KEYBOARD_STEP = 50

POT1_SERVO_GPIO = 5
POT2_SERVO_GPIO = 6
FLEX_SENSOR_SERVO_GPIO = 8
ACCEL_SERVO_GPIO = 7

# Potentiometer 1 servo pulse width limits
POT1_MIN_PW = 500
POT1_MAX_PW = 2500

# Potentiometer 2 servo pulse width limits
POT2_MIN_PW = 25000
POT2_MAX_PW = 50000

# Flex sensor servo pulse width limits
FLEX_SENSOR_MIN_PW = 500
FLEX_SENSOR_MAX_PW = 2500

# Accelerometer servo pulse width limits
ACCEL_MIN_PW = 500
ACCEL_MAX_PW = 2500

# Filtering parameters for potentiometer readings
pot1_smooth = None
pot2_smooth = None
last_pw1 = None
last_pw2 = None
ALPHA = 0.1
DEADBAND = 100

# Potentiometer 1 resistance thresholds
POT1_LOW = 45000
POT1_HIGH = 65000

# Potentiometer 2 resistance thresholds
POT2_LOW = 40000
POT2_HIGH = 50000

# Flex sensor voltage thresholds
FLEX_LOW = 1.3
FLEX_HIGH = 2.1

# Accelerometer thresholds
ACCEL_LOW = -10
ACCEL_HIGH = 10

pi = pigpio.pi()
if not pi.connected:
    print("Could not connect to pigpiod. Did you run 'sudo pigpiod'?")
    exit()

def potentiometer_servo_control(pot1, pot2):
    global pot1_smooth, pot2_smooth, last_pw1, last_pw2
    if pot1 is not None and pot2 is not None:
        pot1_smooth = pot1 if pot1_smooth is None else ALPHA * pot1 + (1 - ALPHA) * pot1_smooth
        pot2_smooth = pot2 if pot2_smooth is None else ALPHA * pot2 + (1 - ALPHA) * pot2_smooth

        pot1, pot2 = pot1_smooth, pot2_smooth

        target_pw_1 = ((POT1_HIGH - pot1) * (POT1_MAX_PW - POT1_MIN_PW) / (POT1_HIGH - POT1_LOW) + POT1_MIN_PW)
        target_pw_2 = ((pot2 - POT2_LOW) * (POT2_MAX_PW - POT2_MIN_PW) / (POT2_HIGH - POT2_LOW) + POT2_MIN_PW)
        safe_target_1 = max(POT1_MIN_PW, min(POT1_MAX_PW, int(target_pw_1)))
        safe_target_2 = max(POT2_MIN_PW, min(POT2_MAX_PW, int(target_pw_2)))

                # Only update the servo if the change is significant to reduce jitter
        if last_pw1 is None or abs(safe_target_1 - last_pw1) > DEADBAND:
            pi.set_servo_pulsewidth(POT1_SERVO_GPIO, safe_target_1)
            last_pw1 = safe_target_1
        # Only update the servo if the change is significant to reduce jitter
        if last_pw2 is None or abs(safe_target_2 - last_pw2) > DEADBAND:
            pi.set_servo_pulsewidth(POT2_SERVO_GPIO, safe_target_2)
            last_pw2 = safe_target_2
        print(f"\rPW1: {safe_target_1} | PW2: {safe_target_2}", end="")

        deg_2 = (safe_target_1-500) / 11.1
        deg_3 = (safe_target_2-25000) / 138.9

        angle_1 = math.radians(45)
        rad_2 = math.radians(deg_2)
        rad_3 = math.radians(deg_3)

        yke = (5 * math.sin(angle_1)) + (9.5 * math.sin(angle_1 + rad_2)) + (14 * math.sin(angle_1 + rad_2 + rad_3))
        if yke < 1.0:
            if last_pw1 is None or abs(safe_target_1 - last_pw1) > DEADBAND:
                pi.set_servo_pulsewidth(POT1_SERVO_GPIO, safe_target_1)
                last_pw1 = safe_target_1
            if last_pw2 is None or abs(safe_target_2 - last_pw2) > DEADBAND:
                pi.set_servo_pulsewidth(POT2_SERVO_GPIO, safe_target_2)
                last_pw2 = safe_target_2
            print(f"\rHeight: {yke:.2f} cm | OK", end="")
            return safe_target_1, safe_target_2
        else:
            print(f"\r!!! LIMIT ACTIVE !!! Blocked move to {yke:.2f} cm", end="")
            fallback_1 = last_pw1 if last_pw1 else POT1_MIN_PW
            fallback_2 = last_pw2 if last_pw2 else POT2_MIN_PW
            return fallback_1, fallback_2

    return 0, 0

def flexsensor_servo_control(flex_voltage):
    def flex_sensor_set_servo_pw(pw):
        pw = max(FLEX_SENSOR_MIN_PW, min(FLEX_SENSOR_MAX_PW, int(pw)))
        pi.set_servo_pulsewidth(FLEX_SENSOR_SERVO_GPIO, pw)
        return pw
    if flex_voltage is not None:
        new_pw = (FLEX_HIGH - flex_voltage) * (FLEX_SENSOR_MAX_PW - FLEX_SENSOR_MIN_PW) / (FLEX_HIGH - FLEX_LOW) + FLEX_SENSOR_MIN_PW
        actual_pw = flex_sensor_set_servo_pw(new_pw)
    return

def accelerometer_servo_control(ax):
    def accel_set_servo_pw(accel_pw):
        accel_pw = max(ACCEL_MIN_PW, min(ACCEL_MAX_PW, int(accel_pw)))
        pi.set_servo_pulsewidth(ACCEL_SERVO_GPIO, accel_pw)
        return accel_pw
    if ax is not None:
        new_pw = (ACCEL_HIGH - ax) * (ACCEL_MAX_PW - ACCEL_MIN_PW) / (ACCEL_HIGH - ACCEL_LOW) + ACCEL_MIN_PW
        actual_pw = accel_set_servo_pw(new_pw)

    return

def keyboard_servo_control(i_pressed, k_pressed, j_pressed, l_pressed):
    global cam_initial_1, cam_initial_2
    # Servo 1 (I and K)
    if i_pressed:
        cam_initial_1 = min(2500, cam_initial_1 + KEYBOARD_STEP)
    elif k_pressed:
        cam_initial_1 = max(500, cam_initial_1 - KEYBOARD_STEP)

    # Servo 2 (J and L)
    if j_pressed:
        cam_initial_2 = min(2500, cam_initial_2 + KEYBOARD_STEP)
    elif l_pressed:
        cam_initial_2 = max(500, cam_initial_2 - KEYBOARD_STEP)

    pi.set_servo_pulsewidth(cam_servo_1, cam_initial_1)
    pi.set_servo_pulsewidth(cam_servo_2, cam_initial_2)

    return cam_initial_1, cam_initial_2