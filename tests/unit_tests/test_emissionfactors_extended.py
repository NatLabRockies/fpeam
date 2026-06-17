"""Edge-case tests for EmissionFactors module.

These complement the golden-CSV regression in test_emissionfactors.py with
focused unit-level checks that do not require a full production dataset.
"""
import pytest
import pandas as pd

from FPEAM.EngineModules import EmissionFactors
from FPEAM.IO import load_configs, _resource_path, CONFIG_FOLDER


@pytest.fixture(scope='module')
def ef_config():
    return load_configs(_resource_path('%s/run_config.ini' % CONFIG_FOLDER))


def _make_equipment(feedstock='corn grain', resource='nitrogen', rate=1.0):
    return pd.DataFrame([{
        'feedstock': feedstock, 'tillage_type': 'conventional tillage',
        'equipment_group': 'grp1', 'rotation_year': 1,
        'activity': 'chemical application',
        'equipment_name': 'tractor', 'equipment_horsepower': 100.0,
        'resource': resource, 'rate': rate,
        'unit_numerator': 'lb', 'unit_denominator': 'ac',
    }])


def _make_production(feedstock='corn grain', feedstock_measure='harvested',
                     feedstock_amount=100.0):
    return pd.DataFrame([{
        'feedstock': feedstock, 'tillage_type': 'conventional tillage',
        'region_production': '17031', 'region_destination': '17031',
        'equipment_group': 'grp1',
        'feedstock_measure': feedstock_measure,
        'feedstock_amount': feedstock_amount,
        'unit_numerator': 'dt', 'unit_denominator': 'ac',
        'source_lon': -87.6, 'source_lat': 41.8,
        'destination_lon': -87.6, 'destination_lat': 41.8,
    }])


class TestEmissionFactorsEdgeCases:

    def test_empty_production_returns_empty_results(self, ef_config):
        """EmissionFactors.run() with an empty production frame returns empty results."""
        from FPEAM.Data import Equipment, Production
        # build minimal but typed empty frames using the Data subclass
        equip_df = _make_equipment()
        prod_df = _make_production()
        equip = Equipment(df=equip_df, backfill=False)
        # empty production — one row but wrong feedstock_measure so nothing matches
        prod = Production(df=_make_production(feedstock_measure='nonexistent'), backfill=False)
        with EmissionFactors(config=ef_config, equipment=equip, production=prod) as ef:
            ef.run()
        assert ef.status == 'complete'
        assert ef.results is not None
        assert len(ef.results) == 0

    def test_non_default_feedstock_measure_type_filters_correctly(self, ef_config):
        """Only rows matching feedstock_measure_type contribute to results."""
        from FPEAM.Data import Equipment, Production
        equip = Equipment(df=_make_equipment(), backfill=False)
        # two rows: one 'harvested', one 'production'
        mixed = pd.concat([
            _make_production(feedstock_measure='harvested'),
            _make_production(feedstock_measure='production', feedstock_amount=999.0),
        ], ignore_index=True)
        prod = Production(df=mixed, backfill=False)
        with EmissionFactors(config=ef_config, equipment=equip, production=prod) as ef:
            ef.run()
        # default feedstock_measure_type is 'harvested'
        # the 999-unit production row should not appear in results
        assert ef.status == 'complete'
        assert ef.results is not None
        # all results should come from the 100-unit row, not 999
        assert (ef.results['pollutant_amount'] <= 150).all(), \
            "Expected only harvested-measure rows; production-measure row leaked in"

    def test_run_sets_status_complete_on_success(self, ef_config):
        """Successful run() sets module status to 'complete'."""
        from FPEAM.Data import Equipment, Production
        equip = Equipment(df=_make_equipment(), backfill=False)
        prod = Production(df=_make_production(), backfill=False)
        with EmissionFactors(config=ef_config, equipment=equip, production=prod) as ef:
            ef.run()
        assert ef.status == 'complete'

    def test_results_have_required_columns(self, ef_config):
        """Results DataFrame always has the expected output columns."""
        from FPEAM.Data import Equipment, Production
        equip = Equipment(df=_make_equipment(), backfill=False)
        prod = Production(df=_make_production(), backfill=False)
        with EmissionFactors(config=ef_config, equipment=equip, production=prod) as ef:
            ef.run()
        required = {'region_production', 'region_destination', 'feedstock',
                    'tillage_type', 'module', 'activity', 'resource',
                    'resource_subtype', 'pollutant', 'pollutant_amount'}
        assert required.issubset(set(ef.results.columns))

    def test_pollutant_amounts_are_non_negative(self, ef_config):
        """Emission factors and rates are non-negative so results should be too."""
        from FPEAM.Data import Equipment, Production
        equip = Equipment(df=_make_equipment(), backfill=False)
        prod = Production(df=_make_production(), backfill=False)
        with EmissionFactors(config=ef_config, equipment=equip, production=prod) as ef:
            ef.run()
        assert (ef.results['pollutant_amount'] >= 0).all()
