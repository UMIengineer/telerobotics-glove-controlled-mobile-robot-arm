import network
import socket
import time
from picozero import pico_led as led, pico_temp_sensor as tempSensor
import machine
from rp2 import bootsel_button as button
import sys
import json #Use JSON for sending multiple sensor values https://softwareengineering.stackexchange.com/a/374064
from accelerometer import get_acceleration_data
from magnometer_directional_control import get_magnometer_readings
from flex_sensor_testing import flex_sensor
from potentiometer_voltage_reading import get_potentiometer_readings
from math import sqrt, atan2, pi, copysign, sin, cos

SSID = 'group_5_assignment_2' #network settings
PASSWORD = ''

STATIC_IP = ('10.42.0.178', '255.255.255.0', '10.42.0.1', '10.42.0.1') #(IP, Subnet Mask, Gateway, DNS)
PORT = 5000 #standard high number

def flashLed(onTime, offTime, count = 1):
    for i in range(0, count):
        led.on()
        time.sleep(onTime)
        led.off()
        time.sleep(offTime)
def connectStatic():#Connect to WLAN
    wlan = network.WLAN(network.STA_IF)
    wlan.disconnect()
    wlan.active(True)
    wlan.ifconfig(STATIC_IP)
    wlan.connect(SSID, PASSWORD)
    while wlan.isconnected() == False: #Waiting for connection
        if button() == 1: #Break connection button
            print('connection search interrupted: exiting')
            sys.exit()
        print('connecting to ', SSID, '...', sep = '')
        flashLed(0.1, 0.1)
    print('Connected! Static IP assigned:', wlan.ifconfig()[0]) #Print only local IP
    flashLed(0.3, 0.1, 3)
    return wlan.ifconfig()[0]

def openSocket(ip): #Create the socket using TCP (standard)
    address = (ip, PORT)
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) #rebind to port immediately https://github.com/orgs/micropython/discussions/10438
    s.bind(address)
    s.listen(1)
    print('Listening on ', ip, ':', PORT, '...', sep='')
    return s

ip = connectStatic() #Connect to 4B hotspot WLAN
serverSocket = openSocket(ip)

while True: #https://pythonprogramming.net/sockets-tutorial-python-3/
    try:
        clientSocket, clientAddress = serverSocket.accept()
        print(f'Connection from {clientAddress}')

        # Keep connection continuously open and send data as it comes in
        while True:
            raw_pot_1, raw_pot_2 = get_potentiometer_readings()
            potData= {'Pot 1 Resistance': raw_pot_1, 'Pot 2 Resistance': raw_pot_2}

            flex_sensor_voltage = (flex_sensor.read_u16() * (3.3 / 65535))
            flexData= {'Flex Sensor Voltage': flex_sensor_voltage}
            accel = get_acceleration_data()
            ax, ay, az = accel[0], accel[1], accel[2]
            accelData = {'x': ax, 'y': ay, 'z': az}
            azimuth, heading = get_magnometer_readings(ax, ay, az)
            magData = {'Degrees': azimuth, 'Direction': heading}

            dataPacket = {
                'accelerometer': accelData,
                'mag': magData,
                'flex': flexData,
                'pot': potData
            }

            jsonData = json.dumps(dataPacket) + '\n' # Add newline as a delimiter for the client to read full packets
            clientSocket.send(jsonData.encode('utf-8'))

    except Exception as e:
        print(f'Error: {e}')
        clientSocket.close()
        time.sleep(0.5)