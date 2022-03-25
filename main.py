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


def read_holding(slave_address):
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

    time.sleep(0.5)
    # while True:
    timecheck = time.perf_counter()
    for i in range(0, len(data_request_byte)):
        ser.write(data_request_byte[i])

    data_responce = []
    i = 1

    timeout = time.perf_counter()
    status_timeout = 0
    while (ser.inWaiting()) == 0:  # Or: while ser.inWaiting():
        if (time.perf_counter() - timeout) > 1:
            print('RS-485 Timeout')
            status_timeout = 1
            break
    if status_timeout == 1:
        return 0
    countLoop = 0
    quantity = 0
    quantity_breaK = 2
    # while True:
    #     print(ser.read())
    #     print(quantity)
    #     quantity = quantity + 1
    #     time.sleep(.1)
    data_responce_str_hex = []
    data_responce_byte = []
    if status_timeout == 0:
        while quantity <= quantity_breaK:
            while ser.inWaiting():  # Or: while ser.inWaiting():
                data_responce.append(ser.read())
                # dat_ser = ser.read()
                # data_responce.append((int.from_bytes(dat_ser, byteorder='big')))
                data_responce_str_hex.append(hex(int.from_bytes(data_responce[countLoop], byteorder='big')))
                data_responce_byte.append((int.from_bytes(data_responce[countLoop], byteorder='big')))
                if quantity == 2:
                    quantity_breaK = (int.from_bytes(data_responce[quantity], byteorder='big')) + 4
                quantity = quantity + 1
                countLoop = countLoop + 1

    # print(quantity_breaK)
    # print(countLoop)
    # print(len(data_responce))
    # print(data_responce)
    # print(data_responce_str_hex)
    # print(data_responce_byte)
    res_lowByte = data_responce_byte.pop()
    res_highByte = data_responce_byte.pop()
    data_responce.pop()
    data_responce.pop()
    data_responce.pop(0)
    data_responce.pop(0)
    data_responce.pop(0)
    # print(data_responce)
    # print(hex(res_lowByte))
    # print(hex(res_highByte))

    crc = compute_crc.modbus_rtu_crc(data_responce_byte)
    highByte = crc & 0x00FF
    lowByte = crc >> 8
    # print(hex(highByte))
    # print(hex(lowByte))

    if (res_lowByte == lowByte) and (res_highByte == highByte):
        print("CRC Corrected")
        # print(int.from_bytes(data_responce[27], byteorder='big'))
        # Request QR
        strmac_id = ''
        for i in range(2, 12):
            strmac_id = strmac_id + chr(int.from_bytes(data_responce[i], byteorder='big'))

        if int.from_bytes(data_responce[27], byteorder='big') == 0x01:
            print("request_qr")
            # strMac_id = ''

            print(strmac_id)
            hmi_amount = int.from_bytes(data_responce[26], byteorder='big')
            hmi_pg = int.from_bytes(data_responce[22], byteorder='big')
            print(hmi_amount)
            print(hmi_pg)
            request_qr(slave_address, hmi_amount, strmac_id, hmi_pg)

        machine_type = int.from_bytes(data_responce[1], byteorder='big')
        machine_status = int.from_bytes(data_responce[14], byteorder='big')
        machine_actionby = int.from_bytes(data_responce[15], byteorder='big')
        time_minutes = int.from_bytes(data_responce[16], byteorder='big')
        time_seconds = int.from_bytes(data_responce[17], byteorder='big')
        current_coin = int.from_bytes(data_responce[18], byteorder='big')
        total_current_coin = int.from_bytes(data_responce[19], byteorder='big')
        current_running_program_number = int.from_bytes(data_responce[20], byteorder='big')
        wifi_connect_success = int.from_bytes(data_responce[21], byteorder='big')

        return [slave_address, strmac_id, machine_type, machine_status, machine_actionby, time_minutes, time_seconds,
                current_coin, \
                total_current_coin, current_running_program_number, wifi_connect_success]


