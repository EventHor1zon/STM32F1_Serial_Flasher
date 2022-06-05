

class InformationNotRetrieved(Exception):
    pass

class InvalidAddressError(Exception):
    pass

class InvalidReadLengthError(Exception):
    pass

class InvalidWriteLengthError(Exception):
    pass

class InvalidResponseLengthError(Exception):
    pass

class AckNotReceivedError(Exception):
    pass

class NoResponseError(Exception):
    pass

class UnexpectedResponseError(Exception):
    pass

class InvalidEraseLengthError(Exception):
    pass

class DeviceNotConnectedError(Exception):
    pass

class CommandFailedError(Exception):
    pass

class UnpackInfoFailedError(Exception):
    pass

class DeviceNotSupportedError(Exception):
    pass