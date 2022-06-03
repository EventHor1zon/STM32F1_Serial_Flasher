from STM32F1_Serial_Flasher.SerialFlasher.SerialFlasher import SerialTool
from .constants import *
from .errors import *
from .devices import DeviceDensity 

class StmDeviceObject:
    """ The device object should:
        - describe the connected device
        - keep track of the device information retrieved
        - provide higher level interface to the device
        - allow reading/writing of specific sections
        - translate device areas into specific memory addresses
        - lock/unlock flash sections
    """
    

    def __init__(self, serialTool = None):
        self.connected = False
        self.validCmds = []
        self.bootLoaderVersion = None
        self.deviceId = None
        self.productId = None
        self.serialTool = None if serialTool is None else serialTool
        self.connected = False if serialTool is None else serialTool.getConnectedState()

    @staticmethod
    def checkValidWriteAddress(address):
        pass

    @staticmethod
    def checkValidReadAddress(address):
        pass

    def densityFromFlashMemorySize(self, memory):
        if memory > 16000 and memory < 64000:
            return DeviceDensity.DEVICE_TYPE_LOW_DENSITY
        elif memory > 64000 and memory < 256000:
            return DeviceDensity.DEVICE_TYPE_MEDIUM_DENSITY
        elif memory > 256000 and memory < 768000:
            return DeviceDensity.DEVICE_TYPE_HIGH_DENSITY
        elif memory > 768000:
            return DeviceDensity.DEVICE_TYPE_XL_DENSITY
        else:
            return None

    def updateFromGETrsp(self, data: bytearray):
        self.bootloader_version = data[2]
        self.valid_cmds = data[3:13]

    def updateFromIDrsp(self, data: bytearray):
        pid_msb = data[2]
        pid_lsb = data[3]
        self.device_id = (pid_msb << 8) | pid_lsb

    def connectToDevice(self, port: str, baud: int = 9600):
        if self.serialTool == None:
            self.serialTool = SerialTool(
                port=port,
                baud=baud
            )
        self.connected = True
        return self.serialTool.connect()

    def unpackDeviceInfo(self, id, info):
        self.bootLoaderVersion = ".".join([c for c in str(hex(info[0])).strip("0x")])
        for i in range(1, len(info)):
            #TODO: A better class for commands 
            # - commandFromCode
            self.validCmds.append(info[i])
        self.productId = id[0]
        self.deviceId = id[1]

    def getMapFromId(self):
        return None


    def collectDeviceDetails(self):
        """ collects the objects device characteristics 
            NOTE: probably shouldn't have so many exceptions here?
            TODO: Google when to use exceptions
        """
        if not self.connected:
            raise DeviceNotConnectedError("Device connection not started")

        success, id = self.serialTool.cmdGetId()

        if not success:
            raise CommandFailedError("GetId Command failed")

        success, info = self.serialTool.cmdGetInfo()

        if not success:
            raise CommandFailedError("GetInfo Command failed")

        success = self.unpackDeviceInfo(self, id, info)
        
        if not success:
            raise UnpackInfoFailedError("Error unpacking the device info")

        self.registerMap = self.getMapFromId()

        return True


    def getDeviceBootloaderVersion(self):
        if self.device_info == None or self.bootloader_read == False:
            raise InformationNotRetrieved("Bootloader version not read yet")
        else:
            return self.device_info.bootloader_version

    def getDeviceValidCommands(self):
        if self.device_info == None or self.valid_cmds_read == False:
            raise InformationNotRetrieved("Valid commands have not been read yet")
        else:
            return self.device_info.valid_cmds

    def getDeviceId(self):
        if self.device_info == None or self.device_id_read == False:
            raise InformationNotRetrieved("Device ID has not been read yet")
        else:
            return self.device_info.device_id



    def readOptionBytes(self):
        pass
