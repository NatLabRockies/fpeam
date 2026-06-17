import pytest
from importlib.resources import files as _pkg_files

from FPEAM.EngineModules import EmissionFactors
from FPEAM.IO import load_configs, CONFIG_FOLDER, DATA_FOLDER
from FPEAM import Data
import pandas


def _r(relpath):
    return str(_pkg_files('FPEAM').joinpath(relpath))


@pytest.fixture(scope='module')
def config():
    """
    Provide access to default configuration
    :return: [ConfigObj]
    """

    return load_configs(_r('%s/run_config.ini' % CONFIG_FOLDER))


@pytest.fixture(scope='module')
def default_emission_factors_results():
    """
    Provide access to results for the default configuration.
    :return: [DataFrame]
    """

    return pandas.read_csv(_r('%s/outputs/default_emission_factors_results.csv' % DATA_FOLDER),
                           index_col=False, dtype={'region_production': str,
                                                   'region_destination': str})


@pytest.fixture(scope='module')
def equipment():
    """
    Provide access to default equipment list.
    :return: [DataFrame]
    """

    return Data.Equipment(fpath=_r('%s/equipment/bts16_equipment.csv' % DATA_FOLDER))


@pytest.fixture(scope='module')
def production():
    """
    Provide access to default production data.
    :return: [DataFrame]
    """

    return Data.Production(fpath=_r('%s/production/production_2015_bc1060.csv' % DATA_FOLDER))


def test_emission_factors_run(config, equipment, production, default_emission_factors_results):

    _kvals = {'config': config,
              'equipment': equipment,
              'production': production}

    with EmissionFactors(**_kvals) as EF:
        EF.run()

        assert EF.results.round(3).equals(default_emission_factors_results.round(3))
