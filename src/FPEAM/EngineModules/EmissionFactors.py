from .Module import Module
from .. import utils
from ..Data import (EmissionFactor, ResourceDistribution, GeophysicalContext)
from ..EmissionFactorProviders import EmissionFactorProvider, TableProvider

import pandas as pd

LOGGER = utils.logger(name=__name__)

_BUILTIN_PROVIDERS = {
    'table': None,  # resolved lazily below to avoid circular import at module level
    'ammonia_fertilizer': 'FPEAM.EmissionFactorProviders.ammonia.AmmoniaFertilizerProvider',
}


def _resolve_provider(name: str):
    """Return the provider class for a given name or dotted import path."""
    dotted = _BUILTIN_PROVIDERS.get(name, name)
    if dotted is None:
        return None  # 'table' sentinel — use TableProvider
    parts = dotted.rsplit('.', 1)
    import importlib
    mod = importlib.import_module(parts[0])
    return getattr(mod, parts[1])


class EmissionFactors(Module):
    """Calculates pollutants from static (optionally region-keyed) emission factors.

    If the emission_factors CSV contains a ``region`` column, the module uses
    region-specific rates for matching counties and falls back to national rows
    (where ``region`` is blank/NaN) for counties that have no regional override.
    When no ``region`` column is present the behavior is identical to prior versions.
    """

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

        # Check that emission factor units are the expected lb/lb contract.
        _unexpected_units = self.emission_factors[
            (self.emission_factors['unit_numerator'].str.lower() != 'pound') |
            (self.emission_factors['unit_denominator'].str.lower() != 'pound')
        ]
        if not _unexpected_units.empty:
            LOGGER.warning(
                'EmissionFactors assumes lb_pollutant/lb_resource units but '
                '%d rows have different units: %s',
                len(_unexpected_units),
                _unexpected_units[['resource', 'resource_subtype',
                                   'unit_numerator', 'unit_denominator']].to_dict('records'),
            )

        # Resource subtype distribution, Units: unit-less fraction
        self.resource_distribution = ResourceDistribution(fpath=self.config.get('resource_distribution'),
                                                          backfill=backfill)

        # Selector for the crop amount that scales emission factors
        self.feedstock_measure_type = self.config.get('feedstock_measure_type')

        # Detect whether region-keyed factors are present
        self._has_region_factors = 'region' in self.emission_factors.columns

        # merge emissions factors and resource subtype distribution
        _factors_merge = self.resource_distribution.merge(self.emission_factors,
                                                          on=['resource', 'resource_subtype'])

        _factors_merge = _factors_merge.assign(
            overall_rate=_factors_merge['distribution'] * _factors_merge['rate']
        )

        # group columns depend on whether a region dimension is present
        _group_cols = ['feedstock', 'activity', 'resource', 'resource_subtype', 'pollutant']
        if self._has_region_factors:
            _group_cols.append('region')

        self.overall_factors = _factors_merge.groupby(_group_cols, as_index=False,
                                                       dropna=False).sum()

        if self._has_region_factors:
            LOGGER.info('EmissionFactors loaded with region-keyed factors; '
                        'national rows (region=NaN) will be used as fallback.')

        # Load optional geophysical context and configure provider
        _provider_name = (self.config.get('provider') or 'table').strip()
        _context_path = (self.config.get('geophysical_context') or '').strip()
        _params_path = (self.config.get('provider_params') or '').strip()

        self._geophysical_context = None
        if _context_path:
            self._geophysical_context = GeophysicalContext(fpath=_context_path, backfill=False)

        if _provider_name == 'table':
            self._provider = TableProvider(self.overall_factors)
        else:
            _provider_cls = _resolve_provider(_provider_name)
            if _provider_cls is None:
                LOGGER.warning('Unknown provider "%s"; falling back to TableProvider.', _provider_name)
                self._provider = TableProvider(self.overall_factors)
            else:
                self._provider = _provider_cls(params=_params_path if _params_path else None)
                LOGGER.info('EmissionFactors using dynamic provider: %s', _provider_name)
                raise NotImplementedError(
                    'Dynamic provider "%s" is configured but the provider → '
                    'get_emissions() wiring is not yet complete.  '
                    'The geophysical context must be joined onto the '
                    'production×equipment records before passing to '
                    'provider.factors().  Remove this error when that wiring '
                    'is implemented.' % _provider_name
                )

    def get_emissions(self):
        """
        Calculate all emissions. When region-keyed factors are loaded, region-specific
        rates take precedence and national rates cover any remaining regions.

        :return: [DataFrame] pollutant amounts
        """

        _idx = ['feedstock', 'tillage_type', 'equipment_group']
        _prod_columns = _idx + ['region_production', 'region_destination', 'feedstock_amount']
        _equip_columns = _idx + ['rate', 'resource']
        _factors_columns = ['feedstock', 'activity', 'resource',
                            'resource_subtype', 'overall_rate', 'pollutant']

        _prod_rows = self.production.feedstock_measure == self.feedstock_measure_type

        # base merged frame: production × equipment
        _base = (self.production[_prod_rows][_prod_columns]
                 .merge(self.equipment[_equip_columns], on=_idx, suffixes=['_prod', '_equip']))

        if self._has_region_factors:
            _regional_cols = _factors_columns + ['region']

            # rows with a non-null region value
            _regional_factors = self.overall_factors[
                self.overall_factors['region'].notna()
            ][_regional_cols].copy()

            # rows without a region value (national defaults)
            _national_factors = self.overall_factors[
                self.overall_factors['region'].isna()
            ][_factors_columns]

            # apply regional factors (inner join on region_production == region)
            _df_regional = _base.merge(
                _regional_factors,
                left_on=['feedstock', 'resource', 'region_production'],
                right_on=['feedstock', 'resource', 'region'],
            )
            _df_regional = _df_regional.drop(columns=['region'])

            # apply national factors only to (feedstock, resource, region_production)
            # combinations NOT covered by a regional override.
            # IMPORTANT: use a (feedstock, resource, region_production) triplet as
            # the "covered" key.  Using region alone is wrong — a region that has an
            # override for nitrogen but not for herbicide would lose its national
            # herbicide factors if we only checked region membership.
            _covered_keys = _df_regional[['feedstock', 'resource', 'region_production']]\
                .drop_duplicates()
            _base_national = _base.merge(
                _covered_keys,
                on=['feedstock', 'resource', 'region_production'],
                how='left',
                indicator=True,
            )
            _base_national = _base_national[
                _base_national['_merge'] == 'left_only'
            ].drop(columns=['_merge'])

            _df_national = _base_national.merge(_national_factors, on=['feedstock', 'resource'])

            _df = pd.concat([_df_regional, _df_national], ignore_index=True, sort=False)
        else:
            _df = _base.merge(self.overall_factors[_factors_columns], on=['feedstock', 'resource'])

        _df = _df.assign(pollutant_amount=_df['overall_rate'] * _df['feedstock_amount'] * _df['rate'])
        _df['module'] = 'emission factors'

        _df = _df[['region_production', 'region_destination', 'feedstock',
                   'tillage_type', 'module', 'activity', 'resource',
                   'resource_subtype', 'pollutant', 'pollutant_amount']]

        return _df

    def run(self):
        """Execute all calculations."""

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
