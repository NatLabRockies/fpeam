# Emission Factor Providers

FPEAM supports pluggable emission-factor providers. The default provider
uses static lookup tables; dynamic providers compute rates from geophysical
and climate inputs at runtime.

## Architecture

```
EmissionFactors module
    │
    ├── TableProvider (default)          ← existing static CSV path
    ├── AmmoniaFertilizerProvider        ← NH3 from climate/soil context
    └── <any subclass of EmissionFactorProvider>
```

Providers are selected per-module via the `provider` key in the
`[emissionfactors]` section of your config.

**Status**: dynamic-provider wiring into `EngineModules.EmissionFactors` is
complete and unit-tested (`tests/unit_tests/test_region_emission_factors.py::TestDynamicProviderWiring`).
Setting `provider = ammonia_fertilizer` (or any other `EmissionFactorProvider`
subclass) now runs through the standard `EmissionFactors.run()` path end to
end — records are joined against `resource_distribution` and
`geophysical_context`, missing climate context falls back to neutral
reference-condition defaults, and the provider's output is merged into the
same emissions-calculation flow the static `table` provider already uses.

---

## Provider interface

All providers implement `EmissionFactorProvider` from
`FPEAM.EmissionFactorProviders.base`:

```python
class EmissionFactorProvider(abc.ABC):
    RATE_COLUMNS = ('region', 'resource', 'resource_subtype', 'activity',
                    'pollutant', 'rate', 'unit_numerator', 'unit_denominator')

    @abc.abstractmethod
    def factors(self, records: pd.DataFrame) -> pd.DataFrame:
        """Return emission rates for the given input records."""
```

`records` is a DataFrame carrying at minimum `region` and `resource_subtype`,
plus any geophysical context columns the provider needs.  The returned
DataFrame must contain all `RATE_COLUMNS`.

---

## Built-in providers

### `table` (default)

Wraps the static `emission_factors.csv` and `resource_distribution.csv` path.
No additional configuration needed.

```ini
[emissionfactors]
provider = table
```

This is the default and is equivalent to omitting the `provider` key.

---

### `ammonia_fertilizer`

Computes NH3 volatilisation from nitrogen fertilizer applications as a
function of fertilizer subtype and geophysical context.

**Model**

```
NH3_fraction = base_rate(subtype)
             × f_T(temperature_c)
             × f_wind(wind_speed_m_s)
             × f_ph(soil_ph)
```

The correction functions are the upland-crop terms of Zhan et al. (2021),
Table S5. Each is applied as a ratio to its value at the reference condition,
so every factor is 1.0 there and the provider returns the base rate unchanged.
The fitted prefactors of the two exponential terms cancel under that
normalisation, leaving only the exponents and the wind slope.

| Modifier | Variable | Published form | Applied as |
|---|---|---|---|
| `f_T` | temperature_c | `0.1790·exp(0.0940·A)` (n=42, R²=0.61) | `exp(0.0940·(T − t_ref_c))` |
| `f_wind` | wind_speed_m_s (at 10 m) | `0.2737·ln(u) + 0.9975` (n=60, R²=0.77) | ratio to the value at `w_ref_m_s` |
| `f_ph` | soil_ph | `0.0429·exp(0.4955·pH)` (n=42, R²=0.33) | `exp(0.4955·(pH − ph_ref))` |

The bundled reference is the Zhan et al. (2021) Table S3 measurement condition:
20 °C and pH 7.0, with an FPEAM-chosen reference wind of 2 m/s. Table S3 reports
observed ranges of 0.6–29.0 °C and pH 5.5–8.6.

Inputs are clamped rather than extrapolated: `soil_ph` to [5.5, 8.6] (the
published range) and `wind_speed_m_s` to [0.5, 10.0]. The wind bounds are not
published — Zhan et al. state that observations were insufficient to constrain
the wind response, and no wind column appears in their Supplementary Data. They
are set from the domain of the input climatology and act as a numerical guard,
since `f_wind` is undefined at u ≤ 0 and crosses zero at u ≈ 0.026 m/s.

Output is **not** clipped. Over the full published input domain, applied to the
largest base rate in the table, no rate reaches the physical bound of 1.0; there
is a test that asserts this.

> **Provenance.** The base rates and the correction functions come from
> different sources. The per-subtype base rates are the pre-existing FPEAM
> static NH3 emission factors from `emission_factors.csv`, rounded; per the
> FPEAM README those derive from Goebes et al. (2003), Davidson et al. (2004)
> and the 17/14 NH3-to-N ratio. They are US national-average factors, **not**
> measurements at 20 °C and pH 7.0. Applying corrections normalised to the
> published reference to national-average base rates shifts the implied national
> total by construction. For a national-scale run, override the reference in a
> custom `provider_params` CSV so that the production-weighted mean correction
> is 1.0; the corrections then redistribute the total spatially without changing
> it. Nothing in this provider comes from Bouwman et al. (2002).
>
> No published precipitation correction for cumulative volatilisation loss was
> identified, so `precipitation_mm` is accepted but has no effect. FPEAM does
> not carry application placement, so the Zhan placement correction (0.25 deep
> placement, 0.50 incorporation) is not applied.

