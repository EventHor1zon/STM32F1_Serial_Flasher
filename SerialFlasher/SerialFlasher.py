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
from time import sleep
import sys
from serial import Serial, SerialTimeoutException, SerialException, PARITY_EVEN
import binascii
from SerialFlasher.constants import *
from .exceptions import InformationNotRetrieved, InvalidAddressError, InvalidReadLength

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
#
#
#
#
# Memory Area   Write command   Read command    Erase command       Go command
#   Flash           Supported       Supported       Supported       Supported
#   RAM Supported   Supported       Not supported   Supported
#   System Memory   Not supported   Supported       Not supported   Not supported
#   Data Memory     Supported       Supported       Not supported   Not supported
#   OTP Memory      Supported       Supported       Not supported   Not supported



class CheckMemoryResponse(Enum):
    STM_ADDRESS_VALID = 1
    STM_ADDRESS_INVALID_SECTION = 2
    STM_ADDRESS_INVALID_LENGTH = 3
    STM_ADDRESS_INVALID_ACCESS = 4


class DeviceMemoryMap:

    BOOTLOADER_START = 0x20000000
    BOOTLOADER_LEN = 2048

    register_map = {
        "FSMC": [0xA0000000, 0xA0000FFF],
        "USB OTG FS ": [0x50000000, 0x5003FFFF],
        "Reserved": [0x40030000, 0x4FFFFFFF],
        "Ethernet": [0x40028000, 0x40029FFF],
        "Reserved": [0x40023400, 0x40027FFF],
        "CRC Section": [0x40023000, 0x400233FF],
        "Flash memory interface": [0x40022000, 0x400223FF],
        "Reserved": [0x40021400, 0x40021FFF],
        "Reset and clock control RCC": [0x40021000, 0x400213FF],
        "Reserved": [0x40020800, 0x40020FFF],
        "DMA2": [0x40020400, 0x400207FF],
        "DMA1": [0x40020000, 0x400203FF],
        "Reserved ": [0x40018400, 0x4001FFFF],
        "SDIO": [0x40018000, 0x400183FF],
        "Reserved": [0x40015800, 0x40017FFF],
        "TIM11 timer": [0x40015400, 0x400157FF],
        "TIM10 timer": [0x40015000, 0x400153FF],
        "TIM9 timer ": [0x40014C00, 0x40014FFF],
        "Reserved": [0x40014000, 0x40014BFF],
        "ADC3": [0x40013C00, 0x40013FFF],
        "USART1": [0x40013800, 0x40013BFF],
        "TIM8 timer": [0x40013400, 0x400137FF],
        "SPI1": [0x40013000, 0x400133FF],
        "TIM1 timer": [0x40012C00, 0x40012FFF],
        "ADC2": [0x40012800, 0x40012BFF],
        "ADC1": [0x40012400, 0x400127FF],
        "GPIO Port G": [0x40012000, 0x400123FF],
        "GPIO Port F": [0x40011C00, 0x40011FFF],
        "GPIO Port E": [0x40011800, 0x40011BFF],
        "GPIO Port D": [0x40011400, 0x400117FF],
        "GPIO Port C": [0x40011000, 0x400113FF],
        "GPIO Port B": [0x40010C00, 0x40010FFF],
        "GPIO Port A": [0x40010800, 0x40010BFF],
        "EXTI": [0x40010400, 0x400107FF],
        "AFIO": [0x40010000, 0x400103FF],
        "Reserved": [0x40007800, 0x4000FFFF],
        "DAC": [0x40007400, 0x400077FF],
        "Power control PWR": [0x40007000, 0x400073FF],
        "Backup registers": [0x40006C00, 0x40006FFF],
        "bxCAN1": [0x40006400, 0x400067FF],
        "bxCAN2": [0x40006800, 0x40006BFF],
        "Shared USB/CAN SRAM": [0x40006000, 0x400063FF],
        "USB device FS registers": [0x40005C00, 0x40005FFF],
        "I2C2": [0x40005800, 0x40005BFF],
        "I2C1": [0x40005400, 0x400057FF],
        "UART5": [0x40005000, 0x400053FF],
        "UART4": [0x40004C00, 0x40004FFF],
        "USART3": [0x40004800, 0x40004BFF],
        "USART2": [0x40004400, 0x400047FF],
        "Reserved": [0x40004000, 0x400043FF],
        "SPI3/I2S": [0x40003C00, 0x40003FFF],
        "SPI2/I2S": [0x40003800, 0x40003BFF],
        "Reserved": [0x40003400, 0x400037FF],
        "Independent watchdog": [0x40003000, 0x400033FF],
        "Window watchdog": [0x40002C00, 0x40002FFF],
        "RTC": [0x40002800, 0x40002BFF],
        "Reserved": [0x40002400, 0x400027FF],
        "TIM14 timer": [0x40002000, 0x400023FF],
        "TIM13 timer": [0x40001C00, 0x40001FFF],
        "TIM12 timer": [0x40001800, 0x40001BFF],
        "TIM7 timer": [0x40001400, 0x400017FF],
        "TIM6 timer": [0x40001000, 0x400013FF],
        "TIM5 timer": [0x40000C00, 0x40000FFF],
        "TIM4 timer": [0x40000800, 0x40000BFF],
        "TIM3 timer": [0x40000400, 0x400007FF],
        "TIM2 timer": [0x40000000, 0x400003FF],
    }

    flash_interface_registers = {
        "MainMemoryStart": {"address": 0x0800000, 'length': 2000},
        "Sytem Memory": {'address': 0x1FFFF000, 'length': 2000 }, ## variable length depending on device type
        "OptionBytes": {'address': 0x1FFFF800, 'length': 16 },
        "FLASH_ACR": {"address": 0x40022000, "length": 4,},
        "FLASH_KEYR": {"address": 0x40022004, "length": 4,},
        "FLASH_OPTKEYR": {"address": 0x40022008, "length": 4,},
        "FLASH_SR": {"address": 0x4002200C, "length": 4,},      ## status refister
        "FLASH_CR": {"address": 0x40022010, "length": 4,},      ## control register
        "FLASH_AR": {"address": 0x40022014, "length": 4,},      ## address register
        "FLASH_OBR": {"address": 0x4002201C, "length": 4,},     ## option byte register
        "FLASH_WRPR": {"address": 0x40022020, "length": 4,},    ## write protect register
    }

    flash_keys = {
        'RDPRT_KEY' : 0x00A5,
        'KEY_1': 0x45670123,
        'KEY_2': 0xCDEF89AB,
    }

    STMF1_SRAM_START = 0x20000000


