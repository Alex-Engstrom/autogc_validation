# -*- coding: utf-8 -*-
"""
Created on Fri Jan 16 16:35:59 2026

@author: aengstrom
"""
from typing import Dict, Type
from .canister import CanisterType, PrimaryCanister, CanisterConcentration, SiteCanister
from .site import Site
from .mdl import MDL
from .voc import VOCInfo
from .version import Version

MODEL_LIST: list = [Site, VOCInfo, CanisterType, PrimaryCanister, CanisterConcentration, SiteCanister, MDL, Version]
MODEL_REGISTRY: Dict[str, Type] = {model.__tablename__ : model for model in MODEL_LIST}

