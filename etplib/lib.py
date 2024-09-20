"""
Copyright (C) 2024, Jabez Winston C

Embedded Tester Protocol Library

Author  : Jabez Winston C <jabezwinston@gmail.com>
License : MIT
Date    : 13-Sep-2024

"""

import serial
import struct
import queue
import threading
import time

from .gpio import GPIO
from .adc import ADC
from .i2c import I2C
from .pwm import PWM

class ETP:
    general_ops = {
        'fw_info': 0,
        'reset': 1,
        'get_supported_ops': 2
    }

    fw_info_cmds = {
        'version': 1,
        'build_date': 2,
        'hw_type': 3
    }

    payload_types = {
        'cmd': 1,
        'data': 2,
        'rsp': 3,
        'event': 4
    }

    def __init__(self, **kwargs):
        if 'transport' in kwargs:
            self.transport = kwargs['transport']

        if 'port' in kwargs:
            self.port = kwargs['port']

        if 'baudrate' in kwargs:
            self.baudrate = kwargs['baudrate']
        else:
            self.baudrate = 115200

        self.ser = None
        self.ser_open = False
        self.rsp = []
        self.cmd_queue = queue.Queue()
        self.rsp_queue = queue.Queue()
        self.lock = threading.Lock()

    def reader_thread(self):
        while self.ser_open:
            try:
                if (self.ser.in_waiting > 0):
                    self.rsp.extend(self.ser.read(self.ser.in_waiting))
                    if len(self.rsp) > 0:
                        length = self.rsp[0]
                        self.rsp.extend(self.ser.read(length - len(self.rsp)))
                        self.rsp_queue.put(self.rsp[0: self.rsp[0]])
                        self.rsp = self.rsp[self.rsp[0]:]
                else:
                    time.sleep(0.001)
            except Exception as e:
                print(f"Error reading from serial port: {e}")
                break

    def writer_thread(self):
        while self.ser_open:
            try:
                if not self.cmd_queue.empty():
                    cmd = self.cmd_queue.get()
                    self.ser.write(cmd)
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
        packet = struct.pack('<BBHH', len(data) + 6, self.payload_types['cmd'], self.transaction_id, cmd) + bytes(data)
        return packet

    def read_rsp(self):
        try:
            rsp = self.rsp_queue.get(timeout=1)
            rsp = bytearray(rsp[6:])
            return rsp
        except Exception as e:
            return None

    def open(self):
        if self.transport == 'serial':
            self.ser = serial.Serial(self.port, self.baudrate, timeout=1)
            self.ser.timeout = 0.1
            self.ser_open = True

        time.sleep(0.2)

        self.reader_thread_handle = threading.Thread(target=self.reader_thread)
        self.reader_thread_handle.start()
        self.writer_thread_handle = threading.Thread(target=self.writer_thread)
        self.writer_thread_handle.start()

        self.gpio = GPIO(self)
        self.adc = ADC(self)
        self.i2c = I2C(self)
        self.pwm = PWM(self)

    """
    Get Firmware Information
    
    """
    def get_fw_info(self):
        self.cmd_queue.put(self.frame_packet(self.general_ops['fw_info'], [self.fw_info_cmds['version']]))
        rsp = self.read_rsp()
        version = struct.unpack('<BBB', rsp[:3])
        version_str = '.'.join([str(x) for x in version])

        self.cmd_queue.put(self.frame_packet(self.general_ops['fw_info'], [self.fw_info_cmds['build_date']]))
        rsp = self.read_rsp()
        year, month, day = struct.unpack('<HBB', rsp[:4])
        hr, min, sec = struct.unpack('<BBB', rsp[4:])
        build_date_str = f"{day}-{month}-{year},{hr}:{min}:{sec}"

        self.cmd_queue.put(self.frame_packet(self.general_ops['fw_info'], [self.fw_info_cmds['hw_type']]))
        rsp = self.read_rsp()
        hw_type = rsp.decode('utf-8')
        return {'version': version_str, 'build_date': build_date_str, 'hw_type': hw_type}
    
    """
    Reset the device
        
    """
    def reset(self):
        self.cmd_queue.put(self.frame_packet(self.general_ops['reset'], [1]))
        rsp = self.read_rsp()
        return rsp
    
    """
    Get Supported Operations

    """
    def get_supported_ops(self, start_op = 0, end_op = 0xFFFF):
        supported_ops = []
        sub_cmd = [start_op & 0xFF, start_op >> 8, end_op & 0xFF, end_op >> 8]
        p = self.frame_packet(self.general_ops['get_supported_ops'], sub_cmd)
        self.cmd_queue.put(p)
        rsp = self.read_rsp()

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
            rsp = self.read_rsp()

            report_ops += rsp[2]
            ops = rsp[3:]

            for i in range(0, len(ops), 2):
                supported_ops.append(ops[i] | ops[i + 1] << 8)

        return supported_ops

    def close(self):
        self.ser_open = False
        self.reader_thread_handle.join()
        self.writer_thread_handle.join()
        self.ser.close()
