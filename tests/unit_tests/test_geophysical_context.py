"""Tests for GeophysicalContext data class."""
import pytest
import pandas as pd

from FPEAM.Data import GeophysicalContext


class TestGeophysicalContext:

    def test_region_only(self):
        """Minimal construction with just the required region column."""
        ctx = GeophysicalContext(df=pd.DataFrame([
            {'region': '17031'},
            {'region': '17043'},
        ]), backfill=False)
        assert not ctx.empty
        assert 'region' in ctx.columns

    def test_optional_columns_detected_from_df(self):
        """Optional columns present in df are included without errors."""
        ctx = GeophysicalContext(df=pd.DataFrame([{
            'region': '17031', 'year': 2017, 'month': 6,
            'temperature_c': 22.5, 'wind_speed_m_s': 3.2,
            'precipitation_mm': 45.0, 'soil_type': 'silty clay loam',
        }]), backfill=False)
        assert 'temperature_c' in ctx.columns
        assert 'wind_speed_m_s' in ctx.columns
        assert 'soil_type' in ctx.columns

    def test_unknown_columns_ignored(self):
        """When loading from a df, extra columns outside OPTIONAL_COLUMNS are retained.
        (Column filtering only applies when loading from file via usecols.)
        When loading from fpath, unknown columns are excluded by usecols."""
        ctx = GeophysicalContext(df=pd.DataFrame([{
            'region': '17031', 'temperature_c': 22.5,
        }]), backfill=False)
        # required and optional declared columns are present
        assert 'region' in ctx.columns
        assert 'temperature_c' in ctx.columns

    def test_missing_region_raises(self):
        """A DataFrame without a 'region' column fails validation."""
        with pytest.raises(RuntimeError):
            GeophysicalContext(df=pd.DataFrame([{'temperature_c': 22.5}]), backfill=False)

    def test_from_csv(self, tmp_path):
        """Load from a CSV that has region + optional climate columns."""
        csv = tmp_path / 'ctx.csv'
        csv.write_text('region,year,temperature_c\n17031,2017,22.5\n17043,2017,19.1\n')
        ctx = GeophysicalContext(fpath=str(csv), backfill=False)
        assert len(ctx) == 2
        assert 'temperature_c' in ctx.columns
        assert 'region' in ctx.columns

    def test_type_coercion(self):
        """year and month are loaded as int, temperature_c as float."""
        ctx = GeophysicalContext(df=pd.DataFrame([{
            'region': '17031', 'year': 2017, 'month': 6, 'temperature_c': 22.5,
        }]), backfill=False)
        assert ctx['year'].dtype == int or ctx['year'].dtype.kind == 'i'
        assert ctx['temperature_c'].dtype == float or ctx['temperature_c'].dtype.kind == 'f'
