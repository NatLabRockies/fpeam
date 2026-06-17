import os
import shutil
import sys
import tempfile

if sys.version_info[1] >= 10:
    from collections.abc import Iterable
else:
    from collections import Iterable

import geopandas
import pandas as pd
from FPEAM import EngineModules
from joblib import Memory
from pkg_resources import resource_filename
from shapely.geometry import MultiPolygon

from . import Data
from . import utils
from .IO import (CONFIG_FOLDER, load_configs)
from .Router import Router

LOGGER = utils.logger(name=__name__)


class FPEAM(object):
    """Base class to hold shared information"""

    __version__ = '2.4.0'

    MODULES = {'emissionfactors': EngineModules.EmissionFactors,
               'fugitivedust': EngineModules.FugitiveDust,
               'MOVES': EngineModules.MOVES,
               'NONROAD': EngineModules.NONROAD}

    def __init__(self, run_config):

        """
        :param run_config: [ConfigObj]
        """
        self._config = None

        self._modules = {}

        self._budget = None
        self._production = None

        self._emission_factors = None
        self._fertilizer_distribution = None
        self._fugitive_dust = None

        self.router = None

        self._temp_dir = tempfile.mkdtemp()

        self.memory = Memory(location=self._temp_dir)

        self.results = None
        self.summaries = {}

        self.config = run_config

        # validate module names
        _modules = self.config.get('modules', None) or self.MODULES.keys()
        _module_error = False
        for _module in _modules:
            try:
                assert _module in self.MODULES.keys()
            except AssertionError:
                _module_error = True
                LOGGER.error('invalid module name: %s; must be one of: %s' % (_module, ', '.join(list(self.MODULES.keys()))))
            else:
                self._modules[_module] = self.MODULES[_module]

        if _module_error:
            raise Exception('invalid module name')

        self.equipment = Data.Equipment(fpath=self.config.get('equipment'), backfill=self.config.as_bool('backfill')).reset_index().rename({'index': 'row_id'}, axis=1)
        self.production = Data.Production(fpath=self.config.get('production'), backfill=self.config.as_bool('backfill')).reset_index().rename({'index': 'row_id'}, axis=1)
        self.feedstock_loss_factors = Data.FeedstockLossFactors(fpath=self.config.get('feedstock_loss_factors'), backfill=self.config.as_bool('backfill')).reset_index().rename({'index': 'row_id'}, axis=1)
        self.truck_capacity = Data.TruckCapacity(fpath=self.config.get('truck_capacity'), backfill=self.config.as_bool('backfill')).reset_index().rename({'index': 'row_id'}, axis=1)
        self.vmt_short_haul = self.config.get('vmt_short_haul')
        self.forestry_feedstock_names = self.config.get('forestry_feedstock_names')

        if self.config.as_bool('use_router_engine') and ('MOVES' in self._modules.keys() or 'fugitivedust' in self._modules.keys()):
            _transportation_graph = Data.TransportationGraph(fpath=self.config.get('transportation_graph'), backfill=self.config.as_bool('backfill'))
            _node_locations = Data.TransportationNodeLocations(fpath=self.config.get('node_locations'), backfill=self.config.as_bool('backfill'))

            if not _transportation_graph.empty and not _node_locations.empty:
                LOGGER.info('Loading routing data; this may take a few minutes')
                self.router = Router(edges=_transportation_graph,
                                     node_map=_node_locations,
                                     memory=self.memory)
        else:
            if 'MOVES' in self._modules.keys() or 'fugitivedust' in self._modules.keys():
                LOGGER.warning('Using fixed distance(s) for all transportation distances')

        for _module in _modules:
            _config = run_config.get(_module.lower(), None) or \
                      load_configs(resource_filename('FPEAM', '%s/%s.ini' % (CONFIG_FOLDER, _module.lower()))
                                   )[_module.lower()]
            _config['scenario_name'] = _config.get('scenario_name', '').strip() or self.config.get('scenario_name')

            _config['project_path'] = self.config['project_path']

            try:
                self.__setattr__(_module,
                                 FPEAM.MODULES[_module](config=_config,
                                                        equipment=self.equipment,
                                                        production=self.production,
                                                        router=self.router,
                                                        feedstock_loss_factors=self.feedstock_loss_factors,
                                                        truck_capacity=self.truck_capacity,
                                                        vmt_short_haul=self.vmt_short_haul,
                                                        forestry_feedstock_names=self.forestry_feedstock_names,
                                                        backfill=self.config.as_bool('backfill')))
            except KeyError:
                if _module not in FPEAM.MODULES.keys():
                    LOGGER.warning('invalid module name: {}.'
                                   ' Must be one of: {}'.format(_module,
                                                                FPEAM.MODULES.keys()))
                else:
                    raise
            except Exception:
                raise
            else:
                self._modules[_module] = self.__getattribute__(_module)

    @property
    def config(self):
        return self._config

    @config.setter
    def config(self, value):

        _fpeam_spec = resource_filename('FPEAM', '%s/fpeam.spec' % (CONFIG_FOLDER, ))

        try:
            _fpeam_config = value['fpeam']
        except KeyError:
            _fpeam_config = resource_filename('FPEAM', '%s/fpeam.ini' % (CONFIG_FOLDER, ))

        _fpeam_config = utils.validate_config(config=_fpeam_config, spec=_fpeam_spec)

        _spec = resource_filename('FPEAM', '%s/run_config.spec' % (CONFIG_FOLDER, ))
        _config = utils.validate_config(config=value['run_config'], spec=_spec)

        _config['config']['fpeam'] = _fpeam_config['config']

        if _config['extras']:
            LOGGER.warning('extra values: %s' % (_config['extras'], ))

        try:
            assert not _config['missing'] and not _config['errors']
        except AssertionError:
            if _config['missing']:
                LOGGER.error('missing values: %s' % (_config['missing'], ))
            if _config['errors']:
                LOGGER.error('invalid values: %s' % (_config['errors'], ))
            raise RuntimeError('Verify config file(s) are complete')
        else:
            self._config = _config['config']

    def run(self, modules=None):
        """
        Execute each Module in <module>.

        :param modules: [list] module classes with run() and save() methods
        :return: [dict] {<module>: <status>, ...}
        """

        if modules and not isinstance(modules, Iterable):
            modules = [modules, ]

        _results = {}

        for _module in modules or self._modules.values():
            LOGGER.info('running module: {}'.format(_module))
            _module.run()
            LOGGER.info('{}: {}'.format(_module, _module.status))
            # @TODO: add results/status details
            _results[_module] = _module.status

        self.results = self.collect(modules)

    def collect(self, modules=None):
        """
        Assemble the full set of results from each module's results and
        merge with the production data to allow for normalizing

        :param modules: [list] module classes with result property.\
        :return: [DataFrame]
        """

        _df_modules = pd.DataFrame()
        _prod = self.production

        # preprocess the feedstock loss factor dataset to obtain factors
        # that can be used to calculate delivered feedstock amounts
        _loss_factors = self.feedstock_loss_factors

        # turn the loss factors into remaining fraction
        _loss_factors.eval('dry_matter_remaining = 1 - dry_matter_loss',
                           inplace=True)

        # calculate separate data frame including only loss factors associated
        # with on-farm activities
        _loss_factors_farmgate = _loss_factors[_loss_factors.supply_chain_stage.isin(['harvest',
                                                                                      'field treatment',
                                                                                      'field drying',
                                                                                      'on farm transport'])]

        # calculate total remaining fraction by feedstock by multiplying
        # the remaining fractions
        _loss_factors = _loss_factors.groupby(['feedstock'],
                                              as_index=False).prod()[['feedstock',
                                                                      'dry_matter_remaining']]

        # calculate total remaining fraction at farm gate
        _loss_factors_farmgate = _loss_factors_farmgate.groupby(['feedstock'],
                                                                as_index=False).prod()[['feedstock',
                                                                                        'dry_matter_remaining']]

        # subset the feedstock production df by which feedstock measures
        # will be used in normalizing pollutant amounts
        # @TODO turn this into user input via a config file
        # @todo check that the measures used here match the ones used in individual modules
        _prod_row_filter = _prod['feedstock_measure'].isin(['harvested',
                                                            'production']).values

        # delete the columns from prod that don't need to be merged into
        # results
        del _prod['region_destination'], _prod['equipment_group'], \
            _prod['row_id']

        # rename the feedstock production units columns to avoid confusion
        # with the pollutant units columns in the results
        _prod.rename(index=str, columns={'unit_numerator':
                                         'feedstock_unit_numerator',
                                         'unit_denominator':
                                         'feedstock_unit_denominator'},
                     inplace=True)

        _prod_filtered = _prod[_prod_row_filter]

        # create a copy of prod to which the feedstock loss factors will be
        # applied to calculate the 'delivered' feesdtock measure type
        _prod_losses = _prod_filtered[_prod_filtered.feedstock_measure == 'production']
        _prod_losses_farmgate = _prod_losses

        # merge with the loss factor dataframes
        _prod_losses = _prod_losses.merge(_loss_factors, on='feedstock')
        _prod_losses_farmgate = _prod_losses_farmgate.merge(_loss_factors_farmgate,
                                                            on='feedstock')

        # recalculate the feedstock amounts to account for losses
        _prod_losses['feedstock_amount'] = _prod_losses.feedstock_amount *\
                                           _prod_losses.dry_matter_remaining
        _prod_losses_farmgate['feedstock_amount'] = _prod_losses_farmgate.feedstock_amount *\
                                                    _prod_losses_farmgate.dry_matter_remaining

        # change the feedstock measure columns to reflect the new feedstock
        # amounts
        _prod_losses['feedstock_measure'] = 'at biorefinery'
        _prod_losses_farmgate['feedstock_measure'] = 'at farm gate'

        # remove the now extraneous loss factor columns
        del _prod_losses['dry_matter_remaining'], _prod_losses_farmgate['dry_matter_remaining']

        # tack on the delivered feedstock dataframes to the filtered one
        _prod_filtered.append(_prod_losses, ignore_index=True, sort=False)
        _prod_filtered.append(_prod_losses_farmgate, ignore_index=True,
                              sort=False)

        # loop thru all modules being run and stack the data frames
        # containing output from each module
        # this will add empty values if a data frame is missing a column,
        # which does happend for some id variables from some modules
        for _module in modules or self._modules.values():
            _df_modules = _df_modules.append(_module.results,
                                             ignore_index=True,
                                             sort=False)

        _df_modules['unit_numerator'] = 'lb pollutant'
        _df_modules['unit_denominator'] = 'county-year'

        # merge the module results with the production df
        _df = _df_modules.merge(_prod_filtered,
                                on=('feedstock',
                                    'tillage_type',
                                    'region_production'))

        return _df

    def summarize(self):
        """
        summarization method called on the results dataframe created by the
        collect method

        :param modules:
        :return:
        """
        LOGGER.info('summarizing results')

        # feedstock-tillage type-region_production
        _summarize_by_region_production = self.results.groupby(['feedstock',
                                                                'tillage_type',
                                                                'region_production',
                                                                'pollutant'],
                                                               as_index=False).sum()

        _summarize_by_region_production['unit_numerator'] = 'lb pollutant'  # @TODO: should we be reading this in from the data?
        _summarize_by_region_production['unit_denominator'] = 'county-year'

        _summarize_by_region_production[['feedstock', 'tillage_type',
                                         'region_production', 'pollutant',
                                         'pollutant_amount',
                                         'unit_numerator',
                                         'unit_denominator']].to_csv(
            os.path.join(self.config.get('project_path'),
                         '%s' %
                         self.config.get('scenario_name') +
                         '_total_emissions_by_production_region.csv'),
            index=False)

        # cache for results tab graphics
        self.summaries['by_region_production'] = _summarize_by_region_production[['feedstock',
                                                                                  'tillage_type',
                                                                                  'region_production',
                                                                                  'pollutant',
                                                                                  'pollutant_amount',
                                                                                  'unit_numerator',
                                                                                  'unit_denominator']]
        if self.config['fpeam'].get('inmap_county_export', False) is True:
            # save InMAP county-level output
            _shp_fpath_in = resource_filename('FPEAM', 'data/inputs/tl_2019_us_county/tl_2019_us_county.shp')
            _df = geopandas.read_file(_shp_fpath_in, dtype={'STATEFP': str, 'COUNTYFP': str, 'geometry': MultiPolygon})[['STATEFP', 'COUNTYFP', 'NAME', 'geometry']]
            _df['region_production'] = _df.STATEFP + _df.COUNTYFP

            _grp_df = _summarize_by_region_production[['region_production', 'pollutant', 'pollutant_amount']].groupby(['region_production', 'pollutant'], as_index=False).sum()
            _grp_df_pivot = _grp_df.pivot(index='region_production', columns='pollutant', values='pollutant_amount')

            _gdf_join = _df[['region_production', 'NAME', 'geometry']].join(other=_grp_df_pivot, on='region_production', how='right')

            _gdf_join.rename(columns={'region_production': 'cnty_fips',
                                      'NAME': 'cnty_name',
                                      'co': 'CO',
                                      'nh3': 'NH3',
                                      'nox': 'NOx',
                                      'pm10': 'PM10',
                                      'pm25': 'PM2_5',
                                      'so2': 'SO2',
                                      'voc': 'VOC'}, inplace=True)

            _shp_fname_out = '%s_county_inmap.shp' % self.config.get('scenario_name')
            _shp_fpath_out = os.path.join(self.config.get('project_path'), _shp_fname_out)
            _gdf_join.to_file(_shp_fpath_out)

        # feedstock-tillage type-region_production
        _results_to_normalize = self.results

        # calculate raw normalized pollutant amounts
        _results_to_normalize.eval('normalized_pollutant_amount = '
                                   'pollutant_amount / feedstock_amount',
                                   inplace=True)

        # add unit columns for normalized pollutant amounts
        _results_to_normalize['normalized_pollutant_unit_numerator'] = \
            _results_to_normalize['unit_numerator']
        _results_to_normalize['normalized_pollutant_unit_denominator'] = \
            _results_to_normalize['feedstock_unit_numerator']

        # sum normalized pollutant amounts over modules and activities
        _results_normalized = _results_to_normalize.groupby(['feedstock',
                                                             'feedstock_measure',
                                                             'tillage_type',
                                                             'region_production',
                                                             'feedstock_amount',
                                                             'feedstock_unit_numerator',
                                                             'pollutant',
                                                             'unit_numerator',
                                                             'normalized_pollutant_unit_numerator',
                                                             'normalized_pollutant_unit_denominator'],
                                                            as_index=False).sum()
        # cache for results tab graphics
        self.summaries['normalized'] = _results_normalized

        # save to csv
        _results_normalized.to_csv(os.path.join(self.config.get('project_path'),
                                                '%s' % self.config.get('scenario_name') +
                                                '_normalized_total_emissions_by_production_region.csv'),
                                   index=False)

        if 'region_transportation' in self.results.columns:
            # feedstock-tillage type-region_transportation
            _summarize_by_region_transportation = self.results.groupby(['feedstock',
                                                                        'tillage_type',
                                                                        'region_transportation',
                                                                        'pollutant'],
                                                                       as_index=False).sum()

            _summarize_by_region_transportation['unit_numerator'] = 'lb pollutant'
            _summarize_by_region_transportation['unit_denominator'] = 'transportation county-year'

            self.summaries['by_region_transportation'] = _summarize_by_region_transportation

            _summarize_by_region_transportation[['feedstock', 'tillage_type',
                                                 'region_transportation',
                                                 'pollutant',
                                                 'pollutant_amount']].to_csv(
                os.path.join(self.config.get('project_path'),
                             '%s' %
                             self.config.get('scenario_name') +\
                             '_transportation_emissions_by_region.csv'),
                index=False)

        # feedstock-tillage type-module
        _summarize_by_module = self.results.groupby(['feedstock',
                                                     'tillage_type',
                                                     'module',
                                                     'pollutant'],
                                                    as_index=False).sum()

        _summarize_by_module['unit_numerator'] = 'lb pollutant'
        _summarize_by_module['unit_denominator'] = 'county-year'

        self.summaries['by_module'] = _summarize_by_module

        _fpath_summary = os.path.join(self.config.get('project_path'),
                                      '%s_total_emissions_by_module.csv'
                                      % self.config.get('scenario_name'))

        _summarize_by_module[['feedstock', 'tillage_type', 'module', 'pollutant',
                              'pollutant_amount']].to_csv(_fpath_summary, index=False)

    def plot(self, modules):
        for _module in modules or self._modules.values():
            LOGGER.debug('plotting %s' % _module)

        raise NotImplementedError

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        shutil.rmtree(self._temp_dir)

        # process exceptions
        if exc_type is not None:
            LOGGER.exception('%s\n%s\n%s' % (exc_type, exc_val, exc_tb))
            return False
        else:
            return self

    def __str__(self):
        return self.__name__
