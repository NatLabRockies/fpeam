import pandas as pd

from . import utils
from .IO import load

LOGGER = utils.logger(name=__name__)


class Data(pd.DataFrame):
    """
    FPEAM data representation.
    """

    COLUMNS = []

    INDEX_COLUMNS = []

    def __init__(self, df=None, fpath=None, columns=None, backfill=True):

        if df is not None:
            _df = pd.DataFrame(df)
        elif fpath is not None:
            _df = load(fpath=fpath, columns=columns)
        else:
            _df = pd.DataFrame({})

        super(Data, self).__init__(data=_df)

        self.source = fpath or 'DataFrame'

        # Only enforce validation when the caller supplied data; empty
        # default construction is allowed for subclassing/composition.
        if df is not None or fpath is not None:
            if not self.validate():
                raise RuntimeError(
                    '{cls} failed validation (source={src})'.format(
                        cls=type(self).__name__, src=self.source,
                    )
                )

        if backfill:
            for _column in self.COLUMNS:
                if _column['backfill'] is not None:
                    self.backfill(column=_column['name'], value=_column['backfill'])

    def backfill(self, column, value=0):
        """
        Replace NaNs in <column> with <value>.

        :param column: [string]
        :param value: [any]
        :return:
        """

        _dataset = str(type(self)).split("'")[1]

        _backfilled = False

        # if any values are missing,
        if self[column].isna().any():
            # count the missing values
            _count_missing = sum(self[column].isna())
            # count the total values
            _count_total = self[column].__len__()

            # fill the missing values
            self[column] = self[column].fillna(value)

            # log a warning with the number of missing values
            LOGGER.warning('%s of %s data values in %s.%s were backfilled as %s' %
                           (_count_missing, _count_total, _dataset,
                            column, value))

            _backfilled = True

        else:
            # log if no values are missing
            LOGGER.debug('no missing data values in %s.%s' % (_dataset, column))

        return _backfilled

    def summarize(self):
        # @TODO: add summarization methods
        raise NotImplementedError

    def validate(self):

        # @TODO: add validation methods
        _name = type(self).__name__

        _valid = True

        LOGGER.debug('validating %s' % (_name, ))

        if self.empty:
            LOGGER.warning('no data provided for %s' % (_name, ))
            _valid = False

        LOGGER.debug('validated %s' % (_name, ))

        return _valid

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # process exceptions
        if exc_type is not None:
            LOGGER.exception('%s\n%s\n%s' % (exc_type, exc_val, exc_tb))
            return False
        else:
            return self


class Equipment(Data):

    COLUMNS = ({'name': 'feedstock', 'type': str, 'index': True, 'backfill': None},
               {'name': 'tillage_type', 'type': str, 'index': True, 'backfill': None},
               {'name': 'equipment_group', 'type': str, 'index': True, 'backfill': None},
               {'name': 'rotation_year', 'type': int, 'index': True, 'backfill': None},
               {'name': 'activity', 'type': str, 'index': True, 'backfill': None},
               {'name': 'equipment_name', 'type': str, 'index': True, 'backfill': None},
               {'name': 'equipment_horsepower', 'type': float, 'index': True, 'backfill': None},
               {'name': 'resource', 'type': str, 'index': True, 'backfill': None},
               {'name': 'rate', 'type': float, 'index': False, 'backfill': 0},
               {'name': 'unit_numerator', 'type': str, 'index': True, 'backfill': None},
               {'name': 'unit_denominator', 'type': str, 'index': True, 'backfill': None})

    def __init__(self, df=None, fpath=None,
                 columns={d['name']: d['type'] for d in COLUMNS for k in d.keys()},
                 backfill=True):
        super(Equipment, self).__init__(df=df, fpath=fpath, columns=columns, backfill=backfill)


