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

class SerialTool():

    @staticmethod
    def checkBaudValid(baud):
        pass


    def __init__(self, port=None, baud: int=9600, s: Serial=None):
        if s is not None:
            self.serial = s
            self.port = s.port
            self.baud = s.baud
        else:
            self.port = port
            self.baud = baud
            self.serial = Serial(port, baud)


    def baud(self):
        return self.baud

    def setBaud(self, baud):
        pass


    def getPort(self):
        pass


    def connect(self):
        """ connect to the STM chip """
        pass

    def disconnect(self):
        """ close the socket """
        pass

    def setSerialTimeout(self, timeout):
        pass

    def getSerialTimeout(self):
        pass

    def getSerialState(self):
        """ get serial state """
        pass

    def getConnectedState(self):
        """ get the connected state """
        pass

    def writeDevice(self, data):
        """ write data to the device 
            this should be a staticmethod?
        """
        pass

    def readDevice(self, len):
        """ attempt to read len bytes from the device 
            return read_len, bytes
        """
        pass

    def cmdGetInfo(self):
        """ get the device information """
        pass

    def cmdGetVersionProt(self):
        """ get the device's bootloader protocol version """
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





