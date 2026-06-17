"""Abstract base class for emission-factor providers."""

import abc
import pandas as pd


class EmissionFactorProvider(abc.ABC):
    """Interface that any emission-rate source must satisfy.

    A provider converts a table of input *records* (carrying region keys,
    resource amounts, and any additional context columns) into a table of
    emission rates.

    The returned DataFrame must have exactly these columns:

    ============= ======================================================
    Column        Description
    ============= ======================================================
    region        Region key (str or NaN for national default).
    resource      Resource name (e.g. ``nitrogen``).
    resource_sub  Resource subtype (e.g. ``anhydrous ammonia``).
    activity      Activity name (e.g. ``chemical application``).
    pollutant     Pollutant name (e.g. ``nh3``, ``voc``).
    rate          Emission rate in lb pollutant / lb resource (float ≥ 0).
    unit_num      Unit numerator label (always ``pound`` for now).
    unit_den      Unit denominator label (always ``pound`` for now).
    ============= ======================================================

    Providers MAY consume additional columns on *records* (e.g. temperature,
    wind speed, soil type) to compute dynamic rates.  They MUST return one row
    per (region, resource, resource_subtype, activity, pollutant) combination
    for which they can provide a rate.

    Parameters
    ----------
    records : pd.DataFrame
        Input records.  At minimum contains ``region``, ``resource``, and any
        geophysical context columns the provider needs.

    Returns
    -------
    pd.DataFrame
        Rate table with the columns listed above.
    """

    RATE_COLUMNS = ('region', 'resource', 'resource_subtype', 'activity',
                    'pollutant', 'rate', 'unit_numerator', 'unit_denominator')

    @abc.abstractmethod
    def factors(self, records: pd.DataFrame) -> pd.DataFrame:
        """Return emission rates for the given input records."""

    def validate_output(self, df: pd.DataFrame) -> None:
        """Raise ValueError if the output is missing required columns."""
        missing = set(self.RATE_COLUMNS) - set(df.columns)
        if missing:
            raise ValueError(
                '%s.factors() output is missing required columns: %s'
                % (type(self).__name__, sorted(missing))
            )
