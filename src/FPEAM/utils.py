"""Shared utilities and simple objects"""

import logging
from validate import (VdtTypeError, VdtValueError, ValidateError)

LOGGER = logging.getLogger(name=__name__)


def logger(name='FPEAM'):
    """
    Produce Logger.

    :param name: [string]
    :return: [Logger]
    """

    return logging.getLogger(name=name)


def validate_config(config, spec):
    """
    Perform validation against <config> using <spec>, returning type-casted ConfigObj, any errors,
    and any extra values.

    :param config: [ConfigObj]
    :param spec: [string] filepath to config specification file
    :return: [dict] {config: ConfigObj,
                     errors: {<section>: <error>, ...},
                     missing: [<section>, ...]
                     extras: {<section>: <value>, ...}
                     }
    """

    from validate import Validator
    from configobj import (ConfigObj, flatten_errors, get_extra_values)

    _return = {'config': None, 'errors': {}, 'missing': [], 'extras': {}}

    _validator = Validator()
    _validator.functions['filepath'] = filepath
    _config = ConfigObj(config, configspec=spec, stringify=True)
    _result = _config.validate(_validator, preserve_errors=True)

    # http://configobj.readthedocs.io/en/latest/configobj.html#flatten-errors
    for _entry in flatten_errors(_config, _result):
        _section_list, _key, _error = _entry
        if _key is not None:
            _return['errors'][_key] = _error
            _section_list.append(_key)
        elif _error is False:
            _return['missing'].append(_key)

    # http://configobj.readthedocs.io/en/latest/configobj.html#get-extra-values
    for _sections, _name in get_extra_values(_config):

        # this code gets the extra values themselves
        _the_section = _config
        for _subsection in _sections:
            _the_section = _the_section[_subsection]

        # the_value may be a section or a value
        _the_value = _the_section[_name]

        _return['extras'][_name] = _the_value

    _return['config'] = _config

    return _return


def filepath(fpath, max_length=None):
    """
    Validate filepath <fpath> by asserting it exists.

    :param fpath: [string]
    :return: [bool] True on success
    """

    if max_length:
        try:
            assert len(fpath) <= int(max_length)
        except AssertionError:
            raise VdtPathTooLong(fpath, max_length)

    from os.path import exists, abspath, expanduser
    from pathlib import Path
    from pkg_resources import resource_filename

    # get a full path
    if fpath.startswith('~'):
        _fpath = expanduser(fpath)
    elif fpath.startswith('.'):
        _fpath = abspath(fpath)
    else:
        _fpath = fpath

    LOGGER.debug('validating %s' % fpath)

    # check if exists as regular file
    _exists = exists(_fpath)

    try:
        assert _exists
    except AssertionError:
        # convert to resource filename if not regular file
        try:
            _fpath = resource_filename('FPEAM', _fpath)
        except ValueError:
            raise VdtPathDoesNotExist(value=fpath)
    else:
        return Path(_fpath)

    # check if resource exists
    _exists = exists(_fpath)

    try:
        assert _exists
    except AssertionError:
        raise VdtPathDoesNotExist(value=fpath)
    else:
        return _fpath


class VdtPathDoesNotExist(VdtValueError):
    """The value supplied is an invalid path."""

    def __init__(self, value):
        """
        >>> raise VdtPathDoesNotExist('/not/a/path')
        Traceback (most recent call last):
        VdtValueTooSmallError: the path "/not/a/path" does not exist
        """

        ValidateError.__init__(self, 'the path "%s" does not exist' % (value, ))


class VdtPathTooLong(VdtValueError):
    """The value supplied has too many characteres."""

    def __init__(self, value, max_length):
        """
        >>> raise VdtPathTooLong('/path/too/long')
        Traceback (most recent call last):
        VdtValueTooSmallError: the path "/path/too/long" exceeds the maximum length of <length> characters
        """

        ValidateError.__init__(self, 'the path "%s" exceeds the maximum length of %s characters' % (value, max_length))
