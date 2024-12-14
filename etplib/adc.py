"""
Copyright (C) 2024, Jabez Winston C

Embedded Tester Protocol Library - ADC

Author  : Jabez Winston C <jabezwinston@gmail.com>
License : MIT
Date    : 19-Sep-2024

"""

import struct

class ADC:
    code = 2
    ops = {
        'info': 0,
        'init': 1,
        'ctrl': 2,
        'read': 3
    }

    def __init__(self, etp):
        self.etp = etp
        self.reference_mv = 3300
        self.resolution = 10

    def get_info(self) -> dict:
        """Query ADC information.
        
        Returns:
            dict: Dictionary containing ADC information of the following format:

                | Key           | Value Type | Description                                  |
                |---------------|------------|----------------------------------------------|
                | num_adc       | int        | Number of ADCs                               |
                | num_channels  | int        | Number of channels                           |
                | resolution    | int        | Resolution of ADC                            |
                | reference     | int        | Reference voltage of ADC                     |
                | max_rate      | int        | Maximum sampling rate of ADC                 |
                | port_count    | int        | Number of ADC ports                          |
                | ports         | list       | List of ADC ports and their corresponding pins |
            
        """
        adc_info_cmd = self.code << 8 | self.ops['info']
        cmd = self.etp.frame_packet(adc_info_cmd)
        self.etp.cmd_queue.put(cmd)
        rsp, _ = self.etp.read_rsp()
        num_adc, num_channels, resolution, reference, max_rate, port_count = struct.unpack('<BBBHIB', rsp[0:10])
        adc_ports = list(struct.iter_unpack('<BI', rsp[10:]))
        adc_info = []
        for port in adc_ports:
            adc_info.append({'port': chr(port[0]), 'pins': self.etp.mask_to_bits(port[1], 32)})

        self.reference_mv = reference
        self.resolution = resolution

        return {
            'num_adc': num_adc,
            'num_channels': num_channels,
            'resolution': resolution,
            'reference': reference,
            'max_rate': max_rate,
            'port_count': port_count,
            'ports': adc_info
        }


    def init(self, pin_list: dict) -> int:
        """Enable/Disable ADC pins.
        
        Args:
            pin_list: Dictionary of pins to enable/disable.
        
        """
        adc_init_cmd = self.code << 8 | self.ops['init']
        adc_pin_mask = 0
        adc_enable_mask = 0
        for pin in pin_list.keys():
            port, pin_num = self.etp.gpio.decode_gpio_pin(pin)
            if pin_list[pin] is True:
                adc_enable_mask |= (1 << pin_num)
            adc_pin_mask |= (1 << pin_num)

        cmd = self.etp.frame_packet(adc_init_cmd, struct.pack('<BII', ord(port), adc_pin_mask, adc_enable_mask))
        self.etp.cmd_queue.put(cmd)
        _, status = self.etp.read_rsp()
        return status

    def ctrl(self, pin: str, **kwargs) -> int:
        """
        Control ADC pin.

        Args:
            pin: ADC pin to control.
            **kwargs (dict): Keyword arguments.

        Keyword Args: **kwargs:
            resolution (int, optional): Resolution of ADC pin. Defaults to self.resolution.
            reference_mv (int, optional): Reference voltage of ADC pin. Defaults to self.reference_mv.
            rate (int, optional): Sampling rate of ADC pin. Defaults to 1000.
            start (int, optional): Start value of ADC pin. Defaults to 0.

        Returns:
            Status code.
        """
        adc_ctrl_cmd = self.code << 8 | self.ops['ctrl']
        port, pin = self.etp.gpio.decode_gpio_pin(pin)

        if 'resolution' in kwargs:
            resolution = kwargs['resolution']
        else:
            resolution = self.resolution

        if 'reference_mv' in kwargs:
            reference_mv = kwargs['reference_mv']
        else:
            reference_mv = self.reference_mv

        if 'rate' in kwargs:
            rate = kwargs['rate']
        else:
            rate = 1000

        if rate < 65536:
            unit = 0x01
        else:
            unit = 0x02
            rate = rate // 1000

        if 'start' in kwargs:
            start = kwargs['start']
        else:
            start = 0

        cmd = self.etp.frame_packet(adc_ctrl_cmd, struct.pack('<BBBHHBB', ord(port), pin, resolution, reference_mv, rate, unit, start))
        self.etp.cmd_queue.put(cmd)
        _, status = self.etp.read_rsp()
        return status

    def read(self, pin: str) -> int:
        """Read data from ADC pin.
        
        Args:
            pin: ADC pin to read from.

        Returns:
            ADC value read from the pin.
        """
        adc_read_cmd = self.code << 8 | self.ops['read']
        port, pin = self.etp.gpio.decode_gpio_pin(pin)
        cmd = self.etp.frame_packet(adc_read_cmd, struct.pack('<BB', ord(port), pin))
        self.etp.cmd_queue.put(cmd)
        rsp, _ = self.etp.read_rsp()
        value = struct.unpack('<I', rsp)[0]
        return value
