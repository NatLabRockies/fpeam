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
             × f_precip(precipitation_mm)
             × f_soil(soil_type)
```

| Modifier | Variable | Behaviour |
|---|---|---|
| `f_T` | temperature_c | Logistic increase; reference at 15°C |
| `f_wind` | wind_speed_m_s | Square-root increase; capped at 3 m/s |
| `f_precip` | precipitation_mm | Exponential decay; dry=max, wet=reduced |
| `f_soil` | soil_type (USDA texture) | Lookup table; clay > loam > sand |

**Base rates** (bundled defaults from Bouwman 2002, Table 3 median values):

| Fertilizer subtype | Base rate (lb NH3-N / lb N) | Notes |
|---|---|---|
| Anhydrous ammonia | 0.040 | See caveat below |
| Ammonium nitrate | 0.008 | |
| Ammonium sulfate | 0.088 | |
| Urea | 0.025 | |
| Nitrogen solutions | 0.028 | |

**Important caveat — anhydrous ammonia application method**

The Bouwman 2002 base rate of 0.040 applies to **surface-incorporated** anhydrous ammonia.
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
region,year,month,temperature_c,wind_speed_m_s,precipitation_mm,soil_type
17031,2017,6,22.5,3.2,45.0,silty clay loam
17043,2017,6,19.1,2.8,30.0,loam
```

The `region` column must match the `region_production` values in your production data.
All climate columns are optional; missing columns default to reference-condition
modifiers (f = 1.0), which is equivalent to using the base rate alone.

**References**

- Bouwman, A.F. et al. (2002). "Estimation of global NH3 volatilization loss from
  synthetic fertilizers and animal manure applied to arable lands and grasslands."
  *Global Biogeochemical Cycles*, 16(2), 8-1 to 8-14. doi:10.1029/2000GB001389

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
| `precipitation_mm` | float | no | Precipitation total (mm) |
| `soil_type` | str | no | USDA texture class |

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
