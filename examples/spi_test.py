# Simple example to show SPI transfer

import etplib

etp = etplib.ETP(transport='serial', port='/dev/ttyACM0', baudrate=115200)
etp.open()
etp.reset()

# Init
etp.spi.init(0, etp.spi.MODE0, 500)

# Transfer
tx_data = [0x9F, 0x00, 0x00, 0x00]
rx_data = etp.spi.transfer(0, tx_data)
print(f"SPI RX data: {rx_data}")

etp.close()
