"""TableProvider — wraps existing static CSV-based emission factors.

This provider is a thin adapter that makes the existing EmissionFactor /
ResourceDistribution CSV pair available behind the EmissionFactorProvider
interface.  It is the default provider used when no explicit provider is
configured in run_config.

The static overall_factors table (pre-computed in EmissionFactors.__init__)
is passed in directly, so no additional I/O occurs at call time.
"""

import pandas as pd

from .base import EmissionFactorProvider


class TableProvider(EmissionFactorProvider):
    """Provides rates from a pre-loaded static factors table.

    Parameters
    ----------
    overall_factors : pd.DataFrame
        The merged and aggregated factors table produced by
        ``EmissionFactors.__init__``.  Must contain at minimum:
        feedstock, activity, resource, resource_subtype, pollutant, overall_rate.
        Optionally also contains ``region`` when region-keyed factors are loaded.
    """

    def __init__(self, overall_factors: pd.DataFrame):
        self._factors = overall_factors.copy()
        # Rename overall_rate → rate to match the provider contract
        if 'overall_rate' in self._factors.columns and 'rate' not in self._factors.columns:
            self._factors = self._factors.rename(columns={'overall_rate': 'rate'})
        # Ensure unit columns exist (static table may not carry them post-groupby)
        if 'unit_numerator' not in self._factors.columns:
            self._factors['unit_numerator'] = 'pound'
        if 'unit_denominator' not in self._factors.columns:
            self._factors['unit_denominator'] = 'pound'
        if 'region' not in self._factors.columns:
            self._factors['region'] = None

    def factors(self, records: pd.DataFrame) -> pd.DataFrame:
        """Return the pre-loaded static factors (ignores dynamic context columns).

        The static table already contains national and (optionally) region-keyed
        rows.  The caller is responsible for performing any region-based join or
        national-fallback logic.

        Note: RATE_COLUMNS does not include ``feedstock``.  The feedstock
        dimension enters the calculation in ``EmissionFactors.get_emissions()``
        via the resource_distribution merge that produced ``overall_factors``
        before this provider was constructed.  Providers are intentionally
        feedstock-agnostic; the same rates apply across all feedstocks that
        use the same resource subtype.
        """
        result = self._factors[list(self.RATE_COLUMNS)].copy()
        self.validate_output(result)
        return result
