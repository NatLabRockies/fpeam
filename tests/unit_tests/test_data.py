"""Focused tests for FPEAM.Data base class validation flow.

Covers the regression fixed in `Data.__init__` where:
- the RuntimeError message used the module __name__ instead of the class name
- failed validation on caller-supplied data was caught and silently swallowed
- the `df=` keyword was effectively unused because `load()` always ran when
  `fpath` was None, crashing on `os.path.abspath(None)` before validation
"""
import unittest

import pandas as pd

from FPEAM.Data import Data, RegionFipsMap


class _StrictData(Data):
    """Subclass that fails validation when the frame is missing a 'required' column."""

    COLUMNS = (
        {'name': 'required', 'type': str, 'index': True, 'backfill': None},
    )

    def __init__(self, df=None, fpath=None, backfill=True):
        super().__init__(
            df=df,
            fpath=fpath,
            columns={c['name']: c['type'] for c in self.COLUMNS},
            backfill=backfill,
        )

    def validate(self):
        return 'required' in self.columns and not self.empty


class DataInitTest(unittest.TestCase):

    def test_default_construction_does_not_raise(self):
        """Data() with no arguments yields an empty frame without enforcing validation."""
        d = Data()
        self.assertTrue(d.empty)
        self.assertEqual(d.source, 'DataFrame')

    def test_explicit_empty_df_triggers_validation_failure(self):
        """Passing an explicit empty DataFrame is treated as supplied data and must validate."""
        with self.assertRaises(RuntimeError) as ctx:
            _StrictData(df=pd.DataFrame())
        self.assertIn('_StrictData', str(ctx.exception),
                      msg='RuntimeError should name the failing subclass')
        self.assertIn('source=', str(ctx.exception),
                      msg='RuntimeError should expose the data source for debugging')

    def test_valid_df_constructs_cleanly(self):
        d = _StrictData(df=pd.DataFrame({'required': ['a', 'b']}))
        self.assertFalse(d.empty)
        self.assertEqual(d.source, 'DataFrame')


class RegionFipsMapValidationTest(unittest.TestCase):

    def test_duplicate_region_raises(self):
        """RegionFipsMap.validate raises ValueError when regions or FIPS are non-unique."""
        df = pd.DataFrame({
            'region': ['r1', 'r1', 'r2'],
            'fips': ['00001', '00002', '00003'],
        })
        with self.assertRaises(ValueError):
            RegionFipsMap(df=df, backfill=False)


if __name__ == '__main__':
    unittest.main()
