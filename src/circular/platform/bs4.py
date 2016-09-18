import sys

if sys.platform == "brython":
    from .brython.bs4 import *
elif sys.platform == "linux":
    from .linux.bs4 import *


