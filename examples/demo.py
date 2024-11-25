"""
Embedded Tester Protocol Demo using Arduino Uno

Author  : Jabez Winston C <jabezwinston@gmail.com>

"""

import etplib
import time


def main():
    print(f"ETP Library Version: {etplib.__version__}")

    etp = etplib.ETP(transport='serial', port='/dev/ttyACM0', baudrate=115200)
    etp.open()

    etp.reset()
    print(f"ETP Firmware Info : {etp.get_fw_info()}]\n")

    supported_ops = etp.get_supported_ops()
    print("Supported Operations:")
    print([hex(op) for op in supported_ops])

    # GPIO
    print(f"GPIO Info: {etp.gpio.get_info()}\n")
    etp.gpio.init({
        'PB5': {"mode": 'output', "type": 'push_pull'},
        'PB4': {"mode": 'input', "type": 'pull_up'},
        'PB3': {"mode": 'input', "type": 'pull_down'}
    })

    print(f"GPIO read : {etp.gpio.read(['PB4', 'PB3'])}\n")

    # PWM
    # 3, 5, 6, 9, 10, 11
    print(f"PWM Info: {etp.pwm.get_info()}\n")
    etp.pwm.init({"_3": True, "_5": True, "_6": True, "_9": True, "_10": True, "_11": True})
    etp.pwm.ctrl("_3", duty_cycle=22) # 22%
    etp.pwm.ctrl("_5", duty_cycle=47) # 47%
    etp.pwm.ctrl("_6", duty_cycle=68) # 68%

    # I2C
    print(f"I2C Info: {etp.i2c.get_info()}\n")
    etp.i2c.init(0, 100)  # Bus 0, 100 KHz
    print(f"I2C Scan: {etp.i2c.scan(0)}\n")

    # ADC
    print(f"ADC Info: {etp.adc.get_info()}\n")
    etp.adc.init({"a0": True, "a1": True, "a2": True, "a3": True})

    for i in range(10):
        print("(A0) ADC sample " + str(i) + " :", etp.adc.read("a0"))
        time.sleep(0.5)

    # SPI
    print(f"SPI Info: {etp.spi.get_info()}\n")
    etp.spi.init(0, etp.spi.MODE0, 500)  # Bus 0, Mode 0, 500 KHz
    rx_data = etp.spi.transfer(0, [0x01, 0x02, 0x03, 0x04])
    print("SPI Transfer : ", rx_data)

    # Blink LED - 10 times
    for i in range(10):
        etp.gpio.write({"PB5": 1})
        time.sleep(0.2)
        etp.gpio.write({"PB5": 0})
        time.sleep(0.2)

    etp.close()


if __name__ == '__main__':
    main()
