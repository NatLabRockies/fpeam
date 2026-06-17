from .Module import Module
from .. import utils
from ..Data import (EmissionFactor, ResourceDistribution)

LOGGER = utils.logger(name=__name__)


class EmissionFactors(Module):
    """Base class to manage execution of pollutants calculated from emission factors"""

    def __init__(self, config, equipment, production, backfill=True, **kvals):
        """
        :param config [ConfigObj] configuration options
        :param equipment: [DataFrame] equipment group
        :param production: [DataFrame] production values
        :param backfill: [boolean] backfill missing data values with 0
        """

        # init parent
        super(EmissionFactors, self).__init__(config=config)

        # init properties
        self.equipment = equipment
        self.production = production

        # Emissions factors, Units: lb pollutant/lb resource
        self.emission_factors = EmissionFactor(fpath=self.config.get('emission_factors'),
                                               backfill=backfill)

        # Resource subtype distribution, Units: unit-less fraction
        self.resource_distribution = ResourceDistribution(fpath=self.config.get('resource_distribution'),
                                                          backfill=backfill)

        # Selector for the crop amount that scales emission factors
        self.feedstock_measure_type = self.config.get('feedstock_measure_type')

        # merge emissions factors and resource subtype distribution
        # dataframes by matching resource and resource subtype
        _factors_merge = self.resource_distribution.merge(self.emission_factors,
                                                          on=['resource', 'resource_subtype'])

        # calculate overall rate as the product of the resource subtype
        # distributions and the subtype-specific emission factors
        _factors_merge.eval('overall_rate = distribution * rate', inplace=True)

        # sum emissions factors within unique combinations of
        # feedstock-activity-resource-pollutant to generate overall factors
        # that will convert resource mass to pollutant mass
        self.overall_factors = _factors_merge.groupby(['feedstock',
                                                       'activity',
                                                       'resource',
                                                       'resource_subtype',
                                                       'pollutant'],
                                                      as_index=False).sum()

    def get_emissions(self):
        """
        Calculate all emissions from <resource> for which a subtype
        distribution and emissions factors are provided.

        :return: [DataFrame] pollutant amounts
        """

        # create column selectors
        _idx = ['feedstock', 'tillage_type', 'equipment_group']
        _prod_columns = _idx + ['region_production',
                                'region_destination',
                                'feedstock_amount']
        _equip_columns = _idx + ['rate', 'resource']
        _factors_columns = ['feedstock', 'activity', 'resource',
                            'resource_subtype', 'overall_rate', 'pollutant']

        # create row selectors
        _prod_rows = self.production.feedstock_measure == self.feedstock_measure_type

        # combine production and equipment and overall factors
        _df = self.production[_prod_rows][_prod_columns].merge(self.equipment[_equip_columns],
                                                               on=_idx,
                                                               suffixes=['_prod', '_equip'])\
            .merge(self.overall_factors[_factors_columns], on=['feedstock', 'resource'])

        # calculate emissions
        _df.eval('pollutant_amount = overall_rate * feedstock_amount * rate',
                 inplace=True)

        # add column to identify the module
        _df['module'] = 'emission factors'

        # clean up DataFrame
        _df = _df[['region_production', 'region_destination', 'feedstock',
                   'tillage_type', 'module', 'activity', 'resource',
                   'resource_subtype', 'pollutant',
                   'pollutant_amount']]

        return _df

    def run(self):
        """
        Execute all calculations.

        :return:
        """

        _results = None
        _status = self.status
        _e = None

        try:
            _results = self.get_emissions()
        except Exception as e:
            _e = e
            LOGGER.exception(_e)
            _status = 'failed'
        else:
            _status = 'complete'
        finally:
            self.status = _status
            self.results = _results
            if _e:
                raise _e

    def summarize(self):
        pass