**Base rates** (bundled defaults: FPEAM's existing NH3 emission factors, from Goebes et al. 2003 via `emission_factors.csv`):

| Fertilizer subtype | Base rate (lb NH3-N / lb N) | Notes |
|---|---|---|
| Anhydrous ammonia | 0.040 | See caveat below |
| Ammonium nitrate | 0.008 | |
| Ammonium sulfate | 0.088 | |
| Urea | 0.025 | |
| Nitrogen solutions | 0.028 | |

**Important caveat — anhydrous ammonia application method**

The base rate of 0.040 applies to **surface-applied** anhydrous ammonia.
Anhydrous ammonia is often injected below the soil surface (deep injection), which results
in near-zero atmospheric NH3 volatilisation because the gas reacts immediately with soil
moisture and is retained.  If your equipment dataset represents injected anhydrous ammonia,
the correct rate is approximately 0.003–0.010 lb NH3-N / lb N.

To model this distinction: supply a custom `provider_params` CSV that overrides the
`anhydrous ammonia` base rate to reflect your application method.

**Configuration**

```ini
[emissionfactors]
provider = ammonia_fertilizer
geophysical_context = data/inputs/my_climate_data.csv
provider_params = data/inputs/ammonia_provider_params.csv  # optional; defaults to bundled
```

**Geophysical context CSV format**

```csv
region,year,month,temperature_c,wind_speed_m_s,soil_ph
17031,2017,6,22.5,3.2,6.8
17043,2017,6,19.1,2.8,7.4
```

The `region` column must match the `region_production` values in your production data.
All climate columns are optional; missing columns default to reference-condition
modifiers (f = 1.0), which is equivalent to using the base rate alone.

**Note on `wind_speed_m_s`.** Zhan et al. (2021) define wind speed at 10 m.
Supply a 10 m value; standard NOAA station wind is reported at that height.

**References**

- Goebes, M.D., Strader, R., Davidson, C. (2003). "An ammonia emission inventory
  for fertilizer application in the United States." *Atmospheric Environment*,
  37(18), 2539-2550. doi:10.1016/S1352-2310(03)00129-8
- Zhan, X., Adalibieke, W., Cui, X., Winiwarter, W., Reis, S., Zhang, L., Bai, Z.,
  Wang, Q., Huang, W., Zhou, F. (2021). "Improved estimates of ammonia emissions
  from global croplands." *Environmental Science & Technology*, 55(2), 1329-1338.
  doi:10.1021/acs.est.0c05149
- Williams, J.R., Izaurralde, R.C., Steglich, E.M., et al. (2023). *Agricultural
  Policy / Environmental eXtender Model: Theoretical Documentation, Version 1501.*
  Texas A&M AgriLife, Blackland Research and Extension Center.

---

## Writing a custom provider

1. Subclass `EmissionFactorProvider`:

```python
# my_package/my_provider.py
from FPEAM.EmissionFactorProviders import EmissionFactorProvider
import pandas as pd

class MyProvider(EmissionFactorProvider):
    def factors(self, records: pd.DataFrame) -> pd.DataFrame:
        # compute rates ...
        result = ...  # must contain RATE_COLUMNS
        self.validate_output(result)
        return result
```

2. Configure by dotted import path:

```ini
[emissionfactors]
provider = my_package.my_provider.MyProvider
```

---

## Geophysical context schema

| Column | Type | Required | Description |
|---|---|---|---|
| `region` | str | **yes** | Matches `region_production` in production data |
| `year` | int | no | Scenario year |
| `month` | int | no | Month (1–12) |
| `temperature_c` | float | no | Mean air temperature (°C) |
| `wind_speed_m_s` | float | no | Mean wind speed at 2 m height (m/s) |
| `precipitation_mm` | float | no | Precipitation total (mm); accepted but unused |
| `soil_ph` | float | no | Soil pH (1:1 H2O) |
| `soil_type` | str | no | USDA texture class; retained for schema stability, unused |

Load with `FPEAM.Data.GeophysicalContext(fpath='...')`.

---

## Worked example (ammonia provider, county-level climate data)

```python
from FPEAM.IO import load_configs
from FPEAM.Data import Equipment, Production
from FPEAM.EngineModules import EmissionFactors

# config points to ammonia_fertilizer provider + county climate CSV
config = load_configs('my_run_config.ini')
equipment = Equipment(fpath='data/equipment/bts16_equipment.csv')
production = Production(fpath='data/production/production_2017.csv')

with EmissionFactors(config=config, equipment=equipment, production=production) as ef:
    ef.run()
    ef.results.to_csv('results.csv', index=False)
```

The output `results.csv` has the same columns as the static provider but with
county-specific NH3 rates derived from the climate data.
