# FPEAM Architecture

## Overview

FPEAM calculates spatially explicit emissions inventories from biomass feedstock production and transportation. It is structured as a central orchestrator (`FPEAM` class) that assembles shared inputs, configures independent emission modules, runs them, and merges results.

## Package layout

```
src/FPEAM/
├── __init__.py             # Public surface re-exports: FPEAM, Data, IO, utils, EngineModules
├── FPEAM.py                # Orchestrator class
├── Data.py                 # Data container classes (subclass pd.DataFrame)
├── IO.py                   # CSV loading, config loading, resource path helper
├── utils.py                # Logger factory, configure_logging(), config validator, filepath validator
├── Router.py               # Shortest-path routing on a county road graph (networkx + scipy)
├── Interfaces.py           # Stub interfaces for external models (InMAP, BenMAP, Polysys)
├── Figures.py              # Stub figure module
├── EngineModules/
│   ├── __init__.py         # Re-exports all four modules
│   ├── EmissionFactors.py  # Static emission-factor calculations
│   ├── FugitiveDust.py     # On-farm and on-road particulate matter
│   ├── MOVES.py            # EPA MOVES wrapper (on-road transportation)
│   └── NONROAD.py          # EPA NONROAD wrapper (on-farm equipment)
├── configs/
│   ├── *.spec              # Annotated config schema (configobj format)
│   └── *.ini               # Default config values
├── data/
│   ├── equipment/          # Equipment use rate tables
│   ├── inputs/             # Reference data (emission factors, silt, FIPS maps, …)
│   ├── outputs/            # Example/golden outputs (tracked in git)
│   └── production/         # Example production scenarios
├── gui/                    # Legacy PyQt5 GUI (see GUI section below)
└── scripts/
    └── fpeam.py            # CLI entrypoint
```

## Data flow

```
run_config.ini
      │
      ▼
 FPEAM.__init__
  ├── load Equipment, Production, FeedstockLossFactors, TruckCapacity
  ├── (optionally) build Router from transportation graph + node locations
  └── configure each requested module (EmissionFactors, FugitiveDust, MOVES, NONROAD)
         │
         ▼
 FPEAM.run()
  ├── EmissionFactors.run()   → results DataFrame (lb pollutant / row)
  ├── FugitiveDust.run()      → results DataFrame
  ├── MOVES.run()             → results DataFrame (requires MOVES + MySQL)
  └── NONROAD.run()           → results DataFrame (requires NONROAD + MySQL)
         │
         ▼
 FPEAM.collect()
  ├── stack module results
  ├── apply feedstock loss factors to production quantities
  └── merge with production to enable normalisation
         │
         ▼
 FPEAM.summarize()
  └── write per-region, per-module, and normalised CSVs to project_path
```

## Key classes

### `Data` (`Data.py`)

Thin subclass of `pd.DataFrame`. Each concrete subclass (`Equipment`, `Production`, `EmissionFactor`, `ResourceDistribution`, etc.) declares a `COLUMNS` tuple that drives type-casting and optional backfill.  
`__init__` validates after load; raises `RuntimeError` naming the subclass and source on failure.

### `Module` (`EngineModules/Module.py`)

Abstract base for all engine modules. Handles config loading (merges defaults from bundled `.ini`, validates against bundled `.spec`), unit conversions dict, and a standard `run()`/`save()`/`__enter__`/`__exit__` contract.

### `FPEAM` (`FPEAM.py`)

Orchestrator. Owns shared datasets, the joblib memory cache (temp dir), and the router. `collect()` is the most important post-processing step: it merges module results with production data and applies loss factors to derive delivered feedstock quantities.

### `Router` (`Router.py`)

Wraps a `networkx.Graph` built from a county road edge table. `get_route(start, end)` finds the shortest path between two lat/lon points (nearest-node snapping via `scipy.spatial.cKDTree`) and returns VMT by county and road class.

## Configuration system

Each module uses `configobj` for hierarchical INI-style configs.

1. Default values come from the bundled `configs/<module>.ini`.
2. The schema (type, range, default) is defined in `configs/<module>.spec`.
3. User-supplied config values override defaults via `ConfigObj.merge()`.
4. Validation runs at module `__init__` time; errors are logged and raise `ConfigObjError`.

The orchestrator reads `run_config.ini` (schema in `run_config.spec`) plus one optional INI per module.

## External dependencies (MOVES and NONROAD)

MOVES 3/5 and NONROAD are Windows-only EPA models that must be installed separately. FPEAM:

1. Reads from and writes to a local MySQL database used by MOVES.
2. Generates input XML files for each MOVES run (one per county/year).
3. Invokes MOVES via a `.bat` file and reads results back from MySQL.
4. NONROAD follows a similar pattern with flat-file inputs/outputs.

Running FPEAM with only `EmissionFactors` and/or `FugitiveDust` does **not** require MOVES, NONROAD, or MySQL.

## GUI (legacy)

`src/FPEAM/gui/` contains a PyQt5 GUI (`AllModuleTab.py`) that was developed for Windows and is not exercised by tests or CI. It is present for reference but should be considered unmaintained. Use the CLI (`fpeam` entrypoint) or Python API for current workflows.

## Testing

Tests live in `tests/unit_tests/`. Run with:

```bash
pixi run test
# or
PYTHONPATH=src python -m pytest tests/
```

CI runs on push/PR to `dev` and `master` via `.github/workflows/test.yml`.

Current coverage: `test_data`, `test_io`, `test_emissionfactors`, `test_emissionfactors_extended`, `test_router`, `test_fugitivedust`, `test_region_emission_factors`, `test_provider_interface`, `test_geophysical_context`, `test_ammonia_provider`.

## Dynamic emission-factor providers

See [`docs/emission_factor_providers.md`](emission_factor_providers.md) for the full provider architecture, `AmmoniaFertilizerProvider` documentation, geophysical context schema, and a guide to writing custom providers.
