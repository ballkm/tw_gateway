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

# ser = serial.Serial(port=usbport, baudrate=9600, bytesize=8, parity='N', stopbits=1, timeout=2)
ser = serial.Serial(port='/dev/ttyUSB0', baudrate=9600, bytesize=8, parity='N', stopbits=1, timeout=1)
# ser = serial.Serial(port='/dev/cu.usbserial-14130', baudrate=9600, bytesize=8, parity='N', stopbits=1, timeout=1)
# ser = serial.Serial(port='COM9', baudrate=9600, bytesize=8, parity='N', stopbits=1, timeout=1)
print(ser.name)
print(ser.is_open)

slave_address = 0x01
function = 0x03
start_address_high = 0x00
start_address_low = 0x00
number_point_high = 0x00
number_point_low = 0x0F

# = 0x01
function = 0x03
start_address_high = 0x00
start_address_low = 0x00
number_point_high = 0x00
number_point_low = 0x32

data_request = [slave_address, function, start_address_high, start_address_low, number_point_high, number_point_low]
crc = compute_crc.modbus_rtu_crc(data_request)
highByte = crc & 0x00FF
lowByte = crc >> 8
# print(hex(highByte))
# print(hex(lowByte))
data_request.append(highByte)
data_request.append(lowByte)
# print(hex(data_request[6]))

data_request_byte = []
for i in range(0, len(data_request)):
    data_request_byte.append((data_request[i]).to_bytes(1, byteorder="big"))

# print(data_request_byte)

# time.sleep(0.5)
# # while True:
# timecheck = time.perf_counter()
# for i in range(0, len(data_request_byte)):
#     ser.write(data_request_byte[i])

time.sleep(1)
while True:
    timecheck = time.perf_counter()
    for i in range(0, len(data_request_byte)):
        ser.write(data_request_byte[i])
    while ser.inWaiting():  # Or: while ser.inWaiting():
        print(ser.read())
    time.sleep(1)
