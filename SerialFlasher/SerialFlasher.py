##
#  @file  Serial_Flasher.py
#
#   Description: Python module creates an object with methods for
#   interacting with the STM32 F1 line of microcontrollers via the
#   Bootloader's serial interface.
#
#   Also builds a profile of the device and its settings.
#

from dataclasses import dataclass
from enum import Enum
from struct import unpack
from time import sleep
import sys
from serial import Serial, SerialTimeoutException, SerialException, PARITY_EVEN
import binascii
from SerialFlasher.constants import *
from .errors import (
    InformationNotRetrieved,
    InvalidAddressError,
    InvalidReadLength,
    InvalidResponseLengthError,
    AckNotReceivedError
)

## SerialFlasher Class
#   This class represents the object used to interface
#   with the microcontroller.
#
#   methods:
#
#   @param serial_port  - the name of the serial port to connect over
#   @param baud         - baud rate of connection. Use common rates, 1200 - 115200 inclusive.
#
#
#   Flash programming is gonna be fun!
#   after reset, FPEC block is protected
#   FLASH_CR not accessible in write mode
#   two write cycles to unlock
#       -   1 : Key1 -> FLASH_KEYREG
#       -   2 : Key2 -> FLASH_KEYREG
#
#
#
#   Memory Area   Write command   Read command    Erase command       Go command
#   Flash           Supported       Supported       Supported       Supported
#   RAM Supported   Supported       Not supported   Supported
#   System Memory   Not supported   Supported       Not supported   Not supported
#   Data Memory     Supported       Supported       Not supported   Not supported
#   OTP Memory      Supported       Supported       Not supported   Not supported
#
#
# REFACTOR
#   Trying to do everything in a single class again!
#
#   Project structure needs some thinking about
#
#   High Level Commands -
#           Write data to flash storage
#           Get device information
#           Get device status, etc
#
#   Mid level commands:
#       Send Bootloader commands
#       Check Bootloader responses
#       Configure driver
#       Read registers
#       Write registers
#
#   Low level commands -
#       read bytes
#       write bytes
#       wait for ack
#       reset with DTR
#
#   Device Model  - high level, abstracted user-friendly methods
#   Bootloader Interface - mid level, sanity checking, device controller
#   Serial interface - low level, serial port interface, timeouts etc
#
#   Flash memory programming sequence in standard mode:
#       - check no flash mem operation (see BSY bit in FLASH_SR)
#       - set the PG bit in FLASH_SR
#       - perform the 16-bit write at desired address
#       - wait for BSY bit to be unset
#       - read the programmed value & verify
#
#   Programming the option bytes:
#       - write KEYS 1 & 2 to the FLASH_OPTKEYR register to set the OPTWRE bit in the FLASH_CR
#       - check no flash mem operation as above
#       - set the OPTPG bit in the FLASH_CR
#       - write the 16-bit value to desired address
#       - wait for BSY to be unset & verify
#
#   Erasing the option bytes:
#       - unlock the OPTWRE bit in the FLASH_CR as above
#       - set the OPTER bit in the FLASH_CR
#       - set the STRT but in the FLASH_CR
#       - wait for BSY & verify
#




