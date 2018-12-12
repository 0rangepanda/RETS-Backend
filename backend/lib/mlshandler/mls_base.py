import abc
import librets

"""When we dealing with more than one MLS,
Complete this base class
"""

class PropertyInstance(object):
    """Base class of mls handler"""


class RequestInstance(object):
    """Base class of mls handler"""


class MlsBase(object):
    """Base class of mls handler"""

    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def load(self, input):
        """Retrieve data from the input source and return an object."""
        return

    @abc.abstractmethod
    def save(self, output, data):
        """Save the data object to the output."""
        return

    @abc.abstractmethod
    def search(self, request):
        """Save the data object to the output."""
        return

    @abc.abstractmethod
    def getImage(self, property):
        """Save the data object to the output."""
        return
