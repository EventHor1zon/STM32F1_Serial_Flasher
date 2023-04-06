"""
 file  serialtool.py
 Description: Python module creates an object with methods for
 interacting with the STM32 F1 line of microcontrollers via the
 Bootloader's serial interface.
"""

from time import sleep
import sys
from serial import Serial, SerialTimeoutException, SerialException, PARITY_EVEN
from .constants import *
from .errors import (
    InvalidReadLengthError,
    InvalidResponseLengthError,
    AckNotReceivedError,
    InvalidWriteLengthError,
    NoResponseError,
    UnexpectedResponseError,
    InvalidEraseLengthError,
)
from .utilities import getByteComplement


class SerialTool:
    """SerialTool
    This class should:
    - provide access to the underlying PySerial object
    - send and receive bootloader commands
    - provide functions to read/write data to memory addresses
    - contain various utility functions for use in device commands
    - handle handshake & initial serial connection
    - return the bytearrays read from the device

    """

    connected = False

    # =========== UTILITY FUNCTIONS =========#

    @staticmethod
    def validBaud(baud: int) -> bool:
        """staticmethod to check validity of connection baudrate

        Args:
            baud (int): baudrate
        """
        return baud < 115200 and baud > 1200

    @staticmethod
    def appendChecksum(data: bytearray) -> bytearray:
        chk = 0
        for b in data:
            chk ^= b
        data.append(chk)
        return data

    @staticmethod
    def addressToBytes(address: int) -> bytearray:
        """return address as bytearray, MSB first"""
        return bytearray(
            [
                ((address >> 24) & 0xFF),
                ((address >> 16) & 0xFF),
                ((address >> 8) & 0xFF),
                (address & 0xFF),
            ]
        )

    def reset(self):
        """!
        reset the device with
        """
        print("Resetting device via DTR pin")
        self.serial.setDTR(1)
        sleep(0.001)
        self.serial.setDTR(0)

    def __init__(self, port=None, baud: int = 9600, serial: Serial = None):
        """the contructor for SerialTool

        Args:
            port (str, optional): serial port to connect to. Defaults to None.
            baud (int, optional): baudrate to connect with. Defaults to 9600.
            serial (Serial, optional): user can supply a configured pyserial Serial object for more
            granular control of the interface. If the Serial object is not supplied then
            the port __must__ be supplied. Defaults to None.

        Raises:
            TypeError: Must supply a serial port OR a configured Serial object
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

    # ============ GETTERS/SETTERS ============#

    def getBaud(self) -> int:
        """return the baud rate of the serial object

        Returns:
            int -- baud rate
        """
        return self.baud

    def setBaud(self, baud: int) -> bool:
        """set the baud rate

        Arguments:
            baud {int} -- See README for min/max

        Raises:
            ValueError: on invalid baud

        Returns:
            bool -- success
        """
        if self.connected == True:
            return False
        elif not self.validBaud(baud):
            raise ValueError("Baud rate max: 115200bps, min: 1200bps")
        else:
            self.serial.baudrate = baud
        return True

    def getPort(self) -> str:
        """returns the configured serial port
        Returns:
            str -- port
        """
        return self.serial.port

    def setSerialReadWriteTimeout(self, timeout: float):
        """Set the serial timeout value

        Args:
            timeout (float): timeout in seconds
        """
        self.serial.timeout = timeout
        self.serial.write_timeout = timeout

    def getSerialTimeout(self) -> float:
        """get the serial timeout

        Returns:
            timeout (float): timeout of the serial object
        """
        return self.serial.timeout

    def getSerialState(self):
        """get the serial state

        Returns:
            bool: serial open state
        """
        return self.serial.is_open

    def getConnectedState(self):
        """get the connected state

        Returns:
            bool: device connected state
        """
        return self.connected

    # ============= Serial Interaction =========#

    def writeDevice(self, data: bytearray) -> bool:
        """write bytes over the serial interface

        Args:
            data (bytearray): data to send

        Returns:
            bool: success
        """
        tx = self.serial.write(data)
        if tx != len(data):
            return False
        return True

    def readDevice(self, length: int) -> tuple:
        """attempt to read length bytes from the
            serial interface
        Args:
            length (int): number of bytes to read

        Returns:
            tuple: (bool Success, bytearray Recevied data)
        """
        rx = self.serial.read(length)
        return (len(rx) == length), rx

    def writeAndWaitAck(self, data: bytearray) -> bool:
        """Write data to the device and await a single
           acknowledge byte

        Args:
            data (bytearray): data to send

        Returns:
            bool: Success
        """
        success = self.writeDevice(data)
        if success:
            success = self.waitForAck()
        return success

    def waitForAck(self, timeout: float = 1.0) -> bool:
        """wait for an ack packet - this function is syncronous
        and uses the timeout set by the user if no timeout is already
        configured

        TODO: Why return a success if raising errors? Smarter approach rqd

        Args:
            timeout (float, optional): timeout in seconds. Defaults to 1.0.

        Raises:
            NoResponseError: No response received before timeout
            UnexpectedResponseError: Data returned was not recognised

        Returns:
            bool: Success
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
            raise UnexpectedResponseError(
                f"Invalid response byte received: {hex(rx[0])}"
            )

    # ============== Device Interaction =========#

    def connect(self) -> bool:
        """connect to the STM chip bootloader by sending the
        handshake byte

        Returns:
            bool: Success
        """
        success = self.writeAndWaitAck(bytearray([STM_CMD_HANDSHAKE]))
        if success:
            self.connected = True
        return success

    def disconnect(self) -> None:
        """close the serial socket"""
        self.serial.close()
        self.connected = False

    def reconnect(self) -> bool:
        """Disconnect and reconnect to the device
        (useful after commands which cause reset)

        Returns:
            bool: Success
        """
        self.disconnect()
        sleep(0.1)
        self.serial.open()
        return self.connect()

    # =============== DEVICE COMMANDS ==========#

    def writeCommand(self, data: bytearray, length: int) -> tuple:
        """Write a command to the device

            TODO: length is a bit weird here, remove & get the expected length
                  from the first byte of command?

        Args:
            data (bytearray): the command & any arguments, plus checksum byte
            length (int): expected length of the response

        Raises:
            InvalidResponseLengthError: Invalid response length

        Returns:
            tuple: (bool Success, bytearray received data)
        """
        rx = bytearray()

        success = self.writeAndWaitAck(data)

        if success:
            # read the response length byte
            success, rx = self.readDevice(STM_RSP_LEN_BYTE)

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

    def cmdGetId(self) -> tuple:
        """Send the ID command

        Returns:
            tuple: (bool Success, bytearray Rx data)
        """
        id_command = bytearray([STM_CMD_GET_ID, getByteComplement(STM_CMD_GET_ID)])
        return self.writeCommand(id_command, STM_GET_ID_RSP_LEN)

    def cmdGetInfo(self) -> tuple:
        """Send the Info command

        Returns:
            tuple: (bool Success, bytearray received data)
        """
        get_commands = bytearray(
            [
                STM_CMD_GET,
                getByteComplement(STM_CMD_GET),
            ]
        )
        return self.writeCommand(get_commands, STM_RSP_GET_LEN)

    def cmdGetVersionProt(self) -> tuple:
        """Get the device's bootloader protocol version
        this command is structured differently, presumably for backwards
        compatibility. Likely better to use the GetInfo command unless the
        option(al?) bytes are specifically required

        Returns:
             tuple: (bool Success, bytearray received data)
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

    def cmdReadFromMemoryAddress(self, address: int, length: int) -> tuple:
        """Send the read memory command

        Args:
            address (int): address to read from
            length (int): number of bytes to read

        Raises:
            InvalidReadLengthError: an invalid number of bytes was requested

        Returns:
            tuple: (bool Success, bytearray received data)
        """
        # check read length
        if length > 255 or length < 1:
            raise InvalidReadLengthError("Read length must be > 0 and < 256 bytes")

        # read command bytes
        commands = bytearray(
            [
                STM_CMD_READ_MEM,
                getByteComplement(STM_CMD_READ_MEM),
            ]
        )

        # initialise rx as empty bytearray
        rx = bytearray()

        # address bytes
        address_bytes = self.addressToBytes(address)
        address_bytes = self.appendChecksum(address_bytes)
        # length bytes
        length_bytes = bytearray(
            [
                length - 1,
                getByteComplement(length - 1),
            ]
        )

        # write the command, address & length to the device
        success = self.writeAndWaitAck(commands)

        if success:
            success = self.writeAndWaitAck(address_bytes)

        if success:
            success = self.writeAndWaitAck(length_bytes)

        if success:
            success, rx = self.readDevice(length)

        return success, rx

    def cmdWriteToMemoryAddress(self, address: int, data: bytearray) -> tuple:
        """Send the Write to memory command

        Args:
            address (int): address to write to
            data (bytearray): the data to write

        Raises:
            InvalidWriteLengthError: An invalid write length was requested
            NoResponseError: No response was received from the device - this can occur
            if the user requests a write to a disallowed or locked address. See readme.

        Returns:
            tuple: (bool Success, bytearray received data)
        """
        if len(data) > 256 or len(data) < 1:
            raise InvalidWriteLengthError(f"Invalid length: {len(data)}")

        if len(data) % 4 > 0:
            raise InvalidWriteLengthError("Must be a multiple of 4 bytes")

        commands = bytearray(
            [
                STM_CMD_WRITE_MEM,
                getByteComplement(STM_CMD_WRITE_MEM),
            ]
        )

        # address bytes
        address_bytes = self.addressToBytes(address)
        address_bytes = self.appendChecksum(address_bytes)

        # write the length (N) and N+1 (????) data bytes and Checksum^N
        tx_data = bytearray([len(data) - 1])
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

    def cmdEraseFlashMemoryPages(self, pages: bytearray) -> bool:
        """Send the erase flash memory command with a list of pages. This
            command will cause the device to reset

        Args:
            pages (bytearray): pages to erase

        Raises:
            InvalidEraseLengthError: length of page array too large

        Returns:
            bool: Success
        """
        if len(pages) < 1 or len(pages) > 256:
            raise InvalidEraseLengthError

        commands = bytearray(
            [
                STM_CMD_ERASE_MEM,
                getByteComplement(STM_CMD_ERASE_MEM),
            ]
        )

        tx_data = bytearray(
            [
                len(pages) - 1,
            ]
        )
        tx_data += pages
        tx_data = self.appendChecksum(tx_data)

        success = self.writeAndWaitAck(commands)

        if success:
            success = self.writeAndWaitAck(tx_data)

        return success

    def cmdEraseFlashMemory(self) -> bool:
        """send the command to erase all flash memory pages

        Returns:
            bool: Success
        """
        commands = bytearray(
            [
                STM_CMD_ERASE_MEM,
                getByteComplement(STM_CMD_ERASE_MEM),
            ]
        )

        tx_data = bytearray(
            [
                0xFF,
                getByteComplement(0xFF),
            ]
        )

        success = self.writeAndWaitAck(commands)

        if success:
            success = self.writeAndWaitAck(tx_data)

        return success

    def cmdWriteProtect(self, sectors: bytearray) -> bool:
        """send the bootloader command to write-protect the flash
        memory. This command resets the device, disconnecting it.

        Args:
            sectors (bytearray): flash page sectors to write-protect. See the
                device's datasheet or STM32F10XXX Flash Programming Manual for details

        Returns:
            bool: Success
        """
        if len(sectors) < 1 or len(sectors) > 256:
            raise InvalidWriteLengthError("Invalid sector length")

        commands = bytearray(
            [
                STM_CMD_WRITE_PROTECT_EN,
                getByteComplement(STM_CMD_WRITE_PROTECT_EN),
            ]
        )

        tx_data = bytearray(
            [
                len(sectors) - 1,
            ]
        )
        tx_data += sectors
        tx_data = self.appendChecksum(tx_data)

        success = self.writeAndWaitAck(commands)

        if success:
            success = self.writeAndWaitAck(tx_data)

        # once the write protect command is complete, the device
        # resets, so set connected to false
        if success:
            self.connected = False

        return success

    def cmdWriteUnprotect(self) -> bool:
        """Send the command to disable write protection on the flash. This
            Command will cause the device to reset

        Returns:
            bool: Success
        """
        commands = bytearray(
            [
                STM_CMD_WRITE_PROTECT_DIS,
                getByteComplement(STM_CMD_WRITE_PROTECT_DIS),
            ]
        )

        first_ack = self.writeAndWaitAck(commands)

        second_ack = self.waitForAck()
        self.connected = False

        return first_ack & second_ack

    def cmdReadoutProtect(self) -> bool:
        """Send the readout protect command, protecting the flash memory from read
        access. This command will cause a device reset

        Returns:
            bool: Success
        """
        commands = bytearray(
            [
                STM_CMD_READOUT_PROTECT_EN,
                getByteComplement(STM_CMD_READOUT_PROTECT_EN),
            ]
        )

        first_ack = self.writeAndWaitAck(commands)

        second_ack = self.waitForAck()
        self.connected = False

        return first_ack & second_ack

    def cmdReadoutUnprotect(self) -> bool:
        """Send the commmand to disable readout protect on the flash memory. This
            This command will cause a device reset

        Returns:
            bool: Success
        """
        commands = bytearray(
            [
                STM_CMD_READOUT_PROTECT_DIS,
                getByteComplement(STM_CMD_READOUT_PROTECT_DIS),
            ]
        )

        success = self.writeDevice(commands)

        if success:
            first_ack = self.waitForAck()
            second_ack = self.waitForAck(timeout=0.5)
        self.connected = False

        return first_ack & second_ack

    def cmdGoToAddress(self, address: int) -> bool:
        """send the Go command with associated memory address. This command
        will finish the bootloader's interaction with this driver, however serial bytes
        can still be exchanged if the device application enables uart1.

        Args:
            address (int): address to go to

        Returns:
            bool: Success
        """
        commands = bytearray(
            [
                STM_CMD_GO,
                getByteComplement(STM_CMD_GO),
            ]
        )

        address_bytes = self.addressToBytes(address)
        address_bytes = self.appendChecksum(address_bytes)

        success = self.writeAndWaitAck(commands)

        if success:
            success = self.writeAndWaitAck(address_bytes)

        # we are no longer connected to the bootloader
        if success:
            self.connected = False

        return success
