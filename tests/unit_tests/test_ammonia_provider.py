"""Tests for AmmoniaFertilizerProvider.

Covers:
- Known-temperature reference values reproduce Bouwman-parameterised rates.
- Monotonicity of each climate modifier function.
- Bounds: NH3 fraction always in [0, 1].
- Output schema matches provider contract.
- Empty / irrelevant records return empty result.
"""
import pytest
import numpy as np
import pandas as pd

from FPEAM.EmissionFactorProviders.ammonia import AmmoniaFertilizerProvider


@pytest.fixture(scope='module')
def provider():
    """Provider using the bundled default parameter table."""
    return AmmoniaFertilizerProvider()


@pytest.fixture
def reference_records():
    """Reference conditions: T=15°C, wind=2 m/s, precip=0 mm, soil=loam."""
    return pd.DataFrame([{
        'region': '17031',
        'resource': 'nitrogen',
        'resource_subtype': st,
        'temperature_c': 15.0,
        'wind_speed_m_s': 2.0,
        'precipitation_mm': 0.0,
        'soil_type': 'loam',
    } for st in AmmoniaFertilizerProvider.FERTILIZER_SUBTYPES])


class TestAmmoniaProviderSchemaAndBounds:

    def test_factors_returns_dataframe(self, provider, reference_records):
        result = provider.factors(reference_records)
        assert isinstance(result, pd.DataFrame)

    def test_output_has_required_columns(self, provider, reference_records):
        from FPEAM.EmissionFactorProviders import EmissionFactorProvider
        result = provider.factors(reference_records)
        assert set(EmissionFactorProvider.RATE_COLUMNS).issubset(set(result.columns))

    def test_rates_bounded_0_to_1(self, provider, reference_records):
        """NH3 fraction must be in [0, 1] for all reference conditions."""
        result = provider.factors(reference_records)
        assert (result['rate'] >= 0).all()
        assert (result['rate'] <= 1).all()

    def test_pollutant_is_nh3(self, provider, reference_records):
        """All output rows are for the NH3 pollutant."""
        result = provider.factors(reference_records)
        assert (result['pollutant'] == 'nh3').all()

    def test_resource_is_nitrogen(self, provider, reference_records):
        result = provider.factors(reference_records)
        assert (result['resource'] == 'nitrogen').all()

    def test_empty_on_irrelevant_records(self, provider):
        """Non-nitrogen inputs return empty result (not an error)."""
        records = pd.DataFrame([{
            'region': '17031', 'resource': 'herbicide',
            'resource_subtype': 'generic herbicide',
        }])
        result = provider.factors(records)
        assert len(result) == 0

    def test_empty_on_no_resource_subtype_column(self, provider):
        """Records with no resource_subtype column return empty result."""
        records = pd.DataFrame([{'region': '17031'}])
        result = provider.factors(records)
        assert len(result) == 0


class TestAmmoniaProviderReferenceValues:

    def test_anhydrous_ammonia_at_reference(self, provider):
        """Anhydrous ammonia at reference conditions → base rate (no modifier)."""
        records = pd.DataFrame([{
            'region': '17031', 'resource': 'nitrogen',
            'resource_subtype': 'anhydrous ammonia',
            'temperature_c': 15.0,
            'wind_speed_m_s': 2.0,
            'precipitation_mm': 0.0,
            'soil_type': 'loam',
        }])
        result = provider.factors(records)
        # At reference conditions all modifiers = 1.0 so rate == base_rate_nh3 = 0.04
        assert abs(result['rate'].iloc[0] - 0.04) < 1e-9

    def test_urea_at_reference(self, provider):
        """Urea at reference conditions → base rate 0.025."""
        records = pd.DataFrame([{
            'region': '17031', 'resource': 'nitrogen',
            'resource_subtype': 'urea',
            'temperature_c': 15.0, 'wind_speed_m_s': 2.0,
            'precipitation_mm': 0.0, 'soil_type': 'loam',
        }])
        result = provider.factors(records)
        assert abs(result['rate'].iloc[0] - 0.025) < 1e-9


class TestAmmoniaProviderMonotonicity:

    def _rate(self, provider, **kwargs):
        defaults = {
            'region': '17031', 'resource': 'nitrogen',
            'resource_subtype': 'urea',
            'temperature_c': 15.0, 'wind_speed_m_s': 2.0,
            'precipitation_mm': 0.0, 'soil_type': 'loam',
        }
        defaults.update(kwargs)
        result = provider.factors(pd.DataFrame([defaults]))
        return result['rate'].iloc[0]

    def test_rate_increases_with_temperature(self, provider):
        """Higher temperature → higher NH3 volatilisation."""
        low = self._rate(provider, temperature_c=5.0)
        mid = self._rate(provider, temperature_c=15.0)
        high = self._rate(provider, temperature_c=30.0)
        assert low < mid < high

    def test_rate_increases_with_wind(self, provider):
        """Higher wind speed → higher NH3 loss."""
        low = self._rate(provider, wind_speed_m_s=0.5)
        mid = self._rate(provider, wind_speed_m_s=2.0)
        assert low < mid

    def test_rate_decreases_with_precipitation(self, provider):
        """More rain → lower NH3 loss (rain washes ammonia into soil)."""
        dry = self._rate(provider, precipitation_mm=0.0)
        wet = self._rate(provider, precipitation_mm=50.0)
        assert dry > wet

    def test_clay_soil_higher_than_sandy(self, provider):
        """Clay soils have higher pH and retain more N, leading to higher NH3 loss."""
        sandy = self._rate(provider, soil_type='sand')
        clay = self._rate(provider, soil_type='clay')
        assert clay > sandy


class TestAmmoniaProviderMissingContext:

    def test_missing_context_uses_defaults(self, provider):
        """Records without context columns return a valid rate using neutral defaults."""
        records = pd.DataFrame([{
            'region': '17031', 'resource': 'nitrogen',
            'resource_subtype': 'urea',
        }])
        result = provider.factors(records)
        assert len(result) == 1
        assert 0 <= result['rate'].iloc[0] <= 1
