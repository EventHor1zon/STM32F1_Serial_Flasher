from .constants import *
from .errors import *


class StmDeviceObject:
    """ The device object should:
        - describe the connected device
        - keep track of the device information retrieved
        - provide higher level interface to the device
        - allow reading/writing of specific sections
        - translate device areas into specific memory addresses
    """

    def __init__(
        self, bl_version: int = None, valid_cmds: list = None, dev_id: int = None
    ):
        self.bootloader_version = bl_version
        self.valid_cmds = valid_cmds
        self.device_id = dev_id


    @staticmethod
    def checkValidWriteAddress(address):
        pass

    @staticmethod
    def checkValidReadAddress(address):
        pass

    def updateFromGETrsp(self, data: bytearray):
        self.bootloader_version = data[2]
        self.valid_cmds = data[3:13]

    def updateFromIDrsp(self, data: bytearray):
        pid_msb = data[2]
        pid_lsb = data[3]
        self.device_id = (pid_msb << 8) | pid_lsb

    def getBootloaderVersion(self):
        return self.bootloader_version

    def getValidCommands(self):
        return self.valid_cmds

    def getDeviceId(self):
        return self.device_id

    def unpackDeviceInfo(self, get_rx: bytearray, id_rx: bytearray):
        """
            # TODO - delete & redo
            populate device information from a 'GET' command response 
            and ID commands response
            bytes: 0 - ACK
                    1 - N (11)
                    2 - BL Vers (0 - 255)
                    3 - cmd (0)
                    4 - cmd (1)
                    ...
                    -1 - ACK
        """
        success = False

        ## check acks in both packets
        if get_rx[0] != STM_CMD_ACK:
            print("Invalid Device info byte 1")
        elif get_rx[-1] != STM_CMD_ACK:
            print("Invalid device info byte 15")
        elif id_rx[0] != STM_CMD_ACK:
            print("Invalid device id byte 0")
        elif id_rx[4] != STM_CMD_ACK:
            print("Invalid device id byte 4")
        else:
            ## unpack values 
            bl_v = get_rx[1]
            v_cmds = list(get_rx[3:14])
            d_id = (id_rx[2] << 8) | id_rx[3]

            success = True
        return success

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


    def readDeviceInfo(self):
        """
            read the device information using the
            GET and GET_ID commands
        """

        success, get_rx = self.cmdGetInfo()
        if success:
            success, id_rx = self.cmdGetId()

        if success:
            success = self.unpackDeviceInfo(get_rx, id_rx)

        return success

    def readOptionBytes(self):
        pass
