# -*- coding: utf-8 -*-
"""
Created on Tue Jan 13 14:11:08 2026

@author: aengstrom
"""
from .base import BaseModel
from .canister import CanisterTypes, PrimaryCanister, CanisterConcentration, SiteCanister
from .site import Site
from .mdl import MDL
from .voc import VOCInfo
from .version import Version

# Define models list
MODELS = [
    Site,
    VOCInfo,
    CanisterTypes,
    PrimaryCanister,
    CanisterConcentration,
    SiteCanister,
    MDL,
    Version
]

# Create registry automatically
MODEL_REGISTRY = {model.__tablename__: model for model in MODELS}

# Expose everything
__all__ = [
    # Base classes and utilities
    "BaseModel",
    
    # Models
    "CanisterTypes",
    "PrimaryCanister",
    "CanisterConcentration",
    "SiteCanister",
    "Site",
    "MDL",
    "VOCInfo",
    "Version",
    
    # Registry
    "MODELS",
    "MODEL_REGISTRY",
]