def request_qr(slave_address, amount, strMac_id, pg_mode):
    payload = {'action': 'scb_test',
               'customer_id': '1',
               'amount': str(amount),
               'macaddr': str(strMac_id),
               'mode': str(pg_mode)
               }
    # payload = 'action=scb_test' + '&customer_id=1' + '&amount=' + str(amount) + '&macaddr=' + str(strMac_id)
    print(payload)
    # headers = {"Content-Type: application/x-www-form-urlencoded"}
    # headers = {"content-type": "application/x-www-form-urlencoded"}
    # res_data = requests.post(url, data=payload, headers=headers)
    res_data = requests.post(url_qr_payment, data=payload, timeout=5)
    # res_data = requests.post(url+payload)
    # print(res_data.text)
    str_res_data = res_data.text
    # print(type(str_res_data))
    json_res_data = json.loads(str_res_data)
    # print(json_res_data)
    qr_string = json_res_data['qrcode']
    print(qr_string)
    write_qr(slave_address, qr_string)


def write_control(slave_address, select_program_number, program_option1, program_option2, program_option3,
                  input_number_of_coin, put_start, server_action_wash):
    print('Control Start')
    time.sleep(0.5)
    # write_control(machine_data[0], program_mode, option_wash, 0x00, 0x00, action_price, 0x00, server_action)
    # slave_address = 0x01
    function = 0x10
    start_address_high = 0x00
    start_address_low = 0x64
    number_point_high = 0x00
    number_point_low = 0x07
    byte_count = 0x07
    # select_program_number = 0x06
    # program_option1 = 0x00
    # program_option2 = 0x00
    # program_option3 = 0x00
    # input_number_of_coin = 0x32
    # put_start = 0x00
    # server_action_wash = 0x00

    # data_request = []
    # data_request_byte = []
    data_responce = []

    # data_request = [slave_address, function, start_address_high, start_address_low, number_point_high, number_point_low]
    data_request = [slave_address, function, start_address_high, start_address_low, number_point_high, number_point_low,
                    byte_count, select_program_number, program_option1, program_option2, program_option3,
                    input_number_of_coin,
                    put_start, server_action_wash]
    crc = compute_crc.modbus_rtu_crc(data_request)
    highByte = crc & 0x00FF
    lowByte = crc >> 8
    print(hex(highByte))
    print(hex(lowByte))
    data_request.append(highByte)
    data_request.append(lowByte)
    # print(hex(data_request[6]))

    data_request_byte = []
    for i in range(0, len(data_request)):
        data_request_byte.append((data_request[i]).to_bytes(1, byteorder="big"))
    print(data_request_byte)

    for i in range(0, len(data_request_byte)):
        ser.write(data_request_byte[i])
    time.sleep(0.5)


def write_qr(slave_address, qr_string):
    time.sleep(0.5)
    # slave_address = 0x01
    function = 0x10
    start_address_high = 0x00
    start_address_low = 0x77
    number_point_high = 0x00
    number_point_low = 0x00
    byte_count = 0x00

    qr_status_write = 0x01
    data_block_str = list(qr_string)
    data_block_int = []
    data_block_int.append(qr_status_write)
    for i in range(0, len(data_block_str)):
        data_block_int.append(ord(data_block_str[i]))
    # data_block_int.insert(0, qr_status_write)
    byte_count = len(data_block_int)

    print(hex(data_block_int[0]))
    print(len(data_block_int))
    # data_request = []
    # data_request_byte = []
    data_responce = []

    # data_request = [slave_address, function, start_address_high, start_address_low, number_point_high, number_point_low]
    data_request = [slave_address, function, start_address_high, start_address_low, number_point_high, number_point_low,
                    byte_count]
    data_request.extend(data_block_int)
    crc = compute_crc.modbus_rtu_crc(data_request)
    highByte = crc & 0x00FF
    lowByte = crc >> 8
    print(hex(highByte))
    print(hex(lowByte))
    data_request.append(highByte)
    data_request.append(lowByte)
    # print(hex(data_request[6]))

    data_request_byte = []
    for i in range(0, len(data_request)):
        data_request_byte.append((data_request[i]).to_bytes(1, byteorder="big"))
    print(data_request_byte)
    #
    for i in range(0, len(data_request_byte)):
        ser.write(data_request_byte[i])
    time.sleep(0.5)


