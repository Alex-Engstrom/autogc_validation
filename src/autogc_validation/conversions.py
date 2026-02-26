# -*- coding: utf-8 -*-
"""
Concentration unit conversions for VOC data.

Provides functions for converting between ppbV, ppbC, ppmV, and ppmC.

Relationships:
    ppbC = ppbV * carbon_count
    ppmC = ppmV * carbon_count
    ppbV = ppmV * 1000
    ppbC = ppmC * 1000
"""

from autogc_validation.database.enums import ConcentrationUnit, get_carbon_count

_PPB_PPM_FACTOR = 1000


# ---------------------------------------------------------------------------
# Low-level conversions: carbon-based ↔ volume-based
# ---------------------------------------------------------------------------

def ppbc_to_ppbv(value, carbon_count: int):
    """Convert ppbC to ppbV."""
    return value / carbon_count


def ppbv_to_ppbc(value, carbon_count: int):
    """Convert ppbV to ppbC."""
    return value * carbon_count


def ppmc_to_ppmv(value, carbon_count: int):
    """Convert ppmC to ppmV."""
    return value / carbon_count


def ppmv_to_ppmc(value, carbon_count: int):
    """Convert ppmV to ppmC."""
    return value * carbon_count


# ---------------------------------------------------------------------------
# Low-level conversions: ppb ↔ ppm
# ---------------------------------------------------------------------------

def ppbv_to_ppmv(value):
    """Convert ppbV to ppmV."""
    return value / _PPB_PPM_FACTOR


def ppmv_to_ppbv(value):
    """Convert ppmV to ppbV."""
    return value * _PPB_PPM_FACTOR


def ppbc_to_ppmc(value):
    """Convert ppbC to ppmC."""
    return value / _PPB_PPM_FACTOR


def ppmc_to_ppbc(value):
    """Convert ppmC to ppbC."""
    return value * _PPB_PPM_FACTOR


# ---------------------------------------------------------------------------
# High-level conversion dispatcher
# ---------------------------------------------------------------------------

def convert(value, aqs_code: int, from_unit: ConcentrationUnit, to_unit: ConcentrationUnit):
    """Convert a concentration value between units for a given compound.

    Looks up the carbon count from the AQS code automatically.

    Args:
        value: Concentration value (scalar, array, or pandas Series).
        aqs_code: AQS parameter code identifying the compound.
        from_unit: Source concentration unit.
        to_unit: Target concentration unit.

    Returns:
        Converted value in the same type as input.

    Raises:
        ValueError: If the AQS code is unknown or the unit pair is invalid.
    """
    if from_unit == to_unit:
        return value

    carbon_count = get_carbon_count(aqs_code)

    _converters = {
        (ConcentrationUnit.PPBC, ConcentrationUnit.PPBV): lambda v: ppbc_to_ppbv(v, carbon_count),
        (ConcentrationUnit.PPBV, ConcentrationUnit.PPBC): lambda v: ppbv_to_ppbc(v, carbon_count),
        (ConcentrationUnit.PPMC, ConcentrationUnit.PPMV): lambda v: ppmc_to_ppmv(v, carbon_count),
        (ConcentrationUnit.PPMV, ConcentrationUnit.PPMC): lambda v: ppmv_to_ppmc(v, carbon_count),
        (ConcentrationUnit.PPBV, ConcentrationUnit.PPMV): ppbv_to_ppmv,
        (ConcentrationUnit.PPMV, ConcentrationUnit.PPBV): ppmv_to_ppbv,
        (ConcentrationUnit.PPBC, ConcentrationUnit.PPMC): ppbc_to_ppmc,
        (ConcentrationUnit.PPMC, ConcentrationUnit.PPBC): ppmc_to_ppbc,
        (ConcentrationUnit.PPBC, ConcentrationUnit.PPMV): lambda v: ppbv_to_ppmv(ppbc_to_ppbv(v, carbon_count)),
        (ConcentrationUnit.PPMV, ConcentrationUnit.PPBC): lambda v: ppbv_to_ppbc(ppmv_to_ppbv(v), carbon_count),
        (ConcentrationUnit.PPBV, ConcentrationUnit.PPMC): lambda v: ppbc_to_ppmc(ppbv_to_ppbc(v, carbon_count)),
        (ConcentrationUnit.PPMC, ConcentrationUnit.PPBV): lambda v: ppbc_to_ppbv(ppmc_to_ppbc(v), carbon_count),
    }

    key = (from_unit, to_unit)
    if key not in _converters:
        raise ValueError(f"Unsupported conversion: {from_unit} -> {to_unit}")

    return _converters[key](value)
