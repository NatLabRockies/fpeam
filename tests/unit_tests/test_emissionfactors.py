import pytest

from FPEAM.EngineModules import EmissionFactors
from FPEAM.IO import load_configs, CONFIG_FOLDER, DATA_FOLDER
from FPEAM import Data
from pkg_resources import resource_filename
import pandas


@pytest.fixture(scope='module')
def config():
    """
    Provide access to default configuration
    :return: [ConfigObj]
    """

    _fpath = resource_filename('FPEAM', '%s/run_config.ini' % CONFIG_FOLDER)

    return load_configs(_fpath)


@pytest.fixture(scope='module')
def default_emission_factors_results():
    """
    Provide access to results for the default configuration.
    :return: [DataFrame]
    """

    _fpath = resource_filename('FPEAM', '%s/outputs/default_emission_factors_results.csv' % DATA_FOLDER)

    return pandas.read_csv(_fpath, index_col=False, dtype={'region_production': str,
                                                           'region_destination': str})


@pytest.fixture(scope='module')
def equipment():
    """
    Provide access to default equipment list.
    :return: [DataFrame]
    """

    _fpath = resource_filename('FPEAM', '%s/equipment/bts16_equipment.csv' % DATA_FOLDER)

    return Data.Equipment(fpath=_fpath)


@pytest.fixture(scope='module')
def production():
    """
    Provide access to default production data.
    :return: [DataFrame]
    """

    _fpath = resource_filename('FPEAM', '%s/production/production_2015_bc1060.csv' % DATA_FOLDER)

    return Data.Production(fpath=_fpath)


def test_emission_factors_run(config, equipment, production, default_emission_factors_results):

    _kvals = {'config': config,
              'equipment': equipment,
              'production': production}

    with EmissionFactors(**_kvals) as EF:
        EF.run()

        assert EF.results.round(3).equals(default_emission_factors_results.round(3))