class Production(Data):

    COLUMNS = ({'name': 'feedstock', 'type': str, 'index': True, 'backfill': None},
               {'name': 'tillage_type', 'type': str, 'index': True, 'backfill': None},
               {'name': 'region_production', 'type': str, 'index': True, 'backfill': None},
               {'name': 'region_destination', 'type': str, 'index': True, 'backfill': None},
               {'name': 'equipment_group', 'type': str, 'index': True, 'backfill': None},
               {'name': 'feedstock_measure', 'type': str, 'index': True, 'backfill': None},
               {'name': 'feedstock_amount', 'type': float, 'index': False, 'backfill': 0},
               {'name': 'unit_numerator', 'type': str, 'index': True, 'backfill': None},
               {'name': 'unit_denominator', 'type': str, 'index': True, 'backfill': None},
               {'name': 'source_lon', 'type': float, 'index': False, 'backfill': None},
               {'name': 'source_lat', 'type': float, 'index': False, 'backfill': None},
               {'name': 'destination_lon', 'type': float, 'index': False, 'backfill': None},
               {'name': 'destination_lat', 'type': float, 'index': False, 'backfill': None})

    def __init__(self, df=None, fpath=None,
                 columns={d['name']: d['type'] for d in COLUMNS for k in d.keys()},
                 backfill=True):
        super(Production, self).__init__(df=df, fpath=fpath, columns=columns, backfill=backfill)

    # @todo validate: feedstock, region_production, feedstock_measure missing values trigger runtime error


class FeedstockLossFactors(Data):

    COLUMNS = ({'name': 'feedstock', 'type': str, 'index': True, 'backfill': None},
               {'name': 'supply_chain_stage', 'type': str, 'index': True, 'backfill': None},
               {'name': 'dry_matter_loss', 'type': float, 'index': False, 'backfill': 0},)

    def __init__(self, df=None, fpath=None,
                 columns={d['name']: d['type'] for d in COLUMNS for k in d.keys()},
                 backfill=True):
        super(FeedstockLossFactors, self).__init__(df=df, fpath=fpath, columns=columns,
                                                   backfill=backfill)

    # @todo validate: feedstock or supply_chain_stage missing values trigger runtime error


class ResourceDistribution(Data):

    COLUMNS = ({'name': 'feedstock', 'type': str, 'index': True, 'backfill': None},
               {'name': 'resource', 'type': str, 'index': True, 'backfill': None},
               {'name': 'resource_subtype', 'type': str, 'index': True, 'backfill': None},
               {'name': 'distribution', 'type': float, 'index': True, 'backfill': 0})

    def __init__(self, df=None, fpath=None,
                 columns={d['name']: d['type'] for d in COLUMNS for k in d.keys()},
                 backfill=True):
        super(ResourceDistribution, self).__init__(df=df, fpath=fpath, columns=columns,
                                                   backfill=backfill)

    # @todo validate: distribution column values sum to one within unique feedstock-resource combos
    # @todo validate: resource and resource_subtype values match those in EmissionFactor


class EmissionFactor(Data):
    COLUMNS = ({'name': 'resource', 'type': str, 'index': True, 'backfill': None},
               {'name': 'resource_subtype', 'type': str, 'index': True, 'backfill': None},
               {'name': 'activity', 'type': str, 'index': True, 'backfill': None},
               {'name': 'pollutant', 'type': str, 'index': True, 'backfill': None},
               {'name': 'rate', 'type': float, 'index': False, 'backfill': 0},
               {'name': 'unit_numerator', 'type': str, 'index': True, 'backfill': None},
               {'name': 'unit_denominator', 'type': str, 'index': True, 'backfill': None},)

    def __init__(self, df=None, fpath=None,
                 columns={d['name']: d['type'] for d in COLUMNS for k in d.keys()},
                 backfill=True):
        # If loading from file, include 'region' when the CSV has that column
        # so region-keyed factors are carried through unchanged.
        if fpath is not None and 'region' not in columns:
            import pandas as _pd
            _header = _pd.read_csv(fpath, nrows=0).columns.tolist()
            if 'region' in _header:
                columns = dict(columns)
                columns['region'] = str
        super(EmissionFactor, self).__init__(df=df, fpath=fpath, columns=columns,
                                             backfill=backfill)

    # @todo validate: resource, resource_subtype values match those in ResourceDistribution


