"""
Read DS1307 RTC using ETP library

"""

import etplib
import time


def ds1307_init(etp):
    etp.i2c.init(0, 100)
    dev_addr_list = etp.i2c.scan(0)
    print("I2C devices found : " + str(len(dev_addr_list)))
    for i in range(len(dev_addr_list)):
        print("-" + hex(dev_addr_list[i]))


def dec_to_bcd(dec):
    return ((dec // 10) << 4) + (dec % 10)


def bcd_to_dec(bcd):
    return ((bcd >> 4) * 10) + (bcd & 0x0f)


def ds1307_start_clock_if_stopped(etp):
    control_reg = etp.i2c.read_reg(0, 0x68, 0x00, 1)
    if control_reg[0] & 0x80:
        control_reg[0] &= 0x7f
        etp.i2c.write_reg(0, 0x68, 0x00, control_reg)


def ds1307_read_time(etp):
    raw_time_data = etp.i2c.read_reg(0, 0x68, 0x00, 7)

    time_str = ""

    time_str += str(bcd_to_dec(raw_time_data[4])) + "/"
    time_str += str(bcd_to_dec(raw_time_data[5])) + "/"
    time_str += str(bcd_to_dec(raw_time_data[6])) + " "

    time_str += str(bcd_to_dec(raw_time_data[2])) + ":"
    time_str += str(bcd_to_dec(raw_time_data[1])) + ":"
    time_str += str(bcd_to_dec(raw_time_data[0]))

    return time_str


def main():
    etp = etplib.ETP(transport='serial', port='/dev/ttyACM0', baudrate=115200)
    etp.open()

    etp.reset()

    print(etp.get_fw_info())
    ds1307_init(etp)

    while True:
        print(ds1307_read_time(etp))
        time.sleep(1)


if __name__ == '__main__':
    main()
