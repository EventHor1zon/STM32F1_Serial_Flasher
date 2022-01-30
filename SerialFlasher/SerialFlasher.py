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
from serial import Serial, SerialTimeoutException, SerialException, PARITY_EVEN
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

STM_CMD_HANDSHAKE = 0x7F
STM_CMD_ACK = 0x79
STM_CMD_NACK = 0x1F
STM_CMD_VERSION_READ_PROTECT = 0x01
STM_CMD_GET_ID = 0x02
STM_CMD_READ_MEM = 0x11
STM_CMD_GO = 0x21
STM_CMD_WRITE_MEM = 0x31
STM_CMD_ERASE_MEM = 0x43
STM_CMD_EXT_ERASE = 0x44
STM_CMD_WRITE_PROTECT_EN = 0x63
STM_CMD_WRITE_PROTECT_DIS = 0x73
STM_CMD_READOUT_PROTECT_EN = 0x82
STM_CMD_READOUT_PROTECT_DIS = 0x92

STM_BYTE_END_TX = 0xFF

STM_GET_RETURN_N = 0x0B



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
        self.serial.parity = PARITY_EVEN
        self.serial.setDTR(False)

    def getBaud(self):
        return self.baud

    def setBaud(self, baud: int):
        if self.connected == True:
            return False
        elif baud > 115200 or baud < 1200:
            raise ValueError("Baud rate max: 115200bps, min: 1200bps")
        else:
            self.serial.baudrate = baud
        return True

    def getPort(self):
        return self.serial.port

    def setSerialReadWriteTimeout(self, timeout: float):
        self.serial.timeout = timeout
        self.serial.write_timeout = timeout

    def getSerialTimeout(self):
        return self.serial.timeout

    def getSerialState(self):
        """get serial state"""
        return self.serial.is_open

    def getConnectedState(self):
        """get the connected state"""
        return self.connected

    def writeDevice(self, data: bytearray):
        """write data to the device
        this should be a staticmethod?
        """
        tx = self.serial.write(data)
        if tx != len(data):
            return False
        return True

    def readDevice(self, length):
        """attempt to read len bytes from the device
        return read_len, bytes
        """
        rx = self.serial.read(length)
        return (len(rx) == length), rx

    def connect(self):
        """connect to the STM chip"""
        self.writeDevice(bytearray([STM_CMD_HANDSHAKE]))
        success, data = self.readDevice(1)
        if not success:
            return False
        elif data[0] != STM_CMD_ACK:
            return False
        else:
            self.connected = True
            return True



    def disconnect(self):
        """close the socket"""
        self.serial.close()


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
