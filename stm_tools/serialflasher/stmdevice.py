from struct import unpack
from time import sleep
from .utilities import unpack16BitInt
from .constants import *
from .errors import *
from .devices import DeviceDensity, DeviceType
from .SerialFlasher import SerialTool


class STMInterface:
    """The device object should:
    - describe the connected device
    - keep track of the device information retrieved
    - provide higher level interface to the device
    - allow reading/writing of specific sections
    - translate device areas into specific memory addresses
    - lock/unlock flash sections
    """

    def __init__(self, serialTool: SerialTool = None):
        """constructor

        Args:
            serialTool (SerialTool, optional): user-configured SerialTool object. Defaults to None.
        """
        self.connected = False
        self.serialTool = serialTool
        self.connected = False if serialTool is None else serialTool.getConnectedState()
        self.device = None

    def buildOptionBytesFromDict(self, data: dict) -> bytearray:
        """not sure if I need this"""
        pass

    def unpackBootloaderVersion(self, value: bytes) -> float:
        """unpacks the bootloader version from the supplied byte data

        Args:
            value (bytes): bytes received from id command

        Returns:
            float: the bootloader version
        """
        return float(".".join([c for c in str(hex(value[0])).strip("0x")]))

    def connectToDevice(self, port: str = "", baud: int = 9600) -> bool:
        """Connect to the device at the given port/baud rate

        Args:
            port (str, optional): Serial port to connect to. Defaults to "".
            baud (int, optional): Baudrate to connect at. Defaults to 9600.

        Raises:
            ValueError: Port OR SerialTool object required

        Returns:
            bool: Success
        """
        if self.serialTool is None:
            if len(port) < 1:
                raise ValueError("Must supply port if no SerialTool initialised")
            self.serialTool = SerialTool(port=port, baud=baud)
        sleep(0.01)
        self.connected = self.serialTool.connect()
        return self.connected

    def connectAndReadInfo(
        self, port: str = "", baud: int = 9600, readOptBytes: bool = False
    ) -> bool:
        """Connect to the device and retrieve the device information

        Args:
            port (str, optional): Port to connect to. Defaults to "".
            baud (int, optional): Baud rate to connect at. Defaults to 9600.
            readOptBytes (bool, optional): Read the option-bytes from the device. Defaults to False.

        Returns:
            bool: Success
        """
        success = self.connectToDevice(port, baud)

        if success:
            # clear the device info if it exists
            if self.device is not None:
                self.device = None
            self.readDeviceInfo()

        if success and readOptBytes:
            success = self.readOptionBytes()

        return success

    def readDeviceInfo(self) -> bool:
        """collects the object's id and bootloader version
        and creates a device model from it
        NOTE: probably shouldn't have so many exceptions here?
        Use exceptions for now as this is a fundamental function which
        requires multiple other commands to work in order to build
        Device model
        """
        if not self.connected:
            raise DeviceNotConnectedError("Device connection not started")

        success, id = self.serialTool.cmdGetId()

        if not success:
            raise CommandFailedError("GetId Command failed")

        pid = unpack16BitInt(id)

        success, info = self.serialTool.cmdGetInfo()

        if not success:
            raise CommandFailedError("GetInfo Command failed")

        bl_version = self.unpackBootloaderVersion(info)
        self.device = DeviceType(pid, bl_version)

        return True

    def getDeviceBootloaderVersion(self) -> float:
        """Getter for bootloader version

        Raises:
            InformationNotRetrieved: Bootloader version has not been read

        Returns:
            float: Bootloader version
        """
        if not self.device:
            raise InformationNotRetrieved(
                "Bootloader version not read yet, call self.readDeviceInfo first"
            )
        return self.device.bootloaderVersion

    def getDeviceId(self) -> int:
        """getter for device ID

        Raises:
            InformationNotRetrieved: Device ID not read yet

        Returns:
            int: device ID
        """
        if not self.device:
            raise InformationNotRetrieved(
                "Device ID has not been read yet, call self.readDeviceInfo first"
            )
        return self.device.pid

    def readOptionBytes(self) -> bool:
        """reads the flash option-bytes from the device and creates an
        OptionBytes object from the result

        Raises:
            DeviceNotConnectedError: Device is not connected

        Returns:
            bool: Success
        """
        if not self.connected:
            raise DeviceNotConnectedError

        success, rx = self.serialTool.cmdReadFromMemoryAddress(
            self.device.flash_option_bytes.start,
            16,
        )

        if success:
            if self.device is not None:
                try:
                    self.device.updateOptionBytes(rx)
                except:
                    success = False

        return success

    def writeToOptionBytes(self, data: bytearray, reconnect: bool = False) -> bool:
        """writes data to the device flash option-bytes address. This must be a 16-byte write
        meeting certain conditions - handled by the OptionBytes class. This
        command will cause a device reset to apply the option-bytes settings to the device.
        See the Flash Programming manual for details.

        Args:
            data (bytearray): data bytes to write
            reconnect (bool, optional): Reconnect after the operation. Defaults to False.

        Raises:
            InvalidWriteLengthError: The data length must be 16 bytes
            InformationNotRetrieved: The device type is unknown, read device information first

        Returns:
            bool: Success
        """
        if len(data) != 16:
            raise InvalidWriteLengthError("Option byte data must be exactly 16 bytes")
        if self.device is None:
            raise InformationNotRetrieved("Must read device type first")

        success = self._writeToMem(self.device.flash_option_bytes.start, data)

        if success:
            self.connected = False

        if not self.connected and reconnect:
            self.connected = self.serialTool.reconnect()

        return success

    def readUnprotectFlashMemory(self) -> bool:
        success = self.serialTool.cmdReadoutUnprotect()
        sleep(0.1)
        self.connected = self.serialTool.reconnect()
        return success

    def readProtectFlashMemory(self) -> bool:
        success = self.serialTool.cmdReadoutProtect()
        sleep(0.1)
        self.connected = self.serialTool.reconnect()
        return success

    def writeUnprotectFlashMemory(self) -> bool:
        success = self.serialTool.cmdWriteUnprotect()
        sleep(0.1)
        self.connected = self.serialTool.reconnect()
        return success

    def writeProtectFlashMemory(self) -> bool:
        success = self.serialTool.cmdWriteProtect()
        sleep(0.1)
        self.connected = self.serialTool.reconnect()
        return success

    def _readFromMem(self, address: int, length: int):
        """internal method: read from memory address - does not sanitize, see
        methods readFromRam/Flash
        """
        master_rx = bytearray()
        success = True

        # max read length is 256 so do larger reads in multiples
        full_reads = int(length / 256)
        rem = length % 256

        for i in range(full_reads):
            success, rx = self.serialTool.cmdReadFromMemoryAddress(
                address + (i * 256), 256
            )
            if not success:
                break
            else:
                master_rx += rx
        if rem > 0 and success:
            success, rx = self.serialTool.cmdReadFromMemoryAddress(
                (address + (full_reads * 256)), rem
            )
            if success:
                master_rx += rx

        return success, master_rx

    def _writeToMem(self, address: int, data: bytearray):
        """internal method: write to memory address - does not sanitize, see
        methods writeToRam/Flash
        """
        length = len(data)
        full_writes = int(length / 256)
        rem = length % 256
        success = True

        for i in range(full_writes):
            success = self.serialTool.cmdWriteToMemoryAddress(
                address + (i * 256), data[(i * 256) : ((i + 1) * 256)]
            )
            if not success:
                raise InvalidResponseLengthError("Invalid status")
        if rem > 0:
            success = self.serialTool.cmdWriteToMemoryAddress(
                (address + (full_writes * 256)),
                data[(full_writes * 256) : (full_writes * 256) + rem],
            )
            if not success:
                raise InvalidResponseLengthError(f"Invalid status")
        return success

    def readFromRam(self, address: int, length: int) -> tuple:
        """read bytes from an address in RAM

        Args:
            address (int): address to read from
            length (int): bytes to read

        Raises:
            DeviceNotConnectedError: Device is not connected
            InformationNotRetrieved: Device type is unknown
            InvalidAddressError: Address is not a valid RAM address
            InvalidReadLengthError: Address read length must be multiple of 4 bytes
            InvalidReadLengthError: Read would go out of bounds

        Returns:
            tuple: Success, Recevied data
        """
        if self.connected is False:
            raise DeviceNotConnectedError
        if self.device is None:
            raise InformationNotRetrieved
        if not self.device.ram.is_valid(address):
            raise InvalidAddressError(
                f"Address {hex(address)} is out of range ({hex(self.device.ram.start)} - {hex(self.device.ram.end-1)}"
            )
        if not self.device.ram.is_valid(address + length):
            raise InvalidReadLengthError(f"Read would go out of bounds")
        if length % 4 > 0:
            # only allow 4-byte reads
            raise InvalidReadLengthError("Read length should be multiple of 4 bytes")
        return self._readFromMem(address, length)

    def writeToRam(self, address: int, data: bytearray) -> bool:
        """Write data to an address in RAM

        Args:
            address (int): address to write to
            data (bytearray): data to write

        Returns:
            bool: Success
        """
        if self.connected is False:
            raise DeviceNotConnectedError
        if self.device is None:
            raise InformationNotRetrieved
        if not self.device.ram.is_valid(address):
            raise InvalidAddressError(
                f"Address {hex(address)} is out of range ({hex(self.device.ram.start)} - {hex(self.device.ram.end-1)}"
            )
        if not self.device.ram.is_valid(address + len(data)):
            raise InvalidWriteLengthError(
                f"Write would go out of bounds ({hex(self.device.ram.start)} - {hex(self.device.ram.end-1)}"
            )
        if len(data) % 4 > 0:
            # only allow 4-byte reads
            raise InvalidWriteLengthError("Write length should be multiple of 4 bytes")
        return self._writeToMem(address, data)

    def readFromFlash(self, address: int, length: int):
        """Read data from flash memory

        Args:
            address (int): address to read from
            length (int): bytes to read

        Raises:
            DeviceNotConnectedError: _description_
            InformationNotRetrieved: _description_
            InvalidAddressError: _description_
            InvalidWriteLengthError: _description_
            InvalidReadLengthError: _description_

        Returns:
            tuple: Success, data received
        """
        if self.connected is False:
            raise DeviceNotConnectedError
        if self.device is None:
            raise InformationNotRetrieved
        if not self.device.flash_memory.is_valid(address):
            raise InvalidAddressError(
                f"Address {hex(address)} is out of range ({hex(self.device.ram.start)} - {hex(self.device.ram.end-1)}"
            )
        if not self.device.flash_memory.is_valid(address + length):
            raise InvalidWriteLengthError(
                f"Read would go out of bounds ({hex(self.device.ram.start)} - {hex(self.device.ram.end-1)}"
            )
        if length % 4 > 0:
            raise InvalidReadLengthError("Read length should be multiple of 4 bytes")

        return self._readFromMem(address, length)

    def writeToFlash(self, address: int, data: bytearray) -> bool:
        """Write data to flash memory

        Args:
            address (int): address to write to
            data (bytearray): data to write

        Returns:
            bool: Success
        """
        if self.connected is False:
            raise DeviceNotConnectedError
        if self.device is None:
            raise InformationNotRetrieved
        if not self.device.flash_memory.is_valid(address):
            raise InvalidAddressError(
                f"Address {hex(address)} is out of range ({hex(self.device.flash_memory.start)} - {hex(self.device.flash_memory.end-1)}"
            )
        if not self.device.flash_memory.is_valid(address + len(data)):
            raise InvalidWriteLengthError(
                f"Write would go out of bounds ({hex(self.device.flash_memory.start)} - {hex(self.device.flash_memory.end-1)}"
            )
        if len(data) % 4 > 0:
            raise InvalidWriteLengthError("Write length should be multiple of 4 bytes")

        return self._writeToMem(address, data)

    def globalEraseFlash(self) -> bool:
        """erase all flash pages

        Returns:
            bool: Success
        """
        return self.serialTool.cmdEraseFlashMemory()

    def writeApplicationFileToFlash(self, path: str, offset: int = 0) -> bool:
        """write an application to flash memory

        Args:
            path (str): path to the application file
            offset (int, optional): offset from flash start. Defaults to 0.

        Raises:
            InformationNotRetrieved: Device type unknown

        Returns:
            bool: Success
        """
        success = False

        if self.device is None:
            raise InformationNotRetrieved
        with open(path, "rb") as fp:
            content = fp.read(-1)
            success = self.writeToFlash(
                self.device.flash_memory.start + offset, bytearray(content)
            )

        return success

    def isFlashWriteProtected(self):
        if not self.connected:
            raise DeviceNotConnectedError
        if not self.device:
            raise InformationNotRetrieved
        if self.device.opt_bytes == None:
            raise InformationNotRetrieved
        write_prot = False
        if (
            self.device.opt_bytes.write_protect_0 == 0
            and self.device.opt_bytes.write_protect_1 == 0
            and self.device.opt_bytes.write_protect_2 == 0
            and self.device.opt_bytes.write_protect_3 == 0
        ):
            return True
        else:
            return False

    def isFlashWriteProtected(self):
        if not self.connected:
            raise DeviceNotConnectedError
        if not self.device:
            raise InformationNotRetrieved
        if self.device.opt_bytes == None:
            raise InformationNotRetrieved
        write_prot = False
        if (
            self.device.opt_bytes.write_protect_0 == 0
            and self.device.opt_bytes.write_protect_1 == 0
            and self.device.opt_bytes.write_protect_2 == 0
            and self.device.opt_bytes.write_protect_3 == 0
        ):
            return True
        else:
            return False
