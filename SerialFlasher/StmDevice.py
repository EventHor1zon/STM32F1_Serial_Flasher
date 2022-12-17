from struct import unpack
from time import sleep
from .utilities import unpack16BitInt
from .constants import *
from .errors import *
from .devices import DeviceDensity, DeviceType
from .SerialFlasher import SerialTool


class STMInterface:
    """ The device object should:
        - describe the connected device
        - keep track of the device information retrieved
        - provide higher level interface to the device
        - allow reading/writing of specific sections
        - translate device areas into specific memory addresses
        - lock/unlock flash sections
    """

    def __init__(self, serialTool: SerialTool = None):
        self.connected = False
        self.serialTool = serialTool
        self.connected = False if serialTool is None else serialTool.getConnectedState()
        self.device = None


    def buildOptionBytesFromDict(self, data: dict) -> bytearray:
        """ not sure if I need this """
        pass

    def unpackBootloaderVersion(self, value: bytes) -> float:
        return float(".".join([c for c in str(hex(value[0])).strip("0x")]))

    def connectToDevice(self, port: str = "", baud: int = 9600) -> bool:
        """! Connect to the device over serial 
            @param port - the port to connect to
            @param baud - the baud rate to connect at
            @return True on success
        """
        if self.serialTool is None:
            if len(port) < 1:
                raise ValueError("Must supply port if no SerialTool initialised")
            self.serialTool = SerialTool(port=port, baud=baud)
        sleep(0.01)
        self.connected = self.serialTool.connect()
        return self.connected

    def connectAndReadInfo(self, port: str="", baud: int=9600, readOptBytes: bool=False):
        success = self.connectToDevice(port, baud)

        if success:
            ## clear the device info if it exists
            if self.device is not None:
                self.device = None
            self.readDeviceInfo()

        if success and readOptBytes:
            success = self.readOptionBytes()

        return success

    def readDeviceInfo(self):
        """ collects the object's id and bootloader version
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
        """ get the bootloader version as a float """
        if not self.device:
            raise InformationNotRetrieved("Bootloader version not read yet, call self.readDeviceInfo first")
        return self.device.bootloaderVersion


    def getDeviceId(self) -> int:
        """ get the device id as an int """
        if not self.device:
            raise InformationNotRetrieved("Device ID has not been read yet, call self.readDeviceInfo first")
        return self.device.pid


    def readOptionBytes(self):
        """ reads the flash option bytes and updates the device model's 
            data
        """
        if not self.connected:
            raise DeviceNotConnectedError

        success, rx = self.serialTool.cmdReadFromMemoryAddress(
            self.device.flash_option_bytes.start, 16,
        )

        if success:
            if self.device is not None:
                try:
                    self.device.updateOptionBytes(rx)
                except:
                    success = False

        return success



    def writeToOptionBytes(self, data: bytearray, reconnect: bool = False) -> bool:
        """! write data to the option bytes register. This operation causes a
             device reset to apply changes.
            @param data - The data to write, must be 16 bytes
            @reconnect - reconnect to the device after reset 
        """
        if len(data) != 16:
            raise InvalidWriteLengthError("Option byte data must be exactly 16 bytes")
        if self.device is None:
            raise InformationNotRetrieved("Must read device type first")

        print(f"Writing to option bytes start address: {hex(self.device.flash_option_bytes.start)}")
        success = self._writeToMem(self.device.flash_option_bytes.start, data)

        print(f"Write success {success}")

        if success:
            self.connected = False

        if not self.connected and reconnect:
            self.connected = self.serialTool.reconnect()

        return success


    def readUnprotectFlashMemory(self):
        success = self.serialTool.cmdReadoutUnprotect()
        sleep(0.1)
        self.connected = self.serialTool.reconnect()
        return success


    def readProtectFlashMemory(self):
        success = self.serialTool.cmdReadoutProtect()
        sleep(0.1)
        self.connected = self.serialTool.reconnect()
        return success


    def writeUnprotectFlashMemory(self):
        success = self.serialTool.cmdWriteUnprotect()
        sleep(0.1)
        self.connected = self.serialTool.reconnect()
        return success


    def writeProtectFlashMemory(self):
        success = self.serialTool.cmdWriteProtect()
        sleep(0.1)
        self.connected = self.serialTool.reconnect()
        return success


    def _readFromMem(self, address: int, length: int):
        """ read from memory address - does not sanitize, see
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
        # max write length is 256 so do larger writes in multiples
        length = len(data)
        full_writes = int(length / 256)
        rem = length % 256

        for i in range(full_writes):
            success = self.serialTool.cmdWriteToMemoryAddress(
                address + (i * 256), data[(i * 256) : ((i + 1) * 256)]
            )
            if not success:
                raise InvalidResponseLengthError("Invalid status")
        if rem > 0:
            success = self.serialTool.cmdWriteToMemoryAddress(
                (address + (full_writes * 256)), data[(full_writes * 256) : rem]
            )
            if not success:
                raise InvalidResponseLengthError(f"Invalid status")
        return success


    def readFromRam(self, address: int, length: int):
        """ read length bytes from address in ram """
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
        """ write to an address in ram """
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
        """! write the data to an address in flash memory """
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
                f"Write would go out of bounds ({hex(self.device.ram.start)} - {hex(self.device.ram.end-1)}"
            )
        if len(data) % 4 > 0:
            raise InvalidWriteLengthError("Write length should be multiple of 4 bytes")

        return self._writeToMem(address, data)


    def globalEraseFlash(self):
        """! Erase all of the flash pages 
            @return True on success else false
        """
        return self.serialTool.cmdEraseFlashMemory()



    def writeApplicationFileToFlash(self, path: str) -> bool:
        """! write a binary application to flash memory
            rely on the file io exception if invalid file
            @param path - the path to the file application
            @return success True|False
        """
        success = False

        if self.device is None:
            raise InformationNotRetrieved
        with open(path, "rb") as fp:
            content = fp.read()
            success = self.writeToFlash(self.device.flash_memory.start, bytearray(content))

        return success

