import logging

from . import Data
from . import Figures
from . import IO
from . import Interfaces
# from .FPEAM import Modules
# from . import Modules
from . import EngineModules
from . import utils
from .FPEAM import FPEAM

try:  # Python 2.7+
    from logging import NullHandler
except ImportError:
    class NullHandler(logging.Handler):
        def emit(self, record):
            pass

# Set default logging handler to avoid "No handler found" warnings.
logging.getLogger(__name__).addHandler(NullHandler())

try:
    basestring
except NameError:
    basestring = str
