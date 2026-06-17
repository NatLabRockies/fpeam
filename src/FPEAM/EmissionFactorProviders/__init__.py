"""
EmissionFactorProviders — pluggable emission-rate providers.

Each provider implements the EmissionFactorProvider ABC which accepts a DataFrame
of input records (carrying region keys, resource amounts, and optional geophysical
context columns) and returns emission rates per (region, resource, resource_subtype,
activity, pollutant).

Built-in providers
------------------
TableProvider
    Wraps the existing static CSV-based path so the current EmissionFactors
    module behaviour is unchanged when no explicit provider is configured.

Usage
-----
Import the ABC and built-in providers from here::

    from FPEAM.EmissionFactorProviders import EmissionFactorProvider, TableProvider

Third-party providers should subclass EmissionFactorProvider and implement
``factors(records)``.
"""

from .base import EmissionFactorProvider
from .table import TableProvider
from .ammonia import AmmoniaFertilizerProvider

__all__ = ['EmissionFactorProvider', 'TableProvider', 'AmmoniaFertilizerProvider']
