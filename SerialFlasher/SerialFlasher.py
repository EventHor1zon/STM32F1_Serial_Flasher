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
from .errors import InformationNotRetrieved, InvalidAddressError, InvalidReadLength

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
    ##=========== UTILITY FUNCTIONS =========##

    @staticmethod
    def checkBaudValid(baud):
        pass

    @staticmethod
    def getByteComplement(byte):
        return (byte ^ 0xFF)

    @staticmethod
    def appendChecksum(data: bytearray):
        chk = 0
        for b in data:
            chk ^= b
        data.append(chk)
        return data

    @staticmethod
    def checkValidWriteAddress(address):
        pass

    @staticmethod
    def checkValidReadAddress(address):
        pass

    def address_to_bytes(self, address):
        """ return address as bytearray, MSB first """
        return bytearray([
            ((address >> 24) & 0xFF),
            ((address >> 16) & 0xFF),
            ((address >> 8) & 0xFF),
            (address & 0xFF),
        ])

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


    def parseCommandResponse(self, rsp: bytearray):
        """ assert response is correct """
        n = rsp[0]
        ## TODO: Do we add 1 here? Appnote says N-1 bytes
        pass

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

    def waitForAck(self, timeout: float = 1.0):
        # @brief Wait for an ack byte from the device
        # @param timeout - the time to wait for the ack byte
        ## TODO: This better
        if self.serial.timeout == None or self.serial.write_timeout == None:
            self.setSerialReadWriteTimeout(timeout)
        rx = self.serial.read_until(bytes([STM_CMD_ACK]), size=1)
        if STM_CMD_ACK in rx:
            print(f"ack received")
            return True
        elif STM_CMD_NACK in rx:
            print(f"nack received")
            return False
        else:
            ## TODO: raise invalid byte error or something
            print("neither recieved")
            return False

    ##============== Device Interaction =========##

    def connect(self):
        """connect to the STM chip"""
        self.writeDevice(bytearray([STM_CMD_HANDSHAKE]))
        return self.waitForAck()

    def disconnect(self):
        """close the socket"""
        self.serial.close()
        self.connected = False

    ##=============== DEVICE COMMANDS ==========##

    def cmdGetId(self):
        id_rx = None
        id_commands = bytearray([STM_CMD_GET_ID, self.getByteComplement(STM_CMD_GET_ID)])
        success = self.writeDevice(id_commands)

        if success:
            success = self.waitForAck()
        if success:
            success, id_rx = self.readDevice(STM_GET_ID_RSP_LEN)

        return success, id_rx

    def cmdGetInfo(self):
        """get the device information"""
        get_rx = None
        get_commands = bytearray([STM_CMD_GET, self.getByteComplement(STM_CMD_GET),])
        success = self.writeDevice(get_commands)
        if success:
            success, get_rx = self.readDevice(STM_RSP_GET_LEN)
        if success and get_rx[0] != STM_CMD_ACK:
            success = False

        return success, get_rx

    def cmdGetVersionProt(self):
        """get the device's bootloader protocol version"""
        rx = None
        commands = bytearray(
            [
                STM_CMD_VERSION_READ_PROTECT,
                self.getByteComplement(STM_CMD_VERSION_READ_PROTECT),
            ]
        )
        success = self.writeDevice(commands)
        if success:
            success, rx = self.readDevice(5)
        if success and rx[0] != STM_CMD_ACK:
            success = False
        return success, rx

    def cmdReadFromMemoryAddress(self, address, length):
        """ read length bytes from address """
        rx = bytearray()

        # check address is valid
        if self.checkValidReadAddress(address) != True:
            raise InvalidAddressError()
        
        # check read length
        if length > 255 or length < 1:
            raise InvalidReadLength()

        # read command bytes
        read_command = bytearray([
            STM_CMD_READ_MEM,
            self.getByteComplement(STM_CMD_READ_MEM),
        ])
        
        # address bytes
        address_bytes = self.address_to_bytes(address)
        address_bytes = self.appendChecksum(address_bytes)
        # length bytes
        length_bytes = bytearray([
            length,
            self.getByteComplement(length),
        ])

        # write the command, address & length to the device
        # waiting for ACKs in between
        success = self.writeDevice(read_command)
    
        if success:
            success = self.waitForAck(self)
        else:
            print(f"error write command")

        if success:
            success = self.writeDevice(address_bytes)
        else:
            print(f"error waiting for 1st ack")
    
        if success:
            success = self.waitForAck(self)
        else:
            print(f"error write address bytes")

        if success:
            success = self.writeDevice(length_bytes)
        else:
            print(f"error waiting 2nd ack")
            
        if success:
            success = self.waitForAck(self)
        else:
            print(f"error write length")

        if success:
            success, rx = self.readDevice(length)
        else:
            print(f"error 3rd wait for ack")
        
        print(f"success {success} rx {rx}")

        # return success and data
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




