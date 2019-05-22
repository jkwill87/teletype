from teletype import IS_WINDOWS
from teletype.codes.common import *

if IS_WINDOWS:
    from teletype.codes.windows import *
else:
    from teletype.codes.posix import *
