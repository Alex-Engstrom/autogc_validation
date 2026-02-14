# -*- coding: utf-8 -*-
"""
Created on Fri Jan 23 12:00:54 2026

@author: aengstrom
"""

from .canister_type import CanisterType
from .column_type import ColumnType
from .concentration_unit import ConcentrationUnit
from .priority import Priority
from .voc_category import VOCCategory
from .compound_code import CompoundAQSCode
from .compound_name import CompoundName

def aqs_to_name(code: int) -> str:
    """Convert an AQS code integer to a compound name string."""
    return CompoundName[CompoundAQSCode(code).name].value


def name_to_aqs(name: str) -> int:
    """Convert a compound name string to an AQS code integer."""
    return CompoundAQSCode[CompoundName(name).name].value


__all__ = ["CanisterType",
           "ColumnType",
           "ConcentrationUnit",
           "Priority",
           "VOCCategory",
           "CompoundAQSCode",
           "CompoundName",
           "aqs_to_name",
           "name_to_aqs"]