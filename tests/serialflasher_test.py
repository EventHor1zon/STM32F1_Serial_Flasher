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
import sys
from time import sleep


# a non-existent serial port
DEVICE_SERIAL_PORT = "/dev/ttyUSB1"
DEVICE_SERIAL_BAUD = 57600
DEVICE_SERIAL_WRT_TIMEOUT_S = 1.0
DEVICE_SERIAL_RD_TIMEOUT_S = 1.0

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

    