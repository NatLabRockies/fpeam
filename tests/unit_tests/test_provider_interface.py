"""Tests for the EmissionFactorProvider ABC and TableProvider adapter."""
import pytest
import pandas as pd

from FPEAM.EmissionFactorProviders import EmissionFactorProvider, TableProvider


# ── fixtures ────────────────────────────────────────────────────────────────

@pytest.fixture
def minimal_factors():
    """Minimal overall_factors table as produced by EmissionFactors.__init__."""
    return pd.DataFrame([{
        'feedstock': 'corn grain', 'activity': 'chemical application',
        'resource': 'nitrogen', 'resource_subtype': 'anhydrous ammonia',
        'pollutant': 'nh3', 'overall_rate': 0.04,
    }])


@pytest.fixture
def regional_factors():
    """overall_factors table with a region column."""
    return pd.DataFrame([
        {
            'feedstock': 'corn grain', 'activity': 'chemical application',
            'resource': 'nitrogen', 'resource_subtype': 'anhydrous ammonia',
            'pollutant': 'nh3', 'overall_rate': 0.04, 'region': None,
        },
        {
            'feedstock': 'corn grain', 'activity': 'chemical application',
            'resource': 'nitrogen', 'resource_subtype': 'anhydrous ammonia',
            'pollutant': 'nh3', 'overall_rate': 0.10, 'region': 'REGION_A',
        },
    ])


# ── ABC contract ─────────────────────────────────────────────────────────────

class TestEmissionFactorProviderABC:

    def test_cannot_instantiate_abc_directly(self):
        """EmissionFactorProvider is abstract and cannot be instantiated."""
        with pytest.raises(TypeError):
            EmissionFactorProvider()

    def test_concrete_subclass_must_implement_factors(self):
        """Subclass without factors() implementation raises TypeError at instantiation."""
        class IncompleteProvider(EmissionFactorProvider):
            pass

        with pytest.raises(TypeError):
            IncompleteProvider()

    def test_validate_output_raises_on_missing_columns(self):
        """validate_output raises ValueError when required columns are absent."""
        class MinimalProvider(EmissionFactorProvider):
            def factors(self, records):
                return pd.DataFrame()

        provider = MinimalProvider()
        with pytest.raises(ValueError, match='missing required columns'):
            provider.validate_output(pd.DataFrame({'region': [None]}))


# ── TableProvider ────────────────────────────────────────────────────────────

class TestTableProvider:

    def test_factors_returns_dataframe(self, minimal_factors):
        """factors() always returns a DataFrame."""
        provider = TableProvider(minimal_factors)
        result = provider.factors(pd.DataFrame())
        assert isinstance(result, pd.DataFrame)

    def test_factors_has_required_columns(self, minimal_factors):
        """All RATE_COLUMNS are present in the output."""
        provider = TableProvider(minimal_factors)
        result = provider.factors(pd.DataFrame())
        assert set(EmissionFactorProvider.RATE_COLUMNS).issubset(set(result.columns))

    def test_overall_rate_renamed_to_rate(self, minimal_factors):
        """overall_rate from the source table is exposed as 'rate' in the output."""
        provider = TableProvider(minimal_factors)
        result = provider.factors(pd.DataFrame())
        assert 'rate' in result.columns
        assert 'overall_rate' not in result.columns

    def test_national_row_has_null_region(self, minimal_factors):
        """A factors table without a region column gets a null region column."""
        provider = TableProvider(minimal_factors)
        result = provider.factors(pd.DataFrame())
        assert 'region' in result.columns
        assert result['region'].isna().all()

    def test_regional_factors_preserved(self, regional_factors):
        """A factors table with region column retains both national and regional rows."""
        provider = TableProvider(regional_factors)
        result = provider.factors(pd.DataFrame())
        assert len(result) == 2
        assert result['region'].notna().any()
        assert result['region'].isna().any()

    def test_unit_columns_added_when_missing(self, minimal_factors):
        """Unit columns are added with pound/pound defaults when absent from source."""
        provider = TableProvider(minimal_factors)
        result = provider.factors(pd.DataFrame())
        assert (result['unit_numerator'] == 'pound').all()
        assert (result['unit_denominator'] == 'pound').all()
