"""
Copyright (C) 2024, Jabez Winston C

Embedded Tester Protocol Library - SPI

Author  : Jabez Winston C <jabezwinston@gmail.com>
License : MIT
Date    : 22-Oct-2024

"""

import struct

class SPI:
    code = 6
    ops = {
        'info': 0,
        'init': 1,
        'transfer': 2
    }

    info_cmds = {
        'bus_count': 0x01,
        'bus_speeds': 0x02,
        'pins': 0x03
    }

    def __init__(self, etp):
        self.etp = etp

    MSB_FIRST = 1
    LSB_FIRST = 0

    MODE0 = 0
    MODE1 = 1
    MODE2 = 2
    MODE3 = 3

    def get_info(self) -> dict:
        """Query SPI information, bus counts and supported speeds.

        Returns:
            dict: Dictionary containing SPI bus count, supported speeds and pin information

                | Key           | Value Type | Description                                  |
                |---------------|------------|----------------------------------------------|
                | bus_count     | int        | Number of SPI buses                          |
                | bus_speeds    | list       | List of supported SPI bus speeds             |
                | info          | list       | List of SPI pins and their corresponding pins |

        """
        spi_info_cmd = self.code << 8 | self.ops['info']
        # Get the number of SPI buses
        cmd = self.etp.frame_packet(spi_info_cmd, struct.pack('<B', self.info_cmds['bus_count']))
        self.etp.cmd_queue.put(cmd)
        rsp, _ = self.etp.read_rsp()
        bus_count = struct.unpack('<B', rsp)[0]

        # Get the SPI bus speeds
        cmd = self.etp.frame_packet(spi_info_cmd, struct.pack('<B', self.info_cmds['bus_speeds']))
        self.etp.cmd_queue.put(cmd)
        rsp, _ = self.etp.read_rsp()
        speed_count = rsp[0]
        bus_speeds = list(struct.unpack('<' + 'H'*speed_count, rsp[1:]))

        # Get the SPI pins
        cmd = self.etp.frame_packet(spi_info_cmd, struct.pack('B', self.info_cmds['pins']))
        self.etp.cmd_queue.put(cmd)
        rsp, _ = self.etp.read_rsp()

        # Use iter to unpack the SPI pins as a list of tuples
        pins = list(struct.iter_unpack('<' + 'B'*5, rsp))

        pin_info = []

        for pin in pins:
            pin_info.append({'port': chr(pin[0]), 'pins': {'miso' : pin[1], 'mosi' : pin[2], 'sck' : pin[3], 'cs' : pin[4]}})

        return {"bus_count": bus_count, "bus_speeds": bus_speeds, "info": pin_info}

    
    def init(self, bus, mode, speed, bit_order = MSB_FIRST, cs=0xFF) -> int:
        """Initialize SPI bus.
        
        Args:
            bus (int): SPI bus number.
            mode (int): SPI mode (0, 1, 2, 3).
            speed (int): SPI bus speed in KHz.
            bit_order (int): Bit order (MSB_FIRST, LSB_FIRST).
            cs (int): Chip select pin number.

        Returns:
            int: Status of the operation.
        
        """
        spi_init_cmd = self.code << 8 | self.ops['init']
        cmd = self.etp.frame_packet(spi_init_cmd, struct.pack('<BHBBB', bus, speed, mode, bit_order, cs))
        self.etp.cmd_queue.put(cmd)
        _, status = self.etp.read_rsp()
        return status
    
    def transfer(self, bus: int, tx_data: list[int], cs: int=0xFF) -> list[int]:
        """Transfer data over SPI bus.
        
        Args:
            bus: SPI bus number.
            tx_data: List of bytes to be transmitted.
            cs: Chip select pin number.

        Returns:
            List of bytes received over SPI bus.

        """
        spi_transfer_cmd = self.code << 8 | self.ops['transfer']
        cmd = self.etp.frame_packet(spi_transfer_cmd, struct.pack('<BBB', bus, cs, len(tx_data)) + bytearray(tx_data))
        self.etp.cmd_queue.put(cmd)
        rsp, _ = self.etp.read_rsp()
        rx_data = list(rsp[1:])
        return rx_data
