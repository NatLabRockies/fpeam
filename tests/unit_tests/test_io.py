"""Tests for FPEAM.IO — load() and load_configs() functions."""
import os
import pytest
import pandas as pd

from FPEAM.IO import load


class TestLoad:
    """Tests for IO.load()."""

    def test_basic_csv(self, tmp_path):
        """load() reads a well-formed CSV into a DataFrame with typed columns."""
        csv = tmp_path / 'sample.csv'
        csv.write_text('feedstock,rate\ncorn grain,1.5\nwheat straw,0.8\n')
        df = load(str(csv), columns={'feedstock': str, 'rate': float})
        assert list(df.columns) == ['feedstock', 'rate']
        assert len(df) == 2
        assert df['rate'].dtype == float

    def test_missing_file_raises(self):
        """load() raises FileNotFoundError for a non-existent path."""
        with pytest.raises((FileNotFoundError, IOError, OSError)):
            load('/does/not/exist.csv', columns={'col': str})

    def test_missing_columns_raises(self, tmp_path):
        """load() raises ValueError naming the missing columns."""
        csv = tmp_path / 'partial.csv'
        csv.write_text('feedstock,rate\ncorn grain,1.5\n')
        with pytest.raises(ValueError, match='activity'):
            load(str(csv), columns={'feedstock': str, 'rate': float, 'activity': str})

    def test_extra_columns_ignored(self, tmp_path):
        """Columns present in the file but not in 'columns' dict are not loaded."""
        csv = tmp_path / 'extra.csv'
        csv.write_text('feedstock,rate,extra_col\ncorn grain,1.5,junk\n')
        df = load(str(csv), columns={'feedstock': str, 'rate': float})
        assert 'extra_col' not in df.columns
        assert len(df) == 1

    def test_nan_handling(self, tmp_path):
        """load() returns NaN for blank cells in float columns."""
        csv = tmp_path / 'nulls.csv'
        csv.write_text('feedstock,rate\ncorn grain,\nwheat straw,0.8\n')
        df = load(str(csv), columns={'feedstock': str, 'rate': float})
        assert pd.isna(df.loc[0, 'rate'])
        assert df.loc[1, 'rate'] == 0.8
