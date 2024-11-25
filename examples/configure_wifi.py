"""
Configure WiFi settings of an ETP capable device via UART

"""

import etplib
import getpass

com_port = input("Enter the COM port: ")
ssid = input("Enter the SSID: ")
password = getpass.getpass("Enter the password: ")

etp = etplib.ETP(transport='serial', port=com_port, baudrate=115200)

etp.open()
etp.reset()

etp.configure_transport(transport='wifi', ssid=ssid, password=password)

etp.close()

print("WiFi settings configured successfully !")
