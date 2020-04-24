## @file serialflasher_test.py
#
#   unit tests for the SerialFlasher class


VALID_PORT = "/dev/ttyUSB0"
INVALID_PORT = "/dev/ttyS0"

CMD_HANDSHAKE = b'\x79'
STM_ACK = b'\x7F'

import unittest
import serial
import SerialFlasher
import sys

class SerialFlasherTestCase(unittest.TestCase):

    def setUp(self):
        self.sf = SerialFlasher.SerialFlasher()
    
    def tearDown(self):
        ## on teardown, close the socket
        self.sf.close()
        return super().tearDown()

    ## Utility functions 

    ## open the port 
    def openPort(self):
        try:
            self.sf.port = VALID_PORT
            self.sf.openPort()
        except:
            print("Error Opening port!")
            sys.exit(1)
        return 1


    ## test the initliser values
    def testInvalidLowBaud(self):
        baud = 100  # too low
        with self.assertRaises('ValueError'):
            self.sf.setBaud(baud)

    def testInvalidHighBaud(self):
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

    def testGetSerialState(self):
        self.assertEqual(self.sf.getSerialState(), False)
        self.sf.setPort(VALID_PORT)
        self.sf.openPort()
        self.assertEqual(self.sf.getSerialState(), True)

    def testValidWriteDevice(self):
        d = bytearray(['\x00', '\x01'])
        self.sf.setPort(VALID_PORT)
        self.sf.openPort()
        a = self.sf.writeDevice(d)
        self.assertEqual(a, 2)

    def testInvalidDataWriteDevice(self):
        d = [ 40987, 100293 ]
        self.sf.setPort(INVALID_PORT)
        self.sf.openPort()
        a = self.sf.writeDevice(d)
        self.assertEqual(a, 0)

    def testReadPortType(self):
        ## errrr... test against device??
        ## test against file?? 
        ## test against virtual serial port? 
        self.openPort()
        self.sf.writeDevice(CMD_HANDSHAKE)
        a = self.sf.readDevice(32)
        self.assertIsInstance(a, (bytearray, bytes))
        self.assertTrue(len(a) > 0)
        self.assertEqual(a[0], STM_ACK)

    def testSendHandshake(self):
        # this is above?
        self.openPort()
        a = self.sf.sendHandshake()
        self.assertEqual(a, STM_ACK)
    
    

    
    
    


