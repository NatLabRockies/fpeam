"""Tests for AmmoniaFertilizerProvider.

The modifier functions are the upland-crop correction terms of Zhan et al.
(2021), Table S5, normalised to the Table S3 reference condition. These tests
pin the published coefficients, check monotonicity in each driver, check that
the reference condition reproduces the base rate exactly, and check that the
physical [0, 1] bound holds without clipping over the published input domain.

Covers:
- Reference condition reproduces the Goebes-derived base rate exactly.
- Pinned regression values computed from the published coefficients.
- Monotonicity in temperature, wind speed and soil pH.
- Precipitation is inert, since no published response was found.
- Bounds: NH3 fraction always in [0, 1].
- Output schema matches provider contract.
- Empty / irrelevant records return empty result.
"""

import math

import pytest
import pandas as pd

from FPEAM.EmissionFactorProviders.ammonia import AmmoniaFertilizerProvider


# Reference condition, Zhan et al. (2021) Table S3: broadcast urea measured by
# dynamic chamber, mean daily growing-season air temperature 20 C, soil pH 7.0.
# The reference wind speed is an FPEAM choice; Zhan states no reference wind.
T_REF = 20.0
PH_REF = 7.0
W_REF = 2.0


def _expected_modifier(t_c, w_m_s, ph):
    """Zhan et al. (2021) Table S5 upland terms, normalised to reference.

    The fitted prefactors cancel under normalisation, so only the exponents
    and the wind slope enter.
    """
    f_t = math.exp(0.0940 * (t_c - T_REF))
    f_ph = math.exp(0.4955 * (ph - PH_REF))

    def g(u):
        return 0.2737 * math.log(u) + 0.9975

    return f_t * f_ph * (g(w_m_s) / g(W_REF))


@pytest.fixture(scope="module")
def provider():
    """Provider using the bundled default parameter table."""
    return AmmoniaFertilizerProvider()


@pytest.fixture
def reference_records():
    """Reference conditions: T=20 C, wind=2 m/s, soil pH 7.0."""
    return pd.DataFrame(
        [
            {
                "region": "17031",
                "resource": "nitrogen",
                "resource_subtype": st,
                "temperature_c": T_REF,
                "wind_speed_m_s": W_REF,
                "precipitation_mm": 0.0,
                "soil_ph": PH_REF,
            }
            for st in AmmoniaFertilizerProvider.FERTILIZER_SUBTYPES
        ]
    )


class TestAmmoniaProviderSchemaAndBounds:
    def test_factors_returns_dataframe(self, provider, reference_records):
        result = provider.factors(reference_records)
        assert isinstance(result, pd.DataFrame)

    def test_output_has_required_columns(self, provider, reference_records):
        result = provider.factors(reference_records)
        for col in ("region", "resource", "resource_subtype", "pollutant", "rate"):
            assert col in result.columns

    def test_rates_bounded_0_to_1(self, provider, reference_records):
        result = provider.factors(reference_records)
        assert (result["rate"] >= 0).all()
        assert (result["rate"] <= 1).all()

    def test_pollutant_is_nh3(self, provider, reference_records):
        result = provider.factors(reference_records)
        assert (result["pollutant"] == "nh3").all()

    def test_resource_is_nitrogen(self, provider, reference_records):
        result = provider.factors(reference_records)
        assert (result["resource"] == "nitrogen").all()

    def test_empty_on_irrelevant_records(self, provider):
        records = pd.DataFrame(
            [
                {
                    "region": "17031",
                    "resource": "diesel",
                    "resource_subtype": "diesel",
                }
            ]
        )
        assert provider.factors(records).empty

    def test_empty_on_no_resource_subtype_column(self, provider):
        records = pd.DataFrame([{"region": "17031", "resource": "nitrogen"}])
        assert provider.factors(records).empty

    def test_bound_holds_without_clipping_over_published_domain(self, provider):
        """Across the full published input domain no rate reaches the bound.

        Zhan et al. (2021) Table S3 report observed ranges of 0.6 to 29.0 C
        for temperature and 5.5 to 8.6 for pH. Ammonium sulfate carries the
        largest base rate, 0.088.
        """
        records = pd.DataFrame(
            [
                {
                    "region": "17031",
                    "resource": "nitrogen",
                    "resource_subtype": "ammonium sulfate",
                    "temperature_c": t,
                    "wind_speed_m_s": w,
                    "precipitation_mm": 0.0,
                    "soil_ph": ph,
                }
                for t in (0.6, 15.0, 29.0)
                for w in (0.5, 2.0, 10.0)
                for ph in (5.5, 7.0, 8.6)
            ]
        )
        result = provider.factors(records)
        assert (result["rate"] > 0).all()
        assert (result["rate"] < 1.0).all()


