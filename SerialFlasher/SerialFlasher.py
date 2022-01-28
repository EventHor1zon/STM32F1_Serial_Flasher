##
#  @file  Serial_Flasher.py
#
#   Description: Python module creates an object with methods for
#   interacting with the STM32 F1 line of microcontrollers via the
#   Bootloader's serial interface.
#
#   Also builds a profile of the device and its settings.
#

import sys
from serial import Serial, SerialTimeoutException, SerialException
import binascii


## SerialFlasher Class
#   This class represents the object used to interface
#   with the microcontroller.
#
#   methods:
#
#   @param serial_port  - the name of the serial port to connect over
#   @param baud         - baud rate of connection. Use common rates, 1200 - 115200 inclusive.

valid_bauds = [
    9600,
    57600,
    115200,
    460800,
]


class SerialTool:

    connected = False

    @staticmethod
    def checkBaudValid(baud):
        pass

    def __init__(self, port=None, baud: int = 9600, serial: Serial = None):
        if serial is not None:
            self.serial = serial
            self.port = serial.port
            self.baud = serial.baudrate
        elif port is None:
            raise TypeError("Need a port or Serial object")
        else:
            self.port = port
            self.baud = baud
            self.serial = Serial(port, baud, timeout=1.0, write_timeout=1.0)

    def getBaud(self):
        return self.baud

    def setBaud(self, baud):
        if self.connected == True:
            return False
        elif baud > 115200 or baud < 1200:
            raise ValueError("Baud rate max: 115200bps, min: 1200bps")
        else:
            self.serial.baudrate = baud
        return True

    def getPort(self):
        pass

    def connect(self):
        """connect to the STM chip"""
        pass

    def disconnect(self):
        """close the socket"""
        pass

    def setSerialTimeout(self, timeout):
        pass

    def getSerialTimeout(self):
        pass

    def getSerialState(self):
        """get serial state"""
        pass

    def getConnectedState(self):
        """get the connected state"""
        pass

    def writeDevice(self, data):
        """write data to the device
        this should be a staticmethod?
        """
        pass

    def readDevice(self, len):
        """attempt to read len bytes from the device
        return read_len, bytes
        """
        pass

    def cmdGetInfo(self):
        """get the device information"""
        pass

    def cmdGetVersionProt(self):
        """get the device's bootloader protocol version"""
        pass

    def cmdWriteEnable(self):
        """ """
        pass

    def cmdReadoutProtect(self):
        pass

    def cmdReadoutProtectOff(self):
        pass

    def cmdGoToAddress(self, address):
        pass