class FugitiveDustFactors(Data):

    COLUMNS = ({'name': 'feedstock', 'type': str, 'index': True, 'backfill': None},
               {'name': 'tillage_type', 'type': str, 'index': True, 'backfill': None},
               {'name': 'pollutant', 'type': str, 'index': True, 'backfill': None},
               {'name': 'rate', 'type': float, 'index': False, 'backfill': 0},
               {'name': 'unit_numerator', 'type': str, 'index': True, 'backfill': None},
               {'name': 'unit_denominator', 'type': str, 'index': True, 'backfill': None})

    def __init__(self, df=None, fpath=None,
                 columns={d['name']: d['type'] for d in COLUMNS for k in d.keys()},
                 backfill=True):
        super(FugitiveDustFactors, self).__init__(df=df, fpath=fpath,
                                                  columns=columns,
                                                  backfill=backfill)

    # @todo validate: missing feedstock, pollutant generate error

class SiltContent(Data):

    COLUMNS = ({'name': 'st_name', 'type': str, 'index': True, 'backfill': None},
               {'name': 'st_fips', 'type': str, 'index': True, 'backfill': None},
               {'name': 'uprsm_pct_silt', 'type': float, 'index': True, 'backfill': None})

    def __init__(self, df=None, fpath=None,
                 columns={d['name']: d['type'] for d in COLUMNS for k in d.keys()},
                 backfill=True):
        super(SiltContent, self).__init__(df=df, fpath=fpath, columns=columns, backfill=backfill)

    # @todo validate: missing st_fips values generate error

class FugitiveDustOnroadConstants(Data):

    COLUMNS = ({'name': 'constant', 'type': str, 'index': True, 'backfill': None},
               {'name': 'description', 'type': str, 'index': True, 'backfill': None},
               {'name': 'road_type', 'type': str, 'index': True, 'backfill': None},
               {'name': 'pollutant', 'type': str, 'index': True, 'backfill': None},
               {'name': 'value', 'type': float, 'index': False, 'backfill': 0},
               {'name': 'unit_numerator', 'type': str, 'index': True, 'backfill': None},
               {'name': 'unit_denominator', 'type': str, 'index': True, 'backfill': None})

    def __init__(self, df=None, fpath=None,
                 columns={d['name']: d['type'] for d in COLUMNS for k in d.keys()},
                 backfill=True):
        super(FugitiveDustOnroadConstants, self).__init__(df=df, fpath=fpath, columns=columns, backfill=backfill)

    # @todo validate: missing constant, road_type, pollutant generate error

class SCCCodes(Data):

    COLUMNS = ({'name': 'resource_subtype', 'type': str, 'index': True, 'backfill': None},
               {'name': 'scc', 'type': str, 'index': False, 'backfill': None})

    def __init__(self, df=None, fpath=None,
                 columns={d['name']: d['type'] for d in COLUMNS for k in d.keys()},
                 backfill=True):
        super(SCCCodes, self).__init__(df=df, fpath=fpath, columns=columns, backfill=backfill)

    # @todo validate: any missing values generate error
    # @todo validate: resource_subtypes match those in ResourceDistribution, EmissionFactor


class NONROADEquipment(Data):

    COLUMNS = ({'name': 'equipment_name', 'type': str, 'index': True, 'backfill': None},
               {'name': 'equipment_description', 'type': str, 'index': False, 'backfill': None},
               {'name': 'nonroad_equipment_scc', 'type': str, 'index': False, 'backfill': None})

    def __init__(self, df=None, fpath=None,
                 columns={d['name']: d['type'] for d in COLUMNS for k in d.keys()},
                 backfill=True):
        super(NONROADEquipment, self).__init__(df=df, fpath=fpath, columns=columns,
                                               backfill=backfill)

    # @todo validate: equipment_name values match those in Equipment
    # @todo validate: any missing SCC codes for provided equipment_name generates error


