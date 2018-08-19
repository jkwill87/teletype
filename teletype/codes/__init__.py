from .. import IS_WINDOWS
from .common import *

if IS_WINDOWS:
    from .windows import *
else:
    from .posix import *