class DeviceInformation:
    bootloader_version: int
    valid_cmds: list
    device_id: int

    def __init__(
        self, bl_version: int = None, valid_cmds: list = None, dev_id: int = None
    ):
        self.bootloader_version = bl_version
        self.valid_cmds = valid_cmds
        self.device_id = dev_id

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


class SerialTool:

    connected = False
    device_id_read = False
    bootloader_read = False
    valid_cmds_read = False

    device_info = None

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
        return CheckMemoryResponse.STM_ADDRESS_VALID

    """ return address as array of bytes, MSB first """
    def address_to_bytes(self, address):
        return bytearray([
            ((address >> 24) & 0xFF),
            ((address >> 16) & 0xFF),
            ((address >> 8) & 0xFF),
            (address & 0xFF),
        ])

    def reset(self):
        self.serial.setDTR(1)
        sleep(0.001)
        self.serial.setDTR(0)    

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

    ## TODO: I don't like this, but how else to build
    # a description of the device without a bunch of flags?
    def unpackDeviceInfo(self, get_rx: bytearray, id_rx: bytearray):
        """ populate device information from a 'GET' command response 
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

            ## create device information object
            self.device_info = DeviceInformation(
                bl_version=bl_v, valid_cmds=v_cmds, dev_id=d_id
            )
            ## set read successes
            self.device_id_read = True
            self.bootloader_read = True
            self.valid_cmds_read = True
            success = True
        return success

    ##============ GETTERS/SETTERS ============##

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
        """attempt to read len bytes from the device
        return read_len, bytes
        """
        rx = self.serial.read(length)
        return (len(rx) == length), rx

    def waitForAck(self, timeout: float = 1.0):
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
            print("neither recieved")
            return False

    ##============== Device Interaction =========##

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

    def readOptionBytes(self):
        pass

    ##=============== DEVICE COMMANDS ==========##

    def cmdGetId(self):
        id_rx = None
        id_commands = bytearray([STM_CMD_GET_ID, self.getByteComplement(STM_CMD_GET_ID),])
        success = self.writeDevice(id_commands)

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
            # print(f"GET Bootloader Version {get_rx[2]}")
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
            # print(f"Bootloader Version {rx[1]}, opt byte1 {rx[2]}, opt byte2 {rx[3]} ACK {rx[4]}")
            success = False
        return success, rx

    def cmdReadFromMemoryAddress(self, address, length):
        """ read length bytes from address """
        rx = bytearray()

        # check address is valid
        address_valid = self.checkValidReadAddress(address)
        
        if address_valid != CheckMemoryResponse.STM_ADDRESS_VALID:
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



