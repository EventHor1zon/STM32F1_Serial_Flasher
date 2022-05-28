class InformationNotRetrieved(Exception):
    pass

class InvalidAddressError(Exception):
    pass

class InvalidReadLength(Exception):
    pass

class InvalidResponseLengthError(Exception):
    pass

class AckNotReceivedError(Exception):
    pass



class DeviceNotConnectedError(Exception):
    pass

class CommandFailedError(Exception):
    pass

class UnpackInfoFailedError(Exception):
    pass