def sendDataToServer(machine_data):
    # print(type(machine_data))
    strJson = ''
    machine_no = str(machine_data[1])
    machine_type = machine_data[2]
    machine_status = machine_data[3]
    machine_actionby = ''
    if machine_data[4] == 0:
        machine_actionby = 'NOP'
    if machine_data[4] == 1:
        machine_actionby = 'coin'
    if machine_data[4] == 2:
        machine_actionby = 'mobile'
    machine_time_minutes = machine_data[5]
    machine_time_seconds = machine_data[6]

    machine_update = 'machine_type=' + str(machine_type) + '&no=' + machine_no
    machine_update = machine_update + '&status=' + str(machine_status)
    machine_update = machine_update + '&actionby=' + machine_actionby
    machine_update = machine_update + '&time_minutes=' + str(machine_time_minutes)
    machine_update = machine_update + '&time_seconds=' + str(machine_time_seconds)
    url = host + url_api + machine_update
    print(machine_update)
    print('-----server-----')
    try:
        r = requests.get(url, timeout=5)
        # print(r.text)
        # print(r.status_code)
        strJson = r.text
    except requests.exceptions.ConnectionError as err:
        print(err)
    except requests.exceptions.HTTPError as err:
        print(err)
    except requests.exceptions.Timeout as err:
        print(err)
    except requests.exceptions.TooManyRedirects as err:
        print(err)
    except requests.exceptions.RequestException as err:
        print(err)
        pass
    print('-----end server-----')

    json_error = 0

    try:
        strJsonData = json.loads(strJson)
        # json_error = 0
    except ValueError as err:
        json_error = 1
        print('json:', err)
        pass
    if json_error == 0:
        print(strJsonData)
        print('action:', strJsonData['action'])
        print('action_price:', strJsonData['action_price'])
        print('programs_mode:', strJsonData['programs_mode'])
        print('option_wash:', strJsonData['option_wash'])
        server_action = int(strJsonData['action'])
        action_price = int(strJsonData['action_price'])
        program_mode = int(strJsonData['programs_mode'])
        option_wash = int(strJsonData['option_wash'])
        if server_action == 1:
            write_control(machine_data[0], program_mode, option_wash, 0x00, 0x00, action_price, 0x00, server_action)


def send_coin(machine_data):
    machine_no = machine_data[1]
    machine_type = machine_data[2]
    machine_coin = machine_data[7]
    f = open("coin_log.txt", "a")

    print('/////// coin //////')
    machine_update_coin = 'machine_mode=' + str(machine_type) + '&no=' + str(machine_no)
    machine_update_coin = machine_update_coin + '&status=' + str(3)
    machine_update_coin = machine_update_coin + '&coin_acceptor=' + str(machine_coin)
    # machine_update_coin = machine_update_coin + '&time_minutes=' + str(time_minutes)
    # machine_update_coin = machine_update_coin + '&time_seconds=' + str(time_seconds)
    url_coin = host + url_api + machine_update_coin
    print(url_coin)

    date_time_coin = datetime.datetime.now()
    strDatetime = str(date_time_coin)
    f.write(strDatetime + ' ' + str(machine_coin) + '\n')

    print('-----server-----')
    try:
        # r = requests.get(url_coin)
        r = requests.get(url_coin, timeout=5)
    except requests.exceptions.ConnectionError as err:
        date_time_coin = datetime.datetime.now()
        strDatetime = str(date_time_coin)
        f.write(strDatetime + ' ' + str(err) + '\n')
        print(err)
    except requests.exceptions.HTTPError as err:
        date_time_coin = datetime.datetime.now()
        strDatetime = str(date_time_coin)
        f.write(strDatetime + ' ' + str(err) + '\n')
        print(err)
    except requests.exceptions.Timeout as err:
        date_time_coin = datetime.datetime.now()
        strDatetime = str(date_time_coin)
        f.write(strDatetime + ' ' + str(err) + '\n')
        print(err)
    except requests.exceptions.TooManyRedirects as err:
        date_time_coin = datetime.datetime.now()
        strDatetime = str(date_time_coin)
        f.write(strDatetime + ' ' + str(err) + '\n')
        print(err)
    except requests.exceptions.RequestException as err:
        date_time_coin = datetime.datetime.now()
        strDatetime = str(date_time_coin)
        f.write(strDatetime + ' ' + str(err) + '\n')
        print(err)
    print('-----end server-----')
    f.close()
    print(r.text)
    status_code = r.status_code
    print(status_code)
    strJson = r.text
    print('/////// End coin //////')
    if status_code == 200:
        reset_current_coin(machine_data[0])


