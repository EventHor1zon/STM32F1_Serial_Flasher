#
# @file stmdevice_test.py
# @brief tests for the stmdevice.py file
#

import unittest
import serial
from struct import unpack
from time import sleep
from stm_tools.serialflasher.stmdevice import STMInterface
from stm_tools.serialflasher.constants import *
from stm_tools.serialflasher.errors import (
    DeviceNotConnectedError,
    InformationNotRetrieved,
    InvalidAddressError,
)
from stm_tools.serialflasher.utilities import getByteComplement
from stm_tools.serialflasher.devices import OptionBytes


DEVICE_VALID_BOOTLOADER_VERSION = 2.2

DEVICE_VALID_CMDS = [
    STM_CMD_GET,
    STM_CMD_VERSION_READ_PROTECT,
    STM_CMD_GET_ID,
    STM_CMD_READ_MEM,
    STM_CMD_GO,
    STM_CMD_WRITE_MEM,
    STM_CMD_ERASE_MEM,
    STM_CMD_WRITE_PROTECT_EN,
    STM_CMD_WRITE_PROTECT_DIS,
    STM_CMD_READOUT_PROTECT_EN,
    STM_CMD_READOUT_PROTECT_DIS,
]

DEVICE_SERIAL_PORT = "/dev/ttyUSB0"
DEVICE_SERIAL_BAUD = 57600
DEVICE_SERIAL_WRT_TIMEOUT_S = 1.0
DEVICE_SERIAL_RD_TIMEOUT_S = 1.0
DEVICE_TEST_READ_INVALID_ADDR = 0x20000000
STM_DEVICE_TEST_CHAR = 0x41
STM_TEST_VALID_OPTBYTE_DATA = (
    b'\xa5Z\x04\xfb"\xdd\x11\xee\x00\xff\x00\xff\x00\xff\x00\xff'
)
STM_TEST_BINARY_PATH = "/home/rich/Development/PyDev/STM32Tools/STM32F1_Serial_Flasher/tests/binaries/blackpill_blink.bin"
STM_DEVICE_TEST_RAM_ADDR = 0x20002000


def dump_option_bytes(data: bytes):

    fmt = ">16B"

    (
        nUsr,
        Usr,
        nRdp,
        Rdp,
        nD1,
        D1,
        nD0,
        D0,
        nWrp1,
        Wrp1,
        nWrp0,
        Wrp0,
        nWrp3,
        Wrp3,
        nWrp2,
        Wrp2,
    ) = unpack(fmt, data)

    print(f"{bin(Usr)}|{bin(nUsr)} - {Rdp}|{nRdp}")
    print(f"{D1}|{nD1} - {D0}|{nD0}")
    print(f"{Wrp1}|{nWrp1} - {Wrp0}|{nWrp0}")
    print(f"{Wrp3}|{nWrp3} - {Wrp2}|{nWrp2}")


