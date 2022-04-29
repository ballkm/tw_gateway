"""
Compute the MODBUS RTU CRC
Kamol Chaisri
Adaline Co., LTD
ckm@adaline.co.th
ball.kamol@gmail.com
18 Mar 2020
"""


def modbus_rtu_crc(datalist):
    # datalist = [0x01, 0x04, 0x00, 0x00, 0x00, 0x02]
    #
    # print(datalist)

    crc = 0xFFFF

    for pos in range(0, len(datalist)):
        crc ^= datalist[pos]
        # print(hex(crc))
        for i in range(8, 0, -1):
            # print(i)
            if (crc & 0x0001) is not 0:
                crc >>= 1
                crc ^= 0xA001
            else:
                crc >>= 1

    # print(hex(crc))
    return crc
