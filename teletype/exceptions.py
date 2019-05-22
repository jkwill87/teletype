class TeletypeException(Exception):
    """ Base exception for teletype; raised when an internal preconditon fails
    """


class TeletypeSkipException(TeletypeException):
    """ Raised when a user selects skip as an option from a select component
    """


class TeletypeQuitException(TeletypeException):
    """ Raised when a user selects quit as an option from a select component
    """