class STMInterfaceTestCase(unittest.TestCase):
    def setUp(self):

        self.stm = STMInterface()
        self.stm.connectToDevice(DEVICE_SERIAL_PORT, DEVICE_SERIAL_BAUD)

    def tearDown(self):
        self.stm.serialTool.serial.close()
        self.resetDevice()
        super().tearDown()

    def resetDevice(self):
        self.stm.serialTool.serial.setDTR(1)
        sleep(0.01)
        self.stm.serialTool.serial.setDTR(0)

    def testGetDeviceInformation(self):
        """test we can read the device information"""
        a = self.stm.readDeviceInfo()
        self.assertTrue(a)
        self.assertNotEqual(self.stm.device, None)

    def testGetDeviceBootloaderVersion(self):
        """test we can get the expected device bootloader"""
        self.stm.readDeviceInfo()
        bootloader_version = self.stm.getDeviceBootloaderVersion()
        self.assertEqual(bootloader_version, DEVICE_VALID_BOOTLOADER_VERSION)

    # def testGetDeviceValidCommands(self):
    #     """ test we can get the valid device commands as a list """
    #     self.stm.readDeviceInfo()
    #     valid_cmds = self.stm.getDeviceValidCommands()
    #     self.assertListEqual(valid_cmds, DEVICE_VALID_CMDS)

    # def testGetDeviceValidCmdsBeforeRead(self):
    #     """ test that getting valid commands before read raises exception """
    #     with self.assertRaises(InformationNotRetrieved):
    #         self.stm.getDeviceValidCommands()

    def testGetDeviceBootloaderVersionBeforeRead(self):
        """test that getting bootloader version before read raises exception"""
        with self.assertRaises(InformationNotRetrieved):
            self.stm.getDeviceBootloaderVersion()

    def testGetDeviceIdBeforeRead(self):
        """test that getting device ID before read raises exception"""
        with self.assertRaises(InformationNotRetrieved):
            self.stm.getDeviceId()

    ## Test writing and reading to RAM ##

    def testWriteDataToRam(self):
        """test we can write a byte to RAM"""
        success = self.stm.readDeviceInfo()
        success = self.stm.writeToRam(
            STM_DEVICE_TEST_RAM_ADDR, bytearray([0x01, 0x02, 0x03, 0x04])
        )
        self.assertTrue(success)

    def testReadDataFromRam(self):
        """test we can read a byte from RAM"""
        success = self.stm.readDeviceInfo()
        success = self.stm.writeToRam(
            STM_DEVICE_TEST_RAM_ADDR, bytearray([0x01, 0x02, 0x03, 0x04])
        )
        self.assertTrue(success)
        success, rx = self.stm.readFromRam(STM_DEVICE_TEST_RAM_ADDR, 4)
        self.assertTrue(success)
        self.assertEqual(rx, bytearray([0x01, 0x02, 0x03, 0x04]))

    def testWriteDataToFlash(self):
        success = self.stm.readDeviceInfo()
        self.assertTrue(success)
        success = self.stm.writeToFlash(
            self.stm.device.flash_memory.start, bytearray([0x01, 0x02, 0x03, 0x04])
        )
        self.assertTrue(success)

    def testReadDataFromFlash(self):
        """test we can read a byte from RAM"""
        success = self.stm.readDeviceInfo()
        success = self.stm.writeToFlash(
            self.stm.device.flash_memory.start, bytearray([0x01, 0x02, 0x03, 0x04])
        )
        self.assertTrue(success)
        success, rx = self.stm.readFromFlash(self.stm.device.flash_memory.start, 4)
        self.assertTrue(success)
        self.assertEqual(rx, bytearray([0x01, 0x02, 0x03, 0x04]))

    ## Test using the Flash and option bytes ##

    def testReadOptionBytesData(self):
        success = self.stm.readDeviceInfo()
        success = self.stm.readOptionBytes()
        self.assertTrue(success)
        self.assertEqual(self.stm.device.opt_bytes.read_protect, 0xA5)

    def testWriteOptionBytesData(self):
        """test we can write a valid config to the option bytes
        we check the value of the data byte to ensure write success
        """
        success = self.stm.readDeviceInfo()
        success = self.stm.readOptionBytes()
        self.assertTrue(success)

        write_success = self.stm.writeToOptionBytes(
            STM_TEST_VALID_OPTBYTE_DATA, reconnect=True
        )
        self.assertTrue(write_success)

        success = self.stm.readDeviceInfo()
        success = self.stm.readOptionBytes()
        self.assertEqual(success, True)

        self.assertEqual(
            self.stm.device.opt_bytes.data_byte_0, STM_TEST_VALID_OPTBYTE_DATA[4]
        )

    def testReadUnprotect(self):
        success = self.stm.readUnprotectFlashMemory()
        self.assertEqual(success, True)

    def testReadProtect(self):
        """assert we can successfully call readProtectFlashMemory
        and assert that reads from flash fail
        """
        success = self.stm.readProtectFlashMemory()
        self.assertEqual(success, True)

        success = self.stm.readDeviceInfo()
        success = self.stm.readOptionBytes()

        success, rx = self.stm.readFromFlash(self.stm.device.flash_memory.start, 4)
        self.assertEqual(success, False)

        self.assertEqual(self.stm.device.opt_bytes.readProtect, True)

        """ cleanup for this test """
        self.stm.readUnprotectFlashMemory()

    def testLongWriteToFlash(self):
        """test we can write a 516 len bytes to
        flash memory, testing the multiple write
        and remainder function
        """
        self.stm.readDeviceInfo()

        success = self.stm.writeToFlash(
            self.stm.device.flash_memory.start, bytearray([STM_DEVICE_TEST_CHAR] * 516)
        )

        self.assertEqual(success, True)

    def testApplicationWriteToFlash(self):
        self.stm.readDeviceInfo()
        success = self.stm.writeApplicationFileToFlash(STM_TEST_BINARY_PATH)

        self.assertEqual(success, True)
