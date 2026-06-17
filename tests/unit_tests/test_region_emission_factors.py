"""Tests for region-keyed emission factors (Phase 1 of dynamic EF roadmap).

Covers:
- National-only factors produce identical results to pre-region behavior (regression).
- Region-specific factors override national defaults for matching counties.
- Unknown regions fall back to national defaults.
- Mixed CSVs (some regions, some national) work correctly.
"""
import io
import pytest
import pandas as pd

from FPEAM.EngineModules import EmissionFactors
from FPEAM.Data import Equipment, Production, EmissionFactor, ResourceDistribution
from FPEAM.IO import load_configs, _resource_path, CONFIG_FOLDER


@pytest.fixture(scope='module')
def ef_config():
    return load_configs(_resource_path('%s/run_config.ini' % CONFIG_FOLDER))


def _equipment():
    return Equipment(df=pd.DataFrame([{
        'feedstock': 'corn grain', 'tillage_type': 'conventional tillage',
        'equipment_group': 'grp1', 'rotation_year': 1,
        'activity': 'chemical application', 'equipment_name': 'tractor',
        'equipment_horsepower': 100.0, 'resource': 'nitrogen', 'rate': 1.0,
        'unit_numerator': 'lb', 'unit_denominator': 'ac',
    }]), backfill=False)


def _production_two_regions():
    return Production(df=pd.DataFrame([
        {
            'feedstock': 'corn grain', 'tillage_type': 'conventional tillage',
            'region_production': 'REGION_A', 'region_destination': 'REGION_A',
            'equipment_group': 'grp1', 'feedstock_measure': 'harvested',
            'feedstock_amount': 100.0, 'unit_numerator': 'dt', 'unit_denominator': 'ac',
            'source_lon': -87.6, 'source_lat': 41.8,
            'destination_lon': -87.6, 'destination_lat': 41.8,
        },
        {
            'feedstock': 'corn grain', 'tillage_type': 'conventional tillage',
            'region_production': 'REGION_B', 'region_destination': 'REGION_B',
            'equipment_group': 'grp1', 'feedstock_measure': 'harvested',
            'feedstock_amount': 200.0, 'unit_numerator': 'dt', 'unit_denominator': 'ac',
            'source_lon': -95.0, 'source_lat': 40.0,
            'destination_lon': -95.0, 'destination_lat': 40.0,
        },
    ]), backfill=False)


# Minimal factors CSV content (national, no region column)
_NATIONAL_FACTORS_CSV = """\
resource,resource_subtype,activity,pollutant,rate,unit_numerator,unit_denominator
nitrogen,anhydrous ammonia,chemical application,nh3,0.04,pound,pound
"""

# Regional factors CSV: REGION_A gets a higher rate; REGION_B falls back to national
_REGIONAL_FACTORS_CSV = """\
resource,resource_subtype,activity,pollutant,rate,unit_numerator,unit_denominator,region
nitrogen,anhydrous ammonia,chemical application,nh3,0.04,pound,pound,
nitrogen,anhydrous ammonia,chemical application,nh3,0.10,pound,pound,REGION_A
"""

_DISTRIBUTION_CSV = """\
feedstock,resource,resource_subtype,distribution
corn grain,nitrogen,anhydrous ammonia,1.0
"""


def _make_ef_from_csv(config, equip, prod, factors_csv, dist_csv=_DISTRIBUTION_CSV):
    """Construct EmissionFactors from in-memory CSV strings via temporary files."""
    import tempfile, os

    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f_ef:
        f_ef.write(factors_csv)
        ef_path = f_ef.name
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f_rd:
        f_rd.write(dist_csv)
        rd_path = f_rd.name

    # Patch config to point at temp files
    from configobj import ConfigObj
    cfg = ConfigObj(config)
    cfg['emission_factors'] = ef_path
    cfg['resource_distribution'] = rd_path

    try:
        ef = EmissionFactors(config=cfg, equipment=equip, production=prod)
        ef.run()
        return ef
    finally:
        os.unlink(ef_path)
        os.unlink(rd_path)