class TestAmmoniaProviderReferenceValues:
    @pytest.mark.parametrize(
        "subtype, base_rate",
        [
            ("anhydrous ammonia", 0.040),
            ("ammonium nitrate", 0.008),
            ("ammonium sulfate", 0.088),
            ("urea", 0.025),
            ("nitrogen solutions", 0.028),
        ],
    )
    def test_base_rate_reproduced_at_reference(self, provider, subtype, base_rate):
        """At the reference condition every modifier is 1, so rate == base rate."""
        records = pd.DataFrame(
            [
                {
                    "region": "17031",
                    "resource": "nitrogen",
                    "resource_subtype": subtype,
                    "temperature_c": T_REF,
                    "wind_speed_m_s": W_REF,
                    "precipitation_mm": 0.0,
                    "soil_ph": PH_REF,
                }
            ]
        )
        result = provider.factors(records)
        assert result["rate"].iloc[0] == pytest.approx(base_rate, abs=1e-12)


class TestAmmoniaProviderPinnedValues:
    """Regression values computed directly from the published coefficients."""

    @pytest.mark.parametrize(
        "subtype, base_rate, t_c, w_m_s, ph, expected",
        [
            ("urea", 0.025, 25.0, 3.0, 7.5, 0.05603560),
            ("anhydrous ammonia", 0.040, 10.0, 1.5, 6.0, 0.00888848),
        ],
    )
    def test_pinned_rate(self, provider, subtype, base_rate, t_c, w_m_s, ph, expected):
        records = pd.DataFrame(
            [
                {
                    "region": "17031",
                    "resource": "nitrogen",
                    "resource_subtype": subtype,
                    "temperature_c": t_c,
                    "wind_speed_m_s": w_m_s,
                    "precipitation_mm": 0.0,
                    "soil_ph": ph,
                }
            ]
        )
        result = provider.factors(records)
        assert result["rate"].iloc[0] == pytest.approx(expected, rel=1e-6)
        # cross-check against an independent evaluation of the published form
        assert result["rate"].iloc[0] == pytest.approx(
            base_rate * _expected_modifier(t_c, w_m_s, ph), rel=1e-9
        )


class TestAmmoniaProviderMonotonicity:
    def _rate(self, provider, **kwargs):
        defaults = {
            "region": "17031",
            "resource": "nitrogen",
            "resource_subtype": "urea",
            "temperature_c": T_REF,
            "wind_speed_m_s": W_REF,
            "precipitation_mm": 0.0,
            "soil_ph": PH_REF,
        }
        defaults.update(kwargs)
        result = provider.factors(pd.DataFrame([defaults]))
        return result["rate"].iloc[0]

    def test_rate_increases_with_temperature(self, provider):
        """Zhan f(A) is exponential and increasing in air temperature."""
        low = self._rate(provider, temperature_c=5.0)
        mid = self._rate(provider, temperature_c=20.0)
        high = self._rate(provider, temperature_c=29.0)
        assert low < mid < high

    def test_temperature_response_matches_published_q10(self, provider):
        """The Table S5 slope of 0.0940 per C implies a Q10 of exp(0.94)."""
        r15 = self._rate(provider, temperature_c=15.0)
        r25 = self._rate(provider, temperature_c=25.0)
        assert r25 / r15 == pytest.approx(math.exp(0.940), rel=1e-9)

    def test_rate_increases_with_wind(self, provider):
        """Zhan f(u) is logarithmic and increasing in wind speed."""
        low = self._rate(provider, wind_speed_m_s=0.5)
        mid = self._rate(provider, wind_speed_m_s=2.0)
        high = self._rate(provider, wind_speed_m_s=8.0)
        assert low < mid < high

    def test_rate_increases_with_ph(self, provider):
        """Higher soil pH shifts the NH4+/NH3 equilibrium toward NH3."""
        acid = self._rate(provider, soil_ph=5.5)
        neutral = self._rate(provider, soil_ph=7.0)
        alkaline = self._rate(provider, soil_ph=8.6)
        assert acid < neutral < alkaline

    def test_precipitation_has_no_effect(self, provider):
        """No published precipitation response was found, so the term is inert."""
        dry = self._rate(provider, precipitation_mm=0.0)
        wet = self._rate(provider, precipitation_mm=150.0)
        assert dry == pytest.approx(wet, rel=1e-12)


