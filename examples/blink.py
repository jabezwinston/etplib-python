"""
Blink LED on Arduino Uno

Author  : Jabez Winston C <jabezwinston@gmail.com>

"""

import etplib
import time

etp = etplib.ETP(transport='serial', port='/dev/ttyACM0', baudrate=115200)
etp.open()
etp.reset()

pin = "_13"

etp.gpio.init({pin: {"mode": 'output', "type": 'push_pull'}})

try:
    print(f"Blinking LED on pin {pin}")
    while True:
        etp.gpio.write({pin: 1})
        time.sleep(1)
        etp.gpio.write({pin: 0})
        time.sleep(1)
except KeyboardInterrupt:
    print("\nStopping program !")

etp.close()