class TestNationalOnlyFactors:

    def test_national_regression(self, ef_config):
        """National-only CSV: behavior identical to pre-region implementation."""
        equip = _equipment()
        prod = _production_two_regions()
        ef = _make_ef_from_csv(ef_config, equip, prod, _NATIONAL_FACTORS_CSV)
        assert ef.status == 'complete'
        # Both regions get the same national rate (0.04 lb/lb × 1 lb/unit × feedstock)
        assert len(ef.results) > 0
        assert not ef._has_region_factors
        results_by_region = ef.results.groupby('region_production')['pollutant_amount'].sum()
        # region B has 2× the feedstock amount so 2× the emissions
        assert abs(results_by_region['REGION_B'] / results_by_region['REGION_A'] - 2.0) < 1e-9


class TestRegionKeyedFactors:

    def test_region_flag_detected(self, ef_config):
        """EmissionFactors detects region column in factors CSV."""
        equip = _equipment()
        prod = _production_two_regions()
        ef = _make_ef_from_csv(ef_config, equip, prod, _REGIONAL_FACTORS_CSV)
        assert ef._has_region_factors

    def test_regional_rate_applied_to_region_a(self, ef_config):
        """REGION_A gets the higher regional rate (0.10), not the national rate (0.04)."""
        equip = _equipment()
        prod = _production_two_regions()
        ef = _make_ef_from_csv(ef_config, equip, prod, _REGIONAL_FACTORS_CSV)
        assert ef.status == 'complete'
        results_a = ef.results[ef.results['region_production'] == 'REGION_A']['pollutant_amount'].sum()
        # REGION_A: 100 feedstock × 1 lb/unit × 0.10 rate
        assert abs(results_a - 10.0) < 1e-9

    def test_national_fallback_for_region_b(self, ef_config):
        """REGION_B (no regional override) falls back to national rate (0.04)."""
        equip = _equipment()
        prod = _production_two_regions()
        ef = _make_ef_from_csv(ef_config, equip, prod, _REGIONAL_FACTORS_CSV)
        results_b = ef.results[ef.results['region_production'] == 'REGION_B']['pollutant_amount'].sum()
        # REGION_B: 200 feedstock × 1 lb/unit × 0.04 rate
        assert abs(results_b - 8.0) < 1e-9

    def test_required_columns_present(self, ef_config):
        """Results have standard output columns regardless of regional mode."""
        equip = _equipment()
        prod = _production_two_regions()
        ef = _make_ef_from_csv(ef_config, equip, prod, _REGIONAL_FACTORS_CSV)
        required = {'region_production', 'region_destination', 'feedstock',
                    'tillage_type', 'module', 'activity', 'resource',
                    'resource_subtype', 'pollutant', 'pollutant_amount'}
        assert required.issubset(set(ef.results.columns))
        assert 'region' not in ef.results.columns  # internal column must not leak out

    def test_no_duplicate_rows_for_region_a(self, ef_config):
        """Region A should not also appear with the national rate."""
        equip = _equipment()
        prod = _production_two_regions()
        ef = _make_ef_from_csv(ef_config, equip, prod, _REGIONAL_FACTORS_CSV)
        rows_a = ef.results[ef.results['region_production'] == 'REGION_A']
        # With one feedstock measure row and one resource/subtype there should be exactly one result row
        assert len(rows_a) == 1


class TestDynamicProviderNotYetWired:

    def test_ammonia_fertilizer_provider_config_raises_not_implemented(self, ef_config):
        """Configuring provider=ammonia_fertilizer must raise NotImplementedError
        until the geophysical context → get_emissions() wiring is complete."""
        import tempfile, os
        from configobj import ConfigObj
        cfg = ConfigObj(ef_config)
        cfg['provider'] = 'ammonia_fertilizer'

        equip = _equipment()
        prod = _production_two_regions()

        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(_NATIONAL_FACTORS_CSV)
            ef_path = f.name
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(_DISTRIBUTION_CSV)
            rd_path = f.name
        cfg['emission_factors'] = ef_path
        cfg['resource_distribution'] = rd_path

        try:
            with pytest.raises(NotImplementedError):
                EmissionFactors(config=cfg, equipment=equip, production=prod)
        finally:
            os.unlink(ef_path)
            os.unlink(rd_path)
