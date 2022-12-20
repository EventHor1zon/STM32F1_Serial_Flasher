# STM32F1_Serial_Flasher
A python module for exploring STM32 F1 devices using the STM Bootloader's Serial interface


Some Planning...


SerialTool is the low-level bootloader interface to the device (via PySerial object)

DeviceDescriptor describes the connected device's characteristics gathered

StmDevice is the higher level functional class allowing user to do more complex operations without worrying about the low-level implementation



            +--------------------+
            |   StmDevice        |
            |   - read, write    |
            |   - program        |
            |   - erase flash    |
            +--------------------+
                    |
                    | 
                    |
        -----------------------------------
        |                                 |
        |                                 |
    +--------------+                +-------------+
    | SerialTool   |                | DeviceDescr |
    | - BL commands|                | - Type      |
    | - Serial Ifc |                | - ValidCmds |
    +--------------+                | - Flash sz  |
                                    +-------------+



This tool should be written with unittests - these unittests are run against the actual device. Because it's fun. And reduces the chances of making an error in the mock, or interpreting the Datasheet. Or Errata in the datasheet. Or writing tests for an invalid bootloader version. 


## Application

The application is built with Textual. Pretty fun to use and looks really nice.

![image](./screenshots/stmapp_disconnected.svg) 
![image](./screenshots/stmapp_connected.svg)