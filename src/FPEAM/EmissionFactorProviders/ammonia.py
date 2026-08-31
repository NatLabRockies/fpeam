"""
AmmoniaFertilizerProvider
=========================

Computes NH3 volatilization from nitrogen fertilizer applications as a
function of fertilizer subtype and geophysical context (air temperature, wind
speed and soil pH).

Model form
----------
The provider applies a multiplicative model::

    NH3_fraction = base_rate(fertilizer_subtype)
                 × f_T(temperature_c)
                 × f_wind(wind_speed_m_s)
                 × f_pH(soil_ph)

The multiplicative structure and the three modifier functions are those of
Zhan et al. (2021), whose Eq. 1a expresses the cropland volatilization rate as
a product of a reference rate and independent correction terms::

    VR = VR0 × f(pH) × f(A) × f(u) × f(T) × f(M)

where A is mean daily air temperature over the growing season, u is wind speed
at 10 m, f(T) is a fertilizer-type term and f(M) a placement term. FPEAM
carries fertilizer subtype in ``base_rate_nh3`` and does not carry placement,
so f(T) and f(M) are not applied here; the remaining three terms are used.

Each term is applied as a ratio to its value at the reference condition. The
fitted prefactors cancel under that normalisation, so only the exponents and
the wind slope enter. This matters because the pH prefactor is the least
determined coefficient in Table S5 (0.0429 with a standard error of 0.0509).

Coefficients (Zhan et al. 2021, Table S5, upland crops)
-------------------------------------------------------
- ``f(pH) = 0.0429 × exp(0.4955 × pH)``, n=42, R2=0.33
- ``f(A)  = 0.1790 × exp(0.0940 × A)``, n=42, R2=0.61
- ``f(u)  = 0.2737 × ln(u) + 0.9975``, n=60, R2=0.77

Reference condition (Zhan et al. 2021, Table S3): VR0 = 9.34% for upland
crops, measured with broadcast urea by dynamic chamber at a mean daily air
temperature of 20 C and a soil pH of 7.0. Table S3 reports observed ranges of
0.6 to 29.0 C for temperature and 5.5 to 8.6 for pH.

Provenance and known limitations
--------------------------------
1. The per-subtype ``base_rate`` values are not from Zhan et al. (2021) and
   not from Bouwman et al. (2002). They are the pre-existing FPEAM static NH3
   emission factors in ``emission_factors.csv``, rounded to three decimals.
   Per the FPEAM README those factors derive from the Carnegie Mellon
   University fertilizer ammonia inventory of Goebes et al. (2003) together
   with Davidson et al. (2004) and the 17/14 NH3-to-N mass ratio. The README
   records that the Davidson et al. source could not be verified online as of
   2018-07-02. Using Zhan modifiers on Goebes base rates preserves the
   FPEAM national level while taking the spatial response from Zhan.
2. Zhan et al. (2021) report no reference wind speed. The 2 m/s reference is
   an FPEAM choice. Because ``f(u)`` is logarithmic it equals 1 at
   u = 1.009 m/s and reaches zero at u = 0.026 m/s, so a wind floor is
   required for numerical safety.
3. Wind speed is defined at 10 m in Zhan et al. (2021). Context data supplied
   in ``wind_speed_m_s`` must be a 10 m value; standard NOAA station wind is
   reported at 10 m.
4. No published precipitation response was found for cumulative
   volatilization loss, so ``precipitation_mm`` is accepted but has no effect.
5. The temperature term is applied without clamping. County mean May air
   temperatures over CONUS cropland fall largely inside the 0.6 to 29.0 C
   range Zhan report, but the warmest counties extrapolate slightly beyond it.
6. EPIC/APEX (Williams et al. 2023, Eqs. 2.5.85 to 2.5.88) applies the same
   temperature factor to both nitrification and volatilization, so temperature
   cancels from its partition and the cumulative volatilized fraction is
   temperature independent. The Zhan fitted response of exp(0.0940 per C),
   equivalent to a Q10 of 2.56, sits between that and the ~3.2 per 10 K
   implied by the pure NH3 thermodynamic driving force. It is therefore a
   damped response consistent with a competing nitrification sink, which is
   the behaviour the FY26 review identified as required.

References
----------
- Zhan, X., Adalibieke, W., Cui, X., Winiwarter, W., Reis, S., Zhang, L.,
  Bai, Z., Wang, Q., Huang, W., Zhou, F. (2021). "Improved estimates of
  ammonia emissions from global croplands." *Environmental Science &
  Technology*, 55(2), 1329-1338. doi:10.1021/acs.est.0c05149
- Goebes, M.D., Strader, R., Davidson, C. (2003). "An ammonia emission
  inventory for fertilizer application in the United States."
  *Atmospheric Environment*, 37(18), 2539-2550.
  doi:10.1016/S1352-2310(03)00129-8
- Williams, J.R., Izaurralde, R.C., Steglich, E.M., et al. (2023).
  *Agricultural Policy / Environmental eXtender Model: Theoretical
  Documentation, Version 1501.* Texas A&M AgriLife, Blackland Research and
  Extension Center.

Context columns consumed
------------------------
temperature_c
    Mean daily air temperature over the application period in C.
wind_speed_m_s
    Mean wind speed at 10 m height in m/s.
soil_ph
    Soil pH (1:1 H2O).
precipitation_mm
    Accepted for schema stability. Not used.

All context columns are optional; if missing, the corresponding driver falls
back to its reference value and the modifier is 1.0.
"""

