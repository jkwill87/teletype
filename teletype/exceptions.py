class TeletypeException(Exception):
    pass


class TeletypeSkipException(TeletypeException):
    pass


class TeletypeQuitException(TeletypeException):
    pass
