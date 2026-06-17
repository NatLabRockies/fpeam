import os
import shutil
from subprocess import Popen

import numpy as np
import pandas as pd
import pymysql
from pkg_resources import resource_filename

from FPEAM import utils
from .Module import Module
from ..Data import (RegionFipsMap, StateFipsMap, NONROADEquipment, Irrigation)
from ..IO import DATA_FOLDER

LOGGER = utils.logger(name=__name__)


class NONROAD(Module):

    def __init__(self, config, production, equipment,
                 forestry_feedstock_names, backfill=True, **kvals):
        """

        :param config: [ConfigObj]
        :param production: [DataFrame]
        :param equipment:  [DataFrame]
        :param backfill: [boolean] backfill missing data values with 0
        """

        # init parent
        super(NONROAD, self).__init__(config=config)

        # flag to encode feedstock, tillage type and activity names in all
        # nonroad filepaths and names
        self.encode_names = self.config.get('encode_names')

        self.model_run_title = self.config.get('scenario_name')
        self.nonroad_path = self.config.get('nonroad_path')
        self.nonroad_datafiles_path = self.config.get('nonroad_datafiles_path')
        self.nonroad_exe = self.config.get('nonroad_exe')

        self.project_path = os.path.join(self.config.get('nonroad_datafiles_path'),
                                         self.model_run_title)

        # store nonroad parameters in self
        self.temp_min = self.config.get('nonroad_temp_min')
        self.temp_mean = self.config.get('nonroad_temp_mean')
        self.temp_max = self.config.get('nonroad_temp_max')
        self.diesel_lhv = self.config.get('diesel_lhv')
        self.diesel_nh3_ef = self.config.get('diesel_nh3_ef')
        self.diesel_thc_voc_conversion = self.config.get('diesel_thc_voc_conversion')
        self.diesel_pm10topm25 = self.config.get('diesel_pm10topm25')
        self.time_resource_name = self.config.get('time_resource_name')
        self.feedstock_measure_type = self.config.get('feedstock_measure_type')
        self.irrigation_feedstock_measure_type = self.config.get('irrigation_feedstock_measure_type')

        # nonroad database parameters
        self.nonroad_database = self.config.get('nonroad_database')

        # open connection to NONROAD database for input/output
        self._conn = pymysql.connect(host=self.config.get('nonroad_db_host'),
                                     port=self.config.get('nonroad_db_port'),
                                     user=self.config.get('nonroad_db_user'),
                                     password=self.config.get('nonroad_db_pass'),
                                     db=self.config.get('nonroad_database'),
                                     local_infile=True)

        # dataframe of equipment names matching the names in the equipment
        # input df and SCC codes from nonroad
        self.nonroad_equipment = NONROADEquipment(fpath=self.config.get('nonroad_equipment'),
                                                  backfill=backfill)

        self.irrigation = Irrigation(fpath=self.config.get('irrigation'), backfill=backfill)

        self._equipment = None
        self.equipment = equipment

        self.production = production

        # create a dictionary of conversion factors for later use
        self.conversion_factors = self._set_conversions()

        # mapping from the region_production column of production
        # to NONROAD fips values, used to derive state identifiers and run
        # scenario through NONROAD
        self.region_fips_map = RegionFipsMap(fpath=self.config.get('region_fips_map'),
                                             backfill=backfill)

        # mapping from 2-digit state FIPS to two-character state name
        # abbreviations
        _fpath = resource_filename('FPEAM', '%s/inputs/state_fips_map.csv' % DATA_FOLDER)
        self.state_fips_map = StateFipsMap(fpath=_fpath, backfill=backfill)

        # scenario year
        self.year = self.config.get('year')

        # add year as an extra column in production
        self.production['year'] = self.year

        # list of feedstock names from equipment and production that
        # correspond to forestry products
        self.forestry_feedstock_names = forestry_feedstock_names

        # list of irrigated feedstocks
        self.irrigated_feedstock_names = self.config.get('irrigated_feedstock_names')

        # merge production with the region_production-fips map for NONROAD fips
        self.production = self.production.merge(self.region_fips_map,
                                                how='inner',
                                                left_on='region_production',
                                                right_on='region')

        # add column with state derived from NONROAD fips column to production
        self.production['state_fips'] = self.production.fips.str.slice(stop=2)

        # create filter to pull out only entries relevant to calculating
        # irrigation activity
        # create filter to select only the feedstock measure used by NONROAD
        _prod_irr_filter = (self.production.feedstock.isin(self.irrigated_feedstock_names)) &\
                           (self.production.feedstock_measure ==
                            self.irrigation_feedstock_measure_type)

        # in irrigation, sum both acreage_fraction and rate by unique combinations
        # of equipment_name [which includes fuel type] and equipment_horsepower
        # min_count = 1 forces sums over NAs to also be NA instead of zero
        _irrigation_group = self.irrigation.groupby(['feedstock',
                                                     'state_fips',
                                                     'equipment_name',
                                                     'equipment_horsepower',
                                                     'activity'],
                                                    as_index=False).sum(
            min_count=1)[['feedstock',
                          'state_fips',
                          'equipment_name',
                          'equipment_horsepower',
                          'activity',
                          'acreage_fraction',
                          'rate']]

        # filter down the raw production df and merge with the summed
        # irrigation df
        _prod_irr = self.production[_prod_irr_filter].merge(_irrigation_group,
                                                            on=['feedstock',
                                                                'state_fips'])

        # calculate the total annual rate for irrigation (hours/acre)
        _prod_irr.eval('total_annual_rate = acreage_fraction * rate * '
                       'feedstock_amount', inplace=True)

        # create filter to remove entries with no annual rate due to missing
        # data
        _prod_irr_filter_na = ~_prod_irr.total_annual_rate.isna()

        # apply missing data filter
        _prod_irr = _prod_irr[_prod_irr_filter_na]

        # merge with the state abbreviation df to have both state codes and
        # state (character) abbreviations
        _prod_irr = _prod_irr.merge(self.state_fips_map, how='inner',
                                    on='state_fips')

        # remove the acreage_fraction column so it doesn't get carried along
        # into the production-equipment merged df
        del _prod_irr['acreage_fraction']

        # merge with the state abbreviation df to have both state codes and
        # state (character) abbreviations - this needs to be done twice b/c
        # two copies of production are being merged, one with irrigation and
        # one with equipment
        self.production = self.production.merge(self.state_fips_map,
                                                how='inner',
                                                on='state_fips')
        # create filter to select only the feedstock measure used by NONROAD
        _prod_filter = self.production.feedstock_measure == \
            self.feedstock_measure_type

        # filter down production rows based on what feedstock measure is
        # used by NONROAD
        self.production = self.production[_prod_filter]

        # create filter to select only the time resource entries from the
        # equipment df
        # @TODO: move this to initial equipment setting so validation only happens once
        _equip_filter = self.equipment.resource == self.time_resource_name

        self.equipment = self.equipment[_equip_filter]

        # in the equipment df: sum resource rates over rotation year to prep
        # for calculating average rates
        _equip_grouped = self.equipment.groupby(['feedstock',
                                                 'tillage_type',
                                                 'equipment_group',
                                                 'activity',
                                                 'equipment_name',
                                                 'equipment_horsepower'],
                                                as_index=False).sum()

        # find the maximum rotation year within groups for calculating
        # average rates
        _max_year = self.equipment.groupby(['feedstock', 'tillage_type',
                                            'equipment_group'],
                                           as_index=False).max()[['feedstock',
                                                                  'tillage_type',
                                                                  'equipment_group',
                                                                  'rotation_year']]

        # rename rotation year to max rotation year
        _max_year.rename(index=str, columns={'rotation_year': 'max_rotation_year'},
                         inplace=True)

        # rename rate column to total rate
        _equip_grouped.rename(index=str,
                              columns={'rate': 'total_rotation_rate'},
                              inplace=True)

        # remove rotation_year column so it can be replaced with the maximum
        #  rotation year
        del _equip_grouped['rotation_year']

        # combine the total rate df with the maximum rotation year df
        _equip_avg = _equip_grouped.merge(_max_year, how='left',
                                          on=['feedstock', 'tillage_type',
                                              'equipment_group'])

        # calculate average rate from total rotation rate and max rotation year
        _equip_avg.eval('average_rate = total_rotation_rate / '
                        'max_rotation_year',
                        inplace=True)

        # merge prod and the equip with average rates on feedstock, tillage
        # type and equipment group
        self.prod_equip_merge = self.production.merge(_equip_avg,
                                                      how='inner',
                                                      on=['feedstock',
                                                          'tillage_type',
                                                          'equipment_group'])

        # calculate total hours for each equipment type - activity type combo
        self.prod_equip_merge.eval('total_annual_rate = feedstock_amount * '
                                   'average_rate',
                                   inplace=True)

        # append the irrigation activity data to the rest of the activity data
        self.prod_equip_merge = self.prod_equip_merge.append(_prod_irr,
                                                             ignore_index=True,
                                                             sort=True)

        # create list of unique state-feedstock-tillage type-activity
        # combinations - one population file, one allocation file and
        # one options sub-directory and one out sub-directory will be created
        # for each of these combos
        # this gets stored in self for use in the methods that create the
        # options, allocate and population files
        self.nr_files = self.prod_equip_merge[['state_abbreviation',
                                               'state_fips',
                                               'feedstock',
                                               'tillage_type',
                                               'activity']].drop_duplicates()

        if self.encode_names:
            # create single-character codes for feedstocks, tillage types and
            # activities for use in nonroad file name creation
            _feedstocks = self.prod_equip_merge.feedstock.unique()
            _feedstocks.sort()
            _feedstock_codes = pd.DataFrame({'feedstock': _feedstocks,
                                             'feedstock_code': np.arange(
                                                     _feedstocks.__len__())})
            _feedstock_codes['feedstock_code'] = 'f' + _feedstock_codes['feedstock_code'].map(str)

            _tillage_types = self.prod_equip_merge.tillage_type.unique()
            _tillage_types.sort()
            _tillage_type_codes = pd.DataFrame({'tillage_type': _tillage_types,
                                                'tillage_type_code': np.arange(
                                                        _tillage_types.__len__())})
            _tillage_type_codes['tillage_type_code'] = 't' + _tillage_type_codes[
                'tillage_type_code'].map(str)

            _activities = self.prod_equip_merge.activity.unique()
            _activities.sort()

            _activity_codes = pd.DataFrame({'activity': _activities,
                                            'activity_code': np.arange(
                                                    _activities.__len__())})
            _activity_codes['activity_code'] = 'a' + _activity_codes['activity_code'].map(str)

            # encode feedstock, tillage types and activities
            self.nr_files = self.nr_files.merge(_feedstock_codes,
                                                how='inner',
                                                on='feedstock').merge(
                    _tillage_type_codes, how='inner', on='tillage_type').merge(
                    _activity_codes, how='inner', on='activity')

            # do some assembly to create parseable filenames for each population
            #  file - .pop extension SHOULD NOT be included as it is tacked on
            # when the complete filepaths are created
            self.nr_files['pop_file_names'] = self.nr_files['state_abbreviation'].map(str) + \
                                              '_' + \
                                              self.nr_files['feedstock_code'].map(str) + \
                                              '_' + \
                                              self.nr_files['tillage_type_code'].map(str) + \
                                              '_' + \
                                              self.nr_files['activity_code'].map(str)

            # create the out and options subdirectory names - the OUT and OPT
            # names are identical so only one column is created
            self.nr_files['out_opt_dir_names'] = self.nr_files['feedstock_code'].map(str) \
                                                 + '_' + \
                                                 self.nr_files['tillage_type_code'].map(str) \
                                                 + '_' + \
                                                 self.nr_files['activity_code'].map(str)

        else:

            # do some assembly to create parseable filenames for each population
            #  file - .pop extension SHOULD NOT be included as it is tacked on
            # when the complete filepaths are created
            self.nr_files['pop_file_names'] = self.nr_files['state_abbreviation'].map(str) + \
                                              '_' + \
                                              self.nr_files['feedstock'].map(str) + \
                                              '_' + \
                                              self.nr_files['tillage_type'].map(str) + \
                                              '_' + \
                                              self.nr_files['activity'].map(str)

            # create the out and options subdirectory names - the OUT and OPT
            # names are identical so only one column is created
            self.nr_files['out_opt_dir_names'] = self.nr_files['feedstock'].map(str) \
                                                 + '_' + \
                                                 self.nr_files['tillage_type'].map(str) \
                                                 + '_' + \
                                                 self.nr_files['activity'].map(str)

        # the filenames for the allocate files are the same as for the
        # population files
        self.nr_files['alo_file_names'] = self.nr_files['pop_file_names']

        # create a column for message file names as well
        self.nr_files['msg_file_names'] = self.nr_files['pop_file_names']

        # create dirs in the project path (which includes the scenario name)
        #  if the directories do not already exist
        _nr_folders = [self.project_path,
                       os.path.join(self.project_path, 'MESSAGES'),
                       os.path.join(self.project_path, 'ALLOCATE'),
                       os.path.join(self.project_path, 'POP'),
                       os.path.join(self.project_path, 'OPT'),
                       os.path.join(self.project_path, 'OUT'),
                       os.path.join(self.project_path, 'FIGURES'),
                       os.path.join(self.project_path, 'QUERIES')]

        # loop through all completely assembled filepaths and create a list
        # of the ones that are more than 60 characters
        _filepath_list = np.array([])

        # go through all directories and file names to assemble complete paths
        for i in np.arange(self.nr_files.shape[0]):
            # message files
            _filepath_list = np.append(_filepath_list,
                                       os.path.join(_nr_folders[1],
                                                    self.nr_files.msg_file_names.iloc[i] +
                                                    '.msg'))
            # allocate files
            _filepath_list = np.append(_filepath_list,
                                       os.path.join(_nr_folders[2],
                                                    self.nr_files.alo_file_names.iloc[i] +
                                                    '.alo'))
            # population files
            _filepath_list = np.append(_filepath_list,
                                       os.path.join(_nr_folders[3],
                                                    self.nr_files.pop_file_names.iloc[i] +
                                                    '.pop'))
            # options files
            _filepath_list = np.append(_filepath_list,
                                       os.path.join(_nr_folders[4],
                                                    self.nr_files.out_opt_dir_names.iloc[i],
                                                    self.nr_files.state_abbreviation.iloc[i] +
                                                    '.opt'))
            # out files
            _filepath_list = np.append(_filepath_list,
                                       os.path.join(_nr_folders[5],
                                                    self.nr_files.out_opt_dir_names.iloc[i],
                                                    self.nr_files.state_abbreviation.iloc[i] +
                                                    '.out'))

        # get a list of just those file paths which exceed 60 characters
        _failpath_list = np.array(_filepath_list)[np.array(self._strlist_len(_filepath_list)) > 60]

        # check that that file path list is empty (all file paths are under
        # the 60 character limit) - if not, record one error per too-long
        # file path
        try:
            assert _failpath_list.__len__() == 0

        except AssertionError:
            for i in _failpath_list:
                LOGGER.error('Filepath too long: %s' % i)

            raise ValueError('Total file path length for each NONROAD file '
                             'cannot exceed 60 characters')

        # if all file paths are under the limit, proceed to creating
        # directories and subdirectories for storing NONROAD files
        for _folder in _nr_folders:
            if os.path.exists(_folder):
                shutil.rmtree(_folder)
            os.makedirs(_folder)

        if self.encode_names:
            LOGGER.debug('saving encoded feedstock, tillage, and activity codes to %s' % self.project_path)
            # save files containing encoded feedstock, tillage type and activity
            #  names
            # these dfs are created above if self.encode_names is True
            _feedstock_codes.to_csv(os.path.join(self.project_path, 'feedstock_codes.csv')
                                    , index=False)
            _tillage_type_codes.to_csv(os.path.join(self.project_path, 'tillage_type_codes.csv'),
                                       index=False)
            _activity_codes.to_csv(
                os.path.join(self.project_path, 'activity_codes.csv'),
                index=False)

        # create subdirectories in the OUT and OPT directories for each
        # feedstock-tillagetype-activity combination

        for _f in ('OUT', 'OPT'):
            for _dir in list(self.nr_files.out_opt_dir_names):
                _fpath = os.path.join(self.project_path, _f, _dir)
                if os.path.exists(_fpath):
                    shutil.rmtree(_fpath)
                os.makedirs(_fpath)

    @property
    def equipment(self):
        return self._equipment

    @equipment.setter
    def equipment(self, value):

        def _validate_hp_ranges():
            _sql = "SELECT CONVERT(SCC, CHAR) AS nonroad_equipment_scc," \
                   " MIN(hpMin) AS hp_min," \
                   " MAX(hpMax) AS hp_max" \
                   " FROM nrsourceusetype source" \
                   " JOIN nrhprangebin hpbin ON (source.NRHPRangeBinID = hpbin.NRHPRangeBinID)" \
                   " GROUP BY SCC" \
                   " ORDER BY SCC;"

            _equip = value[['equipment_name', 'equipment_horsepower']]\
                .drop_duplicates()\
                .merge(self.nonroad_equipment[['equipment_name', 'nonroad_equipment_scc']]
                       .drop_duplicates(), on='equipment_name')\
                .merge(pd.read_sql(sql=_sql, con=self._conn), on='nonroad_equipment_scc')

            _invalid = _equip[~_equip.equipment_horsepower.between(_equip.hp_min, _equip.hp_max)]

            if not _invalid.empty:
                for _row in [list(x) for x in set(tuple(x) for x in _invalid.values.tolist())]:
                    LOGGER.error('{0} ({2}) horsepower must be between {3} and {4} (currently {1})'
                                 .format(*_row))
                return False
            else:
                return True

        if _validate_hp_ranges():
            self._equipment = value
        else:
            raise ValueError('equipment group contains invalid HP ranges')

    @staticmethod
    def _strlist_len(stringlist):
        """
        get length of each string in list of strings
        :param stringlist:
        :return: list of string lengths
        """
        return [len(s) for s in stringlist]

    def create_allocate_files(self):
        """
        write spatial indicators to .alo file for the NonRoad program to
        use. File are written on a state-level basis.
        :return: None
        """

        # @note the indent has to be zero here b/c otherwise it will
        # write to the allocation file
        _preamble = """
------------------------------------------------------------------------
This is the packet that contains the allocation indicator data.  Each
indicator value is a measured or projected value such as human
population or land area.  The format is as follows.

1-3    Indicator code
6-10   FIPS code (can be global FIPS codes e.g. 06000 = all of CA)
11-15  Subregion code (blank means is entire nation, state or county)
16-20  Year of estimate or prediction
21-40  Indicator value
41-45  Blank (unused)
46+    Optional Description (unused)
------------------------------------------------------------------------
/INDICATORS/
"""

        # loop through state-tillagetype-activity to create files and write the
        #  preamble
        for i in np.arange(self.nr_files.shape[0]):

            _fpath = os.path.join(self.project_path, 'ALLOCATE',
                                  self.nr_files.alo_file_names.iloc[i] + '.alo')
            LOGGER.debug('creating allocation file %s (%s/%s)' % (_fpath, i + 1, self.nr_files.shape[0]))
            # initialize file
            with open(_fpath, 'w') as _alo_file_path:

                _alo_file_path.writelines(_preamble)

                # pull out the production rows relevant to the file being generated
                #  to get a list of FIPS - also filters by feedstock measure
                _prod_filter = (self.prod_equip_merge.state_abbreviation ==
                                self.nr_files.state_abbreviation.iloc[i]) & \
                               (self.prod_equip_merge.feedstock ==
                                self.nr_files.feedstock.iloc[i]) & \
                               (self.prod_equip_merge.tillage_type ==
                                self.nr_files.tillage_type.iloc[i]) & \
                               (self.prod_equip_merge.activity ==
                                self.nr_files.activity.iloc[i])

                # filter down production and get the list of both fips and
                # feedstock amounts (indicator values)
                # the groupby and sum accounts for potentially multiple
                # entries with different feedstock amounts but the same
                # fips, from a one-to-many region-to-fips mapping
                _indicator_list = self.prod_equip_merge[_prod_filter][[
                    'fips',
                    'feedstock',
                    'feedstock_amount']].drop_duplicates().groupby(['fips',
                                                                    'feedstock']).sum().reset_index(drop=False)

                # write line with state indicator total
                _ind_state_total = _indicator_list.feedstock_amount.sum()

                # get the state two-digit code for the state total indicator
                #  file line
                _state_code = self.nr_files.state_fips.iloc[i]

                # loop through fips w/in each state-tillagetype-activity to create the
                # indicator lines in the file
                for _fips in _indicator_list['fips'].unique():
                    # calculate indicators by fips - harvested acres for all crop
                    # except for forest residues and forest whole trees; ??? for the
                    # two forest products

                    if self.forestry_feedstock_names is not None:

                        if self.nr_files.feedstock.iloc[i] in \
                                self.forestry_feedstock_names:

                            _ind_code = 'LOG'

                            # calculate forestry indicator
                            _ind = _indicator_list.feedstock_amount[_indicator_list['fips'] == _fips].values[0] * 2000.0 / 30.0

                        else:

                            _ind_code = 'FRM'

                            # calculate harvested acres indicator
                            _ind = _indicator_list.feedstock_amount[
                                _indicator_list.fips ==
                                _fips].values[0]

                    else:

                        _ind_code = 'FRM'

                        # calculate harvested acres indicator
                        _ind = _indicator_list.feedstock_amount[
                            _indicator_list.fips == _fips].values[0]

                    _alo_line = """%s  %s      %s    %s\n""" % (
                        _ind_code, _fips, self.year, _ind)

                    _alo_file_path.writelines(_alo_line)

                if self.forestry_feedstock_names is not None:

                    if self.nr_files.feedstock.iloc[i] in \
                            self.forestry_feedstock_names:

                        _ind_state_total = _ind_state_total * 2000.0 / 30.0

                        _state_line = """LOG  %s000      %s    %s\n""" % (
                            _state_code, self.year, _ind_state_total)

                    else:

                        _state_line = """FRM  %s000      %s    %s\n""" % (
                            _state_code, self.year, _ind_state_total)

                else:

                    _state_line = """FRM  %s000      %s    %s\n""" % (
                        _state_code, self.year, _ind_state_total)

                # write the state total line
                _alo_file_path.writelines(_state_line)

                # write final line of file
                _alo_file_path.writelines('/END/')

    def create_options_files(self):
        """
        creates options file by filling in a template with values from
        config, production and equipment
        :return: None
        """

        # populate dictionary for options file formatting with entries that
        # DO NOT change with state, fips, feedstock, tillage type or activity
        # these values are the SAME in every options file created regardless
        #  of scenario
        kvals = {'episode_year': self.year,
                 'model_run_title': self.model_run_title,
                 'temp_min': self.temp_min,
                 'temp_max': self.temp_max,
                 'temp_mean': self.temp_mean,
                 'ALLOC_XREF': os.path.join(self.nonroad_path, 'data',
                                            'allocate', 'allocate.xrf'),
                 'ACTIVITY': os.path.join(self.nonroad_path,
                                          'data', 'activity', 'activity.dat'),
                 'EXH_TECHNOLOGY': os.path.join(self.nonroad_path,
                                                'data', 'tech',
                                                'tech-exh.dat'),
                 'EVP_TECHNOLOGY': os.path.join(self.nonroad_path,
                                                'data', 'tech',
                                                'tech-evp.dat'),
                 'SEASONALITY': os.path.join(self.nonroad_path,
                                             'data', 'season', 'season.dat'),
                 'REGIONS': os.path.join(self.nonroad_path,
                                         'data', 'season', 'season.dat'),
                 'EPS2_AMS': '',
                 'US_COUNTIES_FIPS': os.path.join(self.nonroad_path, 'data',
                                                  'allocate', 'fips.dat'),
                 'RETROFIT': '',
                 'National_defaults': os.path.join(self.nonroad_path, 'data',
                                                   'growth', 'nation.grw'),
                 'EMFAC_THC_exhaust': os.path.join(self.nonroad_path, 'data',
                                                   'emsfac', 'exhthc.emf'),
                 'EMFAC_CO_exhaust': os.path.join(self.nonroad_path, 'data',
                                                  'emsfac', 'exhco.emf'),
                 'EMFAC_NOX_exhaust': os.path.join(self.nonroad_path, 'data',
                                                   'emsfac', 'exhnox.emf'),
                 'EMFAC_PM_exhaust': os.path.join(self.nonroad_path, 'data',
                                                  'emsfac', 'exhpm.emf'),
                 'EMFAC_BSFC': os.path.join(self.nonroad_path, 'data',
                                            'emsfac', 'bsfc.emf'),
                 'EMFAC_Crankcase': os.path.join(self.nonroad_path, 'data',
                                                 'emsfac', 'crank.emf'),
                 'EMFAC_Spillage': os.path.join(self.nonroad_path, 'data',
                                                'emsfac', 'spillage.emf'),
                 'EMFAC_Diurnal': os.path.join(self.nonroad_path, 'data',
                                               'emsfac', 'evdiu.emf'),
                 'EMFAC_Tank_Perm': os.path.join(self.nonroad_path, 'data',
                                                 'emsfac', 'evtank.emf'),
                 'EMFAC_Non_RM_Hose_Perm': os.path.join(self.nonroad_path,
                                                        'data', 'emsfac',
                                                        'evhose.emf'),
                 'EMFAC_RM_Fill_Neck_Perm': os.path.join(self.nonroad_path,
                                                         'data', 'emsfac',
                                                         'evneck.emf'),
                 'EMFAC_RM_Supply_Return': os.path.join(self.nonroad_path,
                                                        'data', 'emsfac',
                                                        'evsupret.emf'),
                 'EMFAC_RM_Vent_Perm': os.path.join(self.nonroad_path, 'data',
                                                    'emsfac', 'evvent.emf'),
                 'EMFAC_Hot_Soaks': os.path.join(self.nonroad_path, 'data',
                                                 'emsfac', 'evhotsk.emf'),
                 'EMFAC_RuningLoss': os.path.join(self.nonroad_path,
                                                  'data', 'emsfac',
                                                  'evrunls.emf'),
                 'DETERIORATE_THC_exhaust': os.path.join(self.nonroad_path,
                                                         'data', 'detfac',
                                                         'exhthc.det'),
                 'DETERIORATE_CO_exhaust': os.path.join(self.nonroad_path,
                                                        'data', 'detfac',
                                                        'exhco.det'),
                 'DETERIORATE_NOX_exhaust': os.path.join(self.nonroad_path,
                                                         'data', 'detfac',
                                                         'exhnox.det'),
                 'DETERIORATE_PM_exhaust': os.path.join(self.nonroad_path,
                                                        'data', 'detfac',
                                                        'exhpm.det'),
                 'DETERIORATE_Diurnal': os.path.join(self.nonroad_path,
                                                     'data', 'detfac',
                                                     'evdiu.det'),
                 'DETERIORATE_Tank_Perm': os.path.join(self.nonroad_path,
                                                       'data', 'detfac',
                                                       'evtank.det'),
                 'DETERIORATE_Non_RM_Hose_Perm': os.path.join(
                         self.nonroad_path, 'data', 'detfac', 'evhose.det'),
                 'DETERIORATE_RM_Fill_Neck_Perm': os.path.join(
                         self.nonroad_path, 'data', 'detfac', 'evneck.det'),
                 'DETERIORATE_RM_Supply_Return': os.path.join(
                         self.nonroad_path, 'data', 'detfac', 'evsupret.det'),
                 'DETERIORATE_RM_Vent_Perm': os.path.join(self.nonroad_path,
                                                          'data', 'detfac',
                                                          'evvent.det'),
                 'DETERIORATE_Hot_Soaks': os.path.join(self.nonroad_path,
                                                       'data', 'detfac',
                                                       'evhotsk.det'),
                 'DETERIORATE_RuningLoss': os.path.join(self.nonroad_path,
                                                        'data', 'detfac',
                                                        'evrunls.det'),
                 'EXHAUST_BMY_OUT': '',
                 'EVAP_BMY_OUT': '',
                 'SI_report_file_CSV': os.path.join(self.project_path,
                                                    'MESSAGES',
                                                    'NRPOLLUT.csv'),
                 'DAILY_TEMPS_RVP': ''}

        _options_file_template = """
------------------------------------------------------
                  PERIOD PACKET
1  - Char 10  - Period type for this simulation.
                  Valid responses are: ANNUAL, SEASONAL, and MONTHLY
2  - Char 10  - Type of inventory produced.
                  Valid responses are: TYPICAL DAY and PERIOD TOTAL
3  - Integer  - year of episode (4 digit year)
4  - Char 10  - Month of episode (use complete name of month)
5  - Char 10  - Type of day
                  Valid responses are: WEEKDAY and WEEKEND
------------------------------------------------------
/PERIOD/
Period type        : Annual
Summation type     : Period total
Year of episode    : {episode_year}
Season of year     :
Month of year      :
Weekday or weekend : Weekday
Year of growth calc:
Year of tech sel   :
/END/

------------------------------------------------------
                  OPTIONS PACKET
1  -  Char 80  - First title on reports
2  -  Char 80  - Second title on reports
3  -  Real 10  - Fuel RVP of gasoline for this simulation
4  -  Real 10  - Oxygen weight percent of gasoline for simulation
5  -  Real 10  - Percent sulfur for gasoline
6  -  Real 10  - Percent sulfur for diesel
7  -  Real 10  - Percent sulfur for LPG/CNG
8  -  Real 10  - Minimum daily temperature (deg. F)
9  -  Real 10  - maximum daily temperature (deg. F)
10 -  Real 10  - Representative average daily temperature (deg. F)
11 -  Char 10  - Flag to determine if region is high altitude
                      Valid responses are: HIGH and LOW
12 -  Char 10  - Flag to determine if RFG adjustments are made
                      Valid responses are: YES and NO
------------------------------------------------------
/OPTIONS/
Title 1            : {model_run_title}
Title 2            :
Fuel RVP for gas   : 8.0
Oxygen Weight %    : 2.62
Gas sulfur %       : 0.0339
Diesel sulfur %    : 0.0011
Marine Dsl sulfur %: 0.0435
CNG/LPG sulfur %   : 0.003
Minimum temper. (F): {temp_min}
Maximum temper. (F): {temp_max}
Average temper. (F): {temp_mean}
Altitude of region : LOW
EtOH Blend % Mkt   : 78.8
EtOH Vol %         : 9.5
/END/

------------------------------------------------------
                  REGION PACKET
US TOTAL   -  emissions are for entire USA without state
              breakout.

50STATE    -  emissions are for all 50 states
              and Washington D.C., by state.

STATE      -  emissions are for a select group of states
              and are state-level estimates

COUNTY     -  emissions are for a select group of counties
              and are county level estimates.  If necessary,
              allocation from state to county will be performed.

SUBCOUNTY  -  emissions are for the specified sub counties
              and are subcounty level estimates.  If necessary,
              county to subcounty allocation will be performed.

US TOTAL   -  Nothing needs to be specified.  The FIPS
              code 00000 is used automatically.

50STATE    -  Nothing needs to be specified.  The FIPS
              code 00000 is used automatically.

STATE      -  state FIPS codes

COUNTY     -  state or county FIPS codes.  State FIPS
              code means include all counties in the
              state.

SUBCOUNTY  -  county FIPS code and subregion code.
------------------------------------------------------
/REGION/
Region Level       : COUNTY
All STATE          : {state_fips}
/END/

or use -
Region Level       : STATE
Michigan           : 26000
------------------------------------------------------

              SOURCE CATEGORY PACKET

This packet is used to tell the model which source
categories are to be processed.  It is optional.
If used, only those source categories list will
appear in the output data file.  If the packet is
not found, the model will process all source
categories in the population files.
------------------------------------------------------


------------------------------------------------------
/RUNFILES/
ALLOC XREF         : {ALLOC_XREF}
ACTIVITY           : {ACTIVITY}
EXH TECHNOLOGY     : {EXH_TECHNOLOGY}
EVP TECHNOLOGY     : {EVP_TECHNOLOGY}
SEASONALITY        : {SEASONALITY}
REGIONS            : {REGIONS}
MESSAGE            : {MESSAGE}
OUTPUT DATA        : {OUTPUT_DATA}
EPS2 AMS           : {EPS2_AMS}
US COUNTIES FIPS   : {US_COUNTIES_FIPS}
RETROFIT           : {RETROFIT}
/END/

------------------------------------------------------
This is the packet that defines the equipment population
files read by the model.
------------------------------------------------------
/POP FILES/
Population File    : {Population_File}
/END/

------------------------------------------------------
This is the packet that defines the growth files
files read by the model.
------------------------------------------------------
/GROWTH FILES/
National defaults  : {National_defaults}
/END/

/ALLOC FILES/
Harvested acres    : {Harvested_acres}
/END/

------------------------------------------------------
This is the packet that defines the emissions factors
files read by the model.
------------------------------------------------------
/EMFAC FILES/
THC exhaust        : {EMFAC_THC_exhaust}
CO exhaust         : {EMFAC_CO_exhaust}
NOX exhaust        : {EMFAC_NOX_exhaust}
PM exhaust         : {EMFAC_PM_exhaust}
BSFC               : {EMFAC_BSFC}
Crankcase          : {EMFAC_Crankcase}
Spillage           : {EMFAC_Spillage}
Diurnal            : {EMFAC_Diurnal}
Tank Perm          : {EMFAC_Tank_Perm}
Non-RM Hose Perm   : {EMFAC_Non_RM_Hose_Perm}
RM Fill Neck Perm  : {EMFAC_RM_Fill_Neck_Perm}
RM Supply/Return   : {EMFAC_RM_Supply_Return}
RM Vent Perm       : {EMFAC_RM_Vent_Perm}
Hot Soaks          : {EMFAC_Hot_Soaks}
RuningLoss         : {EMFAC_RuningLoss}
/END/

------------------------------------------------------
This is the packet that defines the deterioration factors
files read by the model.
------------------------------------------------------
/DETERIORATE FILES/
THC exhaust        : {DETERIORATE_THC_exhaust}
CO exhaust         : {DETERIORATE_CO_exhaust}
NOX exhaust        : {DETERIORATE_NOX_exhaust}
PM exhaust         : {DETERIORATE_PM_exhaust}
Diurnal            : {DETERIORATE_Diurnal}
Tank Perm          : {DETERIORATE_Tank_Perm}
Non-RM Hose Perm   : {DETERIORATE_Non_RM_Hose_Perm}
RM Fill Neck Perm  : {DETERIORATE_RM_Fill_Neck_Perm}
RM Supply/Return   : {DETERIORATE_RM_Supply_Return}
RM Vent Perm       : {DETERIORATE_RM_Vent_Perm}
Hot Soaks          : {DETERIORATE_Hot_Soaks}
RuningLoss         : {DETERIORATE_RuningLoss}
/END/

Optional Packets - Add initial slash "/" to activate

/STAGE II/
Control Factor     : 0.0
/END/
Enter percent control: 95 = 95% control = 0.05 x uncontrolled
Default should be zero control.

/MODELYEAR OUT/
EXHAUST BMY OUT    : {EXHAUST_BMY_OUT}
EVAP BMY OUT       : {EVAP_BMY_OUT}
/END/

SI REPORT/
SI report file-CSV : {SI_report_file_CSV}
/END/

/DAILY FILES/
DAILY TEMPS/RVP    : {DAILY_TEMPS_RVP}
/END/

PM Base Sulfur
 cols 1-10: dsl tech type;
 11-20: base sulfur wt%; or '1.0' means no-adjust (cert= in-use)
/PM BASE SULFUR/
T2        0.0350    0.02247
T3        0.2000    0.02247
T3B       0.0500    0.02247
T4A       0.0500    0.02247
T4B       0.0015    0.02247
T4        0.0015    0.30
T4N       0.0015    0.30
T2M       0.0350    0.02247
T3M       1.0       0.02247
T4M       1.0       0.02247
/END/
"""

        # assemble id variable-specific kvals of file names and paths and
        # the state identifier

        # loop through the feedstock-tillage-activity combinations stored in
        # nr_files
        for i in np.arange(self.nr_files.shape[0]):
            kvals_fips = {'state_fips': '{fips:0<5}'.format(fips=self.nr_files.state_fips.iloc[i]),
                          'MESSAGE': os.path.join(self.project_path,
                                                  'MESSAGES',
                                                  self.nr_files.msg_file_names.iloc[i] + '.msg'),
                          'OUTPUT_DATA': os.path.join(self.project_path, 'OUT',
                                                      self.nr_files.out_opt_dir_names.iloc[i],
                                                      self.nr_files.state_abbreviation.iloc[
                                                          i] + '.out'),
                          'Population_File': os.path.join(self.project_path,
                                                          'POP',
                                                          self.nr_files.pop_file_names.iloc[
                                                              i] + '.pop'),
                          'Harvested_acres': os.path.join(self.project_path,
                                                          'ALLOCATE',
                                                          self.nr_files.alo_file_names.iloc[
                                                              i] + '.alo')}

            # complete path to state OPT file including the subdirectory
            # name and the filename which is the state abbreviation
            f = os.path.join(self.project_path, 'OPT',
                             self.nr_files.out_opt_dir_names.iloc[i],
                             self.nr_files.state_abbreviation.iloc[i] + '.opt')
            LOGGER.debug('creating option file %s (%s/%s)' % (f, i + 1, self.nr_files.shape[0]))

            with open(f, 'w') as _opt_file:
                _opt_file.writelines(_options_file_template.format(**kvals,
                                                                   **kvals_fips))

    def _write_population_file_line(self, df, _pop_file):
        """
        Function for applying over the rows of a dataframe containing all
        relevant NONROAD equipment population data
        :return: None
        """

        # check that hpMax will not exceed the character limit, and round to
        #  avoid decimal places if so
        if df.hpMax.__str__().__len__() > 5:
            hpMax_trim = np.int(df.hpMax)
        else:
            hpMax_trim = df.hpMax

        kvals = {'fips': df.fips,
                 'sub_reg': '',
                 'year': self.year,
                 'scc_code': df.SCC,
                 'equip_desc': df.equipment_description,
                 'min_hp': df.hpMin,
                 'max_hp': hpMax_trim,
                 'avg_hp': df.hpAvg,
                 'life': np.int(df.equipment_lifetime),
                 'flag': 'DEFAULT',
                 'pop': df.equipment_population}

        _string_to_write = '{fips:0>5} {sub_reg:>5} {year:>4} {scc_code:>10}' \
                           ' {equip_desc:<40} {min_hp:>5} {max_hp:>5} {avg_hp:>5.1f}' \
                           ' {life:>5} {flag:<10} {pop:>17.7f} \n'.format(**kvals)

        _pop_file.writelines(_string_to_write)

        return None

    def create_population_files(self):
        """
        Calculates  populations of all equipment from
        operation-hours found in the equipment input and the annual hours of
        operation from the MOVES database
        :return: None
        """

        # preprocess and merge equipment and production dfs

        # assemble kvals for sql statement formatting
        kvals = {}
        kvals['nonroad_database'] = self.nonroad_database

        # read in nrsourceusetype table to get the hp range IDs, hp averages,
        # and hours used per year (annual activity used to calculate
        # population) by SCC
        _nrsourceusetype_sql = """SELECT SCC, NRHPRangeBinID, 
            medianLifeFullLoad, hoursUsedPerYear, hpAvg
            FROM {nonroad_database}.nrsourceusetype;""".format(**kvals)

        _nrsourceusetype = pd.read_sql(_nrsourceusetype_sql, self._conn)

        # rename the equipment lifetime column
        _nrsourceusetype.rename(index=str,
                                columns={'medianLifeFullLoad':
                                             'equipment_lifetime'},
                                inplace=True)

        # filter down the nrsourceusetype table based on the list of
        # equipment in user-provided nonroad_equipment
        _scc_filter = _nrsourceusetype.SCC.isin(
                self.nonroad_equipment.nonroad_equipment_scc)

        _nrsourceusetype_filtered = _nrsourceusetype[_scc_filter]

        # read in nrhprangebin that matches hp range IDs to hp min and max
        # values
        _nrhprangebin_sql = """SELECT NRHPRangeBinID, hpMin, hpMax
                        FROM {nonroad_database}.nrhprangebin""".format(**kvals)

        _nrhprangebin = pd.read_sql(_nrhprangebin_sql, self._conn)

        # merge the nonroad_equipment, nrsourceusetype and nrhprangebin
        # together to generate a df of information needed in the population
        # file
        # the dropna is because the default nonroad_equipment file has many
        # missing values; it won't impact a file with no missing values
        _nr_pop_info = self.nonroad_equipment.dropna().merge(_nrsourceusetype,
                                                             how='inner',
                                                             left_on='nonroad_equipment_scc',
                                                             right_on='SCC').merge(
                _nrhprangebin,
                how='inner',
                on='NRHPRangeBinID')

        _nr_equip_filter = self.prod_equip_merge[['equipment_name',
                                                  'equipment_horsepower']].drop_duplicates()

        _nr_pop_info_filtered = _nr_pop_info.merge(_nr_equip_filter,
                                                   how='inner',
                                                   on='equipment_name')

        # create horsepower filter based on comparing the equipment hp to hp
        #  bins - this is to avoid multiple entries with different hp
        # ranges for each piece of equipment
        _hp_filter = ((_nr_pop_info_filtered.equipment_horsepower >=
                       _nr_pop_info_filtered.hpMin) & (
                              _nr_pop_info_filtered.equipment_horsepower <=
                              _nr_pop_info_filtered.hpMax))

        _nr_pop_info_filtered = _nr_pop_info_filtered[_hp_filter]

        # merge the nr population info with equipment before calculating equipment
        # population from actual activity hours and hours-per-year from nonroad
        _nr_pop_equip_merge = self.prod_equip_merge.merge(_nr_pop_info_filtered,
                                                          how='left',
                                                          on=['equipment_name',
                                                              'equipment_horsepower'])

        # calculate the equipment population from the annual rate (from the
        # equipment input data) and the hours used per year (from nonroad
        # defaults)
        _nr_pop_equip_merge.eval('equipment_population = total_annual_rate / '
                                 'hoursUsedPerYear', inplace=True)

        # sum equipment populations so there's only one population per
        # equipment type
        # this will also sum up entries with the same fips that result from
        # a one-to-many region-to-fips mapping
        _nr_pop = _nr_pop_equip_merge.groupby(['state_abbreviation',
                                               'feedstock',
                                               'tillage_type',
                                               'activity',
                                               'fips',
                                               'year',
                                               'SCC',
                                               'equipment_description',
                                               'hpMin',
                                               'hpMax',
                                               'hpAvg',
                                               'equipment_lifetime'],
                                              as_index=False).sum()

        # keep only the columns relevant to either the population file name
        # or file contents
        _nr_pop = _nr_pop[['state_abbreviation', 'feedstock',
                           'tillage_type', 'activity', 'fips', 'year',
                           'SCC', 'equipment_description', 'hpMin', 'hpMax',
                           'hpAvg', 'equipment_lifetime',
                           'equipment_population']]

        # use population info to construct population files

        # set path to population file for this scenario
        # project_path already contains the scenario name
        _pop_dir = os.path.join(self.project_path, 'POP')

        _opening_lines = """
------------------------------------------------------------------------------
  1 -   5   FIPS code
  7 -  11   subregion code (used for subcounty estimates)
 13 -  16   year of population estimates
 18 -  27   SCC code (no globals accepted)
 29 -  68   equipment description (ignored)
 70 -  74   minimum HP range
 76 -  80   maximum HP range (ranges must match those internal to model)
 82 -  86   average HP in range (if blank model uses midpoint)
 88 -  92   expected useful life (in hours of use)
 93 - 102   flag for scrappage distribution curve (DEFAULT = standard curve)
106 - 122   population estimate

FIPS       Year  SCC        Equipment Description                    HPmn  HPmx HPavg  Life ScrapFlag     Population
------------------------------------------------------------------------------
/POPULATION/
"""

        # open, create and close all population files for a scenario
        for i in np.arange(self.nr_files.shape[0]):
            # construct complete path to population file
            _pop_path = os.path.join(_pop_dir,
                                     self.nr_files.pop_file_names.iloc[
                                         i] + '.pop')

            LOGGER.debug('creating %s population file (%s/%s)' % (_pop_path, i + 1, self.nr_files.shape[0]))
            # create filter to pull out only the lines in _nr_pop that are
            # relevant to this population file
            _nr_pop_filter = (_nr_pop.state_abbreviation ==
                              self.nr_files.state_abbreviation.iloc[i]) & (
                                     _nr_pop.feedstock == self.nr_files.feedstock.iloc[i]) \
                             & (_nr_pop.tillage_type ==
                                self.nr_files.tillage_type.iloc[i]) & (
                                     _nr_pop.activity == self.nr_files.activity.iloc[i])

            # subset _nr_pop
            _nr_pop_sub = _nr_pop[_nr_pop_filter]

            # # get components of population file lines
            # _state = self.nr_files.state_abbreviation.iloc[i]
            # _feedstock = self.nr_files.feedstock.iloc[i]
            # _tillage_type = self.nr_files.tillage_type.iloc[i]
            # _activity = self.nr_files.activity.iloc[i]

            # open, write and close population file
            with open(_pop_path, 'w') as _pop_file:
                # write the population file preamble to file
                _pop_file.writelines(_opening_lines)

                # apply the writing function over each row of the subsetted
                # _nr_pop dataframe to write each line of the population file
                _nr_pop_sub.apply(func=self._write_population_file_line,
                                  axis=1, args=(_pop_file, ))

                # write ending line
                _pop_file.writelines('/END/')

    def create_batch_files(self):
        """
        Creates all batch files by feedstock-tillage-activity combination
        Creates the master batch file that calls all other batch files
        :return: None
        """
        # specify directory where batch files are saved - same as location
        # of the OPT subdirectories
        _batch_path = os.path.join(self.project_path, 'OPT')

        kvals = {}
        kvals['nonroad_datafiles_path'] = self.project_path
        kvals['nonroad_exe_path'] = os.path.join(self.nonroad_path,
                                                 self.nonroad_exe)

        # create files and write the first line which is identical across
        # all batch files except for the master file
        _files = list(self.nr_files.out_opt_dir_names.drop_duplicates())
        for idx, i in enumerate(_files):
            LOGGER.debug('creating %s batch file (%s/%s)' % (i, idx + 1, len(_files)))
            # create the full path to the batch file
            _batch_filepath = os.path.join(_batch_path, i + '.bat')

            # pull out only the rows of nr_files that are relevant to this
            # batch file
            nr_files_sub = self.nr_files[self.nr_files.out_opt_dir_names == i]

            # initialize the batch file
            with open(_batch_filepath, 'w') as _batch_file:

                # write the first line that sets the current director
                _batch_file.writelines("""cd {nonroad_datafiles_path}\n""".format(
                        **kvals))

                # loop through the subset of nr_files
                for j in np.arange(nr_files_sub.shape[0]):
                    # assemble the full filepath to each .opt file relevant
                    # to this batch file
                    kvals['opt_filepath'] = os.path.join(_batch_path,
                                                         nr_files_sub.out_opt_dir_names.iloc[j],
                                                         nr_files_sub.state_abbreviation.iloc[
                                                             j] + '.opt')

                    # write each line of the batch file
                    _batch_file.writelines(
                        """{nonroad_exe_path} {opt_filepath}\n""".format(**kvals))

                # close the batch file
                _batch_file.close()

        # create the master batch file
        LOGGER.debug('creating master batch file')
        # store in self for use in run method
        self.master_batch_filepath = os.path.join(_batch_path,
                                                  self.model_run_title + '.bat')

        # open the master batch file
        with open(self.master_batch_filepath, 'w') as _master_batch_file:

            # loop through every file in the _batch_path directory
            for _file in os.listdir(_batch_path):

                # add all batch files to the master batch file except for
                # the master batch file itself
                if _file.endswith('.bat') & ~_file.startswith(
                        self.model_run_title):
                    # get the complete filepath to the batch file
                    kvals['batch_filename'] = os.path.join(_batch_path, _file)

                    # write the batch file's line to the master bach file
                    _master_batch_file.writelines("""CALL "{batch_filename}"\n""".format(**kvals))

    def postprocess(self):
        """
        Contains all postprocessing functions for NONROAD raw output
        :return: dataframe of postprocessed nonroad emissions
        """

        # create empty data frame to store the raw nonroad output
        _nr_out = pd.DataFrame()

        # loop through list of nonroad files
        for i in np.arange(self.nr_files.shape[0]):

            # create complete filepath to nonroad .out file
            _nr_out_file = os.path.join(self.project_path, 'OUT',
                                        self.nr_files.out_opt_dir_names.iloc[i],
                                        self.nr_files.state_abbreviation.iloc[i] +
                                        '.out')

            # check if the .out file exists - if so, read in the data
            if os.path.isfile(_nr_out_file):
                # header specifies the file row that contains column names
                # rows above the header are not read in
                # usecols identifies the columns that are read in
                # names gives names to the columns that are read in - the raw
                # column names have whitespaces so it's easier to define new
                #  names
                _to_append = pd.read_csv(_nr_out_file,
                                           sep=',', header=9,
                                           usecols=[0, 5, 6,
                                                    7, 8, 9, 10, 19],
                                           names=['fips', 'thc', 'co',
                                                  'nox', 'co2', 'so2', 'pm', 'fuel'],
                                           dtype={'fips': np.str,
                                                  'thc': np.float,
                                                  'co': np.float,
                                                  'nox': np.float,
                                                  'co2': np.float,
                                                  'so2': np.float,
                                                  'pm': np.float,
                                                  'fuel': np.float})

                # add some id variable columns
                _to_append['feedstock'] = self.nr_files.feedstock.iloc[i]
                _to_append['tillage_type'] = self.nr_files.tillage_type.iloc[i]
                _to_append['activity'] = self.nr_files.activity.iloc[i]

                # append the results of this nonroad run to the full nonroad
                #  output dataframe
                _nr_out = _nr_out.append(_to_append, ignore_index=True)

        # calculate voc emissions in (short) tons
        _nr_out['voc'] = _nr_out.thc * self.diesel_thc_voc_conversion

        # nh3 emissions are calculated as grams and converted to short tons
        # to match the rest of the emissions
        _nr_out['nh3'] = _nr_out.fuel * self.diesel_lhv * self.diesel_nh3_ef \
                         * self.conversion_factors['gram']['ton']

        # pm calculated by nonroad is pm10 - rename for clarity
        _nr_out.rename(index=str, columns={'pm': 'pm10'}, inplace=True)

        # calculate pm25 from pm10
        _nr_out['pm25'] = _nr_out.pm10 * self.diesel_pm10topm25

        # remove columns that are no longer needed
        del _nr_out['thc'], _nr_out['fuel']

        # sum emissions over different equipment types or different horsepowers
        _nr_out = _nr_out.groupby(['feedstock', 'fips',
                                   'tillage_type', 'activity'],
                                  as_index=False).sum()

        # use the nonroad fips-region map to get back to region_production
        _nr_out = _nr_out.merge(self.region_fips_map, how='inner',
                                on='fips')

        # rename region column from region-fips map to region_production
        _nr_out.rename(index=str, columns={'region': 'region_production'},
                       inplace=True)

        # melt the nonroad output to put pollutant names in one column and
        # pollutant amounts in a second column
        _nr_out_melted = _nr_out.melt(id_vars=['feedstock',
                                               'region_production',
                                               'tillage_type',
                                               'activity'],
                                      value_vars=['co', 'nox', 'co2', 'so2', 'pm10',
                                                  'pm25', 'voc', 'nh3'],
                                      var_name='pollutant',
                                      value_name='pollutant_amount')

        # nonroad emissions are calculated in short tons; convert to pounds
        _nr_out_melted['pollutant_amount'] = _nr_out_melted['pollutant_amount'] * \
                                             self.conversion_factors['ton']['pound']

        # add module column
        _nr_out_melted['module'] = 'nonroad'

        return _nr_out_melted

    def run(self):
        """
        Calls all methods to setup and runs NONROAD.

        :return:
        """

        LOGGER.info('creating NONROAD population files')
        self.create_population_files()  # @TODO: add logger output

        LOGGER.info('creating NONROAD allocation files')
        self.create_allocate_files()  # @TODO: add logger output

        LOGGER.info('creating NONROAD option files')
        self.create_options_files()  # @TODO: add logger output

        LOGGER.info('creating NONROAD batch files')
        self.create_batch_files()  # @TODO: add logger output

        # use Popen to run the master batch file
        LOGGER.info('executing NONROAD')
        p = Popen(self.master_batch_filepath)
        p.wait()

        _results = None
        _status = self.status
        _e = None

        try:
            LOGGER.info('calculating emissions')
            _results = self.postprocess()
        except Exception as e:
            _e = e
            LOGGER.exception(_e)
            _status = 'failed'
        else:
            _status = 'complete'
        finally:
            self.status = _status
            self.results = _results
            LOGGER.info('NONROAD complete: %s' % self.status)
            if _e:
                raise _e

    def __enter__(self):

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):

        # close connection to MOVES database
        self._conn.close()

        # process exceptions
        if exc_type is not None:
            LOGGER.exception('%s\n%s\n%s' % (exc_type, exc_val, exc_tb))
            return False
        else:
            return self