class TestAmmoniaProviderInputDomain:
    """Inputs outside the published domain are clamped, not extrapolated."""

    def _rate(self, provider, **kwargs):
        defaults = {
            "region": "17031",
            "resource": "nitrogen",
            "resource_subtype": "urea",
            "temperature_c": T_REF,
            "wind_speed_m_s": W_REF,
            "precipitation_mm": 0.0,
            "soil_ph": PH_REF,
        }
        defaults.update(kwargs)
        return provider.factors(pd.DataFrame([defaults]))["rate"].iloc[0]

    def test_negative_wind_does_not_produce_nan(self, provider):
        """Negative wind speed is physically invalid and must not yield NaN.

        The Zhan wind term is logarithmic, so it is undefined at u <= 0.
        """
        rate = self._rate(provider, wind_speed_m_s=-1.0)
        assert not math.isnan(rate)
        assert rate > 0.0

    def test_wind_clamped_to_published_floor(self, provider):
        """Below the floor the response is held constant, not extrapolated."""
        assert self._rate(provider, wind_speed_m_s=0.0) == pytest.approx(
            self._rate(provider, wind_speed_m_s=AmmoniaFertilizerProvider.WIND_MIN_M_S)
        )

    def test_wind_clamped_to_published_ceiling(self, provider):
        assert self._rate(provider, wind_speed_m_s=40.0) == pytest.approx(
            self._rate(provider, wind_speed_m_s=AmmoniaFertilizerProvider.WIND_MAX_M_S)
        )

    def test_ph_clamped_to_published_range(self, provider):
        """Table S3 reports an observed pH range of 5.5 to 8.6."""
        assert self._rate(provider, soil_ph=2.0) == pytest.approx(
            self._rate(provider, soil_ph=AmmoniaFertilizerProvider.PH_MIN)
        )
        assert self._rate(provider, soil_ph=12.0) == pytest.approx(
            self._rate(provider, soil_ph=AmmoniaFertilizerProvider.PH_MAX)
        )


class TestAmmoniaProviderMissingContext:
    def test_missing_context_uses_reference_defaults(self, provider):
        """Records without context columns fall back to the reference condition."""
        records = pd.DataFrame(
            [
                {
                    "region": "17031",
                    "resource": "nitrogen",
                    "resource_subtype": "urea",
                }
            ]
        )
        result = provider.factors(records)
        assert len(result) == 1
        # reference condition reproduces the base rate exactly
        assert result["rate"].iloc[0] == pytest.approx(0.025, abs=1e-12)


class TestAmmoniaProviderDefaultParams:
    def test_params_csv_loads_without_error(self):
        """The bundled ammonia_provider_params.csv with comments must parse."""
        provider = AmmoniaFertilizerProvider()
        assert set(provider._params.index) == AmmoniaFertilizerProvider.FERTILIZER_SUBTYPES
        assert "base_rate_nh3" in provider._params.columns

    def test_reference_columns_match_published_reference(self):
        """The bundled reference condition must match Zhan Table S3."""
        provider = AmmoniaFertilizerProvider()
        assert (provider._params["t_ref_c"] == T_REF).all()
        assert (provider._params["ph_ref"] == PH_REF).all()
        assert (provider._params["w_ref_m_s"] == W_REF).all()