class SerialTool:
    """
        This class should:
        - provide access to the underlying PySerial object
        - send and receive bootloader commands
        - provide functions to read/write data to memory addresses
        - contain various utility functions for use in device commands
        - handle handshake & initial serial connection
        - return the bytearrays read from the device
    """

    connected = False

    ##=========== UTILITY FUNCTIONS =========##

    @staticmethod
    def checkBaudValid(baud):
        pass

    @staticmethod
    def getByteComplement(byte):
        return byte ^ 0xFF

    @staticmethod
    def appendChecksum(data: bytearray):
        chk = 0
        for b in data:
            chk ^= b
        data.append(chk)
        return data

    def addressToBytes(self, address):
        """ return address as bytearray, MSB first """
        return bytearray(
            [
                ((address >> 24) & 0xFF),
                ((address >> 16) & 0xFF),
                ((address >> 8) & 0xFF),
                (address & 0xFF),
            ]
        )

    def reset(self):
        """ remove this... """
        self.serial.setDTR(1)
        sleep(0.001)
        self.serial.setDTR(0)

    def __init__(self, port=None, baud: int = 9600, serial: Serial = None):
        """ 
            Init the serial flasher object
                Either supply a serial object or a port/baud for the 
                serial connection created
            \param port - the Serial port to connect to 
            \param baud - the baud rate to communicate at
            \param serial - the serial object to use
        """
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


    ##============ GETTERS/SETTERS ============##

    def getBaud(self):
        """ return the baud rate of the serial object """
        return self.baud

    def setBaud(self, baud: int):
        """ 
            set the baud rate of the serial object
            cannot set once the device has connected
        """
        if self.connected == True:
            return False
        elif baud > 115200 or baud < 1200:
            raise ValueError("Baud rate max: 115200bps, min: 1200bps")
        else:
            self.serial.baudrate = baud
        return True

    def getPort(self):
        """ 
            returns the port connected to by the serial object
        """
        return self.serial.port

    def setSerialReadWriteTimeout(self, timeout: float):
        """ set timeout for read/write serial operations """
        self.serial.timeout = timeout
        self.serial.write_timeout = timeout

    def getSerialTimeout(self):
        """ returns the serial object's timeout """
        return self.serial.timeout

    def getSerialState(self):
        """get serial state"""
        return self.serial.is_open

    def getConnectedState(self):
        """get the connected state"""
        return self.connected

    ##============= Serial Interaction =========#

    def writeDevice(self, data: bytearray):
        """write data to the device
        this should be a staticmethod?
        """
        tx = self.serial.write(data)
        if tx != len(data):
            return False
        return True

    def readDevice(self, length):
        """
            attempt to read len bytes from the device
            return read_len, bytes
        """
        rx = self.serial.read(length)
        return (len(rx) == length), rx

    def writeAndWaitAck(self, data: bytearray):
        """ sends data to device and waits for ack """
        success = self.writeDevice(data)
        if success:
            success = self.waitForAck()
        return success

    def waitForAck(self, timeout: float = 1.0):
        """ \brief Wait for an ack byte from the device
            \param timeout - the time to wait for the ack byte
        """

        if self.serial.timeout == None or self.serial.write_timeout == None:
            self.setSerialReadWriteTimeout(timeout)
        rx = self.serial.read_until(bytes([STM_CMD_ACK]), size=1)
        if STM_CMD_ACK in rx:
            return True
        elif STM_CMD_NACK in rx:
            return False
        else:
            ## TODO: raise invalid byte error or return false?
            return False

    ##============== Device Interaction =========##

    def connect(self):
        """connect to the STM chip"""
        success = self.writeAndWaitAck(bytearray([STM_CMD_HANDSHAKE]))
        if success:
            self.connected = True
        return success

    def disconnect(self):
        """close the socket"""
        self.serial.close()
        self.connected = False

    ##=============== DEVICE COMMANDS ==========##
    
    def writeCommand(self, data, length):
        """ write a command byte, check ack and get a response """
        rx = bytearray()

        success = self.writeDevice(data)
        if success:
            success = self.waitForAck()
    
        if success:
            success, rx = self.readDevice(STM32_RSP_LEN_BYTE)

        if success:
            incomming = rx[0]
            if incomming + 1 != length:
                raise InvalidResponseLengthError(
                    f"Device responds with {incomming+1} bytes, but expected {length} bytes"
                )

        if success:
            success, rx = self.readDevice(length)
        
        if success:
            success = self.waitForAck()
        
        return success, rx


    def cmdGetId(self):
        """ send the getId Command """
        id_command = bytearray([STM_CMD_GET_ID, self.getByteComplement(STM_CMD_GET_ID)])
        return self.writeCommand(id_command, STM_GET_ID_RSP_LEN)

    def cmdGetInfo(self):
        """get the device information"""
        get_commands = bytearray([STM_CMD_GET, self.getByteComplement(STM_CMD_GET),])
        return self.writeCommand(get_commands, STM_RSP_GET_LEN)

    def cmdGetVersionProt(self):
        """ get the device's bootloader protocol version
            this command is structured differently, presumably for backwards
            compatibility. Likely better to use the GetInfo command unless the 
            option bytes are specifically required      
        """
        rx = bytearray()

        commands = bytearray(
            [
                STM_CMD_VERSION_READ_PROTECT,
                self.getByteComplement(STM_CMD_VERSION_READ_PROTECT),
            ]
        )
        success = self.writeAndWaitAck(commands)

        if success:
            success, rx = self.readDevice(STM_VERS_RSP_LEN)

        if success:
            self.waitForAck()

        return success, rx

    def cmdReadFromMemoryAddress(self, address, length):
        """ read length bytes from address
            - Send readAddress Command & wait ack
            - Send Address ^ chk & wait ack
            - Send readLength ^ chk & wait ack
        """

        # check read length
        if length > 255 or length < 1:
            raise InvalidReadLength(
                "Read length must be > 0 and < 256 bytes"
            )

        # read command bytes
        commands = bytearray(
            [STM_CMD_READ_MEM, self.getByteComplement(STM_CMD_READ_MEM),]
        )

        # initialise rx as empty bytearray
        rx = bytearray() 

        # address bytes
        address_bytes = self.addressToBytes(address)
        address_bytes = self.appendChecksum(address_bytes)
        # length bytes
        length_bytes = bytearray([length, self.getByteComplement(length),])

        # write the command, address & length to the device
        success = self.writeAndWaitAck(commands)

        if success:
            success = self.writeAndWaitAck(address_bytes)

        if success:
            success = self.writeAndWaitAck(length_bytes)

        if success:
            success, rx = self.readDevice(length)

        return success, rx


    def cmdWriteToMemoryAddress(self, address, data):
        """ write data to a memory address """
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

