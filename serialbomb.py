import json
import os
import sys
import time
import serial
import struct
import IEEE754
import compute_crc
import requests
import datetime
from local_settings import *

json_error = 0

ser = serial.Serial(port=usbport, baudrate=9600, bytesize=8, parity='N', stopbits=1, timeout=2)
# ser = serial.Serial(port='/dev/ttyUSB0', baudrate=9600, bytesize=8, parity='N', stopbits=1, timeout=1)
# ser = serial.Serial(port='/dev/cu.usbserial-AD0JZI5B', baudrate=9600, bytesize=8, parity='N', stopbits=1, timeout=1)
# ser = serial.Serial(port='/dev/ttyUSB1', baudrate=9600, bytesize=8, parity='N', stopbits=1, timeout=1)
print(ser.name)
print(ser.is_open)

print('Start Bomb')

while True:
    ser.write(0xff)