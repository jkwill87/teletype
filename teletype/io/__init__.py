from os import name

from .common import *

if name in ("nt", "cygwin"):
    from .windows import *
else:
    from .unix import *
