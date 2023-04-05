class InformationNotRetrieved(Exception):
    """information has not been read yet"""

    pass


class InvalidAddressError(Exception):
    """the address is invalid"""

    pass


class InvalidReadLengthError(Exception):
    """the read length is invalid"""

    pass


class InvalidWriteLengthError(Exception):
    """the write length is invalid"""

    pass


class InvalidResponseLengthError(Exception):
    """An invalid response length was returned"""

    pass


class AckNotReceivedError(Exception):
    """An expected ack byte was not received"""

    pass


class NoResponseError(Exception):
    """The device did not respond"""

    pass


class UnexpectedResponseError(Exception):
    """An unexpected response was received"""

    pass


class InvalidEraseLengthError(Exception):
    """Invalid erase length"""

    pass


class DeviceNotConnectedError(Exception):
    """The device is not connected"""

    pass


class CommandFailedError(Exception):
    """The command failed in some way"""

    pass


class UnpackInfoFailedError(Exception):
    """The info bytes were unable to be unpacked"""

    pass


class DeviceNotSupportedError(Exception):
    """The device is not currently supported"""

    pass
