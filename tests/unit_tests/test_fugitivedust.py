"""Focused unit tests for FugitiveDust on-farm emissions path."""
import pytest
import pandas as pd

from FPEAM.EngineModules.FugitiveDust import FugitiveDust
from FPEAM.IO import load_configs, _resource_path, CONFIG_FOLDER
from FPEAM.Data import FeedstockLossFactors, TruckCapacity, Production


@pytest.fixture(scope='module')
def fd_config():
    return load_configs(_resource_path('%s/run_config.ini' % CONFIG_FOLDER))


@pytest.fixture(scope='module')
def minimal_production():
    """Single harvested row for corn grain, no router path."""
    return Production(df=pd.DataFrame([{
        'feedstock': 'corn grain',
        'tillage_type': 'conventional tillage',
        'region_production': '17031',
        'region_destination': '17031',
        'equipment_group': 'grp1',
        'feedstock_measure': 'harvested',
        'feedstock_amount': 1000.0,
        'unit_numerator': 'dt',
        'unit_denominator': 'ac',
        'source_lon': -87.6298,
        'source_lat': 41.8781,
        'destination_lon': -87.6298,
        'destination_lat': 41.8781,
        'row_id': 0,
    }]), backfill=False)


@pytest.fixture(scope='module')
def minimal_loss_factors():
    return FeedstockLossFactors(df=pd.DataFrame([{
        'feedstock': 'corn grain',
        'supply_chain_stage': 'farm gate',
        'dry_matter_loss': 0.1,
    }]), backfill=False)


@pytest.fixture(scope='module')
def minimal_truck_capacity():
    return TruckCapacity(df=pd.DataFrame([{
        'feedstock': 'corn grain',
        'truck_capacity': 25.0,
        'unit_numerator': 'dt',
        'unit_denominator': 'trip',
    }]), backfill=False)


class TestFugitiveDustOnFarm:

    def test_onfarm_run_returns_pm10_and_pm25(
        self, fd_config, minimal_production, minimal_loss_factors,
        minimal_truck_capacity
    ):
        """get_onfarm_fugitivedust returns rows for PM10 and PM2.5."""
        fd = FugitiveDust(
            config=fd_config,
            production=minimal_production,
            feedstock_loss_factors=minimal_loss_factors,
            truck_capacity=minimal_truck_capacity,
            vmt_short_haul=20,
            forestry_feedstock_names=[],
            router=None,
            backfill=True,
        )
        result = fd.get_onfarm_fugitivedust()
        assert set(result['pollutant'].unique()) >= {'pm10', 'pm25'}

    def test_onfarm_emissions_positive(
        self, fd_config, minimal_production, minimal_loss_factors,
        minimal_truck_capacity
    ):
        """On-farm emissions are non-negative for valid inputs."""
        fd = FugitiveDust(
            config=fd_config,
            production=minimal_production,
            feedstock_loss_factors=minimal_loss_factors,
            truck_capacity=minimal_truck_capacity,
            vmt_short_haul=20,
            forestry_feedstock_names=[],
            router=None,
            backfill=True,
        )
        result = fd.get_onfarm_fugitivedust()
        assert (result['pollutant_amount'] >= 0).all()

    def test_run_without_router_completes(
        self, fd_config, minimal_production, minimal_loss_factors,
        minimal_truck_capacity
    ):
        """run() without a router finishes with status='complete'."""
        fd = FugitiveDust(
            config=fd_config,
            production=minimal_production,
            feedstock_loss_factors=minimal_loss_factors,
            truck_capacity=minimal_truck_capacity,
            vmt_short_haul=20,
            forestry_feedstock_names=[],
            router=None,
            backfill=True,
        )
        fd.run()
        assert fd.status == 'complete'
        assert fd.results is not None
        assert len(fd.results) > 0
