## @file serialflasher_test.py
#
#   unit tests for the SerialFlasher class


import unittest
import serial
import SerialFlasher

class SerialFlasherTestCase(unittest.TestCase):

    def setUp(self):
        self.sf = SerialFlasher.SerialFlasher()
    
    def tearDown(self):
        ## on teardown, close the socket
        self.object.close()
        return super().tearDown()

    ## test the initliser values
    def testInvalidLowBaud(self):
        baud = 100  # too low
        with self.assertRaises('ValueError'):
            self.sf.setBaud(baud)

    def testInvalidLowBaud(self):
        baud = 1000000  # too high
        with self.assertRaises(ValueError):
            self.sf.setBaud(baud)

    def testInvalidBaudType(self):
        baud = "AAA"
        with self.assertRaises(TypeError):
            self.sf.setBaud(baud)

    def testSetPortInvalidType(self):
        port = 1234
        with self.assertRaises(TypeError):
            self.sf.setPort(port)

    def testSetNonexistentPort(self):
        self.sf.setPort("ABCD")
        with self.assertRaises(serial.SerialException):
            self.sf.openPort()

    def testOpenPortNoneSet(self):
        self.assertFalse(self.sf.open())

    def testGetTimeout(self):
        a = self.sf.getTimeout()
        self.assertIsInstance(a, float)
        self.assertGreater(a, 0.0009)  # ~ 1 / 115200  * 100
        self.assertLess(a, 0.085)      # ~ 1 / 1200  * 100

    