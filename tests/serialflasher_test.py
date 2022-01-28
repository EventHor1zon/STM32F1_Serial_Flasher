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
        a = self.sf.baud
        self.assertEqual(a, DEVICE_SERIAL_BAUD)

    def testGetTimeout(self):
        base = self.serial.timeout
        a = self.sf.getSerialTimeout()
        self.assertEqual(base, a)

    def testGetSerialState(self):
        state = self.serial.is_open
        a = self.sf.getSerialState()
        self.assertEqual(state, a)

    def testConnect(self):
        a = self.sf.connect()
        self.assertTrue(a)
        self.assertTrue(self.sf.connected)


