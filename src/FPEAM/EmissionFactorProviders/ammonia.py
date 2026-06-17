"""
AmmoniaFertilizerProvider
=========================

Computes NH3 volatilization from nitrogen fertilizer applications as a
function of fertilizer subtype, application rate, and geophysical context
(temperature, wind speed, precipitation, soil type).

Model form
----------
The provider implements a simplified Bouwman-style multiplicative model::

    NH3_fraction = base_rate(fertilizer_subtype)
                 × f_T(temperature_c)
                 × f_wind(wind_speed_m_s)
                 × f_precip(precipitation_mm)
                 × f_soil(soil_type)

Each modifier function is monotonic in one climate variable and bounded in
[0, 1] relative to the reference condition.  The base rate and modifier
parameters are loaded from a user-replaceable CSV (``ammonia_provider_params.csv``).

References
----------
- Bouwman, A.F. et al. (2002). "Estimation of global NH3 volatilization loss
  from synthetic fertilizers and animal manure applied to arable lands and
  grasslands." *Global Biogeochemical Cycles*, 16(2), 8-1 to 8-14.
  doi:10.1029/2000GB001389
- Pan, B. et al. (2016). "A meta-analysis of fertilizer-induced soil NO and
  combined NO+N2O emissions." *Global Change Biology*, 22(7), 2494-2512.

Context columns consumed
------------------------
temperature_c
    Mean application-period air temperature in °C.
wind_speed_m_s
    Mean wind speed at 2 m height in m/s.
precipitation_mm
    Total precipitation over the 5 days post-application in mm.
soil_type
    USDA texture class string (e.g. ``silty clay loam``).

All context columns are optional; if missing, the corresponding modifier
defaults to 1.0 (neutral).
"""

import importlib.resources
import numpy as np
import pandas as pd

from .base import EmissionFactorProvider
from .. import utils

LOGGER = utils.logger(__name__)

# Default parameter file bundled with the package
_DEFAULT_PARAMS = 'data/inputs/ammonia_provider_params.csv'


def _load_default_params():
    pkg = importlib.resources.files('FPEAM')
    path = str(pkg.joinpath(_DEFAULT_PARAMS))
    return pd.read_csv(path)


