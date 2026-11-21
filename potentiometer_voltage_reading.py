from machine import ADC, Pin
import time

def get_potentiometer_readings():
    pot1 = ADC(Pin(27))
    pot2 = ADC(Pin(26))

    while True:
        raw_pot_1 = pot1.read_u16()
        raw_pot_2 = pot2.read_u16()

        time.sleep(0.5)
        return raw_pot_1, raw_pot_2