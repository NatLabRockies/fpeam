"""Integration test for FPEAM orchestrator — collect() and summarize().

Runs the FPEAM class end-to-end with the EmissionFactors module using
bundled default data, a pytest tmp_path as the project directory, and
a minimal run config (no MOVES / NONROAD / router needed).

Verifies:
- collect() merges module results with production and attaches the
  correct feedstock-measure variants (harvested, at farm gate, at
  biorefinery).
- summarize() writes the expected output CSV files to project_path.
- Key numeric invariants: all pollutant amounts ≥ 0, feedstock-measure
  types in the full results frame, output files are non-empty.
"""
import os
import pytest
from configobj import ConfigObj
from importlib.resources import files as _pkg_files

from FPEAM.FPEAM import FPEAM
from FPEAM.IO import CONFIG_FOLDER


def _resource(relpath):
    return str(_pkg_files('FPEAM').joinpath(relpath))


@pytest.fixture(scope='module')
def fpeam_run_config(tmp_path_factory):
    """Run config pointing to bundled data, emissionfactors module only."""
    project = tmp_path_factory.mktemp('fpeam_integration')

    # Build a minimal run_config section that mirrors run_config.ini but
    # overrides only the scenario-level keys so the test is reproducible.
    config = ConfigObj()
    config['run_config'] = {
        'scenario_name': 'test_integration',
        'project_path': str(project),
        'modules': 'emissionfactors',
        'logger_level': 'WARNING',
        'use_router_engine': 'False',
        'equipment': 'data/equipment/bts16_equipment.csv',
        'production': 'data/production/production_2015_bc1060.csv',
        'feedstock_loss_factors': 'data/inputs/feedstock_loss_factors.csv',
        'forestry_feedstock_names': ['forest residues', 'forest whole tree'],
        'transportation_graph': 'data/inputs/transportation_graph.csv',
        'vmt_short_haul': '20',
        'truck_capacity': 'data/inputs/truck_capacity.csv',
        'node_locations': 'data/inputs/node_locations.csv',
        'backfill': 'True',
    }
    return config, project


class TestFPEAMCollect:

    def test_fpeam_run_and_collect(self, fpeam_run_config):
        """run() + collect() returns a non-empty DataFrame with required columns."""
        config, project = fpeam_run_config
        with FPEAM(run_config=config) as fpeam:
            fpeam.run()

        assert fpeam.results is not None
        assert not fpeam.results.empty

        required_cols = {
            'feedstock', 'tillage_type', 'region_production',
            'pollutant', 'pollutant_amount', 'feedstock_measure',
            'module',
        }
        assert required_cols.issubset(set(fpeam.results.columns))

    def test_collect_all_pollutant_amounts_non_negative(self, fpeam_run_config):
        """No negative pollutant amounts in collected results."""
        config, project = fpeam_run_config
        with FPEAM(run_config=config) as fpeam:
            fpeam.run()
        assert (fpeam.results['pollutant_amount'] >= 0).all()

    def test_collect_loss_factor_measures_present(self, fpeam_run_config):
        """collect() adds both 'at farm gate' and 'at biorefinery' feedstock-measure rows."""
        config, project = fpeam_run_config
        with FPEAM(run_config=config) as fpeam:
            fpeam.run()
        measures = set(fpeam.results['feedstock_measure'].unique())
        assert 'at biorefinery' in measures, 'expected at-biorefinery loss-factor rows'
        assert 'at farm gate' in measures, \
            ('at farm gate rows absent — the supply-chain-stage filter in '
             'collect() must include "farm gate" to match the bundled data')

    def test_collect_does_not_mutate_production(self, fpeam_run_config):
        """collect() must not alter self.production (e.g. delete columns)."""
        import pandas as pd
        config, project = fpeam_run_config
        with FPEAM(run_config=config) as fpeam:
            cols_before = set(fpeam.production.columns)
            fpeam.run()
            cols_after = set(fpeam.production.columns)
        # region_destination should survive; it was being deleted by collect()
        assert 'region_destination' in cols_after, \
            'collect() mutated self.production and deleted region_destination'
        assert cols_before == cols_after, \
            f'collect() changed production columns: {cols_before.symmetric_difference(cols_after)}'

    def test_collect_harvested_rows_present(self, fpeam_run_config):
        """collect() retains the raw 'harvested' measure rows."""
        config, project = fpeam_run_config
        with FPEAM(run_config=config) as fpeam:
            fpeam.run()
        assert 'harvested' in fpeam.results['feedstock_measure'].unique()

    def test_collect_unit_columns_attached(self, fpeam_run_config):
        """collect() attaches unit_numerator and unit_denominator to results."""
        config, project = fpeam_run_config
        with FPEAM(run_config=config) as fpeam:
            fpeam.run()
        assert (fpeam.results['unit_numerator'] == 'lb pollutant').all()
        assert (fpeam.results['unit_denominator'] == 'county-year').all()


class TestFPEAMSummarize:

    def test_summarize_writes_by_region_csv(self, fpeam_run_config):
        """summarize() writes *_total_emissions_by_production_region.csv."""
        config, project = fpeam_run_config
        with FPEAM(run_config=config) as fpeam:
            fpeam.run()
            fpeam.summarize()

        expected = os.path.join(str(project),
                                'test_integration_total_emissions_by_production_region.csv')
        assert os.path.exists(expected), f'missing: {expected}'
        # File should have data rows (not just a header)
        with open(expected) as f:
            lines = f.readlines()
        assert len(lines) > 1, 'expected non-empty by-region summary'

    def test_summarize_writes_by_module_csv(self, fpeam_run_config):
        """summarize() writes *_total_emissions_by_module.csv."""
        config, project = fpeam_run_config
        with FPEAM(run_config=config) as fpeam:
            fpeam.run()
            fpeam.summarize()

        expected = os.path.join(str(project),
                                'test_integration_total_emissions_by_module.csv')
        assert os.path.exists(expected), f'missing: {expected}'

    def test_summarize_writes_normalized_csv(self, fpeam_run_config):
        """summarize() writes *_normalized_total_emissions_by_production_region.csv."""
        config, project = fpeam_run_config
        with FPEAM(run_config=config) as fpeam:
            fpeam.run()
            fpeam.summarize()

        expected = os.path.join(
            str(project),
            'test_integration_normalized_total_emissions_by_production_region.csv'
        )
        assert os.path.exists(expected), f'missing: {expected}'

    def test_summarize_by_region_amounts_match_totals(self, fpeam_run_config):
        """Total emissions in the summary CSV match the raw collect() output."""
        import pandas as pd
        config, project = fpeam_run_config
        with FPEAM(run_config=config) as fpeam:
            fpeam.run()
            fpeam.summarize()

        raw_total = fpeam.results.groupby(['feedstock', 'tillage_type',
                                           'region_production', 'pollutant'],
                                          as_index=False)['pollutant_amount'].sum()

        summary_path = os.path.join(str(project),
                                    'test_integration_total_emissions_by_production_region.csv')
        summary = pd.read_csv(summary_path)

        # Spot check: total NH3 across all regions should match
        raw_nh3 = raw_total[raw_total['pollutant'] == 'nh3']['pollutant_amount'].sum()
        summary_nh3 = summary[summary['pollutant'] == 'nh3']['pollutant_amount'].sum()
        assert abs(raw_nh3 - summary_nh3) < 1e-6, \
            f'NH3 totals diverge: raw={raw_nh3:.4f}, summary={summary_nh3:.4f}'
