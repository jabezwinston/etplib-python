"""
Copyright (C) 2024, Jabez Winston C

Embedded Tester Protocol Library - ADC

Author  : Jabez Winston C <jabezwinston@gmail.com>
License : MIT
Date    : 13-Sep-2024

"""

from .version import VERSION
from .lib import *

__version__ = VERSION
__author__  = "Jabez Winston C"
__license__ = "MIT"
__all__     = ['ETP', 'GPIO', 'ADC', 'I2C', 'PWM']
__package__ = "etplib"
