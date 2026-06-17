# FPEAM Outputs

FPEAM writes several CSV files to the `project_path` directory defined in `run_config.ini`. All filenames are prefixed with `<scenario_name>` (the `scenario_name` key in `run_config.ini`).

## Files written by `FPEAM.run()` + `FPEAM.summarize()`

### `<scenario_name>_raw.csv`

Written by the CLI entrypoint (`scripts/fpeam.py`) immediately after `FPEAM.run()`.  
This is the full merged result from `FPEAM.collect()`.

**Columns** (varies by which modules are run):

| Column | Description |
|---|---|
| `region_production` | 5-digit FIPS of the production county |
| `region_destination` | 5-digit FIPS of the biorefinery county (if applicable) |
| `region_transportation` | 5-digit FIPS of a county along the transport route (FugitiveDust/MOVES) |
| `feedstock` | Feedstock name (e.g. `corn grain`, `switchgrass`) |
| `tillage_type` | Tillage type (e.g. `conventional tillage`, `no tillage`) |
| `module` | Name of the module that produced the row |
| `activity` | Activity that generated the emission (e.g. `chemical application`) |
| `resource` | Input resource (e.g. `nitrogen`, `herbicide`) |
| `resource_subtype` | Specific form of the resource (e.g. `anhydrous ammonia`) |
| `pollutant` | Pollutant name (e.g. `nh3`, `voc`, `pm10`, `pm25`) |
| `pollutant_amount` | Emission mass in pounds |
| `unit_numerator` | Always `lb pollutant` |
| `unit_denominator` | Always `county-year` |
| `feedstock_measure` | How the feedstock quantity is measured (`harvested`, `production`, `at farm gate`, `at biorefinery`) |
| `feedstock_amount` | Feedstock quantity |
| `feedstock_unit_numerator` | Feedstock mass unit numerator |
| `feedstock_unit_denominator` | Feedstock mass unit denominator |

---

### `<scenario_name>_total_emissions_by_production_region.csv`

Emissions grouped by `feedstock`, `tillage_type`, `region_production`, and `pollutant`. Used for county-level mapping.

**Columns:** `feedstock`, `tillage_type`, `region_production`, `pollutant`, `pollutant_amount`, `unit_numerator` (`lb pollutant`), `unit_denominator` (`county-year`).

---

### `<scenario_name>_normalized_total_emissions_by_production_region.csv`

Same as above but normalised by feedstock amount so the values are in `lb pollutant / dt feedstock` (or equivalent).

**Additional columns:** `feedstock_measure`, `feedstock_amount`, `feedstock_unit_numerator`, `normalized_pollutant_amount`, `normalized_pollutant_unit_numerator`, `normalized_pollutant_unit_denominator`.

---

### `<scenario_name>_transportation_emissions_by_region.csv`

Only written when at least one module produces `region_transportation` data (FugitiveDust on-road or MOVES). Grouped by `feedstock`, `tillage_type`, `region_transportation`, `pollutant`.

**Columns:** `feedstock`, `tillage_type`, `region_transportation`, `pollutant`, `pollutant_amount`.

---

### `<scenario_name>_total_emissions_by_module.csv`

Emissions grouped by `feedstock`, `tillage_type`, `module`, `pollutant`. Useful for comparing module contributions.

**Columns:** `feedstock`, `tillage_type`, `module`, `pollutant`, `pollutant_amount`, `unit_numerator`, `unit_denominator`.

---

### `<scenario_name>_county_inmap.shp` (optional)

Written only when `inmap_county_export = True` in `fpeam.ini`. A shapefile that joins county geometries with aggregated pollutant amounts per county, formatted for InMAP input.

---

## Files written by MOVES module

MOVES writes intermediate XML and CSV files to `moves_datafiles_path` during each county run. These are working files and should not be treated as final outputs. The MOVES output database is the authoritative intermediate store.

## Files written by NONROAD module

NONROAD writes population, allocation, and options files to `nonroad_datafiles_path`. Like MOVES, these are working files, not final deliverables.

## Reproducibility

To reproduce an output:

1. Keep the config files (`.ini` for each module + `run_config.ini`).
2. Keep the input data files referenced in the configs (equipment CSV, production CSV, emission factors CSV, resource distribution CSV).
3. Record the software version (`FPEAM.__version__` or `git rev-parse HEAD`).
4. For MOVES/NONROAD results: record the MOVES/NONROAD version and the MySQL database snapshot used.
