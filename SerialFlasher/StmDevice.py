from ctypes import Union
from .SerialFlasher import SerialTool
from .utilities import unpack16BitInt
from .constants import *
from .errors import *
from .devices import DeviceDensity, DeviceType
from struct import unpack
from time import sleep

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
        self.serialTool = None if serialTool is None else serialTool
        self.connected = False if serialTool is None else serialTool.getConnectedState()
        self.device = None

    def unpackBootloaderVersion(self, value: bytes) -> float:
        return float(".".join([c for c in str(hex(value[0])).strip("0x")]))

    def connectToDevice(self, port: str, baud: int = 9600):
        if self.serialTool is None:
            self.serialTool = SerialTool(
                port=port,
                baud=baud
            )
        sleep(0.01)
        self.connected = self.serialTool.connect()
        return self.connected

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

    def readOptionBytes(self):
        """ reads the flash option bytes and updates the device model's 
            data
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

    def writeToOptionBytes(self, data: bytearray) -> bool:
        pass
        
    def getDeviceBootloaderVersion(self) -> float:
        """ get the bootloader version as a float """
        if self.device == None:
            raise InformationNotRetrieved("Bootloader version not read yet")
        return self.device.bootloaderVersion

    def getDeviceId(self) -> int:
        """ get the device id as an int """
        if self.device == None:
            raise InformationNotRetrieved("Device ID has not been read yet")
        return self.device.pid

    def _readFromMem(self, address: int, length: int):
        """ read from memory address - does not sanitize, see
            methods readFromRam/Flash
        """
        master_rx = bytearray()

        # max read length is 256 so do larger reads in multiples
        full_reads = int(length / 256)
        rem = length % 256

        for i in range(full_reads):
            success, rx = self.serialTool.cmdReadFromMemoryAddress(address + (i * 256), 256)
            if not success:
                raise InvalidResponseLengthError(f"Invalid status")
            master_rx += rx
        if rem > 0:
            success, rx = self.serialTool.cmdReadFromMemoryAddress((address + (full_reads * 256)), rem)
            if not success:
                raise InvalidResponseLengthError(f"Invalid status")
            master_rx += rx
        return master_rx

    def _writeToMem(self, address, data):
        # max write length is 256 so do larger writes in multiples
        length = len(data)
        full_writes = int(length / 256)
        rem = length % 256

        for i in range(full_writes):
            success = self.serialTool.cmdWriteToMemoryAddress(address + (i * 256), data[(i * 256):(i+1 * 256)])
            if not success:
                raise InvalidResponseLengthError(f"Invalid status")
        if rem > 0:
            success = self.serialTool.cmdWriteToMemoryAddress((address + (full_writes * 256)), data[(full_writes * 256): rem])
            if not success:
                raise InvalidResponseLengthError(f"Invalid status")
        return success

    def readFromRam(self, address: int, length: int):
        """ read length bytes from address in ram """
        if not self.device.ram.is_valid(address):
            raise InvalidAddressError(f"Address {hex(address)} is out of range ({hex(self.device.ram.start)} - {hex(self.device.ram.end-1)}")
        if not self.device.ram.is_valid(address + length):
            raise InvalidReadLengthError(f"Read would go out of bounds")
        if length % 4 > 0:
            # only allow 4-byte reads
            raise InvalidReadLengthError("Read length should be multiple of 4 bytes")
        return self._readFromMem(address, length)


    def writeToRam(self, address: int, data: bytearray) -> bool:
        """ write to an address in ram """
        if not self.device.ram.is_valid(address):
            raise InvalidAddressError(f"Address {hex(address)} is out of range ({hex(self.device.ram.start)} - {hex(self.device.ram.end-1)}")
        if not self.device.ram.is_valid(address + len(data)):
            raise InvalidWriteLengthError(f"Read would go out of bounds")
        if len(data) % 4 > 0:
            # only allow 4-byte reads
            raise InvalidWriteLengthError("Write length should be multiple of 4 bytes")
        return self._writeToMem(address, data)

    def writeToFlash(self, address: int, data: bytearray) -> bool:
        pass

    def eraseFlash(self):
        pass

    def writeApplicationFileToFlash(self, path: str) -> bool:
        pass