import importlib.resources
import numpy as np
import pandas as pd

from .base import EmissionFactorProvider
from .. import utils

LOGGER = utils.logger(__name__)

# Default parameter file bundled with the package
_DEFAULT_PARAMS = "data/inputs/ammonia_provider_params.csv"


def _load_default_params():
    pkg = importlib.resources.files("FPEAM")
    path = str(pkg.joinpath(_DEFAULT_PARAMS))
    return pd.read_csv(path, comment="#")


class AmmoniaFertilizerProvider(EmissionFactorProvider):
    """Compute NH3 emission rates from N fertilizer applications dynamically.

    Parameters
    ----------
    params : pd.DataFrame or str, optional
        Parameter table (or path to CSV) defining ``base_rate_nh3`` and the
        reference condition per fertilizer subtype. Defaults to the bundled
        ``ammonia_provider_params.csv``.
    """

    # Fertilizer subtypes handled by this provider
    FERTILIZER_SUBTYPES = frozenset(
        {
            "anhydrous ammonia",
            "ammonium nitrate",
            "ammonium sulfate",
            "urea",
            "nitrogen solutions",
        }
    )

    # Zhan et al. (2021) Table S5, upland crops
    TEMPERATURE_EXPONENT = 0.0940  # per degree C
    PH_EXPONENT = 0.4955  # per pH unit
    WIND_SLOPE = 0.2737
    WIND_INTERCEPT = 0.9975

    # Input domain. pH bounds are the observed range in Zhan et al. (2021)
    # Table S3. Zhan report no wind range, so the wind bounds are set from the
    # domain of the 10 m monthly-mean wind climatology FPEAM consumes: CONUS
    # county May means span roughly 1.5 to 6 m/s, so 0.5 to 10 m/s brackets
    # the input data with margin and the clamp is a numerical guard rather
    # than an active constraint. The floor also keeps ln(u) away from the
    # zero crossing of f(u) at u = 0.026 m/s.
    WIND_MIN_M_S = 0.5
    WIND_MAX_M_S = 10.0
    PH_MIN = 5.5
    PH_MAX = 8.6

    def __init__(self, params=None):
        if params is None:
            self._params = _load_default_params()
        elif isinstance(params, str):
            self._params = pd.read_csv(params, comment="#")
        else:
            self._params = pd.DataFrame(params)

        self._params = self._params.set_index("resource_subtype")

        self._t_ref_c = self._single_reference("t_ref_c", 20.0)
        self._ph_ref = self._single_reference("ph_ref", 7.0)
        self._w_ref_m_s = self._single_reference("w_ref_m_s", 2.0)

    def _single_reference(self, column, default):
        """Return the one reference value shared by every fertilizer subtype."""
        if column not in self._params.columns:
            LOGGER.warning(
                "AmmoniaFertilizerProvider: parameter table has no %s column; using %s.",
                column,
                default,
            )
            return float(default)
        values = self._params[column].astype(float).unique()
        if len(values) > 1:
            raise ValueError(
                "AmmoniaFertilizerProvider: %s must be identical for every "
                "fertilizer subtype; found %s. The modifier functions are "
                "normalised to a single reference condition." % (column, list(values))
            )
        return float(values[0])

    # -- modifier functions ------------------------------------------------

    def _f_temperature(self, t_c):
        """Air temperature modifier, Zhan et al. (2021) Table S5 f(A).

        ``f(A) = 0.1790 * exp(0.0940 * A)``. Taken as a ratio to the reference
        temperature the prefactor cancels::

            f_T(A) = exp(0.0940 * (A - A_ref))

        The slope of 0.0940 per C is a Q10 of exp(0.940) = 2.56. Applied
        without clamping; see limitation 5 in the module docstring.
        """
        return np.exp(self.TEMPERATURE_EXPONENT * (t_c - self._t_ref_c))

    def _f_wind(self, w_m_s):
        """Wind speed modifier, Zhan et al. (2021) Table S5 f(u).

        ``f(u) = 0.2737 * ln(u) + 0.9975`` for u at 10 m. The prefactor does
        not cancel for a logarithmic form, so the ratio is taken directly::

            f_wind(u) = f(u) / f(u_ref)

        Inputs are clamped to ``[WIND_MIN_M_S, WIND_MAX_M_S]`` so that
        negative or zero wind speeds cannot produce NaN or a negative
        modifier.
        """
        w = np.clip(w_m_s, self.WIND_MIN_M_S, self.WIND_MAX_M_S)
        numerator = self.WIND_SLOPE * np.log(w) + self.WIND_INTERCEPT
        denominator = self.WIND_SLOPE * np.log(self._w_ref_m_s) + self.WIND_INTERCEPT
        return numerator / denominator

    def _f_ph(self, ph):
        """Soil pH modifier, Zhan et al. (2021) Table S5 f(pH).

        ``f(pH) = 0.0429 * exp(0.4955 * pH)``. Taken as a ratio to the
        reference pH the prefactor cancels::

            f_pH(pH) = exp(0.4955 * (pH - pH_ref))

        Inputs are clamped to the observed range of Table S3, 5.5 to 8.6,
        rather than extrapolated. The prefactor cancelling is fortunate: its
        standard error, 0.0509, exceeds the fitted value of 0.0429.
        """
        return np.exp(self.PH_EXPONENT * (np.clip(ph, self.PH_MIN, self.PH_MAX) - self._ph_ref))

    @staticmethod
    def _f_precipitation(p_mm):
        """Inert. No published precipitation response was found.

        Zhan et al. (2021) do not include a precipitation correction term, and
        no published response for cumulative volatilization loss was located.
        The term is retained at 1.0 so that ``precipitation_mm`` remains an
        accepted context column without silently affecting results.
        """
        return pd.Series(1.0, index=getattr(p_mm, "index", None))

    # -- provider interface ------------------------------------------------

    def factors(self, records: pd.DataFrame) -> pd.DataFrame:
        """Return dynamic NH3 rates for each (region, resource_subtype) combination.

        Only rows where ``resource_subtype`` is one of the recognised nitrogen
        fertilizer subtypes produce output rows. When ``resource`` is present in
        the input, rows where ``resource != 'nitrogen'`` are also excluded. For
        subtypes not handled by this provider no rows are returned (fall through to
        TableProvider or other providers in the chain).

        Parameters
        ----------
        records : pd.DataFrame
            Must contain at minimum ``region`` and ``resource_subtype``.
            When present, ``resource`` is used to restrict to nitrogen applications.
            Optional context: ``temperature_c``, ``wind_speed_m_s``, ``soil_ph``.

        Returns
        -------
        pd.DataFrame
            One row per (region, resource_subtype, pollutant) combination with
            ``pollutant == 'nh3'``.

        Application type caveat
        -----------------------
        The Goebes-derived base rates represent surface-applied fertilizer.
        Anhydrous ammonia is often injected below the soil surface, which
        produces far lower atmospheric volatilization. Zhan et al. (2021)
        Table S5 give a placement correction of 0.25 for deep placement and
        0.50 for incorporation in upland crops. FPEAM does not carry
        application placement, so no placement term is applied; if equipment
        data distinguishes injected from surface-applied anhydrous ammonia,
        set the rate separately in the parameters CSV.
        """
        _mask = pd.Series(False, index=records.index)
        if "resource_subtype" in records.columns:
            _mask = records["resource_subtype"].isin(self.FERTILIZER_SUBTYPES)
            # Further restrict to nitrogen resource when the column is available
            if "resource" in records.columns:
                _mask = _mask & (records["resource"].str.lower() == "nitrogen")

        _relevant = records[_mask].copy() if _mask.any() else pd.DataFrame()

        if _relevant.empty:
            # Return empty frame with the correct columns
            return pd.DataFrame(columns=list(self.RATE_COLUMNS))

        # Drivers default to the reference condition when context is absent,
        # which makes every modifier exactly 1.0 and returns the base rate.
        t = _relevant.get("temperature_c", pd.Series(self._t_ref_c, index=_relevant.index))
        w = _relevant.get("wind_speed_m_s", pd.Series(self._w_ref_m_s, index=_relevant.index))
        ph = _relevant.get("soil_ph", pd.Series(self._ph_ref, index=_relevant.index))

        if "soil_ph" not in _relevant.columns:
            LOGGER.debug(
                "AmmoniaFertilizerProvider: soil_ph not in records; using the "
                "reference pH of %s (neutral modifier).",
                self._ph_ref,
            )

        modifier = self._f_temperature(t) * self._f_wind(w) * self._f_ph(ph)

        # Look up base rates for each subtype
        base_rates = (
            _relevant["resource_subtype"].map(self._params["base_rate_nh3"].to_dict()).fillna(0.0)
        )

        _relevant["rate"] = (base_rates * modifier).values
        _relevant["pollutant"] = "nh3"
        _relevant["resource"] = "nitrogen"
        _relevant["activity"] = "chemical application"
        _relevant["unit_numerator"] = "pound"
        _relevant["unit_denominator"] = "pound"
        if "region" not in _relevant.columns:
            _relevant["region"] = None

        result = _relevant[list(self.RATE_COLUMNS)].reset_index(drop=True)
        self.validate_output(result)
        return result