def reset_current_coin(slave_address):
    time.sleep(0.5)
    # slave_address = 0x01
    function = 0x10
    start_address_high = 0x00
    start_address_low = 0x12
    number_point_high = 0x00
    number_point_low = 0x02
    byte_count = 0x02
    data_block18 = 0x00
    data_block19 = 0x00
    data_request = [slave_address, function, start_address_high, start_address_low, number_point_high, number_point_low,
                    byte_count, data_block18, data_block19]
    crc = compute_crc.modbus_rtu_crc(data_request)
    highByte = crc & 0x00FF
    lowByte = crc >> 8
    print(hex(highByte))
    print(hex(lowByte))
    data_request.append(highByte)
    data_request.append(lowByte)
    # print(hex(data_request[6]))

    data_request_byte = []
    for i in range(0, len(data_request)):
        data_request_byte.append((data_request[i]).to_bytes(1, byteorder="big"))
    print(data_request_byte)

    for i in range(0, len(data_request_byte)):
        ser.write(data_request_byte[i])
    time.sleep(0.5)


ser = serial.Serial(port=usbport, baudrate=9600, bytesize=8, parity='N', stopbits=1, timeout=2)
# ser = serial.Serial(port='/dev/ttyUSB0', baudrate=9600, bytesize=8, parity='N', stopbits=1, timeout=1)
# ser = serial.Serial(port='/dev/cu.usbserial-14130', baudrate=9600, bytesize=8, parity='N', stopbits=1, timeout=1)
# ser = serial.Serial(port='/dev/ttyUSB1', baudrate=9600, bytesize=8, parity='N', stopbits=1, timeout=1)
print(ser.name)
print(ser.is_open)

# read_holding()
'''
print('Check Device on Network 1-50')
bus_id_list = []
for i in range(0x00, 0x32):
    print(i)
    for j in range(0, 5):
        if read_holding(i) != 0:
            print('bus ID:' + str(i) + ' Available')
            bus_id_list.append(i)
            break
        else:
            print('bus ID:' + str(i) + ' Not Found')

while True:
    for i in bus_id_list:
        machine_data = read_holding(i)
        if machine_data != 0:
            sendDataToServer(machine_data)
            if machine_data[7] > 0:
                send_coin(machine_data)
            print(machine_data)
    # time.sleep(1)
    '''

while True:
    machine_data = read_holding(0x03)
    if machine_data != 0:
        sendDataToServer(machine_data)
        if machine_data[7] > 0:
            send_coin(machine_data)
        print(machine_data)
    time.sleep(1)


# slave_address = 0x01
# function = 0x03
# start_address_high = 0x00
# start_address_low = 0x00
# number_point_high = 0x00
# number_point_low = 0x0F


# time.sleep(1)
# while True:
#     timecheck = time.perf_counter()
#     for i in range(0, len(data_request_byte)):
#         ser.write(data_request_byte[i])
#     time.sleep(1)
'''
slave_address = 0x01
function = 0x10
start_address_high = 0x00
start_address_low = 0x77
number_point_high = 0x00
number_point_low = 0x00
byte_count = 0x00

qr_string = '00020101021230710016A000000677010112011501055520624410102040001032000010040IW93DD5DD4015303764540400405802TH62100706TDW00163043A3D'
qr_status_write = 0x01
data_block_str = list(qr_string)
data_block_int = []
data_block_int.append(qr_status_write)
for i in range(0, len(data_block_str)):
    data_block_int.append(ord(data_block_str[i]))
# data_block_int.insert(0, qr_status_write)
byte_count = len(data_block_int)

print(hex(data_block_int[0]))
print(len(data_block_int))
# data_request = []
# data_request_byte = []
data_responce = []

# data_request = [slave_address, function, start_address_high, start_address_low, number_point_high, number_point_low]
data_request = [slave_address, function, start_address_high, start_address_low, number_point_high, number_point_low,
                byte_count]
data_request.extend(data_block_int)
crc = compute_crc.modbus_rtu_crc(data_request)
highByte = crc & 0x00FF
lowByte = crc >> 8
print(hex(highByte))
print(hex(lowByte))
data_request.append(highByte)
data_request.append(lowByte)
# print(hex(data_request[6]))

data_request_byte = []
for i in range(0, len(data_request)):
    data_request_byte.append((data_request[i]).to_bytes(1, byteorder="big"))
print(data_request_byte)
#
for i in range(0, len(data_request_byte)):
    ser.write(data_request_byte[i])

time.sleep(1)
'''
