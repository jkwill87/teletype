from teletype import IS_WINDOWS
from teletype.io.common import *

if IS_WINDOWS:
    from teletype.io.windows import *
else:
    from teletype.io.posix import *
