##
#  @file  Serial_Flasher.py
#  
#   Description: Python module creates an object with methods for 
#   interacting with the STM32 F1 line of microcontrollers via the 
#   Bootloader's serial interface.
# 
#   Also builds a profile of the device and its settings. 
#

import serial
import binascii

## SerialFlasher Class
#   This class represents the object used to interface
#   with the microcontroller. 
#   
#   methods:    
#
#   @param serial_port  - the name of the serial port to connect over
#   @param baud         - baud rate of connection. Use common rates, 1200 - 115200 inclusive.
#   


class SerialFlasher:

    port = None
    baud = None
    ser = None

    def __init__(self, port=None, baud=9600):
        self.port = port
        self.baud = baud

    def getBaud(self):
        pass

    def setBaud(self, baud):
        pass

    def __checkBaud(self, baud):
        pass

    def getPort(self):
        pass

    def setPort(self, port):

        pass

    def openPort(self):
        # sanity check connection details then connect
        pass

    def close(self):
        # close the socket
        pass

    def getTimeout(self):
        ## generate read timeout of 100 bitwidths
        spb = float(1) / float(self.baud)
        return 100 * spb

    def getSerialState(self):
        pass

    def writeDevice(self, data):
        ## sanity check data, return serial.write
        pass

    def readDevice(self, len):
        pass

    def sendHandshake(self):
        pass

    def cmdGetInfo(self):
        pass

    def cmdGetVersionProt(self):
        pass
    
    def cmdWriteEnable(self):
        pass

    def cmdReadoutProtect(self):
        pass

    def cmdReadoutProtectOff(self):
        pass

    def cmdGoToAddress(self, address):
        pass





