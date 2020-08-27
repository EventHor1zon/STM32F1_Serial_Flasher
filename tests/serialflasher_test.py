## @file serialflasher_test.py
#
#   unit tests for the SerialFlasher class
#
#   As a super cheeky way of generating resets on the board
#   (reset of each test means handshake each time which breaks stuff)
#   is to use a second MCU on a second serial port to reset the device
#
#   For my tests am using an ESP32 programmed with arduino-style code
#   included with these tests.


DEFAULT_BAUD = 9600
VALID_PORT = "/dev/ttyUSB0"
INVALID_PORT = "/dev/ttyS0"
CHEEKY_RESET_PORT = "/dev/ttyUSB1"

CMD_HANDSHAKE = b"\x7F"
STM_ACK = b"\x79"

import unittest
import serial
import STM_SerialFlasher.SerialFlasher as SF
import sys
from time import sleep


class SerialFlasherTestCase(unittest.TestCase):
    def setUp(self):
        rst = 1
        while rst:
            if self.resetWithExternalDevice():
                rst = 0
        sleep(0.2)
        self.resetFlag = 0
        self.sf = SF.SerialTool()

    def tearDown(self):
        ## on teardown, close the socket
        # and reset the device if neccessary
        self.sf.close()
        if self.resetFlag:
            self.resetWithExternalDevice()

    ## Utility functions

    ## automate steps to open the port
    def openPort(self):
        try:
            self.sf.port = VALID_PORT
            self.sf.openPort()
        except:
            print("Error Opening port!")
            return 0
        return 1

    def openPortWithHandshake(self):
        try:
            self.openPort()
            self.sf.writeDevice(CMD_HANDSHAKE)
            a = self.sf.readDevice(1)
            if a != STM_ACK:
                print("[***] Handshake ACK failed " + hex(a))
                return 0
        except:
            return 0
        self.resetFlag = 1
        return 1

    def resetWithExternalDevice(self):
        ## uses an external device to reset the test device?
        # @ret True/False
        try:
            reset_serial = serial.Serial(
                port=CHEEKY_RESET_PORT, write_timeout=1, timeout=1
            )
        except:
            print("[!] Unable to open the reset device serial")
            raise
        reset_serial.write(b"\x33")
        reset_serial.close()
        print("[:)] Reset Device")
        sleep(0.02)
        return True

    ## test the initliser values
    def testInvalidLowBaud(self):
        baud = 100  # too low
        a = self.sf.setBaud(baud)
        self.assertEqual(a, False)

    def testInvalidHighBaud(self):
        baud = 1000000  # too high
        a = self.sf.setBaud(baud)
        self.assertEqual(a, False)

    def testInvalidBaudType(self):
        baud = "AAA"
        a = self.sf.setBaud(baud)
        self.assertEqual(a, False)

    def testSetPortInvalidType(self):
        port = 1234
        with self.assertRaises(TypeError):
            self.sf.setPort(port)

    def testGetBaudType(self):
        a = self.sf.getBaud()
        self.assertIsInstance(a, int)
        self.assertEqual(a, DEFAULT_BAUD)

    # def testSetNonexistentPort(self):
    #    self.sf.setPort("ABCD")

    def testOpenPortNoneSet(self):
        self.assertFalse(self.sf.openPort())

    def testClosePort(self):
        self.openPort()
        a = self.sf.ser.is_open
        self.assertEqual(a, True)
        self.sf.close()
        b = self.sf.ser.is_open
        self.assertNotEqual(a, b)

    def testGetTimeout(self):
        a = self.sf.getTimeout()
        self.assertIsInstance(a, float)
        self.assertGreater(a, 0.0009)  # ~ 1 / 115200  * 100
        self.assertLess(a, 0.085)  # ~ 1 / 1200  * 100

    def testGetSerialState(self):
        self.assertEqual(self.sf.utilGetSerialState(), False)
        self.sf.setPort(VALID_PORT)
        self.sf.openPort()
        a = self.sf.utilGetSerialState()
        self.assertEqual(a, True)

    def testValidWriteDevice(self):
        d = b"\x79"
        self.sf.setPort(VALID_PORT)
        self.sf.openPort()
        a = self.sf.writeDevice(d)
        self.assertEqual(a, 1)
        self.resetFlag = 1

    def testInvalidDataWriteDevice(self):
        d = ["string", ("tupple", 1)]
        self.sf.setPort(INVALID_PORT)
        self.sf.openPort()
        a = self.sf.writeDevice(d)
        self.assertEqual(a, 0)
        self.resetFlag

    def testReadPortType(self):
        ## errrr... test against device??
        ## test against file??
        ## test against virtual serial port?
        self.assertEqual(1, 1)

    def testCheckRxForAck(self):
        a = bytes([0x79, 0x00, 0x33])
        b = bytearray([0x79, 0x01, 0x02])
        x = self.sf.checkRxForAck(a)  # should return true
        y = self.sf.checkRxForAck(b)  # should return false
        self.assertTrue(x)
        self.assertFalse(y)

    def testSendHandshake(self):
        self.openPort()
        a = self.sf.sendHandshake()
        self.assertIsInstance(a, (bytearray, bytes))
        self.assertTrue(len(a) > 0)
        self.assertEqual(a, STM_ACK)
        self.resetFlag = 1

    def testCmdGetInfo(self):
        self.openPortWithHandshake()
        a = self.sf.cmdGetInfo()
        self.assertIsInstance(a, (bytearray, bytes))
        self.assertTrue(len(a) > 0)

    def testCmdGetVersionProt(self):
        self.openPortWithHandshake()
        a = self.sf.cmdGetVersionProt()
        self.assertIsInstance(a, (bytes, bytearray))
        self.assertTrue(len(a) > 0)

    def testCmdGetDeviceId(self):
        self.openPortWithHandshake()
        a = self.sf.cmdGetDeviceID()
        self.assertIsInstance(a, int)
        self.assertGreater(a, 0x03FF)  # min val is 0x0400
        self.assertLess(a, 0x0500)  ## max val is 0x04FF

    def testGetDeviceInfo(self):
        self.openPortWithHandshake()
        a = self.sf.getDeviceInfo()
        self.assertIsInstance(a, dict)
        for key in self.sf.deviceInfo:
            self.assertIn(key, a.keys())
            self.assertNotEqual(a[key], None)


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(SerialFlasherTestCase)
    unittest.TextTestRunner().run(suite)
