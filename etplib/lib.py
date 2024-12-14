"""
Copyright (C) 2024, Jabez Winston C

Embedded Tester Protocol Library

Author  : Jabez Winston C <jabezwinston@gmail.com>
License : MIT
Date    : 13-Sep-2024

"""

import serial
import socket
import struct
import queue
import threading
import time

from .gpio import GPIO
from .adc import ADC
from .i2c import I2C
from .pwm import PWM
from .spi import SPI

class ETP:
    """Embedded Tester Protocol Library"""
    general_ops = {
        'fw_info': 0,
        'reset': 1,
        'get_supported_ops': 2,
        'configure_transport': 3,
        'debug_print': 0xdb,
    }

    fw_info_cmds = {
        'version': 1,
        'fw_version': 2,
        'build_date': 3,
        'hw_type': 4
    }

    payload_types = {
        'cmd': 1,
        'data': 2,
        'rsp': 3,
        'event': 4
    }

    LOG_LEVEL_NONE = 0
    LOG_LEVEL_INFO = 1
    LOG_LEVEL_WARN = 2
    LOG_LEVEL_ERROR = 3

    transport_types = {
        'uart': 0x01,
        'usb': 0x02,
        'wifi': 0x03,
        'ble': 0x04,
        'bluetooth': 0x05,
        'tcp_ip': 0x06
    }
    
    # Default TCP port for ETP
    TCP_PORT = 7820

    def __init__(self, **kwargs):
        if 'transport' in kwargs:
            self.transport = kwargs['transport']

        if self.transport == 'serial':
            if 'port' in kwargs:
                self.port = kwargs['port']

            if 'baudrate' in kwargs:
                self.baudrate = kwargs['baudrate']
            else:
                self.baudrate = 115200

        elif self.transport == 'tcp':
            if 'ip' in kwargs:
                self.ip = kwargs['ip']

            if 'port' in kwargs:
                self.port = kwargs['port']
            else:
                self.port = self.TCP_PORT

        self.transport_handle = None
        self.transport_open = False
        self.rsp = []
        self.cmd_queue = queue.Queue()
        self.rsp_queue = queue.Queue()
        self.evt_queue = queue.Queue()
        self.lock = threading.Lock()

        self.gpio = GPIO(self)
        self.adc = ADC(self)
        self.i2c = I2C(self)
        self.pwm = PWM(self)
        self.spi = SPI(self)

    def dbg_print(self, level, msg):
        if level == self.LOG_LEVEL_ERROR:
            color_start = '\033[91m'
            color_end = '\033[0m'
        elif level == self.LOG_LEVEL_WARN:
            color_start = '\033[93m'
            color_end = '\033[0m'
        elif level == self.LOG_LEVEL_INFO:
            color_start = '\033[92m'
            color_end = '\033[0m'
        print(f"ETP FW : {color_start}{msg}{color_end}")

    def transport_read_all(self):
        if self.transport == 'serial':
            if self.transport_handle.in_waiting > 0:
                return self.transport_handle.read(self.transport_handle.in_waiting)
            else:
                return bytearray()
        elif self.transport == 'tcp':
            return self.transport_handle.recv(1024)
        else:
            return bytearray()
        
    def transport_read(self, length):
        if length > 0:
            if self.transport == 'serial':
                return self.transport_handle.read(length)
            elif self.transport == 'tcp':
                return self.transport_handle.recv(length)
            else:
                return bytearray()
        else:
            return bytearray()
        
    def transport_write(self, data):
        if self.transport == 'serial':
            self.transport_handle.write(data)
        elif self.transport == 'tcp':
            self.transport_handle.send(data)

    def reader_thread(self):
        while self.transport_open:
            temp = self.transport_read_all()
            if len(temp) > 0:
                self.rsp.extend(temp)
                length = self.rsp[0] ## | self.rsp[1] << 8 ## TODO: Handle length > 255
                if len(self.rsp) < length:
                    self.rsp.extend(self.transport_read(length - len(self.rsp)))
                if len(self.rsp) >= length:
                    if self.rsp[2] == self.payload_types['rsp']:
                        self.rsp_queue.put(self.rsp[0: length])
                    elif self.rsp[2] == self.payload_types['event']:
                        if self.rsp[6] == self.general_ops['debug_print']:
                            self.dbg_print(self.rsp[8], bytes(self.rsp[8:]).decode('utf-8'))
                        else:
                            self.evt_queue.put(self.rsp[0: length])
                
                    self.rsp = self.rsp[length:]
            time.sleep(0.001)

    def writer_thread(self):
        while self.transport_open:
            try:
                if not self.cmd_queue.empty():
                    cmd = self.cmd_queue.get()
                    self.transport_write(cmd)
                else:
                    time.sleep(0.001)
            except Exception as e:
                print(f"Error writing to serial port: {e}")
                break


    def mask_to_bits(self, mask, bit_count):
        bits = []
        for i in range(bit_count):
            if mask & (1 << i):
                bits.append(i)
        return bits

    def frame_packet(self, cmd, data=b''):
        self.transaction_id = 0
        packet = struct.pack('<HBBHH', len(data) + 8, self.payload_types['cmd'], 0, self.transaction_id, cmd) + bytes(data)
        return packet

    def read_rsp(self):
        try:
            rsp = self.rsp_queue.get(timeout=1)
            rsp, status = bytearray(rsp[8:]), rsp[3]
            return rsp, status
        except Exception as e:
            return None

    def open(self):
        """ Open ETP Device."""
        if self.transport == 'serial':
            self.transport_handle = serial.Serial(self.port, self.baudrate, timeout=1)
            self.transport_handle.timeout = 0.1
            self.transport_open = True

        elif self.transport == 'tcp':
            self.transport_handle = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.transport_handle.connect((self.ip, self.port))
            self.transport_open = True
        
        time.sleep(0.2)

        self.reader_thread_handle = threading.Thread(target=self.reader_thread)
        self.reader_thread_handle.start()
        self.writer_thread_handle = threading.Thread(target=self.writer_thread)
        self.writer_thread_handle.start()



    def get_fw_info(self) -> dict:
        """ Get Firmware Information 
        
        Returns:
            dict: Firmware information.

                | Key           | Value Type | Description                                  |
                |---------------|------------|----------------------------------------------|
                | version       | str        | Firmware version                             |
                | fw_version    | str        | Firmware version                             |
                | build_date    | str        | Firmware build date                          |
                | hw_type       | str        | Hardware type                                |
        """
        self.cmd_queue.put(self.frame_packet(self.general_ops['fw_info'], [self.fw_info_cmds['version']]))
        rsp, _ = self.read_rsp()
        version = struct.unpack('<BBB', rsp[1:4])
        version_str = '.'.join([str(x) for x in version])

        self.cmd_queue.put(self.frame_packet(self.general_ops['fw_info'], [self.fw_info_cmds['fw_version']]))
        rsp, _ = self.read_rsp()
        fw_version = struct.unpack('<BBB', rsp[1:4])
        fw_version_str = '.'.join([str(x) for x in fw_version])

        self.cmd_queue.put(self.frame_packet(self.general_ops['fw_info'], [self.fw_info_cmds['build_date']]))
        rsp, _ = self.read_rsp()
        year, month, day = struct.unpack('<HBB', rsp[1:5])
        hr, min, sec = struct.unpack('<BBB', rsp[5:8])
        build_date_str = f"{day}-{month}-{year},{hr}:{min}:{sec}"

        self.cmd_queue.put(self.frame_packet(self.general_ops['fw_info'], [self.fw_info_cmds['hw_type']]))
        rsp, _ = self.read_rsp()
        hw_type = rsp[1:].decode('utf-8')
        return {'version': version_str, 'fw_version': fw_version_str, 'build_date': build_date_str, 'hw_type': hw_type}
    

    def reset(self):
        """ Reset the device."""
        self.cmd_queue.put(self.frame_packet(self.general_ops['reset'], [1]))
        self.read_rsp()

    def get_supported_ops(self, start_op: int = 0, end_op: int = 0xFFFF) -> list[int]:
        """ Get Supported Operations 
        
        
        Args:
            start_op: Start operation code
            end_op: End operation code

        Returns:
            List of supported operation codes.

        """
        supported_ops = []
        sub_cmd = [start_op & 0xFF, start_op >> 8, end_op & 0xFF, end_op >> 8]
        p = self.frame_packet(self.general_ops['get_supported_ops'], sub_cmd)
        self.cmd_queue.put(p)
        rsp, _ = self.read_rsp()

        total_ops = struct.unpack('<H', rsp[:2])[0]
        report_ops = rsp[2]

        ops = rsp[3:]

        for i in range(0, len(ops), 2):
            supported_ops.append(ops[i] | ops[i + 1] << 8)

        next_op = supported_ops[-1] + 1

        while total_ops > report_ops:
            sub_cmd = [next_op & 0xFF, next_op >> 8, end_op & 0xFF, end_op >> 8]
            p = self.frame_packet(self.general_ops['get_supported_ops'], sub_cmd)
            self.cmd_queue.put(p)
            rsp, _ = self.read_rsp()

            report_ops += rsp[2]
            ops = rsp[3:]

            for i in range(0, len(ops), 2):
                supported_ops.append(ops[i] | ops[i + 1] << 8)

        return supported_ops
    
    """
    Debug Print control
    
    """
    def fw_dbg_print_ctrl(self, log_level: int):
        self.cmd_queue.put(self.frame_packet(self.general_ops['debug_print'], [log_level]))

    def configure_transport(self, transport, **kwargs):
        """Configure Transport."""
        if transport == 'serial':
            self.port = kwargs['port']
            self.baudrate = kwargs['baudrate']
            p = self.frame_packet(self.general_ops['configure_transport'], struct.pack('<BIB', self.transport_types['uart'], self.baudrate, 0))

        elif transport == 'tcp':
            self.ip = kwargs['ip']
            self.port = kwargs['port']
            ip = struct.unpack('<I', socket.inet_aton(self.ip))[0]
            p = self.frame_packet(self.general_ops['configure_transport'], struct.pack('<BIBH', self.transport_types['tcp_ip'], 0, ip, self.port))
        
        elif transport == 'usb':
            p = self.frame_packet(self.general_ops['configure_transport'], struct.pack('<BB', self.transport_types['usb'], kwargs['device_class']))

        elif transport == 'wifi':
            ssid = kwargs['ssid']
            password = kwargs['password']
            p = self.frame_packet(self.general_ops['configure_transport'], struct.pack('<BBB', self.transport_types['wifi'], len(ssid), len(password)) + ssid.encode('utf-8') + b'\0' + password.encode('utf-8') + b'\0')

        elif transport == 'ble' or transport == 'bluetooth':
            device_name = kwargs['device_name']
            p = self.frame_packet(self.general_ops['configure_transport'], struct.pack('<B', self.transport_types['ble']) + device_name.encode('utf-8'))

        self.cmd_queue.put(p)
        rsp, _ = self.read_rsp()
        return rsp[0]


    def close(self):
        """Close ETP Device."""
        self.transport_open = False
        self.reader_thread_handle.join()
        self.writer_thread_handle.join()
        self.transport_handle.close()
