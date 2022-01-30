## @file serialflasher_test.py
#
#   unit tests for the SerialFlasher class


VALID_PORT = "/dev/ttyUSB0"
INVALID_PORT = "/dev/ttyS0"

CMD_HANDSHAKE = b"\x79"
STM_ACK = b"\x7F"

from asyncore import write
import unittest
import serial
import SerialFlasher.SerialFlasher as SF
from SerialFlasher import (
    STM_CMD_HANDSHAKE,
    STM_CMD_ACK,
    STM_CMD_NACK,
    STM_CMD_GET,
    STM_CMD_VERSION_READ_PROTECT,
    STM_CMD_GET_ID,
    STM_CMD_READ_MEM,
    STM_CMD_GO,
    STM_CMD_WRITE_MEM,
    STM_CMD_ERASE_MEM,
    STM_CMD_EXT_ERASE,
    STM_CMD_WRITE_PROTECT_EN,
    STM_CMD_WRITE_PROTECT_DIS,
    STM_CMD_READOUT_PROTECT_EN,
    STM_CMD_READOUT_PROTECT_DIS,
    DeviceInformationNotReadError,
)
import sys
from time import sleep


# a non-existent serial port
DEVICE_SERIAL_PORT = "/dev/ttyUSB1"
DEVICE_SERIAL_BAUD = 57600
DEVICE_SERIAL_WRT_TIMEOUT_S = 1.0
DEVICE_SERIAL_RD_TIMEOUT_S = 1.0

## may have to refine this based on testing device!
DEVICE_ID_EXPECTED = 0x92
DEVICE_VALID_BOOTLOADER_VERSION = 1.0 
DEVICE_VALID_CMDS = [
    STM_CMD_HANDSHAKE,
    STM_CMD_ACK,
    STM_CMD_NACK,
    STM_CMD_GET,
    STM_CMD_VERSION_READ_PROTECT,
    STM_CMD_GET_ID,
    STM_CMD_READ_MEM,
    STM_CMD_GO,
    STM_CMD_WRITE_MEM,
    STM_CMD_ERASE_MEM,
    STM_CMD_EXT_ERASE,
    STM_CMD_WRITE_PROTECT_EN,
    STM_CMD_WRITE_PROTECT_DIS,
    STM_CMD_READOUT_PROTECT_EN,
    STM_CMD_READOUT_PROTECT_DIS,    
]

SFTEST_INVALID_SERIAL_PORT = "/dev/ttyABCD"


class SerialFlasherTestCase(unittest.TestCase):
    def setUp(self):
        self.serial = serial.Serial(
            DEVICE_SERIAL_PORT,
            DEVICE_SERIAL_BAUD,
            timeout=DEVICE_SERIAL_RD_TIMEOUT_S,
            write_timeout=DEVICE_SERIAL_WRT_TIMEOUT_S,
        )
        self.serial.setDTR(False)
        self.sf = SF.SerialTool(
            serial=self.serial
        )

    def tearDown(self):
        """Teardown: Close socket and reset device"""
        self.serial.close()
        self.resetDevice()
        return super().tearDown()

    def resetDevice(self):
        """uses the DTR pin of USB->Serial to reset board"""
        self.serial.setDTR(1)
        sleep(0.001)
        self.serial.setDTR(0)

    def testGetBaud(self):
        """ test we can get the baud property """
        a = self.sf.getBaud()
        self.assertEqual(a, DEVICE_SERIAL_BAUD)

    def testSetBaudValid(self):
        """ test we can set valid baud """
        b = 9600
        a = self.sf.setBaud(b)
        self.assertTrue(a)

    def testSetBaudTooLow(self):
        """ test setting baud below min raises value error """
        b = 1199
        with self.assertRaises(ValueError):
            self.sf.setBaud(b)

    def testSetBaudTooHigh(self):
        """ test setting baud above max raises value error """
        b = 115201
        with self.assertRaises(ValueError):
            self.sf.setBaud(b)

    def testGetPort(self):
        """ test we can get the connected port """
        p = self.sf.getPort()
        self.assertEqual(p, DEVICE_SERIAL_PORT)

    def testGetTimeout(self):
        """ test we can get the serial timeout """
        base = self.serial.timeout
        a = self.sf.getSerialTimeout()
        self.assertEqual(base, a)

    def testSetSerialTimeout(self):
        """ test we can set the serial timeout """
        t = 1.2
        self.sf.setSerialReadWriteTimeout(t)
        base = self.serial.timeout
        self.assertAlmostEqual(t, base)

    def testGetSerialState(self):
        """ test we can get the serial state """
        state = self.serial.is_open
        a = self.sf.getSerialState()
        self.assertEqual(state, a)

    def testConnect(self):
        """ test we can connect to the device """
        a = self.sf.connect()
        self.assertTrue(a)

    def testConnectedState(self):
        a = self.sf.connect()
        self.assertTrue(self.sf.connected)

    def testDisconnect(self):
        """ test we can disconnect from the device and close the serial port """
        a = self.sf.connect()
        self.sf.disconnect()
        self.assertFalse(self.sf.connected)
        self.assertFalse(self.serial.is_open)

    def testSetBaudWhilstConnected(self):
        """ test that setting baud whilst connected returns false """
        self.sf.connect()
        a = self.sf.setBaud(DEVICE_SERIAL_BAUD)
        self.assertFalse(a)

    def testReadDeviceInformation(self):
        """ test we can read the device information """
        self.sf.connect()
        a = self.sf.readDeviceInfo()
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
        bootloader_version = self.sf.getBootloaderVersion()
        self.assertEqual(bootloader_version, DEVICE_VALID_BOOTLOADER_VERSION)

    def testGetDeviceId(self):
        self.sf.connect()
        self.sf.readDeviceId()
        device_id = self.sf.getDeviceId()
        self.assertEqual(device_id, DEVICE_ID_EXPECTED)

    def testGetDeviceValidCmdsBeforeRead(self):
        """ test that getting valid commands before read raises exception """
        with self.assertRaises(DeviceInformationNotReadError):
            self.sf.getDeviceValidCommands()

    def testGetDeviceBootloaderVersionBeforeRead(self):
        """ test that getting bootloader version before read raises exception """
        with self.assertRaises(DeviceInformationNotReadError):
            self.sf.getDeviceBootloaderVersion()

    def testGetDeviceIdBeforeRead(self):
        """ test that getting device ID before read raises exception """
        with self.assertRaises(DeviceInformationNotReadError):
            self.sf.getDeviceId()