class AmmoniaFertilizerProvider(EmissionFactorProvider):
    """Compute NH3 emission rates from N fertilizer applications dynamically.

    Parameters
    ----------
    params : pd.DataFrame or str, optional
        Parameter table (or path to CSV) defining ``base_rate`` and modifier
        parameters per fertilizer subtype.  Defaults to the bundled
        ``ammonia_provider_params.csv``.
    """

    # Fertilizer subtypes handled by this provider
    FERTILIZER_SUBTYPES = frozenset({
        'anhydrous ammonia',
        'ammonium nitrate',
        'ammonium sulfate',
        'urea',
        'nitrogen solutions',
    })

    def __init__(self, params=None):
        if params is None:
            self._params = _load_default_params()
        elif isinstance(params, str):
            self._params = pd.read_csv(params)
        else:
            self._params = pd.DataFrame(params)

        self._params = self._params.set_index('resource_subtype')

    # ── climate modifier functions ────────────────────────────────────────

    @staticmethod
    def _f_temperature(t_c: pd.Series) -> pd.Series:
        """Temperature modifier: logistic increase, saturates at ~30°C.

        f_T = 1 / (1 + exp(-0.15 * (T - 15)))   [reference at 15°C → 0.5]
        Normalised so f_T(15°C) = 1.0.
        """
        ref = 1.0 / (1.0 + np.exp(-0.15 * (15.0 - 15.0)))  # = 0.5
        return (1.0 / (1.0 + np.exp(-0.15 * (t_c - 15.0)))) / ref

    @staticmethod
    def _f_wind(w_m_s: pd.Series) -> pd.Series:
        """Wind speed modifier: square-root increase, capped at 3.0 m/s.

        f_W = min(sqrt(W / 2.0), sqrt(3.0 / 2.0)) / sqrt(2.0 / 2.0)
        Normalised so f_W(2.0 m/s) = 1.0.
        """
        ref = np.sqrt(2.0 / 2.0)  # = 1.0
        return np.minimum(np.sqrt(w_m_s / 2.0), np.sqrt(3.0 / 2.0)) / ref

    @staticmethod
    def _f_precipitation(p_mm: pd.Series) -> pd.Series:
        """Precipitation damping modifier: exponential decay with rain.

        f_P = exp(-0.02 * P)   (Bouwman 2002 parameterisation)
        Normalised so f_P(0 mm) = 1.0 (dry conditions → maximum volatilisation).
        """
        return np.exp(-0.02 * p_mm)

    @staticmethod
    def _f_soil(soil_type: pd.Series) -> pd.Series:
        """Soil modifier: lookup table by USDA texture class.

        Based on Bouwman 2002 Table 2 relative volatilisation adjustments.
        Unknown textures default to 1.0.
        """
        _lookup = {
            'sand': 0.7,
            'loamy sand': 0.75,
            'sandy loam': 0.85,
            'loam': 1.0,
            'silt loam': 1.0,
            'silt': 1.05,
            'sandy clay loam': 0.9,
            'clay loam': 0.95,
            'silty clay loam': 1.05,
            'sandy clay': 0.85,
            'silty clay': 1.1,
            'clay': 1.15,
        }
        return soil_type.str.lower().map(_lookup).fillna(1.0)

    # ── provider interface ────────────────────────────────────────────────

    def factors(self, records: pd.DataFrame) -> pd.DataFrame:
        """Return dynamic NH3 rates for each (region, resource_subtype) combination.

        Only rows where ``resource == 'nitrogen'`` and ``resource_subtype`` is one
        of the recognised fertilizer subtypes produce output rows.  For subtypes not
        handled by this provider no rows are returned (fall through to TableProvider
        or other providers in the chain).

        Parameters
        ----------
        records : pd.DataFrame
            Must contain at minimum ``region`` and ``resource_subtype``.
            Optional context: ``temperature_c``, ``wind_speed_m_s``,
            ``precipitation_mm``, ``soil_type``.

        Returns
        -------
        pd.DataFrame
            One row per (region, resource_subtype, pollutant) combination with
            ``pollutant == 'nh3'``.
        """
        _relevant = records[
            records.get('resource_subtype', pd.Series(dtype=str)).isin(self.FERTILIZER_SUBTYPES)
        ].copy() if 'resource_subtype' in records.columns else pd.DataFrame()

        if _relevant.empty:
            # Return empty frame with the correct columns
            return pd.DataFrame(columns=list(self.RATE_COLUMNS))

        # Apply climate modifiers (default to neutral 1.0 if context not provided)
        t = _relevant.get('temperature_c', pd.Series(15.0, index=_relevant.index))
        w = _relevant.get('wind_speed_m_s', pd.Series(2.0, index=_relevant.index))
        p = _relevant.get('precipitation_mm', pd.Series(0.0, index=_relevant.index))
        s = _relevant.get('soil_type', pd.Series('loam', index=_relevant.index))

        modifier = (self._f_temperature(t)
                    * self._f_wind(w)
                    * self._f_precipitation(p)
                    * self._f_soil(s))

        # Look up base rates for each subtype
        base_rates = _relevant['resource_subtype'].map(
            self._params['base_rate_nh3'].to_dict()
        ).fillna(0.0)

        _relevant = _relevant.copy()
        _relevant['rate'] = (base_rates * modifier).clip(lower=0.0, upper=1.0)
        _relevant['pollutant'] = 'nh3'
        _relevant['resource'] = 'nitrogen'
        _relevant['activity'] = 'chemical application'
        _relevant['unit_numerator'] = 'pound'
        _relevant['unit_denominator'] = 'pound'
        if 'region' not in _relevant.columns:
            _relevant['region'] = None

        result = _relevant[list(self.RATE_COLUMNS)].reset_index(drop=True)
        self.validate_output(result)
        return result
