"""Canonical registry of the commodities this API serves.

Derived from the ETL source configs so there's a single source of truth —
adding a series to services/eia.py or services/fred.py exposes it here too.
"""
from services.eia import EIA_SERIES
from services.fred import FRED_SERIES

# name -> unit
COMMODITY_UNITS = {name: cfg[2] for name, cfg in EIA_SERIES.items()}
COMMODITY_UNITS.update({name: cfg[1] for name, cfg in FRED_SERIES.items()})

KNOWN_COMMODITIES = frozenset(COMMODITY_UNITS)


def is_known(commodity: str) -> bool:
    return commodity in KNOWN_COMMODITIES