class Irrigation(Data):

    COLUMNS = ({'name': 'feedstock', 'type': str, 'index': True, 'backfill': None},
               {'name': 'state_fips', 'type': str, 'index': True, 'backfill': None},
               {'name': 'activity', 'type': str, 'index': True, 'backfill': None},
               {'name': 'equipment_name', 'type': str, 'index': True, 'backfill': None},
               {'name': 'equipment_horsepower', 'type': float, 'index': True, 'backfill': None},
               {'name': 'irrigation_water_source', 'type': str, 'index': True, 'backfill': None},
               {'name': 'acreage_fraction', 'type': float, 'index': False, 'backfill': 0},
               {'name': 'resource', 'type': str, 'index': True, 'backfill': None},
               {'name': 'rate', 'type': float, 'index': False, 'backfill': 0},
               {'name': 'unit_numerator', 'type': str, 'index': True, 'backfill': None},
               {'name': 'unit_denominator', 'type': str, 'index': True, 'backfill': None})

    def __init__(self, df=None, fpath=None,
                 columns={d['name']: d['type'] for d in COLUMNS for k in d.keys()},
                 backfill=True):
        super(Irrigation, self).__init__(df=df, fpath=fpath, columns=columns, backfill=backfill)

    # @todo validate: missing equipment_horsepower values triggers error


class TransportationGraph(Data):

    COLUMNS = ({'name': 'edge_id', 'type': int, 'index': True, 'backfill': None},
               {'name': 'statefp', 'type': str, 'index': False, 'backfill': None},
               {'name': 'countyfp', 'type': str, 'index': False, 'backfill': None},
               {'name': 'u_of_edge', 'type': int, 'index': False, 'backfill': None},
               {'name': 'v_of_edge', 'type': int, 'index': False, 'backfill': None},
               {'name': 'weight', 'type': float, 'index': False, 'backfill': None},
               {'name': 'fclass', 'type': int, 'index': False, 'backfill': None})

    def __init__(self, df=None, fpath=None,
                 columns={d['name']: d['type'] for d in COLUMNS for k in d.keys()},
                 backfill=True):
        super(TransportationGraph, self).__init__(df=df, fpath=fpath, columns=columns,
                                                  backfill=backfill)


class TransportationNodeLocations(Data):

    COLUMNS = ({'name': 'node_id', 'type': int, 'index': True, 'backfill': None},
               {'name': 'x', 'type': float, 'index': False, 'backfill': None},
               {'name': 'y', 'type': float, 'index': False, 'backfill': None})

    def __init__(self, df=None, fpath=None,
                 columns={d['name']: d['type'] for d in COLUMNS for k in d.keys()},
                 backfill=True):
        super(TransportationNodeLocations, self).__init__(df=df, fpath=fpath, columns=columns,
                                                          backfill=backfill)


class RegionFipsMap(Data):

    COLUMNS = ({'name': 'region', 'type': str, 'index': True, 'backfill': None},
               {'name': 'fips', 'type': str, 'index': True, 'backfill': None})

    def __init__(self, df=None, fpath=None,
                 columns={d['name']: d['type'] for d in COLUMNS for k in d.keys()},
                 backfill=True):
        super(RegionFipsMap, self).__init__(df=df, fpath=fpath, columns=columns, backfill=backfill)

    def validate(self):
        try:
            assert self.region.nunique() == self.fips.nunique()
        except AssertionError:
            _region_counts = self.region.value_counts()
            _dup_regions = list(_region_counts.loc[_region_counts != 1].index)
            if _dup_regions:
                LOGGER.error('Duplicated region values in region_fips_map data: %s' % _dup_regions)

            _fips_counts = self.fips.value_counts()
            _dup_fips = list(_fips_counts.loc[_fips_counts != 1].index)
            if _dup_fips:
                LOGGER.error('Duplicated FIPS values in region_fips_map data: %s' % _dup_fips)
            raise ValueError('region_fips_map data must have only 1 '
                             'FIPS per region and 1 region per FIPS')
        else:
            return True


class StateFipsMap(Data):

    COLUMNS = ({'name': 'state_abbreviation', 'type': str, 'index': True, 'backfill': None},
               {'name': 'state_fips', 'type': str, 'index': False, 'backfill': None})

    def __init__(self, df=None, fpath=None,
                 columns={d['name']: d['type'] for d in COLUMNS for k in d.keys()},
                 backfill=True):
        super(StateFipsMap, self).__init__(df=df, fpath=fpath, columns=columns, backfill=backfill)


