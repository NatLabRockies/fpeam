from . import utils

LOGGER = utils.logger(name=__name__)


class Interface(object):
    def __init__(self):
        pass

    def from_csv(self, fpath):
        raise NotImplementedError

    def to_csv(self, fpath):
        raise NotImplementedError

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # process exceptions
        if exc_type is not None:
            LOGGER.exception("%s\n%s\n%s" % (exc_type, exc_val, exc_tb))
            return False
        else:
            return self


class Polysys(Interface):
    def __init__(self):
        super(Polysys).__init__()


class InMAP(Interface):
    def __init__(self):
        super(InMAP).__init__()


class BenMAP(Interface):
    def __init__(self):
        super(BenMAP).__init__()
