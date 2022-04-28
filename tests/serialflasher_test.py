## @file serialflasher_test.py
#
#   unit tests for the SerialFlasher class
#   First attempt at test-driven development
#   Write a driver to interface with the STM F1 series of chips
#   Want to provide interface to:
#       - Connect with the device over serial UART
#       - Read the device information
#       - Read from a memory address
#       - Write to a memory address
#       - Lock/Unlock Flash sections
#       - etc.
#
############################################


VALID_PORT = "/dev/ttyUSB0"
INVALID_PORT = "/dev/ttyS0"

CMD_HANDSHAKE = b"\x79"
STM_ACK = b"\x7F"

from asyncore import write
import unittest
import serial
import SerialFlasher.SerialFlasher as SF
from SerialFlasher.constants import *

import sys
from time import sleep

from SerialFlasher.errors import InvalidAddressError


# a non-existent serial port
DEVICE_SERIAL_PORT = "/dev/ttyUSB0"
DEVICE_SERIAL_BAUD = 57600
DEVICE_SERIAL_WRT_TIMEOUT_S = 1.0
DEVICE_SERIAL_RD_TIMEOUT_S = 1.0

## may have to refine this based on testing device!
DEVICE_ID_EXPECTED = 1040
DEVICE_VALID_BOOTLOADER_VERSION = 11
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

DEVICE_TEST_READ_ADDR_OPTIONBYTES = 0x1FFFF800
DEVICE_TEST_READ_ADDR_OPTBYTES_LEN = 16
DEVICE_TEST_READ_INVALID_ADDR = 0x000000020


class SerialFlasherTestCase(unittest.TestCase):
    def setUp(self):
        self.serial = serial.Serial(
            DEVICE_SERIAL_PORT,
            DEVICE_SERIAL_BAUD,
            timeout=DEVICE_SERIAL_RD_TIMEOUT_S,
            write_timeout=DEVICE_SERIAL_WRT_TIMEOUT_S,
        )
        self.serial.setDTR(False)
        self.sf = SF.SerialTool(serial=self.serial)

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
        bootloader_version = self.sf.getDeviceBootloaderVersion()
        self.assertEqual(bootloader_version, DEVICE_VALID_BOOTLOADER_VERSION)

    def testGetDeviceId(self):
        """ test we can get the device id """
        self.sf.connect()
        self.sf.readDeviceInfo()
        device_id = self.sf.getDeviceId()
        self.assertEqual(device_id, DEVICE_ID_EXPECTED)

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

    def testCmdGetVersionProt(self):
        """ interested to see what these other commands return 
            and compare to the GET command output
        """
        self.sf.connect()
        success, rx = self.sf.cmdGetVersionProt()
        self.assertTrue(success)

    def testReadMemoryAddress(self):
        """ test we can read from a known memory address
            read a known fixed value from the device...
            let's go look at the data sheet...
            option byte seems a good target
            also the flash CR 
         """
        self.sf.connect()
        success, rx = self.sf.cmdReadFromMemoryAddress(
            DEVICE_TEST_READ_ADDR_OPTIONBYTES, DEVICE_TEST_READ_ADDR_OPTBYTES_LEN
        )
        self.assertTrue(success)
        """ as detailed in Rev 2 1/31 PM0075 flash option bytes 
            are a 4 * 4 set of control registers. Each 4-byte set contains
            2 data and 2 !data bytes. Compare these & make sure pattern 
            is observed
        """
        rx_row_0 = rx[0:4]
        rx_row_1 = rx[4:8]
        rx_row_2 = rx[8:12]
        rx_row_3 = rx[12:16]
        ## no need to try them all
        self.assertEqual(rx_row_0[0], (rx_row_0[1] ^ 0xFF))
        self.assertEqual(rx_row_1[2], (rx_row_1[3] ^ 0xFF))

    def testReadInvalidAddress(self):
        self.sf.connect()
        with self.assertRaises(InvalidAddressError):
            self.sf.cmdReadFromMemoryAddress(DEVICE_TEST_READ_INVALID_ADDR, 1)

    def testFlashUnlock(self):
        """ test that we can unlock the flash succesfully
            Read the flash register, ensure it's locked
            then call the flash unlock method and 
            read the register again, asserting that the bit is unset
        """
        self.sf.connect()
        success = self.sf.unlockFlash()
        self.assertTrue(success)
