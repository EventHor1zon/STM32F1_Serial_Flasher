import unittest
from SerialFlasher.StmDevice import STMInterface
from SerialFlasher.constants import *
from SerialFlasher.errors import DeviceNotConnectedError, InformationNotRetrieved, InvalidAddressError
from time import sleep
import serial

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
STM_TEST_VALID_OPTBYTE_DATA = b'\xa5Z\xff\xffZ\xa5\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff'

class STMInterfaceTestCase(unittest.TestCase):

    def setUp(self):

        self.stm = STMInterface()
        self.stm.connectToDevice(
            DEVICE_SERIAL_PORT,
            DEVICE_SERIAL_BAUD
        )

    def tearDown(self):
        self.stm.serialTool.serial.close()
        self.resetDevice()
        super().tearDown()

    def resetDevice(self):
        self.stm.serialTool.serial.setDTR(1)
        sleep(0.01)
        self.stm.serialTool.serial.setDTR(0)

    def testGetDeviceInformation(self):
        """ test we can read the device information """
        a = self.stm.readDeviceInfo()
        self.assertTrue(a)
        self.assertNotEqual(self.stm.device, None)

    def testGetDeviceBootloaderVersion(self):
        """ test we can get the expected device bootloader """
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
        """ test that getting bootloader version before read raises exception """
        with self.assertRaises(InformationNotRetrieved):
            self.stm.getDeviceBootloaderVersion()

    def testGetDeviceIdBeforeRead(self):
        """ test that getting device ID before read raises exception """
        with self.assertRaises(InformationNotRetrieved):
            self.stm.getDeviceId()

    ### Test writing and reading to RAM ###

    def testWriteDataToRam(self):
        """ test we can write a byte to RAM """
        success = self.stm.readDeviceInfo()
        success = self.stm.writeToRam(0x20002000, bytearray([0x01, 0x02, 0x03, 0x04]))
        self.assertTrue(success)

    def testReadDataFromRam(self):
        """ test we can read a byte from RAM """
        success = self.stm.readDeviceInfo()
        success = self.stm.writeToRam(0x20002000, bytearray([0x01, 0x02, 0x03, 0x04]))
        rx = self.stm.readFromRam(0x20002000, 4)
        self.assertTrue(success)
        self.assertEqual(rx, bytearray([0x01, 0x02, 0x03, 0x04]))


    #### Test using the Flash and option bytes ###

    def testReadOptionBytesData(self):
        success = self.stm.readDeviceInfo()
        success = self.stm.readOptionBytes()
        self.assertTrue(success)
        self.assertEqual(self.stm.device.option_bytes_contents.nUser, 0xA5)


    def testWriteOptionBytesData(self):
        success = self.stm.readDeviceInfo()
        success &= self.stm.readOptionBytes()
        self.assertTrue(success)
        write_success = self.stm.writeToOptionBytes(STM_TEST_VALID_OPTBYTE_DATA, reconnect=True)
        self.assertTrue(write_success)
        success = self.stm.readOptionBytes()
        self.assertEqual(self.stm.device.option_bytes_contents.data0, STM_TEST_VALID_OPTBYTE_DATA[5])