class TruckCapacity(Data):

    COLUMNS = ({'name': 'feedstock', 'type': str, 'index': True, 'backfill': None},
               {'name': 'truck_capacity', 'type': float, 'index': False, 'backfill': None},
               {'name': 'unit_numerator', 'type': str, 'index': True, 'backfill': None},
               {'name': 'unit_denominator', 'type': str, 'index': True, 'backfill': None})

    def __init__(self, df=None, fpath=None,
                 columns={d['name']: d['type'] for d in COLUMNS for k in d.keys()},
                 backfill=True):
        super(TruckCapacity, self).__init__(df=df, fpath=fpath, columns=columns, backfill=backfill)


class AVFT(Data):

    COLUMNS = ({'name': 'sourceTypeID', 'type': int, 'index': True, 'backfill': None},
               {'name': 'modelYearID', 'type': int, 'index': True, 'backfill': None},
               {'name': 'fuelTypeID', 'type': int, 'index': True, 'backfill': None},
               {'name': 'engTechID', 'type': int, 'index': True, 'backfill': None},
               {'name': 'fuelEngFraction', 'type': float, 'index': False, 'backfill': None})

    def __init__(self, df=None, fpath=None,
                 columns={d['name']: d['type'] for d in COLUMNS for k in d.keys()},
                 backfill=True):
        super(AVFT, self).__init__(df=df, fpath=fpath, columns=columns, backfill=backfill)

    # @todo validate: any missing values generates error (filling in with zeros or NaNs may break MOVES)


class GeophysicalContext(Data):
    """Geophysical and meteorological context keyed by region and time period.

    Used by dynamic emission-factor providers (e.g. AmmoniaFertilizerProvider)
    that require climate or soil data to compute spatially explicit emission rates.

    All columns except ``region`` are optional; providers declare which ones they
    require.  Load from a CSV with any subset of the columns below::

        region,year,month,temperature_c,wind_speed_m_s,precipitation_mm,soil_type
        17031,2017,6,22.5,3.2,45.0,silty clay loam

    Columns
    -------
    region : str
        Region key that matches ``region_production`` in production data.
    year : int (optional)
        Scenario year.
    month : int (optional)
        Month (1–12).  Omit for annual averages.
    temperature_c : float (optional)
        Mean air temperature in degrees Celsius.
    wind_speed_m_s : float (optional)
        Mean wind speed in m/s at 2 m height.
    precipitation_mm : float (optional)
        Total precipitation in mm over the relevant period.
    soil_type : str (optional)
        USDA soil texture class (e.g. ``silty clay loam``, ``sandy loam``).
    """

    # Only 'region' is strictly required; all other columns are context-dependent.
    COLUMNS = (
        {'name': 'region', 'type': str, 'index': True, 'backfill': None},
    )

    # Optional context columns with their expected types
    OPTIONAL_COLUMNS = {
        'year': int,
        'month': int,
        'temperature_c': float,
        'wind_speed_m_s': float,
        'precipitation_mm': float,
        'soil_type': str,
    }

    def __init__(self, df=None, fpath=None, backfill=False):
        # Detect which optional context columns are present in the source
        columns = {d['name']: d['type'] for d in self.COLUMNS}
        if fpath is not None:
            import pandas as _pd
            _header = _pd.read_csv(fpath, nrows=0).columns.tolist()
            for col, dtype in self.OPTIONAL_COLUMNS.items():
                if col in _header:
                    columns[col] = dtype
        elif df is not None:
            for col, dtype in self.OPTIONAL_COLUMNS.items():
                if col in df.columns:
                    columns[col] = dtype
        super(GeophysicalContext, self).__init__(df=df, fpath=fpath,
                                                 columns=columns, backfill=backfill)

    def validate(self):
        """Require that the 'region' column is present."""
        if 'region' not in self.columns:
            LOGGER.error('GeophysicalContext requires a "region" column')
            return False
        return super().validate()
