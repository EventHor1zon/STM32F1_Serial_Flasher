from .SerialFlasher import SerialTool
from utilities import unpack16BitInt
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

    def checkValidWriteAddress(address):
        pass

    def checkValidReadAddress(address):
        pass

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
        pass


    # def getDeviceBootloaderVersion(self):
    #     if self.device == None:
    #         raise InformationNotRetrieved("Bootloader version not read yet")
    #     return self.device.bootloaderVersion

    # def getDeviceValidCommands(self):
    #     if self.device == None:
    #         raise InformationNotRetrieved("Valid commands have not been read yet")
    #     return self.device.validCommands

    # def getDeviceId(self):
    #     if self.device == None:
    #         raise InformationNotRetrieved("Device ID has not been read yet")
    #     return self.device.deviceType


    # def writeFlashKeys(self):
    #     if not self.connected:
    #         raise DeviceNotConnectedError
    #     success, rx = self.serialTool.cmdWriteToMemoryAddress(
    #         0x40022004, # flash key reg
            
    #     )


    def writeToRam(self, data):
        pass

    def readOptionBytes(self):
        pass
