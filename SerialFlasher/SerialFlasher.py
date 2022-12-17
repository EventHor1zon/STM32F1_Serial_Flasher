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
    InvalidReadLengthError,
    InvalidResponseLengthError,
    AckNotReceivedError,
    InvalidWriteLengthError,
    NoResponseError,
    UnexpectedResponseError,
    InvalidEraseLengthError,
)
from .utilities import getByteComplement

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
#   RAM             Supported       Supported       Not supported   Supported
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
        print("Resetting device via DTR pin")
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

    def writeDevice(self, data: bytearray) -> bool:
        """! write data to the device
            @param data to send
            @return True on success
        """
        tx = self.serial.write(data)
        if tx != len(data):
            return False
        return True

    def readDevice(self, length) -> tuple:
        """! attempt to read len bytes from the device
            @param length  Bytes to read
            @return Tuple(success, data)
        """
        rx = self.serial.read(length)
        return (len(rx) == length), rx

    def writeAndWaitAck(self, data: bytearray) -> bool:
        """! sends data to device and waits for ack
            @param data - bytearray of data to send
            @return True on success or False
        """
        success = self.writeDevice(data)
        if success:
            success = self.waitForAck()
        return success

    def waitForAck(self, timeout: float = 1.0) -> bool:
        """! Wait for an ack byte from the device
            @param timeout Time to wait for the ack byte
            @return True - ACK False - NACK
        """
        if self.serial.timeout == None or self.serial.write_timeout == None:
            self.setSerialReadWriteTimeout(timeout)
        rx = self.serial.read_until(bytes([STM_CMD_ACK]), size=1)
        if len(rx) < 1:
            raise NoResponseError
        if STM_CMD_ACK in rx:
            return True
        elif STM_CMD_NACK in rx:
            return False
        else:
            raise UnexpectedResponseError(f"Invalid response byte received: {hex(rx[0])}")
            

    ##============== Device Interaction =========##

    def connect(self):
        """! connect to the STM chip bootloader by sending the 
             handshake byte
        """
        success = self.writeAndWaitAck(bytearray([STM_CMD_HANDSHAKE]))
        if success:
            self.connected = True
        return success

    def disconnect(self):
        """! close the serial socket
        """
        self.serial.close()
        self.connected = False

    def reconnect(self):
        self.disconnect()
        sleep(0.1)
        self.serial.open()
        return self.connect()

    ##=============== DEVICE COMMANDS ==========##
    
    def writeCommand(self, data: bytearray, length: int):
        """! write a command byte, check ack and get a response 
             starting with number of bytes
            @param data     bytearray of data to send
            @param length   expected number of bytes in rsp
            @return True on success
        """
        rx = bytearray()

        success = self.writeAndWaitAck(data)
    
        if success:
            # read the response length byte
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
        """! send the getId Command 

            @return tuple (Success, raw data bytes)
        """
        id_command = bytearray([STM_CMD_GET_ID, getByteComplement(STM_CMD_GET_ID)])
        return self.writeCommand(id_command, STM_GET_ID_RSP_LEN)

    def cmdGetInfo(self):
        """! get the device information 

            @return tuple (Success, raw data bytes)
        """
        get_commands = bytearray([STM_CMD_GET, getByteComplement(STM_CMD_GET),])
        return self.writeCommand(get_commands, STM_RSP_GET_LEN)

    def cmdGetVersionProt(self):
        """ !get the device's bootloader protocol version
            this command is structured differently, presumably for backwards
            compatibility. Likely better to use the GetInfo command unless the 
            option(al?) bytes are specifically required

            @return tuple (Success, raw data bytes)
        """
        rx = bytearray()

        commands = bytearray(
            [
                STM_CMD_VERSION_READ_PROTECT,
                getByteComplement(STM_CMD_VERSION_READ_PROTECT),
            ]
        )
        success = self.writeAndWaitAck(commands)

        if success:
            success, rx = self.readDevice(STM_VERS_RSP_LEN)

        if success:
            self.waitForAck()

        return success, rx

    def cmdReadFromMemoryAddress(self, address: int, length: int):
        """ ! Send read command to read length bytes from address
            @param address  address to read from
            @param length   Number of bytes to read
            @return True on success
        """

        # check read length
        if length > 255 or length < 1:
            raise InvalidReadLengthError(
                "Read length must be > 0 and < 256 bytes"
            )

        # read command bytes
        commands = bytearray(
            [STM_CMD_READ_MEM, getByteComplement(STM_CMD_READ_MEM),]
        )

        # initialise rx as empty bytearray
        rx = bytearray() 

        # address bytes
        address_bytes = self.addressToBytes(address)
        address_bytes = self.appendChecksum(address_bytes)
        # length bytes
        length_bytes = bytearray([length-1, getByteComplement(length-1),])

        # write the command, address & length to the device
        success = self.writeAndWaitAck(commands)

        if success:
            success = self.writeAndWaitAck(address_bytes)

        if success:
            success = self.writeAndWaitAck(length_bytes)

        if success:
            success, rx = self.readDevice(length)

        return success, rx


    def cmdWriteToMemoryAddress(self, address: int, data: bytearray):
        """! write data to a memory address. Data must be a multiple of 
                4 bytes in length 
            @param address
            @param data
            @return True on Success
        """
        if len(data) > 256 or len(data) < 1:
            raise InvalidWriteLengthError(f"Invalid length: {len(data)}")
        
        if len(data) % 4 > 0:
            raise InvalidWriteLengthError("Must be a multiple of 4 bytes")

        commands = bytearray(
            [STM_CMD_WRITE_MEM, getByteComplement(STM_CMD_WRITE_MEM),]
        )
        
        # address bytes
        address_bytes = self.addressToBytes(address)
        address_bytes = self.appendChecksum(address_bytes)
        
        # write the length (N) and N+1 (????) data bytes and Checksum^N
        tx_data = bytearray([len(data)-1])
        tx_data += data
        tx_data = self.appendChecksum(tx_data)

        success = self.writeAndWaitAck(commands)

        if success:
            success = self.writeAndWaitAck(address_bytes)

        if success:
            # no NACK returned if invalid write area
            try:
                success = self.writeAndWaitAck(tx_data)
            except NoResponseError:
                # want to raise an exception with a specific message
                raise NoResponseError("Invalid write address")

        return success


    def cmdEraseFlashMemoryPages(self, pages: bytearray):
        """ !send the flash erase command to erase certain pages,
            specified by index in pages variable
            @param pages    bytearray of page indexes to erase
            @return         True on success
        """
        if len(pages) < 1 or len(pages) > 256:
            raise InvalidEraseLengthError

        commands = bytearray([
            STM_CMD_ERASE_MEM,
            getByteComplement(STM_CMD_ERASE_MEM),
        ])

        tx_data = bytearray([
            len(pages)-1,
        ])
        tx_data += pages
        tx_data = self.appendChecksum(tx_data)

        success = self.writeAndWaitAck(commands)

        if success:
            success = self.writeAndWaitAck(tx_data)

        return success

    def cmdEraseFlashMemory(self):
        """! send the flash erase all pages command 
            @return True on success
        """

        commands = bytearray([
            STM_CMD_ERASE_MEM,
            getByteComplement(STM_CMD_ERASE_MEM),
        ])

        tx_data = bytearray([
            0xFF,
        ])

        success = self.writeAndWaitAck(commands)

        if success:
            success = self.writeAndWaitAck(tx_data)
        
        return success


    def cmdWriteProtect(self, sectors: bytearray):
        """! send the bootloader command to write-protect the flash
            memory. This command resets the device, disconnecting it.
            @param sectors bytearray of sectors to protect
            @return True on success
        """
        if len(sectors) < 1 or len(sectors) > 256:
            raise InvalidWriteLengthError("Invalid sector length") 

        commands = bytearray([
            STM_CMD_WRITE_PROTECT_EN,
            getByteComplement(STM_CMD_WRITE_PROTECT_EN),
        ])

        tx_data = bytearray([
            len(sectors)-1,
        ])
        tx_data += sectors
        tx_data = self.appendChecksum(tx_data)

        success = self.writeAndWaitAck(commands)

        if success:
            success = self.writeAndWaitAck(tx_data)
        
        ## once the write protect command is complete, the device 
        ## resets, so set connected to false
        if success:
            self.connected = False

        return success

    def cmdWriteUnprotect(self):
        """! send the command to unprotect flash from write
            @return True on success
         """
        commands = bytearray([
            STM_CMD_WRITE_PROTECT_DIS,
            getByteComplement(STM_CMD_WRITE_PROTECT_DIS),
        ])

        first_ack = self.writeAndWaitAck(commands)

        second_ack = self.waitForAck()
        self.connected = False

        return (first_ack & second_ack)

    def cmdReadoutProtect(self):
        """! send the command to protect flash from read
            @return True on success
         """
        commands = bytearray([
            STM_CMD_READOUT_PROTECT_EN,
            getByteComplement(STM_CMD_READOUT_PROTECT_EN),
        ])

        first_ack = self.writeAndWaitAck(commands)

        second_ack = self.waitForAck()
        self.connected = False

        return (first_ack & second_ack)

    def cmdReadoutUnprotect(self):
        """! send the command to unprotect flash from read
            @return True on success
         """
        commands = bytearray([
            STM_CMD_READOUT_PROTECT_DIS,
            getByteComplement(STM_CMD_READOUT_PROTECT_DIS),
        ])

        success = self.writeDevice(commands)

        if success:
            first_ack = self.waitForAck()
            second_ack = self.waitForAck(timeout=0.5)
        self.connected = False

        return (first_ack & second_ack)


    def cmdGoToAddress(self, address):
        """! send the command to Go To an address and execute
             note - read protection should be disabled
            @param address  The address to go to
            @return True on success
         """
        commands = bytearray([
            STM_CMD_GO,
            getByteComplement(STM_CMD_GO),
        ])

        address_bytes = self.addressToBytes(address)
        address_bytes = self.appendChecksum(address_bytes)

        success = self.writeAndWaitAck(commands)

        if success:
            success = self.writeAndWaitAck(address_bytes)

        ## we are no longer connected to the bootloader
        self.connected = False

        return success

