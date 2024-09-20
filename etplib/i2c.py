"""
Copyright (C) 2024, Jabez Winston C

Embedded Tester Protocol Library - I2C

Author  : Jabez Winston C <jabezwinston@gmail.com>
License : MIT
Date    : 19-Sep-2024

"""

import struct

class I2C:
    code = 5
    ops = {
        'info': 0,
        'init': 1,
        'scan': 2,
        'read': 3,
        'write': 4,
        'read_reg': 5,
        'write_reg': 6
    }

    info_cmds = {
        'bus_count': 0x01,
        'bus_speeds': 0x02,
        'pins': 0x03
    }

    def __init__(self, etp):
        self.etp = etp

    """
    Query I2C pin information, bus counts and supported speeds.

    """

    def get_info(self):
        i2c_info_cmd = self.code << 8 | self.ops['info']
        # Get the number of I2C buses
        cmd = self.etp.frame_packet(i2c_info_cmd, struct.pack('<B', self.info_cmds['bus_count']))
        self.etp.cmd_queue.put(cmd)
        rsp = self.etp.read_rsp()
        bus_count = struct.unpack('<B', rsp)[0]

        # Get the I2C bus speeds
        cmd = self.etp.frame_packet(i2c_info_cmd, struct.pack('<B', self.info_cmds['bus_speeds']))
        self.etp.cmd_queue.put(cmd)
        rsp = self.etp.read_rsp()
        speed_count = struct.unpack('<B', rsp[0:1])[0]
        bus_speeds = list(struct.unpack('<' + 'H'*speed_count, rsp[1:]))

        # Get the I2C pins
        cmd = self.etp.frame_packet(i2c_info_cmd, struct.pack('B', self.info_cmds['pins']))
        self.etp.cmd_queue.put(cmd)
        rsp = self.etp.read_rsp()

        # Use iter to unpack the I2C pins as a list of tuples
        pins = list(struct.iter_unpack('<BBB', rsp))

        pin_info = []

        for pin in pins:
            pin_info.append({'port': chr(pin[0]), 'pins': {'sda' : pin[1], 'scl' : pin[2]}})

        return {"bus_count": bus_count, "bus_speeds": bus_speeds, "info": pin_info}
    
    """
    Initialize I2C bus speed
    
    """
    
    def init(self, bus, speed):
        i2c_init_cmd = self.code << 8 | self.ops['init']
        cmd = self.etp.frame_packet(i2c_init_cmd, struct.pack('<BH', bus, speed))
        self.etp.cmd_queue.put(cmd)
        rsp = self.etp.read_rsp()
        return rsp
    
    """
    Scan I2C bus for devices

    """
    
    def scan(self, bus=0, start_addr=0, end_addr=0x7F):
        i2c_scan_cmd = self.code << 8 | self.ops['scan']
        cmd = self.etp.frame_packet(i2c_scan_cmd, struct.pack('<BHH', bus, start_addr, end_addr))
        self.etp.cmd_queue.put(cmd)
        rsp = self.etp.read_rsp()

        addr_count = rsp[0]
        addr_list = list(struct.unpack('<H'*addr_count, rsp[1:]))
        return addr_list
    
    """
    Read data from I2C device

    """
    
    def read(self, bus, addr, num_bytes):
        i2c_read_cmd = self.code << 8 | self.ops['read']
        cmd = self.etp.frame_packet(i2c_read_cmd, struct.pack('<BHB', bus, addr, num_bytes))
        self.etp.cmd_queue.put(cmd)
        rsp = self.etp.read_rsp()
        len = rsp[0]
        data = list(rsp[1:])
        return data
    
    """
    Write data to I2C device

    """
    
    def write(self, bus, addr, data):
        i2c_write_cmd = self.code << 8 | self.ops['write']
        length = len(data)
        cmd = self.etp.frame_packet(i2c_write_cmd, struct.pack('<BHB', bus, addr, length) + bytes(data))
        self.etp.cmd_queue.put(cmd)
        rsp = self.etp.read_rsp()
        return rsp[0]
    
    """
    Read data from I2C device register

    """
    
    def read_reg(self, bus, addr, reg, num_bytes):
        i2c_read_reg_cmd = self.code << 8 | self.ops['read_reg']
        cmd = self.etp.frame_packet(i2c_read_reg_cmd, struct.pack('<BHHB', bus, addr, reg, num_bytes))
        self.etp.cmd_queue.put(cmd)
        rsp = self.etp.read_rsp()
        len = rsp[0]
        data = list(rsp[1:])
        return data
    
    """
    Write data to I2C device register
    
    """
    
    def write_reg(self, bus, addr, reg, data):
        i2c_write_reg_cmd = self.code << 8 | self.ops['write_reg']
        length = len(data)
        cmd = self.etp.frame_packet(i2c_write_reg_cmd, struct.pack('<BHHB', bus, addr, reg, length) + bytes(data))
        self.etp.cmd_queue.put(cmd)
        rsp = self.etp.read_rsp()
        return rsp[0]

        