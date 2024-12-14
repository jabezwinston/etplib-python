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

    def get_info(self) -> dict:
        """Query PWM information.
        
        Returns:
            Dictionary containing PWM information of the following format:
                
                | Key           | Value Type | Description                                  |
                |---------------|------------|----------------------------------------------|
                | num_pwm       | int        | Number of PWMs                               |
                | max_freq      | int        | Maximum frequency of PWM                     |
                | port_count    | int        | Number of PWM ports                          |
                | ports         | list       | List of PWM ports and their corresponding pins |

        """
        pwm_info_cmd = self.code << 8 | self.ops['info']
        cmd = self.etp.frame_packet(pwm_info_cmd)
        self.etp.cmd_queue.put(cmd)
        rsp, _ = self.etp.read_rsp()
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

    def init(self, pin_list: dict) -> int:
        """Enable/Disable PWM pins.
        
        Args:
            pin_list: Dictionary containing PWM pins and their enable status.

        Returns:
            Initialization status.    

        """
        pwm_init_cmd = self.code << 8 | self.ops['init']
        pwm_pin_mask = 0
        pwm_enable_mask = 0
        for pin in pin_list.keys():
            port, pin_num = self.etp.gpio.decode_gpio_pin(pin)
            if pin_list[pin] is True:
                pwm_enable_mask |= (1 << pin_num)
            pwm_pin_mask |= (1 << pin_num)

        cmd = self.etp.frame_packet(pwm_init_cmd, struct.pack('<BII', ord(port), pwm_pin_mask, pwm_enable_mask))
        self.etp.cmd_queue.put(cmd)
        _, status = self.etp.read_rsp()
        return status

    def ctrl(self, pin: str, duty_cycle: float, freq: int = 1000) -> int:
        """Control PWM pin.

        Args:
            pin: PWM pin identifier.
            duty_cycle (float): Duty cycle of the PWM signal.
            freq (int): Frequency of the PWM signal in Hz.

        Returns:
            Control status.

        """
        pwm_ctrl_cmd = self.code << 8 | self.ops['ctrl']
        port, pin_num = self.etp.gpio.decode_gpio_pin(pin)
        freq_unit = 0
        if freq < 65535:
            freq_unit = 0
        else:
            freq_unit = 1

        duty_cycle = int(duty_cycle * 100)
        cmd = self.etp.frame_packet(pwm_ctrl_cmd, struct.pack('<BBHBH', ord(port), pin_num, freq, freq_unit, duty_cycle))
        self.etp.cmd_queue.put(cmd)
        _, status = self.etp.read_rsp()
        return status
