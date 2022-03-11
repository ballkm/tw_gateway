"""
Kamol Chaisri
Adaline Co., LTD
ckm@adaline.co.th
ball.kamol@gmail.com
18 Mar 2020
"""


def floating_point(bin_data):
    if bin_data >> 31 == 0:
        sign = 1
    else:
        sign = -1
    # print('sign:', sign)
    exponent = bin_data >> 23 & 0b011111111
    exponent = 2 ** (exponent - 127)
    # print('exponent:', exponent)
    bin_data = bin_data & 0b00000000011111111111111111111111
    # print('mantissa:', bin(bin_data))
    shift_bit = 23
    fraction = 0.0
    while shift_bit > 0:
        fraction = fraction + float((bin_data & 0b1) * (2 ** (-1 * shift_bit)))
        bin_data = bin_data >> 1
        shift_bit = shift_bit - 1
        # print(bin(i))
    # print(fraction)
    value = float(sign * exponent) * (1 + fraction)
    # print(value)
    # mantissa =
    return value
