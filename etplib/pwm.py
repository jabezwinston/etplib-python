"""
Copyright (C) 2024, Jabez Winston C

Embedded Tester Protocol Library - PWM

Author  : Jabez Winston C <jabezwinston@gmail.com>
License : MIT
Date    : 19-Sep-2024

"""

import struct

class PWM:
    code = 3
    ops = {
        'info': 0,
        'init': 1,
        'ctrl': 2
    }

    def __init__(self, etp):
        self.etp = etp

    """
    Query PWM information
    
    """

    def get_info(self):
        pwm_info_cmd = self.code << 8 | self.ops['info']
        cmd = self.etp.frame_packet(pwm_info_cmd)
        self.etp.cmd_queue.put(cmd)
        rsp = self.etp.read_rsp()
        num_pwm, max_freq, freq_unit, port_count = struct.unpack('<BHBB', rsp[0:5])
        pwm_ports = list(struct.iter_unpack('<BI', rsp[5:]))
        pwm_info = []
        for port in pwm_ports:
            pwm_info.append({'port': chr(port[0]), 'pins': self.etp.mask_to_bits(port[1], 32)})

        if freq_unit == 1:
            max_freq *= 1
        elif freq_unit == 2:
            max_freq *= 1000

        return {
            'num_pwm': num_pwm,
            'max_freq': max_freq,
            'port_count': port_count,
            'ports': pwm_info
        }
    
    """
    Enable/Disable PWM pins

    """

    def init(self, pin_list):
        pwm_init_cmd = self.code << 8 | self.ops['init']
        pwm_pin_mask = 0
        pwm_enable_mask = 0
        for pin in pin_list.keys():
            port, pin_num = self.etp.gpio.decode_gpio_pin(pin)
            if (pin_list[pin] == True):
                pwm_enable_mask |= (1 << pin_num)
            pwm_pin_mask |= (1 << pin_num)

        cmd = self.etp.frame_packet(pwm_init_cmd, struct.pack('<BII', ord(port), pwm_pin_mask, pwm_enable_mask))
        self.etp.cmd_queue.put(cmd)

    """
    Control PWM pins
    
    """

    def ctrl(self, pin_str, duty_cycle, freq = 1000):
        pwm_ctrl_cmd = self.code << 8 | self.ops['ctrl']
        port, pin_num = self.etp.gpio.decode_gpio_pin(pin_str)
        freq_unit = 0
        if freq < 65535:
            freq_unit = 0
        else:
            freq_unit = 1

        duty_cycle = int(duty_cycle * 100)
        cmd = self.etp.frame_packet(pwm_ctrl_cmd, struct.pack('<BBHBH', ord(port), pin_num, freq, freq_unit, duty_cycle))
        self.etp.cmd_queue.put(cmd)
