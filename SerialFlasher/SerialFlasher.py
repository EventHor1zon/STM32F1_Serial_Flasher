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
import sys
from serial import Serial, SerialTimeoutException, SerialException, PARITY_EVEN
import binascii
from SerialFlasher.constants import *

## SerialFlasher Class
#   This class represents the object used to interface
#   with the microcontroller.
#
#   methods:
#
#   @param serial_port  - the name of the serial port to connect over
#   @param baud         - baud rate of connection. Use common rates, 1200 - 115200 inclusive.


class DeviceInformation():
    bootloader_version: int
    valid_cmds: list
    device_id: int

    def __init__(self, bl_version: int=None, valid_cmds: list=None, dev_id: int=None):
        self.bootloader_version = bl_version
        self.valid_cmds = valid_cmds
        self.device_id = dev_id

    def updateFromGETrsp(self, data: bytearray):
        self.bootloader_version = data[2]
        self.valid_cmds = data[3:13]
    
    def updateFromIDrsp(self, data: bytearray):
        pid_msb = data[2]
        pid_lsb = data[3]
        self.device_id = ((pid_msb << 8) | pid_lsb)

    def getBootloaderVersion(self):
        return self.bootloader_version

    def getValidCommands(self):
        return self.valid_cmds
    
    def getDeviceId(self):
        return self.device_id

class InformationNotRetrieved(Exception):
    pass


class SerialTool:

    connected = False
    device_id_read = False
    bootloader_read = False
    valid_cmds_read = False

    device_info = None

    @staticmethod
    def checkBaudValid(baud):
        pass

    @staticmethod
    def crcXorByte(bytes):
        return sum(bytes) ^ 0xFF


    def __init__(self, port=None, baud: int = 9600, serial: Serial = None):
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

    def unpackDeviceInfo(self, get_rx: bytearray, id_rx:bytearray):
        """ populate device information from a 'GET' command response 
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
            d_id = ((id_rx[2] << 8) | id_rx[3])

            ## create device information object
            self.device_info = DeviceInformation(
                bl_version=bl_v,
                valid_cmds=v_cmds,
                dev_id=d_id
            )
            ## set read successes
            self.device_id_read = True
            self.bootloader_read = True
            self.valid_cmds_read = True
            success = True
        return success


    def getBaud(self):
        return self.baud


    def setBaud(self, baud: int):
        if self.connected == True:
            return False
        elif baud > 115200 or baud < 1200:
            raise ValueError("Baud rate max: 115200bps, min: 1200bps")
        else:
            self.serial.baudrate = baud
        return True

    def getPort(self):
        return self.serial.port

    def setSerialReadWriteTimeout(self, timeout: float):
        """ set timeout for read/write serial operations """
        self.serial.timeout = timeout
        self.serial.write_timeout = timeout

    def getSerialTimeout(self):
        return self.serial.timeout

    def getSerialState(self):
        """get serial state"""
        return self.serial.is_open

    def getConnectedState(self):
        """get the connected state"""
        return self.connected

    def writeDevice(self, data: bytearray):
        """write data to the device
        this should be a staticmethod?
        """
        tx = self.serial.write(data)
        if tx != len(data):
            return False
        return True

    def readDevice(self, length):
        """attempt to read len bytes from the device
        return read_len, bytes
        """
        rx = self.serial.read(length)
        return (len(rx) == length), rx

    def connect(self):
        """connect to the STM chip"""
        self.writeDevice(bytearray([STM_CMD_HANDSHAKE]))
        success, data = self.readDevice(1)
        if not success:
            return False
        elif data[0] != STM_CMD_ACK:
            return False
        else:
            self.connected = True
            return True

    def disconnect(self):
        """close the socket"""
        self.serial.close()
        self.connected = False

    def readDeviceInfo(self):
        """read the device information using the
        GET and GET_ID commands
        """
        
        success, get_rx = self.cmdGetInfo()
        if success:
            success, id_rx = self.cmdGetId()

        if success:
            success = self.unpackDeviceInfo(get_rx, id_rx)
        
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


    def cmdGetId(self):
        id_rx = None
        id_commands = bytearray([
            STM_CMD_GET_ID,
            self.crcXorByte([STM_CMD_GET_ID]),
        ])
        success = self.writeDevice(id_commands) 

        if success:
            success, id_rx = self.readDevice(STM_GET_ID_RSP_LEN)
        
        return success, id_rx

    def cmdGetInfo(self):
        """get the device information"""
        get_rx = None
        get_commands = bytearray(
            [
                STM_CMD_GET,
                self.crcXorByte([STM_CMD_GET]),
            ]
        )
        success = self.writeDevice(get_commands)
        if success:
            success, get_rx = self.readDevice(STM_RSP_GET_LEN)
        
        return success, get_rx

    def cmdGetVersionProt(self):
        """get the device's bootloader protocol version"""
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
