import unittest
from SerialFlasher.constants import *

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

class StmDeviceTestCase(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass


    def testReadDeviceInformation(self):
        """ test we can read the device information """
        self.stm.connect()
        a = self.stm.readDeviceInfo()
        self.assertTrue(a)

    def testGetDeviceValidCommands(self):
        """ test we can get the valid device commands as a list """
        self.sf.connect()
        self.sf.readDeviceInfo()
        valid_cmds = self.sf.getDeviceValidCommands()
        self.assertListEqual(valid_cmds, DEVICE_VALID_CMDS)

    def testGetDeviceBootloaderVersion(self):
        """ test we can get the expected device bootloader """
        self.sf.connect()
        self.sf.readDeviceInfo()
        bootloader_version = self.sf.getDeviceBootloaderVersion()
        self.assertEqual(bootloader_version, DEVICE_VALID_BOOTLOADER_VERSION)

    def testGetDeviceValidCmdsBeforeRead(self):
        """ test that getting valid commands before read raises exception """
        with self.assertRaises(SF.InformationNotRetrieved):
            self.sf.getDeviceValidCommands()

    def testGetDeviceBootloaderVersionBeforeRead(self):
        """ test that getting bootloader version before read raises exception """
        with self.assertRaises(SF.InformationNotRetrieved):
            self.sf.getDeviceBootloaderVersion()

    def testGetDeviceIdBeforeRead(self):
        """ test that getting device ID before read raises exception """
        with self.assertRaises(SF.InformationNotRetrieved):
            self.sf.getDeviceId()


    def testReadInvalidAddress(self):
        self.sf.connect()
        with self.assertRaises(InvalidAddressError):
            self.sf.cmdReadFromMemoryAddress(DEVICE_TEST_READ_INVALID_ADDR, 1)

